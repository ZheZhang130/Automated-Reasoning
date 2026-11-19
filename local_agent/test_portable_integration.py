"""Opt-in real Docker/official-judge smoke with a fake Ollama, never real inference."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from local_agent import cli
from local_agent.platform_support import REPO, Settings
from local_agent.portable_sanity import fixtures


@unittest.skipUnless(os.environ.get('CSC2108_DOCKER_TESTS') == '1', 'Explicitly opt in after portable prepare')
class DockerIntegration(unittest.TestCase):
    def test_original_agent_loop_public_test_submission_and_separate_judge(self):
        settings = Settings.load('portable')
        settings.initialize()
        expected_digest = cli.read(REPO / 'local_optimization/final_selection.json')['model_digest']
        replies = ["cat > /workspace/solution.py <<'PY'\nimport sys\nprint(sum(map(int, sys.stdin.read().split())))\nPY",
                   'python -I /public/check.py', 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT']
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, value):
                data = json.dumps(value).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self.send({'/api/tags': {'models': [{'name': cli.MODEL, 'digest': expected_digest,
                          'details': {'quantization_level': 'Q4_K_M'}}]},
                          '/api/version': {'version': 'fake-software-control'}, '/api/ps': {'models': []}}[self.path])

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path == '/api/show':
                    self.send({'details': {'family': 'qwen35'}, 'capabilities': ['completion']})
                    return
                if self.path != '/api/chat' or len(calls) >= len(replies):
                    self.send_error(500, 'Unexpected inference/control request')
                    return
                command = replies[len(calls)]
                calls.append(payload)
                self.send({'model': cli.MODEL, 'created_at': '2026-11-18T00:00:00Z', 'done': True,
                           'done_reason': 'stop', 'message': {'role': 'assistant', 'content': '```mswea_bash_command\n' + command + '\n```'},
                           'eval_count': 20, 'prompt_eval_count': 10, 'eval_duration': 1000,
                           'prompt_eval_duration': 1000, 'load_duration': 1000})
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # Retain smoke evidence rather than deleting generated candidates/logs on failures.
            output = Path(tempfile.mkdtemp(prefix='fake-ollama-smoke-', dir=settings.root / 'tmp'))
            bundle = fixtures(output / 'fixture', settings)
            env = os.environ | {'CSC2108_ROOT': str(settings.root), 'CSC2108_VENDOR': str(settings.vendor),
                  'CSC2108_OLLAMA_ENDPOINT': 'http://127.0.0.1:' + str(server.server_port), 'PYTHONDONTWRITEBYTECODE': '1'}
            command = [sys.executable, '-m', 'local_agent', '--backend', 'portable']
            def execute(arguments, name):
                result = subprocess.run(command + arguments, capture_output=True, text=True, encoding='utf-8', env=env, timeout=90)
                (output / (name + '.stdout.log')).write_text(result.stdout, encoding='utf-8')
                (output / (name + '.stderr.log')).write_text(result.stderr, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)
            result = execute(['run', '--task', bundle['public'], '--output', str(output / 'run')], 'agent')
            self.assertEqual(result['status'], 'Submitted')
            record = cli.read(output / 'run/runtime/result.json')
            self.assertEqual((record['actions'], record['action_limit'], record['repair_limit'], record['time_limit_seconds']), (3, 20, 3, 600))
            self.assertEqual(len(record['public_tests']), 1)
            self.assertEqual(record['public_tests'][0]['returncode'], 0)
            self.assertTrue(record['sampler_wire_verified'])
            self.assertEqual(record['format_errors'], 0)
            self.assertTrue(Path(result['trajectory_path']).is_file())
            profile = cli.read(REPO / 'local_eval_v2/profiles.json')[cli.PROFILE]
            expected = profile['sampler'] | {'num_ctx': 16384, 'num_predict': 4096, 'temperature': .2, 'seed': 2108}
            self.assertEqual(len(calls), 3)
            for call in calls:
                self.assertEqual(call['options'], expected)
                self.assertIs(call['think'], False)
            frozen_prompt = cli.read(REPO / 'evidence/local_eval_v2/benchmark_provenance.json')['rendered_system_prompt']
            self.assertEqual(calls[0]['messages'][0]['content'], frozen_prompt)
            judged = execute(['evaluate', '--run', str(output / 'run'), '--private-row', bundle['private_row'],
                              '--output', str(output / 'judge')], 'judge')
            self.assertEqual(judged['status'], 'pass')
            self.assertEqual(len(calls), 3, 'Independent judging must not call the model')
            cli.save(output / 'verification.json', {'status': 'pass', 'real_model_calls': 0, 'fake_requests': 3,
                     'original_prompt_sampler_budgets_preserved': True, 'official_synthetic_evaluation': 'pass'})
            print('Portable fake-Ollama Docker smoke evidence:', output)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
