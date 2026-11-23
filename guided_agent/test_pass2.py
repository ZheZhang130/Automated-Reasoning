"""Pass-2 tests for contract-v3, Condition E (diagnosis) and Condition B (frontier coder).

Offline tests: no model, Docker or network.     python -m unittest guided_agent.test_pass2
Integration tests (real frozen runtime, real Docker sandbox and judge-public, SCRIPTED coder, no inference,
no frontier calls) run only with CSC2108_INTEGRATION=1 and CSC2108_STUDY_ROOT pointing at a prepared study
that holds the synthetic fixture (python -m guided_agent prepare-fixture).
"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from guided_agent import backend, diagnosis, frontier_coder, guidance
from guided_agent.common import sha256_bytes, sha256_text

STATEMENT = '# Sum\n\nRead A and B and print A+B.\n'
GOOD_DIAGNOSIS = ('## Observed failure\nCase 2 expected -1 but printed 5.\n## Likely cause\nabs() drops the sign.\n'
                  '## Repair direction\nAdd the signed values.\n## Verification target\nRerun the public tests.\n')


def failure(verdict='WA', status='candidate_failure'):
    first = {'name': 'case-2', 'verdict': verdict, 'input': '-3 2\n', 'expected': '-1\n', 'actual': '5\n'}
    return {'suite': 'public', 'task_id': 't', 'status': status, 'passed': 1, 'total': 2, 'first_failure': first,
            'report': 'PUBLIC TESTS: 1/2 passed\nFirst failure: case case-2: WA (wrong answer)\n--- input ---\n-3 2',
            'tests_sha256': 'd'}  # no code_sha256: pass 3 checks it against the snapshot when present


class FakeBudget:
    def __init__(self, actions=3, limit=20):
        self.actions, self.action_limit, self.repairs, self.repair_limit = actions, limit, 0, 3


class FakeEnv:
    def __init__(self, budget=None, deadline=1e9):
        self.budget, self.deadline = budget or FakeBudget(), deadline


class FakeAgent:
    def __init__(self, env):
        self.env, self.messages, self._start_time = env, [], 1000.0

    def add_messages(self, *messages):
        self.messages.extend(messages)
        return list(messages)


def controller(tmp, provider):
    return diagnosis.DiagnosisController(provider=provider, statement=STATEMENT, task_id='t', out_dir=Path(tmp) / 'd',
                                         max_wait_seconds=30)


class TriggerPolicy(unittest.TestCase):
    def test_only_candidate_caused_failures_of_a_real_candidate_qualify(self):
        src = b'print(1)\n'
        for verdict in ('WA', 'RE', 'TLE', 'CE'):
            self.assertTrue(diagnosis.qualifies(failure(verdict), src)[0], verdict)
        self.assertEqual(diagnosis.qualifies(failure('MISSING'), src), (False, 'non_qualifying_verdict:MISSING'))
        self.assertEqual(diagnosis.qualifies(failure(), b''), (False, 'missing_candidate'))
        self.assertEqual(diagnosis.qualifies(failure(), None), (False, 'missing_candidate'))
        self.assertEqual(diagnosis.qualifies({'status': 'pass'}, src), (False, 'public_pass'))
        self.assertFalse(diagnosis.qualifies({'status': 'infrastructure_error'}, src)[0])

    def test_first_qualifying_failure_triggers_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS)
            ctl, env = controller(tmp, provider), FakeEnv()
            agent = FakeAgent(env)
            self.assertFalse(ctl.on_public_result(result={'status': 'pass'}, source=b'x', digest='h0',
                                                  budget=env.budget, deadline=env.deadline))
            self.assertTrue(ctl.on_public_result(result=failure(), source=b'print(1)\n', digest='h1',
                                                 budget=env.budget, deadline=env.deadline))
            ctl.deliver(agent)
            self.assertFalse(ctl.on_public_result(result=failure(), source=b'print(2)\n', digest='h2',
                                                  budget=env.budget, deadline=env.deadline))
            self.assertIsNone(ctl.deliver(agent))
            self.assertEqual((provider.calls, len(agent.messages), ctl.record['later_public_failures']), (1, 1, 1))
            self.assertEqual(ctl.record['packet']['candidate_sha256'], sha256_bytes(b'print(1)\n'))

    def test_no_local_action_left_means_no_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS)
            ctl, env = controller(tmp, provider), FakeEnv(FakeBudget(actions=20))
            ctl.on_public_result(result=failure(), source=b'x\n', digest='h', budget=env.budget, deadline=env.deadline)
            self.assertIsNone(ctl.deliver(FakeAgent(env)))
            self.assertEqual((provider.calls, ctl.record['frontier_requested'], ctl.record['error_category']),
                             (0, False, 'no_local_budget'))


class Delivery(unittest.TestCase):
    def armed(self, tmp, provider, deadline=500.0):
        ctl, env = controller(tmp, provider), FakeEnv(deadline=deadline)
        ctl.on_public_result(result=failure(), source=b'print(abs(1))\n', digest='h', budget=env.budget,
                             deadline=env.deadline, now=100.0)
        return ctl, env, FakeAgent(env)

    def test_diagnosis_is_one_user_message_after_the_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent = self.armed(tmp, diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS))
            agent.messages = [{'role': 'system'}, {'role': 'user'}, {'role': 'assistant'}, {'role': 'user', 'content': 'obs'}]
            before = list(agent.messages)
            ctl.deliver(agent)
            self.assertEqual(agent.messages[:4], before)  # history untouched
            message = agent.messages[4]
            self.assertEqual((message['role'], message['extra']['interrupt_type']), ('user', 'FrontierDiagnosis'))
            self.assertIn('## Likely cause', message['content'])
            self.assertIn('17 actions left', message['content'])
            self.assertEqual(ctl.record['delivered_message_index'], 4)
            saved = json.loads((Path(tmp) / 'd/diagnosis.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['packet']['candidate_sha256'], sha256_bytes(b'print(abs(1))\n'))

    def test_frontier_wait_is_excluded_from_local_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent = self.armed(tmp, diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS, delay=0.3))
            ctl.deliver(agent)
            # >= 0.28: time.sleep(0.3) measured by the monotonic clock can read 0.296 s on Windows (timer tick)
            self.assertGreaterEqual(env.deadline - 500.0, 0.28)
            self.assertGreaterEqual(agent._start_time - 1000.0, 0.28)
            self.assertAlmostEqual(env.deadline - 500.0, ctl.record['frontier_wait_seconds'], places=2)
            self.assertEqual(env.budget.actions, 3)  # no action or repair consumed

    def test_provider_failures_are_recorded_and_the_agent_continues(self):
        cases = [(diagnosis.FixedDiagnoser(error=('timeout', '300 s'), delay=0.05), 'timeout'),
                 (diagnosis.FixedDiagnoser(error=('transport_error', 'reset')), 'transport_error'),
                 (diagnosis.FixedDiagnoser(error=('isolation_violation', 'command item')), 'isolation_violation'),
                 (diagnosis.FixedDiagnoser(error=('budget_exhausted', 'ceiling')), 'budget_exhausted'),
                 (diagnosis.FixedDiagnoser(''), 'empty_diagnosis'),
                 (diagnosis.FixedDiagnoser('Just add the numbers.'), 'invalid_format'),
                 (diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS + '```python\nprint(a+b)\n```\n'), 'invalid_format')]
        for provider, category in cases:
            with tempfile.TemporaryDirectory() as tmp:
                ctl, env, agent = self.armed(tmp, provider)
                self.assertIsNone(ctl.deliver(agent))
                self.assertEqual((ctl.record['error_category'], ctl.record['delivered'], len(agent.messages),
                                  provider.calls), (category, False, 0, 1), category)
                self.assertTrue(ctl.record['frontier_requested'])
                self.assertGreaterEqual(env.deadline, 500.0)

    def test_unexpected_provider_exception_is_contained(self):
        def broken(system, user, evidence_dir, packet=None):
            raise ConnectionResetError('boom')
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent = self.armed(tmp, broken)
            self.assertIsNone(ctl.deliver(agent))
            self.assertEqual(ctl.record['error_category'], 'provider_error')

    def test_replay_requires_the_identical_candidate_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent = self.armed(tmp, diagnosis.FixedDiagnoser(GOOD_DIAGNOSIS))
            ctl.deliver(agent)
            recorded = Path(tmp) / 'd/diagnosis.json'
            ok = controller(tmp + '/r1', diagnosis.ReplayDiagnoser(recorded))
            ok.on_public_result(result=failure(), source=b'print(abs(1))\n', digest='h', budget=FakeBudget(),
                                deadline=500.0)
            self.assertIsNotNone(ok.deliver(FakeAgent(FakeEnv())))
            bad = controller(tmp + '/r2', diagnosis.ReplayDiagnoser(recorded))
            bad.on_public_result(result=failure(), source=b'print(2)\n', digest='h2', budget=FakeBudget(), deadline=500.0)
            self.assertIsNone(bad.deliver(FakeAgent(FakeEnv())))
            self.assertEqual(bad.record['error_category'], 'replay_mismatch')


class EvidencePacket(unittest.TestCase):
    def test_packet_holds_only_public_evidence_bound_by_hashes(self):
        packet = diagnosis.evidence_packet(statement=STATEMENT, source=b'print(abs(1))\n', result=failure(),
                                           task_id='t', actions_used=3, action_limit=20, repairs_used=0,
                                           repair_limit=3, seconds_left=412.7)
        user = packet['user_message']
        for part in (STATEMENT.strip(), 'print(abs(1))', 'First failure: case case-2', '3 of 20 actions used',
                     'about 412 seconds'):
            self.assertIn(part, user)
        self.assertEqual(user.count(f"<<<DATA-{packet['nonce']} "), 3)
        self.assertEqual(packet['report_sha256'], sha256_text(failure()['report']))
        self.assertNotIn('hidden', user.lower())

    def test_large_program_is_clipped_explicitly(self):
        source = ('x = 1\n' * 5000).encode()
        packet = diagnosis.evidence_packet(statement=STATEMENT, source=source, result=failure(), task_id='t',
                                           actions_used=1, action_limit=20, repairs_used=0, repair_limit=3,
                                           seconds_left=100)
        self.assertTrue(packet['program_clipped'])
        self.assertIn('truncated by the harness', packet['user_message'])
        self.assertEqual(packet['candidate_sha256'], sha256_bytes(source))


class FrontierCoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from local_agent.platform_support import Settings
        # CI sets CSC2108_TEST_BACKEND=portable so Windows runners (no E: data root) use the portable adapter.
        portable = os.name != 'nt' or os.environ.get('CSC2108_TEST_BACKEND') == 'portable'
        cls.runtime = backend.frozen_runtime(Settings.load('portable', environ={'CSC2108_ROOT': tempfile.mkdtemp()})) \
            if portable else backend.frozen_runtime(Settings.load('windows'))

    def model(self, coder):
        cls = frontier_coder.make_coder_class(self.runtime, coder)
        return cls(model_name='ollama_chat/frontier', model_kwargs={'timeout': 50}, cost_tracking='ignore_errors',
                   observation_template='<returncode>{{output.returncode}}</returncode>\n{{output.output[:6000]}}',
                   format_error_template=self.runtime.FORMAT_ERROR,
                   action_regex=r'```(?:mswea_bash_command|bash)\s*\n(.*?)\n```')

    def test_actions_use_the_frozen_text_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            coder = frontier_coder.ScriptedCoder(['```mswea_bash_command\nls\n```', 'no block'], tmp)
            model = self.model(coder)
            message = model.query([{'role': 'system', 'content': 's'}, {'role': 'user', 'content': 'u'}])
            self.assertEqual(message['extra']['actions'], [{'command': 'ls'}])
            from minisweagent.exceptions import FormatError
            with self.assertRaises(FormatError):
                model.query([{'role': 'user', 'content': 'u'}])

    def test_request_cap_stops_cleanly_and_errors_are_never_retried(self):
        from minisweagent.exceptions import LimitsExceeded
        with tempfile.TemporaryDirectory() as tmp:
            model = self.model(frontier_coder.ScriptedCoder(['```bash\nls\n```'], tmp, max_requests=1))
            model.query([{'role': 'user', 'content': 'u'}])
            with self.assertRaises(LimitsExceeded):
                model.query([{'role': 'user', 'content': 'u'}])
            calls = []

            def failing(messages, timeout):
                calls.append(1)
                raise TimeoutError('slow')
            failing.model_label = 'x'
            with self.assertRaises(frontier_coder.FrontierCoderError):
                self.model(failing).query([{'role': 'user', 'content': 'u'}])
            self.assertEqual(len(calls), 1)  # tenacity did not retry

    def test_api_coder_respects_the_ledger_without_network(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('OPENAI_API_KEY=sk-test\nFRONTIER_MODEL=openai/gpt-6.2-sol\n', encoding='utf-8')
            ledger = Path(tmp) / 'ledger.json'
            data = providers.Ledger(ledger).data
            data['requests'] = [{'bound_usd_conservative': 0.0, 'usage': {'prompt_tokens': 0, 'completion_tokens': 0}}] * 12
            providers.write_json(ledger, data)
            with mock.patch.dict(os.environ, {'CSC2108_ENV_FILE': str(env)}), \
                    mock.patch('urllib.request.urlopen', side_effect=AssertionError('network used')):
                coder = frontier_coder.ApiCoder(log_dir=tmp, ledger_path=ledger, purpose='test', max_requests=3)
                with self.assertRaises(RuntimeError):
                    coder([{'role': 'user', 'content': 'u'}], 10)

    def test_non_ollama_globals_never_touch_the_gpu_or_ollama_metadata(self):
        calls = []
        base = {'api': lambda *a, **k: calls.append(a) or {}, 'MODELS': ('qwen3.5:9b',)}
        extra = frontier_coder.non_ollama_globals(base, object, 'frontier:m')
        self.assertIsNone(extra['exclusive_gpu']())
        self.assertEqual(extra['api'](11435, '/api/show', {'model': 'frontier:m'})['non_ollama_coder'], 'frontier:m')
        self.assertIn('frontier:m', extra['MODELS'])
        self.assertEqual(calls, [])


# ----------------------------------------------------------------------------- integration (Docker + judge)
WRONG = "cat > /workspace/solution.py <<'PY'\na, b = map(int, input().split())\nprint(abs(a) + abs(b))\nPY"
FIX = "sed -i 's/abs(a) + abs(b)/a + b/' /workspace/solution.py"
TEST = 'python -I /public/check.py'
SUBMIT = 'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'
GOOD = "cat > /workspace/solution.py <<'PY'\na, b = map(int, input().split())\nprint(a + b)\nPY"


def block(command):
    return f'```mswea_bash_command\n{command}\n```'


@unittest.skipUnless(os.environ.get('CSC2108_INTEGRATION') == '1', 'set CSC2108_INTEGRATION=1 (Docker + judge image)')
class IntegrationE(unittest.TestCase):
    """Real frozen runtime + sandbox + judge-public; scripted coder; fixed diagnosis provider."""

    def run_e(self, responses, diag, name, judge_wrapper=None, condition='E'):
        from guided_agent import runner
        study = Path(os.environ['CSC2108_STUDY_ROOT'])
        out = study / 'runs' / 'integration-tests' / f'{name}-{int(time.time() * 1000)}'
        spec = {'task_id': 'fixture-sum-signed', 'condition': condition, 'run_id': out.name, 'output': str(out),
                'study': str(study), 'backend': os.environ.get('CSC2108_TEST_BACKEND', 'auto'),
                'coder': {'provider': 'scripted', 'responses': [block(r) for r in responses]},
                'diagnosis': diag, 'batch': 'integration-tests', 'cohort': 'integration (scripted coder)'}
        if judge_wrapper:
            original = backend.judge_client
            with mock.patch.object(backend, 'judge_client', lambda s, suite: judge_wrapper(original(s, suite))):
                record = runner.run_attempt(spec)
        else:
            record = runner.run_attempt(spec)
        trajectory = json.loads(next((out).glob('agent-*/trajectory.json')).read_text(encoding='utf-8'))
        return record, trajectory['messages'], out

    def test_1_diagnosis_then_same_session_repair_passes(self):
        diag = {'provider': 'fixed', 'text': GOOD_DIAGNOSIS, 'delay': 2.0}
        record, messages, out = self.run_e([WRONG, TEST, FIX, TEST, SUBMIT], diag, 'repair')
        d = record['diagnosis']
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        self.assertEqual((d['trigger_observed'], d['frontier_requested'], d['delivered']), (True, True, True))
        self.assertEqual((d['trigger_action'], d['local_actions_after'], d['public_tests_after']), (2, 3, 1))
        self.assertTrue(d['candidate_changed_after'] and d['public_pass_after'])
        self.assertEqual(record['n_actions'], 5)  # one continuous action counter, no extra action for E
        roles = [m['role'] for m in messages]
        index = d['delivered_message_index']
        self.assertEqual(messages[index]['extra']['interrupt_type'], 'FrontierDiagnosis')
        self.assertIn('PUBLIC TESTS', messages[index - 1]['content'])      # public feedback stays visible, first
        self.assertEqual(roles[index + 1], 'assistant')                     # next query sees the diagnosis
        self.assertEqual(sum(m.get('extra', {}).get('interrupt_type') == 'FrontierDiagnosis' for m in messages), 1)
        coder_calls = json.loads((out / 'coder/coder-calls.json').read_text(encoding='utf-8'))
        self.assertEqual([c['n_messages'] for c in coder_calls], [2, 4, 7, 9, 11])  # history only grows
        self.assertGreaterEqual(record['frontier_wait_seconds'], 2.0)
        self.assertAlmostEqual(record['local_coding_seconds'] - record['local_coding_seconds_net'],
                               record['frontier_wait_seconds'], places=1)
        self.assertTrue(record['frozen_verification']['frozen_files_verified'])
        config = json.loads(next(out.glob('agent-*/configuration.json')).read_text(encoding='utf-8'))
        self.assertEqual(json.dumps(config).count('"container_timeout": "990s"'), 1)  # 660 s + 300 s wait + 30 s

    def test_2_public_pass_means_no_request(self):
        record, messages, _ = self.run_e([GOOD, TEST, SUBMIT], {'provider': 'fixed', 'text': GOOD_DIAGNOSIS}, 'no-trigger')
        self.assertEqual(record['exit_status'], 'submitted')
        self.assertEqual((record['diagnosis']['trigger_observed'], record['diagnosis']['frontier_requested']), (False, False))
        self.assertFalse(any(m.get('extra', {}).get('interrupt_type') == 'FrontierDiagnosis' for m in messages))

    def test_3_provider_failure_logged_and_agent_continues(self):
        diag = {'provider': 'fixed', 'error': ['transport_error', 'simulated']}
        record, messages, _ = self.run_e([WRONG, TEST, FIX, TEST, SUBMIT], diag, 'provider-failure')
        d = record['diagnosis']
        self.assertEqual(record['exit_status'], 'submitted')
        self.assertEqual((d['trigger_observed'], d['frontier_requested'], d['delivered'], d['error_category']),
                         (True, True, False, 'transport_error'))
        self.assertEqual(record['n_actions'], 5)

    def test_4_judge_infrastructure_error_requests_nothing(self):
        class InfraJudge:
            def __init__(self, inner):
                self.inner = inner

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def run(self, task_id, code, timeout=None):
                return {'suite': 'public', 'task_id': task_id, 'status': 'infrastructure_error', 'error': 'simulated',
                        'report': 'PUBLIC TESTS: infrastructure error (simulated)'}
        record, messages, _ = self.run_e([WRONG, TEST, SUBMIT], {'provider': 'fixed', 'text': GOOD_DIAGNOSIS},
                                         'infra', judge_wrapper=InfraJudge)
        self.assertEqual(record['exit_status'], 'infra_error')
        self.assertEqual((record['diagnosis']['trigger_observed'], record['diagnosis']['frontier_requested']), (False, False))
        self.assertEqual(record['diagnosis']['observations'][-1]['status'], 'infrastructure_error')

    def test_5_only_first_of_multiple_failures_triggers(self):
        still_wrong = "sed -i 's/abs(a) + abs(b)/abs(a + b)/' /workspace/solution.py"
        fix_second = "sed -i 's/abs(a + b)/a + b/' /workspace/solution.py"
        record, messages, _ = self.run_e([WRONG, TEST, still_wrong, TEST, fix_second, TEST, SUBMIT],
                                         {'provider': 'fixed', 'text': GOOD_DIAGNOSIS}, 'multiple')
        d = record['diagnosis']
        self.assertEqual(record['exit_status'], 'submitted')
        self.assertEqual((d['trigger_action'], d['later_public_failures']), (2, 1))
        self.assertEqual(sum(m.get('extra', {}).get('interrupt_type') == 'FrontierDiagnosis' for m in messages), 1)

    def test_6_a_is_unchanged_by_the_e_machinery(self):
        record, messages, out = self.run_e([WRONG, TEST, FIX, TEST, SUBMIT], None, 'control-a', condition='A')
        self.assertEqual(record['exit_status'], 'submitted')
        self.assertNotIn('diagnosis', record)
        config = json.loads(next(out.glob('agent-*/configuration.json')).read_text(encoding='utf-8'))
        self.assertEqual(json.dumps(config).count('"container_timeout": "660s"'), 1)  # frozen value
        self.assertFalse(any(m.get('extra', {}).get('interrupt_type') == 'FrontierDiagnosis' for m in messages))


if __name__ == '__main__':
    unittest.main()
