"""Offline tests: no model, no Docker, no network. Run: python -m unittest guided_agent.test_guided"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from guided_agent import backend, guidance, providers
from guided_agent.common import sha256_text

STATEMENT = '# Sum\n\nRead A and B and print A+B.\n'
PLAN = '## Observations\n1. Addition.\n## Solution sketch\n1. "Addition." Read, add, print.\n'
CONTRACT = ('## Description\nSum.\n## Preconditions\nPRE-1 (Unverified)\n## Postconditions\nPOST-1 (Unverified)\n'
            '## Test suggestions\n- 2 3 -> 5 (POST-1)\n## Unspecified behavior\nNone.\n')


def make_artifact(tmp, kind, text, statement=STATEMENT, task='t'):
    record = guidance.artifact(kind=kind, prompt_id=f'{kind}-v1', statement=statement, text=text, task_id=task,
                               provider='codex-replay', requested_model='gpt-6.2-sol', observed_model=None,
                               reasoning_effort='medium', generation={}, label='test')
    path = Path(tmp) / f'{kind}.json'
    guidance.save_artifact(path, record)
    return path


class GuidanceArtifacts(unittest.TestCase):
    def test_replay_through_teammate_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind, text in (('plan', PLAN), ('contract', CONTRACT)):
                generated, raw = guidance.load_for_run(make_artifact(tmp, kind, text), STATEMENT)
                self.assertEqual(generated['text'], text)
                self.assertEqual(raw['statement_sha256'], sha256_text(STATEMENT))

    def test_wrong_statement_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                guidance.load_for_run(make_artifact(tmp, 'plan', PLAN), STATEMENT + 'x')

    def test_fenced_code_rejected_but_soft_flags_only_recorded(self):
        self.assertTrue(guidance.validate('plan', PLAN + '```python\nprint(1)\n```\n'))
        self.assertTrue(guidance.validate('plan', PLAN + '```\nimport sys\n```\n'))
        self.assertTrue(guidance.validate('plan', PLAN + '```text\n3\n'))
        self.assertEqual(guidance.validate('contract', CONTRACT + '  ```text\n  3\n  0 1 0\n  ```\n'), [])
        self.assertEqual(guidance.validate('plan', PLAN + 'Then print( the sum.\n'), [])
        self.assertTrue(guidance.soft_flags('print(x)'))

    def test_artifacts_are_write_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_artifact(tmp, 'plan', PLAN)
            with self.assertRaises(FileExistsError):
                guidance.save_artifact(path, {})

    def test_plan_and_contract_templates_are_parallel(self):
        for version in guidance.INJECTION.values():
            for template in filter(None, version.values()):
                self.assertTrue(template.startswith('{{task}}'))
                self.assertIn('{{guide}}', template)
                self.assertNotIn('1 2 1', template)  # no task-specific material in shared framing


class FakeJudge:
    def __init__(self, statuses):
        self.statuses, self.calls = list(statuses), []

    def run(self, task_id, code, timeout=None):
        self.calls.append((task_id, code))
        status = self.statuses.pop(0)
        return {'suite': 'public', 'task_id': task_id, 'status': status, 'report': f'PUBLIC TESTS: {status}',
                'passed': int(status == 'pass'), 'total': 1}


class Backend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from local_agent.platform_support import Settings
        # CI sets CSC2108_TEST_BACKEND=portable so Windows runners (no E: data root) use the portable adapter.
        portable = os.name != 'nt' or os.environ.get('CSC2108_TEST_BACKEND') == 'portable'
        cls.runtime = backend.frozen_runtime(Settings.load('portable', environ={'CSC2108_ROOT': tempfile.mkdtemp()})) \
            if portable else backend.frozen_runtime(Settings.load('windows'))

    def env(self, judge, attempts, source=b'print(1)\n'):
        _, env_cls = backend.make_classes(self.runtime, guidance_text=None, template=None, judge=judge,
                                          task_id='t', attempts=attempts)
        env = object.__new__(env_cls)
        env.deadline, env.evidence, env.last_candidate = float('inf'), [], None
        env.budget = self.runtime.v3.Budget(20, 3)
        env.snapshot = lambda: source
        return env

    def test_recognized_test_goes_to_judge_and_counts_an_action(self):
        attempts, judge = [], FakeJudge(['candidate_failure', 'pass'])
        env = self.env(judge, attempts)
        out = env.execute({'command': 'python -I /public/check.py'})
        self.assertEqual(out['returncode'], 1)
        self.assertEqual(env.budget.actions, 1)
        self.assertIsNotNone(env.budget.failed_hash)
        self.assertTrue(env.evidence[-1]['recognized_public_test'])
        out = env.execute({'command': 'python3 /public/check.py'})
        self.assertEqual((out['returncode'], len(attempts), len(judge.calls)), (0, 2, 2))

    def test_judge_infrastructure_error_stops_run(self):
        env = self.env(FakeJudge(['infrastructure_error']), [])
        with self.assertRaises(Exception) as raised:
            env.execute({'command': 'python -I /public/check.py'})
        self.assertIn('InfrastructureError', str(raised.exception.messages if hasattr(raised.exception, 'messages') else raised.exception))

    def test_agent_template_unchanged_for_a(self):
        for text, expected in ((None, '{{task}}'), ('G', 'X{{task}}{{guide}}')):
            agent_cls, _ = backend.make_classes(self.runtime, guidance_text=text, template='X{{task}}{{guide}}',
                                                judge=None, task_id='t', attempts=[])
            agent = agent_cls(None, None, system_template='s', instance_template='{{task}}')
            self.assertEqual(agent.config.instance_template, expected)

    def test_bound_run_keeps_frozen_bytecode(self):
        agent_cls, env_cls = backend.make_classes(self.runtime, guidance_text=None, template=None, judge=None,
                                                  task_id='t', attempts=[])
        run = backend.bound_run(self.runtime.run, agent_cls, env_cls)
        self.assertIs(run.__code__, self.runtime.run.__code__)
        self.assertIs(run.__globals__['Agent'], agent_cls)
        self.assertIs(run.__globals__['v3'], self.runtime.run.__globals__['v3'])

    def test_composes_with_portable_host_adapter(self):
        from local_agent.platform_support import Settings
        from local_agent.portable import adapted_run
        with tempfile.TemporaryDirectory() as root:
            settings = Settings.load('portable', system='Darwin', environ={'CSC2108_ROOT': root,
                                                                           'CSC2108_OLLAMA_ENDPOINT': 'http://127.0.0.1:11500'})
            portable = adapted_run(self.runtime, settings, {'agent': {'reference': 'img@sha256:x'}})
            agent_cls, env_cls = backend.make_classes(self.runtime, guidance_text=None, template=None, judge=None,
                                                      task_id='t', attempts=[])
            run = backend.bound_run(portable, agent_cls, env_cls)
            self.assertEqual(run.__globals__['ENDPOINT'], 'http://127.0.0.1:11500')
            self.assertEqual(run.__globals__['v3'].IMAGE, 'img@sha256:x')
            self.assertIs(run.__globals__['Environment'], env_cls)


class Providers(unittest.TestCase):
    def test_codex_command_is_isolated(self):
        command = providers.codex_command('gpt-6.2-sol', 'medium', Path('w'), Path('o'))
        for flag in ('--ignore-user-config', '--ephemeral', '--ignore-rules', 'read-only', 'web_search="disabled"'):
            self.assertIn(flag, ' '.join(command))
        self.assertIn('shell_tool', command)

    def test_ledger_enforces_request_and_cost_ceilings_before_sending(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = providers.Ledger(Path(tmp) / 'ledger.json')
            for _ in range(providers.MAX_REQUESTS):
                ledger.reserve({'bound_usd_conservative': 0.01})
            with self.assertRaises(RuntimeError):
                ledger.reserve({'bound_usd_conservative': 0.01})
            fresh = providers.Ledger(Path(tmp) / 'other.json')
            with self.assertRaises(RuntimeError):
                fresh.reserve({'bound_usd_conservative': providers.MAX_USD + 1})
            self.assertEqual(json.loads((Path(tmp) / 'ledger.json').read_text())['requests'][0]['state'], 'pending')

    def test_api_refuses_when_ledger_full_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('OPENAI_API_KEY=sk-test\nFRONTIER_MODEL=openai/gpt-6.2-sol\n', encoding='utf-8')
            ledger = providers.Ledger(Path(tmp) / 'l.json')
            for _ in range(providers.MAX_REQUESTS):
                ledger.reserve({'bound_usd_conservative': 0.0})
            with mock.patch.dict(os.environ, {'CSC2108_ENV_FILE': str(env)}), \
                    mock.patch('urllib.request.urlopen', side_effect=AssertionError('network used')):
                with self.assertRaises(RuntimeError):
                    providers.api_author(kind='plan', prompt_id='plan-v1', statement=STATEMENT, task_id='t',
                                         out_path=Path(tmp) / 'a.json', ledger_path=Path(tmp) / 'l.json', purpose='test')


class Tasks(unittest.TestCase):
    def test_no_newline_translation(self):
        from guided_agent.tasks import _NoTranslatePath
        with tempfile.TemporaryDirectory() as tmp:
            path = _NoTranslatePath(tmp) / 'x.in'
            path.write_text('1\n2\n', encoding='utf-8')
            self.assertEqual(Path(path).read_bytes(), b'1\n2\n')

    def test_selection_order_is_deterministic(self):
        from guided_agent.selection import order
        self.assertEqual(order(['b', 'a', 'c'], 's'), order(['c', 'b', 'a'], 's'))


if __name__ == '__main__':
    unittest.main()
