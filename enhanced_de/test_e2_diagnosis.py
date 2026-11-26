"""Offline unit tests for enhanced_de.e2_diagnosis (E2 strict / stall / review controllers and providers).

No model inference, no paid API calls, no network: providers are deterministic fakes or mocks and every
candidate execution goes through an injected fake sandbox. One optional real-Docker smoke test runs only with
CSC2108_DOCKER_TESTS=1 (local container, no network inside, no GPU).

    python -m unittest enhanced_de.test_e2_diagnosis
"""
import inspect
import json
import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from enhanced_de import e2_diagnosis as e2
from enhanced_de import ledger_guard
from guided_agent.common import sha256_bytes, sha256_text, write_json

STATEMENT = ('# Signed sum\n\nRead integers A and B and print A+B.\n\nConstraints: -10^9 <= A, B <= 10^9.\n'
             '$1 \\le N \\le 2 \\times 10^5$\n')
SRC_BAD = b'a, b = map(int, input().split())\nprint(abs(a) + abs(b))\n'
SRC_GOOD = b'a, b = map(int, input().split())\nprint(a + b)\n'
PUBLIC_CASES = [{'input': '1 2\n', 'output': '3\n', 'testtype': 'stdin'},
                {'input': '-3 2\n', 'output': '-1\n', 'testtype': 'stdin'}]


def failure(verdict='WA', status='candidate_failure', source=SRC_BAD, suite='public', with_hash=True):
    first = {'name': 'case-2', 'verdict': verdict, 'input': '-3 2\n', 'expected': '-1\n', 'actual': '5\n'}
    result = {'suite': suite, 'task_id': 't', 'status': status, 'passed': 1, 'total': 2, 'first_failure': first,
              'report': 'PUBLIC TESTS: 1/2 passed\nFirst failure: case case-2: WA (wrong answer)\n--- input ---\n-3 2',
              'tests_sha256': 'd', 'time_limit_s': 2.0,
              'cases': [{'name': 'case-1', 'verdict': 'AC', 'time_s': 0.031},
                        {'name': 'case-2', 'verdict': verdict, 'time_s': 0.029}]}
    if with_hash and source:
        result['code_sha256'] = sha256_bytes(source)
    return result


def public_pass(source=SRC_GOOD):
    return {'suite': 'public', 'task_id': 't', 'status': 'pass', 'passed': 2, 'total': 2, 'first_failure': None,
            'report': 'PUBLIC TESTS: 2/2 passed', 'tests_sha256': 'd', 'time_limit_s': 2.0,
            'code_sha256': sha256_bytes(source),
            'cases': [{'name': 'case-1', 'verdict': 'AC', 'time_s': 0.03},
                      {'name': 'case-2', 'verdict': 'AC', 'time_s': 0.03}]}


def strict_text(mode='LOCAL-FIX', direction='Add the signed values instead of their absolute values.',
                verification='Rerun the public tests.\n\nV-1\n```text\n-5 -7\n```\n```text\n-12\n```\n'):
    return ('## Observed failure\nCase 2 expected -1 but the program printed 5.\n'
            '## Likely cause\nThe abs() calls on line 2 discard the sign of negative inputs.\n'
            f'## Repair mode\n{mode} — the method is right; one expression is wrong.\n'
            f'## Repair direction\n{direction}\n'
            f'## Verification target\n{verification}')


STALL_TEXT = ('## Where reasoning stalled\nIt kept re-deriving the sign handling for negative numbers.\n'
              '## Key observation\nPython integers are unbounded and signed, so no special casing is needed.\n'
              '## Concrete next approach\nRead both integers and print their plain sum; O(1).\n'
              '## Implementation discipline\nStop deliberating and immediately write a concise '
              '/workspace/solution.py in one command, then run the public tests.\n')

REVIEW_NO_DEFECT = '## Verdict\nNO-DEFECT — the program handles every valid input.\n'


def review_defect(cases='C-1\n```text\n1000000000 1000000000\n```\n```text\n2000000000\n```\n'):
    return ('## Verdict\nDEFECT — large inputs are mishandled.\n'
            '## Likely bug\nLine 2 truncates the sum.\n'
            f'## Counterexample\n{cases}'
            '## Repair direction\nPrint the exact integer sum without truncation.\n')


class FakeBudget:
    def __init__(self, actions=3, limit=20):
        self.actions, self.action_limit, self.repairs, self.repair_limit = actions, limit, 0, 3
        self.tested_calls = []

    def before(self):
        self.actions += 1

    def tested(self, digest, returncode):
        self.tested_calls.append((digest, returncode))


class FakeEnv:
    def __init__(self, budget=None, deadline=500.0):
        self.budget, self.deadline = budget or FakeBudget(), deadline


class FakeAgent:
    def __init__(self, env):
        self.env, self.messages, self._start_time = env, [], 1000.0
        self.n_consecutive_format_errors = 2
        self.workspace = {'solution.py': 'untouched'}

    def add_messages(self, *messages):
        self.messages.extend(messages)
        return list(messages)


class FakeSandbox:
    """Executes the two toy programs symbolically: SRC_BAD prints |a|+|b|, SRC_GOOD prints a+b."""

    def __init__(self, override=None):
        self.calls, self.override = [], override

    def __call__(self, source, stdin, time_limit):
        self.calls.append((source, stdin, time_limit))
        if self.override is not None:
            return dict(self.override)
        try:
            a, b = map(int, stdin.split())
        except ValueError:
            return {'verdict': 'RE', 'stdout': '', 'stderr_tail': 'ValueError', 'returncode': 1, 'seconds': 0.1}
        value = abs(a) + abs(b) if source == SRC_BAD else a + b
        if source not in (SRC_BAD, SRC_GOOD):
            value = -999
        return {'verdict': 'OK', 'stdout': f'{value}\n', 'stderr_tail': '', 'returncode': 0, 'seconds': 0.1}


def fixed(text=None, error=None, delay=0.0):
    return e2.E2FixedProvider(text=text, error=error, delay=delay)


def make_strict(tmp, provider, sandbox=None, **kw):
    return e2.E2StrictController(provider, STATEMENT, 't', Path(tmp) / 'd', sandbox_runner=sandbox or FakeSandbox(),
                                 **kw)


def arm_strict(ctl, env, source=SRC_BAD, result=None, now=100.0):
    return ctl.on_public_result(result=result or failure(source=source), source=source,
                                digest=sha256_bytes(source), budget=env.budget, deadline=env.deadline,
                                public_cases=PUBLIC_CASES, now=now)


def plan_artifact(tmp, statement=STATEMENT, name='plan.json', **over):
    raw = {'schema': 'csc2108-guidance-v1', 'kind': 'plan', 'prompt_id': 'plan-v1', 'task_id': 't',
           'text': '## Observations\nThe sum fits easily in Python ints.\n## Solution sketch\nRead A and B, print A+B.\n',
           'statement_sha256': sha256_text(statement), 'author': 'codex:gpt-6.2-sol'} | over
    path = Path(tmp) / name
    write_json(path, raw)
    return path


def stall_error(ctl, env, consecutive=2, done_reason='length', has_candidate=False, raw='x' * 6000):
    return ctl.on_format_error(done_reason=done_reason, raw_content=raw, consecutive_errors=consecutive,
                               has_candidate=has_candidate, budget=env.budget, deadline=env.deadline, now=100.0)


# ============================================================================= providers
class Providers(unittest.TestCase):
    def test_fixed_provider_text_error_and_delay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = e2.make_e2_provider({'provider': 'fixed', 'text': 'hello'}, tmp)
            self.assertEqual(p('s', 'u', Path(tmp) / 'a')['text'], 'hello')
            bad = e2.make_e2_provider({'provider': 'fixed', 'error': ['timeout', '9 s']}, tmp)
            with self.assertRaises(e2.DiagnosisFailure) as ctx:
                bad('s', 'u', Path(tmp) / 'b')
            self.assertEqual((ctx.exception.category, ctx.exception.detail), ('timeout', '9 s'))
            slow = e2.make_e2_provider({'provider': 'fixed', 'text': 'x', 'delay': 0.05}, tmp)
            started = time.monotonic()
            slow('s', 'u', Path(tmp) / 'c')
            self.assertGreaterEqual(time.monotonic() - started, 0.045)
            self.assertEqual(slow.calls, 1)

    def test_codex_provider_uses_isolated_codex_infer_with_spec_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = e2.make_e2_provider({'provider': 'codex'}, tmp)
            ret = {'text': 'diag\n', 'isolation': {'mechanism': 'm'}, 'usage': {'input_tokens': 5},
                   'wall_seconds': 1.5}
            with mock.patch.object(ledger_guard, 'isolated_codex_infer', return_value=ret) as infer:
                out = p('SYS', 'USER', Path(tmp) / 'ev')
            kwargs = infer.call_args.kwargs
            self.assertEqual(kwargs['work_root'], Path(tmp) / 'codex-work')
            self.assertEqual((kwargs['model'], kwargs['effort'], kwargs['timeout']), ('gpt-6.2-sol', 'medium', 300))
            self.assertEqual((kwargs['system'], kwargs['user']), ('SYS', 'USER'))
            self.assertEqual(out['text'], 'diag\n')
            self.assertEqual(out['provider'], 'codex-live')
            p2 = e2.make_e2_provider({'provider': 'codex', 'model': 'm2', 'effort': 'high', 'timeout': 77}, tmp)
            self.assertEqual((p2.model, p2.effort, p2.timeout), ('m2', 'high', 77))

    def test_codex_provider_maps_failures(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            p = e2.make_e2_provider({'provider': 'codex'}, tmp)
            cases = [(subprocess.TimeoutExpired('codex', 3), 'timeout'),
                     (providers.CodexIsolationError('tool used'), 'isolation_violation'),
                     (RuntimeError('rc=1'), 'provider_error')]
            for i, (exc, category) in enumerate(cases):
                with mock.patch.object(ledger_guard, 'isolated_codex_infer', side_effect=exc):
                    with self.assertRaises(e2.DiagnosisFailure) as ctx:
                        p('s', 'u', Path(tmp) / f'ev{i}')
                self.assertEqual(ctx.exception.category, category)

    def test_api_provider_requires_purpose_and_verified_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                e2.make_e2_provider({'provider': 'api'}, tmp)
            with self.assertRaises(RuntimeError):  # no ledger -> fail closed at setup
                e2.make_e2_provider({'provider': 'api', 'purpose': 'pilot'}, tmp)
            ledger_guard.init_ledger(Path(tmp) / 'api-ledger.json', max_requests=5, max_usd=2.0)
            p = e2.make_e2_provider({'provider': 'api', 'purpose': 'pilot'}, tmp)
            self.assertEqual(p.ledger_path, Path(tmp) / 'api-ledger.json')
            self.assertEqual((p.max_completion_tokens, p.effort, p.timeout), (4096, 'medium', 300))
            other = Path(tmp) / 'other.json'
            ledger_guard.init_ledger(other, max_requests=3, max_usd=1.0)
            p2 = e2.make_e2_provider({'provider': 'api', 'purpose': 'x', 'ledger_path': str(other),
                                      'max_completion_tokens': 1000, 'effort': 'low', 'timeout': 50}, tmp)
            self.assertEqual((p2.ledger_path, p2.max_completion_tokens, p2.effort, p2.timeout),
                             (other, 1000, 'low', 50))

    def test_api_provider_calls_guarded_api_chat_and_maps_outcomes(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            ledger_guard.init_ledger(Path(tmp) / 'api-ledger.json', max_requests=5, max_usd=2.0)
            p = e2.make_e2_provider({'provider': 'api', 'purpose': 'pilot'}, tmp)
            ok = {'text': 'diag', 'payload': {'model': 'gpt-x'}, 'finish_reason': 'stop', 'api_model': 'gpt-x',
                  'usage': {'prompt_tokens': 3}, 'latency_seconds': 1.0, 'cost_usd': 0.01, 'request_id': 'r',
                  'ledger_index': 0}
            with mock.patch.object(ledger_guard, 'guarded_api_chat', return_value=ok) as chat:
                out = p('SYS', 'USER', Path(tmp) / 'ev0', packet={'prompt_id': 'E2_STRICT_V1', 'task_id': 't'})
            kw = chat.call_args.kwargs
            self.assertEqual(kw['ledger_path'], Path(tmp) / 'api-ledger.json')
            self.assertEqual(kw['max_completion_tokens'], 4096)
            self.assertEqual(kw['messages'][0], {'role': 'system', 'content': 'SYS'})
            self.assertEqual(kw['entry']['purpose'], 'pilot')
            self.assertEqual(kw['entry']['prompt_id'], 'E2_STRICT_V1')
            self.assertEqual((out['text'], out['cost_usd']), ('diag', 0.01))
            self.assertTrue((Path(tmp) / 'ev0' / 'response.json').is_file())
            cases = [(dict(ok, finish_reason='length'), None, 'incomplete_response'),
                     (None, RuntimeError('ledger ceiling'), 'budget_exhausted'),
                     (None, providers.ApiRequestError('HTTP 500'), 'transport_error')]
            for i, (ret, exc, category) in enumerate(cases, 1):
                with mock.patch.object(ledger_guard, 'guarded_api_chat', return_value=ret, side_effect=exc):
                    with self.assertRaises(e2.DiagnosisFailure) as ctx:
                        p('s', 'u', Path(tmp) / f'ev{i}')
                self.assertEqual(ctx.exception.category, category)

    def test_replay_provider_binds_to_packet_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = {'prompt_id': 'E2_STRICT_V1', 'trigger_kind': 'public_failure', 'statement_sha256': 's',
                      'candidate_sha256': 'c', 'report_sha256': 'r', 'deliberation_sha256': None}
            path = Path(tmp) / 'diagnosis.json'
            write_json(path, {'packet': packet, 'response': {'text': 'recorded', 'provider': 'codex-live'}})
            p = e2.make_e2_provider({'provider': 'replay', 'path': str(path)}, tmp)
            out = p('s', 'u', Path(tmp) / 'ev0', packet=dict(packet))
            self.assertEqual((out['text'], out['provider']), ('recorded', 'replay:codex-live'))
            for i, change in enumerate(({'candidate_sha256': 'other'}, {'report_sha256': 'x'},
                                        {'statement_sha256': 'x'}, {'prompt_id': 'E2_REVIEW_V1'}), 1):
                with self.assertRaises(e2.DiagnosisFailure) as ctx:
                    p('s', 'u', Path(tmp) / f'ev{i}', packet=packet | change)
                self.assertEqual(ctx.exception.category, 'replay_mismatch')
            with self.assertRaises(e2.DiagnosisFailure):
                p('s', 'u', Path(tmp) / 'ev9', packet=None)

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):
            e2.make_e2_provider({'provider': 'magic'}, '.')


# ============================================================================= strict
class StrictTrigger(unittest.TestCase):
    def test_exact_qualifies_policy_and_at_most_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            for verdict in ('WA', 'RE', 'TLE', 'CE'):
                ctl, env = make_strict(Path(tmp) / verdict, fixed('x')), FakeEnv()
                self.assertTrue(arm_strict(ctl, env, result=failure(verdict)), verdict)
            non = [(failure('MISSING'), SRC_BAD), (failure('INFRA'), SRC_BAD), (public_pass(SRC_BAD), SRC_BAD),
                   (failure(status='infrastructure_error'), SRC_BAD), (failure(source=None), b''),
                   (failure(suite='hidden'), SRC_BAD), (failure(source=SRC_GOOD), SRC_BAD)]
            for i, (result, source) in enumerate(non):
                ctl, env = make_strict(Path(tmp) / f'n{i}', fixed('x')), FakeEnv()
                self.assertFalse(arm_strict(ctl, env, source=source, result=result), i)
                self.assertIsNone(ctl.pending)
                self.assertFalse(ctl.record['trigger_observed'])
            self.assertEqual(ctl.observations[-1]['reason'], 'candidate_hash_mismatch')
            ctl, env = make_strict(Path(tmp) / 'once', fixed('x')), FakeEnv()
            self.assertTrue(arm_strict(ctl, env))
            self.assertFalse(arm_strict(ctl, env))
            self.assertEqual(ctl.record['later_public_failures'], 1)
            self.assertEqual(ctl.record['trigger_kind'], 'public_failure')
            self.assertEqual(ctl.record['prompt_id'], 'E2_STRICT_V1')

    def test_format_errors_never_trigger_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = make_strict(tmp, fixed('x')), FakeEnv()
            self.assertFalse(stall_error(ctl, env))
            self.assertIsNone(ctl.pending)
            self.assertEqual(ctl.observations[-1]['event'], 'format_error')
            ctl.observe_infrastructure_error(action=4, error='judge down')
            self.assertEqual(ctl.observations[-1]['status'], 'infrastructure_error')

    def test_enriched_evidence_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = make_strict(tmp, fixed('x')), FakeEnv()
            arm_strict(ctl, env)
            packet = ctl.pending
            user, nonce = packet['user_message'], packet['nonce']
            for name in ('statement', 'program', 'report', 'static-analysis'):
                self.assertIn(f'<<<DATA-{nonce} {name}>>>', user)
            self.assertEqual(user.count(f'<<<END-DATA-{nonce}>>>'), 4)
            self.assertIn(e2.SUBMISSION_CONTRACT, user)
            self.assertIn(f'sha256 {sha256_bytes(SRC_BAD)}', user)
            self.assertIn(SRC_BAD.decode(), user)
            self.assertIn('case-2:WA(0.029s)', user)            # public timings
            self.assertIn('Parsed statement scales', user)       # static analyzer summary
            self.assertIn('LOCAL STATE: 3 of 20 actions used', user)
            self.assertIn('about 400 seconds', user)
            self.assertEqual(packet['candidate_sha256'], sha256_bytes(SRC_BAD))
            self.assertEqual(packet['statement_sha256'], sha256_text(STATEMENT))
            self.assertNotIn('user_message', ctl.record['packet'])

    def test_nonce_never_collides_with_untrusted_data(self):
        with mock.patch.object(e2.secrets, 'token_hex', side_effect=['abc', 'abc', 'fresh']):
            self.assertEqual(e2._nonce('xx abc yy'), 'fresh')


class StrictDelivery(unittest.TestCase):
    def test_delivers_one_message_and_suspends_exactly_the_wait(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = fixed(strict_text(), delay=0.25)
            ctl, env = make_strict(tmp, provider), FakeEnv()
            agent = FakeAgent(env)
            agent.messages = [{'role': 'system'}, {'role': 'user'}, {'role': 'assistant', 'content': 'a'},
                              {'role': 'user', 'content': 'obs'}]
            arm_strict(ctl, env)
            added = ctl.deliver(agent)
            self.assertEqual(len(added), 1)
            self.assertEqual(provider.calls, 1)
            msg = agent.messages[-1]
            self.assertEqual(msg['role'], 'user')
            self.assertTrue(msg['content'].startswith('[Frontier diagnosis]'))
            self.assertIn('(17 actions left)', msg['content'])
            self.assertEqual(msg['extra']['interrupt_type'], 'FrontierDiagnosisV2')
            self.assertEqual(msg['extra']['repair_mode'], 'LOCAL-FIX')
            self.assertEqual(ctl.record['delivered_message_index'], 4)
            self.assertEqual(ctl.record['repair_mode_declared'], 'LOCAL-FIX')
            # never resets counters, history, workspace or budgets
            self.assertEqual(agent.n_consecutive_format_errors, 2)
            self.assertEqual(agent.workspace, {'solution.py': 'untouched'})
            self.assertEqual((env.budget.actions, env.budget.action_limit), (3, 20))
            self.assertEqual(len(agent.messages), 5)
            # deadline and wall-clock start move forward by exactly the suspended wait
            self.assertGreaterEqual(ctl.record['provider_wait_seconds'], 0.24)
            self.assertAlmostEqual(env.deadline - 500.0, ctl.record['frontier_wait_seconds'], places=2)
            self.assertAlmostEqual(agent._start_time - 1000.0, ctl.record['frontier_wait_seconds'], places=1)
            self.assertIsNone(ctl.pending)
            self.assertIsNone(ctl.deliver(agent))          # at most once
            self.assertEqual(provider.calls, 1)
            saved = json.loads((Path(tmp) / 'd' / 'diagnosis.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['response']['text'], strict_text())

    def test_invalid_formats_are_never_delivered(self):
        long_direction = ' '.join(['word'] * 260)
        bad = {
            'missing_heading': strict_text().replace('## Likely cause', '## Cause'),
            'hedged_dual_mode': strict_text(mode='LOCAL-FIX or METHOD-CHANGE'),
            'no_mode': strict_text(mode='Probably a small fix.'),
            'mode_not_first': strict_text(mode='I think LOCAL-FIX'),
            'code_in_direction': strict_text(direction='Use:\n```python\nprint(a + b)\n```'),
            'text_fence_in_direction': strict_text(direction='Input:\n```text\n1 2\n```'),
            'python_fence_in_vcheck': strict_text(verification='V-1\n```python\nimport sys\n```\n```text\n1\n```\n'),
            'too_long_direction': strict_text(direction=long_direction),
            'heredoc': strict_text(direction="cat > /workspace/solution.py <<'PY'"),
            'empty': '   ',
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in bad.items():
                ctl, env = make_strict(Path(tmp) / name, fixed(text)), FakeEnv()
                agent = FakeAgent(env)
                arm_strict(ctl, env)
                self.assertIsNone(ctl.deliver(agent), name)
                self.assertEqual(agent.messages, [], name)
                self.assertFalse(ctl.record['delivered'], name)
                self.assertIn(ctl.record['error_category'], ('invalid_format', 'empty_diagnosis'), name)
                self.assertTrue(ctl.record['frontier_requested'], name)
                self.assertGreaterEqual(env.deadline, 500.0)

    def test_method_change_and_hedge_terms_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = strict_text(mode='**METHOD-CHANGE**: quadratic scan is too slow.',
                               direction='Use prefix sums. Alternatively you could sort.')
            ctl, env = make_strict(tmp, fixed(text)), FakeEnv()
            arm_strict(ctl, env)
            self.assertIsNotNone(ctl.deliver(FakeAgent(env)))
            self.assertEqual(ctl.record['repair_mode_declared'], 'METHOD-CHANGE')
            self.assertEqual(ctl.record['hedge_terms'], ['alternatively'])

    def test_provider_failures_recorded_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            for category in ('timeout', 'budget_exhausted', 'isolation_violation'):
                provider = fixed(error=(category, 'detail'))
                ctl, env = make_strict(Path(tmp) / category, provider), FakeEnv()
                arm_strict(ctl, env)
                self.assertIsNone(ctl.deliver(FakeAgent(env)))
                self.assertEqual((ctl.record['error_category'], provider.calls), (category, 1))

            class Boom:
                def __call__(self, *a, **k):
                    raise KeyError('bad')
            ctl, env = make_strict(Path(tmp) / 'boom', Boom()), FakeEnv()
            arm_strict(ctl, env)
            self.assertIsNone(ctl.deliver(FakeAgent(env)))
            self.assertEqual(ctl.record['error_category'], 'provider_error')

    def test_wait_beyond_max_wait_is_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = make_strict(tmp, fixed(strict_text(), delay=0.1), max_wait_seconds=0.01), FakeEnv()
            arm_strict(ctl, env)
            self.assertIsNone(ctl.deliver(FakeAgent(env)))
            self.assertEqual(ctl.record['error_category'], 'wait_exceeded')
            self.assertGreaterEqual(env.deadline - 500.0, 0.09)   # the wait is still suspended

    def test_no_local_budget_means_no_provider_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = fixed(strict_text())
            ctl, env = make_strict(tmp, provider), FakeEnv(FakeBudget(actions=3))
            arm_strict(ctl, env)
            env.budget.actions = 20
            self.assertIsNone(ctl.deliver(FakeAgent(env)))
            self.assertEqual((provider.calls, ctl.record['error_category']), (0, 'no_local_budget'))
            self.assertFalse(ctl.record['frontier_requested'])

    def test_deliver_without_pending_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = make_strict(tmp, fixed('x'))
            self.assertIsNone(ctl.deliver(FakeAgent(FakeEnv())))
            self.assertFalse((Path(tmp) / 'd').exists())


class StrictVChecks(unittest.TestCase):
    def run_strict(self, tmp, verification, sandbox=None):
        sandbox = sandbox or FakeSandbox()
        ctl, env = make_strict(tmp, fixed(strict_text(verification=verification)), sandbox), FakeEnv()
        agent = FakeAgent(env)
        arm_strict(ctl, env)
        ctl.deliver(agent)
        return ctl, env, agent, sandbox

    def test_aligned_vcheck_runs_on_trigger_source_in_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent, sandbox = self.run_strict(tmp, 'Rerun.\n\nV-1\n```text\n-5 -7\n```\n```text\n-12\n```\n')
            self.assertEqual(sandbox.calls, [(SRC_BAD, '-5 -7\n', 2.0)])
            self.assertEqual(ctl.record['vcheck_alignment'], 'aligned')
            self.assertEqual(ctl.record['vchecks'][0]['trigger_outcome'], 'WA')
            self.assertTrue(ctl.record['vchecks'][0]['aligned'])
            self.assertIn('V-1', agent.messages[-1]['content'])
            self.assertGreaterEqual(ctl.record['harness_check_seconds'], 0.0)

    def test_contradicting_and_duplicating_vchecks_are_dropped_and_stripped(self):
        verification = ('Rerun.\n\nV-1\n```text\n-3  2\n```\n```text\n5\n```\n'
                        'V-2\n```text\n1 2\n```\n```text\n3\n```\n')
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent, sandbox = self.run_strict(tmp, verification)
            self.assertEqual(sandbox.calls, [])
            drops = {v['id']: v['dropped'] for v in ctl.record['vchecks']}
            self.assertEqual(drops, {'V-1': 'contradicts_public', 'V-2': 'duplicates_public'})
            self.assertEqual(ctl.record['vcheck_alignment'], 'all_dropped')
            content = agent.messages[-1]['content']
            self.assertIn('V-1 removed by the harness: contradicts public', content)
            self.assertIn('V-2 removed by the harness: duplicates public', content)
            self.assertNotIn('```text\n5\n```', content)
            self.assertEqual(ctl.post_public_advisory(SRC_GOOD, sha256_bytes(SRC_GOOD), 'pass'), '')

    def test_non_discriminating_none_and_sandbox_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, *_ = self.run_strict(Path(tmp) / 'a', 'Rerun.\n\nV-1\n```text\n4 5\n```\n```text\n9\n```\n')
            self.assertEqual(ctl.record['vcheck_alignment'], 'non_discriminating')
            ctl, *_ = self.run_strict(Path(tmp) / 'b', 'Rerun the public tests.\n')
            self.assertEqual(ctl.record['vcheck_alignment'], 'none_provided')
            infra = FakeSandbox(override={'verdict': 'INFRA', 'stdout': '', 'stderr_tail': 'no docker'})
            ctl, *_ = self.run_strict(Path(tmp) / 'c', 'V-1\n```text\n-5 -7\n```\n```text\n-12\n```\n', infra)
            self.assertEqual(ctl.record['vcheck_alignment'], 'sandbox_error')
            ctl, *_ = self.run_strict(Path(tmp) / 'd', 'V-1 is below.\n\nV-1\n```text\n-5 -7\n```\n```text\n-12\n```\n')
            self.assertEqual(ctl.record['vcheck_alignment'], 'aligned')   # prose mention does not hide the test

    def test_advisory_is_labelled_non_blocking_and_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env, agent, sandbox = self.run_strict(tmp, 'V-1\n```text\n-5 -7\n```\n```text\n-12\n```\n')
            self.assertEqual(ctl.post_public_advisory(SRC_BAD, sha256_bytes(SRC_BAD), 'candidate_failure'), '')
            n_calls = len(sandbox.calls)
            deadline_before = env.deadline
            fixed_text = ctl.post_public_advisory(SRC_GOOD, sha256_bytes(SRC_GOOD), 'pass')
            self.assertTrue(fixed_text.startswith(e2.ADVISORY_LABEL))
            self.assertIn("V-1: your program now prints the diagnosis' expected output.", fixed_text)
            self.assertEqual(len(sandbox.calls), n_calls + 1)
            self.assertGreaterEqual(env.deadline, deadline_before)       # advisory time is suspended too
            self.assertEqual(ctl.post_public_advisory(SRC_GOOD, sha256_bytes(SRC_GOOD), 'pass'), fixed_text)
            self.assertEqual(len(sandbox.calls), n_calls + 1)            # cached per digest
            other = b'print(-999)\n'
            wrong = ctl.post_public_advisory(other, sha256_bytes(other), 'pass')
            self.assertIn("V-1: output differs from the diagnosis' expected output", wrong)
            self.assertIn("got '-999'", wrong)
            self.assertEqual(len(ctl.record['advisories']), 2)

    def test_advisory_disabled_or_undelivered_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = make_strict(Path(tmp) / 'a', fixed(strict_text()), enable_advisory_vchecks=False)
            env = FakeEnv()
            arm_strict(ctl, env)
            ctl.deliver(FakeAgent(env))
            self.assertEqual(ctl.record['vcheck_alignment'], 'aligned')
            self.assertEqual(ctl.post_public_advisory(SRC_GOOD, sha256_bytes(SRC_GOOD), 'pass'), '')
            ctl2 = make_strict(Path(tmp) / 'b', fixed(strict_text()))
            self.assertEqual(ctl2.post_public_advisory(SRC_GOOD, 'h', 'pass'), '')
            arm_strict(ctl2, FakeEnv())
            self.assertEqual(ctl2.post_public_advisory(SRC_GOOD, 'h', 'pass'), '')   # armed, not delivered

    def test_check_parsing_and_filtering_helpers(self):
        text = strict_text(verification='**V-1**\n```text\n1 1\n```\n```text\n2\n```\nV-2 only prose\n')
        problems, parsed = e2.validate_strict(text)
        self.assertEqual(problems, [])
        ids = {c['id']: c['malformed'] for c in parsed['checks']}
        self.assertEqual(ids, {'V-1': False, 'V-2': True})
        checks = e2.filter_against_public(parsed['checks'], PUBLIC_CASES)
        self.assertEqual({c['id']: c['dropped'] for c in checks}, {'V-1': None, 'V-2': 'malformed'})
        big = [{'id': 'V-1', 'stdin': 'x' * (e2.MAX_CHECK_INPUT_CHARS + 1), 'expected': '1', 'malformed': False}]
        self.assertEqual(e2.filter_against_public(big, [])[0]['dropped'], 'too_large')
        self.assertEqual(e2.classify_run({'verdict': 'OK', 'stdout': '3 \n'}, '3\n'), 'AC')
        self.assertEqual(e2.classify_run({'verdict': 'OK', 'stdout': '4\n'}, '3\n'), 'WA')
        self.assertEqual(e2.classify_run({'verdict': 'TLE'}, '3'), 'TLE')
        self.assertEqual(e2.classify_run(None, '3'), 'INFRA')


# ============================================================================= stall
class StallTrigger(unittest.TestCase):
    def make(self, tmp, provider=None, mode='stall-diag', **kw):
        return e2.E2StallController(provider if provider is not None else fixed(STALL_TEXT), STATEMENT, 't',
                                    Path(tmp) / 'd', mode=mode, sandbox_runner=FakeSandbox(), **kw)

    def test_trigger_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            negatives = [dict(consecutive=1), dict(consecutive=3), dict(done_reason='stop'),
                         dict(done_reason=None), dict(has_candidate=True)]
            for i, kw in enumerate(negatives):
                ctl, env = self.make(Path(tmp) / f'n{i}'), FakeEnv()
                self.assertFalse(stall_error(ctl, env, **kw), kw)
                self.assertIsNone(ctl.pending)
                self.assertFalse(ctl.record['trigger_observed'])
            ctl, env = self.make(Path(tmp) / 'budget'), FakeEnv(FakeBudget(actions=20))
            self.assertFalse(stall_error(ctl, env))
            ctl, env = self.make(Path(tmp) / 'yes'), FakeEnv()
            self.assertTrue(stall_error(ctl, env))
            self.assertEqual(ctl.record['trigger_kind'], 'stall_truncation')
            self.assertEqual(ctl.record['trigger_reason'], 'stall_truncation:stall-diag')
            self.assertTrue(ctl.record['feedback_conditioned_replanning'])
            ctl.pending = None
            self.assertFalse(stall_error(ctl, env))           # at most once
            self.assertIsNone(ctl.pending)
            self.assertEqual(sum(o['event'] == 'format_error' for o in ctl.observations), 2)

    def test_packet_holds_only_last_4500_chars_in_nonce_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = self.make(tmp), FakeEnv()
            raw = 'HEAD-' + 'a' * 5000 + 'TAIL-MARK'
            stall_error(ctl, env, raw=raw)
            packet = ctl.pending
            user, nonce = packet['user_message'], packet['nonce']
            self.assertIn(f'<<<DATA-{nonce} deliberation>>>', user)
            self.assertIn('TAIL-MARK', user)
            self.assertNotIn('HEAD-', user)
            self.assertEqual(packet['deliberation_chars_sent'], 4500)
            self.assertEqual(packet['deliberation_chars_total'], len(raw))
            self.assertEqual(packet['deliberation_sha256'], sha256_text(raw[-4500:]))
            self.assertEqual(packet['prompt_id'], 'E2_STALL_V1')

    def test_stall_diag_delivery_keeps_format_error_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = fixed(STALL_TEXT, delay=0.1)
            ctl, env = self.make(tmp, provider), FakeEnv()
            agent = FakeAgent(env)
            stall_error(ctl, env)
            added = ctl.deliver(agent)
            self.assertEqual(len(added), 1)
            self.assertTrue(agent.messages[-1]['content'].startswith('[Frontier recovery guidance]'))
            self.assertIn('## Key observation', agent.messages[-1]['content'])
            self.assertEqual(agent.n_consecutive_format_errors, 2)
            self.assertGreaterEqual(env.deadline - 500.0, 0.09)
            self.assertEqual(provider.calls, 1)
            self.assertTrue(ctl.record['frontier_requested'])
            self.assertEqual(ctl.post_public_advisory(SRC_GOOD, 'h', 'pass'), '')

    def test_stall_diag_invalid_formats(self):
        bad = {'code': STALL_TEXT + '```text\nx\n```\n', 'long': STALL_TEXT + ' '.join(['w'] * 200),
               'heading': STALL_TEXT.replace('## Key observation', '## Insight')}
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in bad.items():
                ctl, env = self.make(Path(tmp) / name, fixed(text)), FakeEnv()
                agent = FakeAgent(env)
                stall_error(ctl, env)
                self.assertIsNone(ctl.deliver(agent), name)
                self.assertEqual((agent.messages, ctl.record['error_category']), ([], 'invalid_format'), name)

    def test_c_late_verifies_statement_hash_and_makes_no_frontier_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                self.make(Path(tmp) / 'a', mode='c-late')                       # no plan path
            wrong = plan_artifact(tmp, statement='another statement', name='wrong.json')
            with self.assertRaises(ValueError) as ctx:
                self.make(Path(tmp) / 'b', mode='c-late', plan_path=wrong)
            self.assertIn('statement_sha256', str(ctx.exception))
            for i, over in enumerate(({'prompt_id': 'plan-v2'}, {'kind': 'contract'}, {'text': ''},
                                      {'text': 'no headings here'})):
                with self.assertRaises(ValueError):
                    self.make(Path(tmp) / f'c{i}', mode='c-late', plan_path=plan_artifact(tmp, name=f'p{i}.json',
                                                                                           **over))
            provider = fixed(STALL_TEXT)
            path = plan_artifact(tmp)
            ctl, env = self.make(Path(tmp) / 'ok', provider, mode='c-late', plan_path=path), FakeEnv()
            self.assertEqual(ctl.record['plan_artifact']['statement_sha256'], sha256_text(STATEMENT))
            self.assertTrue(stall_error(ctl, env))
            self.assertIsNone(ctl.record['prompt_id'])
            agent = FakeAgent(env)
            ctl.deliver(agent)
            content = agent.messages[-1]['content']
            self.assertTrue(content.startswith('[Recovery plan]'))
            self.assertIn('## Solution sketch\nRead A and B, print A+B.', content)
            self.assertEqual(provider.calls, 0)
            self.assertFalse(ctl.record['frontier_requested'])
            self.assertEqual(ctl.record['frontier_wait_seconds'], 0.0)
            self.assertTrue(ctl.record['feedback_conditioned_replanning'])
            self.assertEqual(env.deadline, 500.0)

    def test_neutral_control_is_fixed_content_free_and_frontier_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = fixed(STALL_TEXT)
            ctl, env = self.make(tmp, provider, mode='neutral'), FakeEnv()
            stall_error(ctl, env, raw='SECRET-DELIBERATION ' * 50)
            agent = FakeAgent(env)
            ctl.deliver(agent)
            content = agent.messages[-1]['content']
            self.assertTrue(content.startswith('[Recovery note]'))
            self.assertIn(e2.NEUTRAL_NUDGE_V1, content)
            self.assertNotIn('SECRET-DELIBERATION', content)
            self.assertNotIn('sum', content.lower())             # nothing task-specific
            self.assertTrue(120 <= len(e2.NEUTRAL_NUDGE_V1.split()) <= 160)
            self.assertEqual(provider.calls, 0)
            self.assertFalse(ctl.record['frontier_requested'])
            self.assertFalse(ctl.record['feedback_conditioned_replanning'])
            self.assertEqual(ctl.record['trigger_kind'], 'stall_truncation')

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            e2.E2StallController(fixed('x'), STATEMENT, 't', '.', mode='other')

    def test_public_failure_does_not_trigger_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = self.make(tmp), FakeEnv()
            self.assertFalse(arm_strict(ctl, env))
            self.assertFalse(ctl.record['trigger_observed'])
            self.assertEqual(ctl.observations[-1]['reason'], 'qualifying:WA')

    def test_public_fallback_delegates_to_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = fixed(strict_text())
            ctl, env = self.make(tmp, provider, enable_public_fallback=True), FakeEnv()
            self.assertTrue(arm_strict(ctl, env))
            self.assertEqual(ctl.record['trigger_kind'], 'public_failure')
            self.assertEqual(ctl.record['prompt_id'], 'E2_STRICT_V1')
            self.assertFalse(stall_error(ctl, env))              # the one trigger is spent
            agent = FakeAgent(env)
            ctl.deliver(agent)
            self.assertTrue(agent.messages[-1]['content'].startswith('[Frontier diagnosis]'))
            self.assertEqual(ctl.record['repair_mode_declared'], 'LOCAL-FIX')
            adv = ctl.post_public_advisory(SRC_GOOD, sha256_bytes(SRC_GOOD), 'pass')
            self.assertTrue(adv.startswith(e2.ADVISORY_LABEL))

    def test_stall_first_blocks_public_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = self.make(tmp, enable_public_fallback=True), FakeEnv()
            self.assertTrue(stall_error(ctl, env))
            ctl.deliver(FakeAgent(env))
            self.assertFalse(arm_strict(ctl, env))
            self.assertEqual(ctl.record['trigger_kind'], 'stall_truncation')
            self.assertEqual(ctl.record['later_public_failures'], 1)


# ============================================================================= review
class Review(unittest.TestCase):
    def make(self, tmp, text, sandbox=None, **kw):
        sandbox = sandbox or FakeSandbox()
        provider = fixed(text)
        return e2.E2ReviewController(provider, STATEMENT, 't', Path(tmp) / 'd', sandbox_runner=sandbox, **kw), \
            provider, sandbox

    def arm(self, ctl, env, source=SRC_BAD, result=None):
        return ctl.on_public_result(result=result or public_pass(source), source=source, digest=sha256_bytes(source),
                                    budget=env.budget, deadline=env.deadline, public_cases=PUBLIC_CASES, now=100.0)

    def test_trigger_first_public_pass_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, *_ = self.make(Path(tmp) / 'a', REVIEW_NO_DEFECT)
            env = FakeEnv()
            self.assertFalse(self.arm(ctl, env, result=failure()))
            self.assertFalse(self.arm(ctl, env, source=b'  \n', result=public_pass(b'  \n')))
            self.assertFalse(self.arm(ctl, env, result=public_pass(SRC_GOOD)))          # hash mismatch
            self.assertFalse(self.arm(ctl, env, result=public_pass(SRC_BAD) | {'suite': 'hidden'}))
            self.assertFalse(ctl.record['trigger_observed'])
            self.assertTrue(self.arm(ctl, env))
            self.assertEqual((ctl.record['trigger_kind'], ctl.record['prompt_id']), ('public_pass', 'E2_REVIEW_V1'))
            self.assertIn('static-analysis', ctl.pending['user_message'])
            self.assertIn('case-2:AC(0.03s)', ctl.pending['user_message'])
            ctl.pending = None
            self.assertFalse(self.arm(ctl, env))
            self.assertFalse(stall_error(ctl, env))
            self.assertEqual(ctl.post_public_advisory(SRC_BAD, 'h', 'pass'), '')

    def test_no_defect_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, provider, sandbox = self.make(tmp, REVIEW_NO_DEFECT)
            env = FakeEnv()
            agent = FakeAgent(env)
            self.arm(ctl, env)
            self.assertIsNone(ctl.deliver(agent))
            self.assertEqual(agent.messages, [])
            self.assertEqual(sandbox.calls, [])
            self.assertEqual((ctl.record['review_outcome'], ctl.record['delivered'], provider.calls),
                             ('no_defect', False, 1))
            self.assertAlmostEqual(env.deadline - 500.0, ctl.record['frontier_wait_seconds'], places=2)

    def test_defect_verified_by_wrong_answer_is_delivered(self):
        case = 'C-1\n```text\n-4 -6\n```\n```text\n-10\n```\n'
        with tempfile.TemporaryDirectory() as tmp:
            ctl, _, sandbox = self.make(tmp, review_defect(case))
            env = FakeEnv()
            agent = FakeAgent(env)
            self.arm(ctl, env)
            added = ctl.deliver(agent)
            self.assertEqual(len(added), 1)
            self.assertEqual(sandbox.calls, [(SRC_BAD, '-4 -6\n', 2.0)])
            content = agent.messages[-1]['content']
            self.assertTrue(content.startswith('[Frontier review — verified counterexample]'))
            self.assertIn("on C-1 it printed output different from the reviewer's expected output", content)
            self.assertIn('Your program printed:\n```text\n10\n```', content)
            self.assertIn('## Repair direction', content)
            self.assertNotIn('## Verdict', content)
            self.assertEqual(ctl.record['review_outcome'], 'verified_delivered')
            self.assertEqual(ctl.record['counterexamples'][0]['candidate_outcome'], 'WA')
            self.assertEqual(agent.messages[-1]['extra']['verified_counterexamples'], ['C-1'])

    def test_defect_verified_by_crash_or_timeout(self):
        case = 'C-1\n```text\n5 5\n```\n```text\n10\n```\n'
        with tempfile.TemporaryDirectory() as tmp:
            for verdict, phrase in (('RE', 'runtime error'), ('TLE', 'did not finish within 2 s')):
                box = FakeSandbox(override={'verdict': verdict, 'stdout': '', 'stderr_tail': 'Traceback\nBoom'})
                ctl, _, _ = self.make(Path(tmp) / verdict, review_defect(case), box)
                env = FakeEnv()
                agent = FakeAgent(env)
                self.arm(ctl, env)
                self.assertIsNotNone(ctl.deliver(agent), verdict)
                self.assertIn(phrase, agent.messages[-1]['content'])
                self.assertEqual(ctl.record['review_outcome'], 'verified_delivered')

    def test_unverified_defects_abstain(self):
        scenarios = {
            'candidate_correct': ('C-1\n```text\n4 6\n```\n```text\n10\n```\n', None),
            'contradicts_public': ('C-1\n```text\n-3 2\n```\n```text\n5\n```\n', None),
            'duplicates_public': ('C-1\n```text\n1 2\n```\n```text\n3\n```\n', None),
            'sandbox_infra': ('C-1\n```text\n-4 -6\n```\n```text\n-10\n```\n',
                              {'verdict': 'INFRA', 'stdout': '', 'stderr_tail': 'docker down'}),
            'no_counterexample': ('None found.\n', None),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, (case, override) in scenarios.items():
                box = FakeSandbox(override=override)
                ctl, provider, sandbox = self.make(Path(tmp) / name, review_defect(case), box)
                env = FakeEnv()
                agent = FakeAgent(env)
                self.arm(ctl, env)
                self.assertIsNone(ctl.deliver(agent), name)
                self.assertEqual(agent.messages, [], name)
                self.assertEqual(ctl.record['review_outcome'], 'unverified_abstain', name)
                self.assertFalse(ctl.record['delivered'], name)
                if name in ('contradicts_public', 'duplicates_public'):
                    self.assertEqual(sandbox.calls, [], name)
                    self.assertEqual(ctl.record['counterexamples'][0]['dropped'], name)

    def test_partial_verification_delivers_only_verified_cases(self):
        cases = ('C-1\n```text\n4 6\n```\n```text\n10\n```\n'
                 'C-2\n```text\n-1 -1\n```\n```text\n-2\n```\n')
        with tempfile.TemporaryDirectory() as tmp:
            ctl, _, _ = self.make(tmp, review_defect(cases))
            env = FakeEnv()
            agent = FakeAgent(env)
            self.arm(ctl, env)
            ctl.deliver(agent)
            content = agent.messages[-1]['content']
            self.assertIn('C-2', content)
            self.assertNotIn('C-1', content)

    def test_invalid_review_formats_are_silent(self):
        bad = {'no_verdict': '## Likely bug\nx\n', 'hedged': '## Verdict\nDEFECT or NO-DEFECT\n',
               'bad_token': '## Verdict\nMaybe\n',
               'code': review_defect().replace('Print the exact', '```python\nprint(1)\n```\nPrint the exact'),
               'missing_section': review_defect().replace('## Likely bug', '## Bug')}
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in bad.items():
                ctl, _, sandbox = self.make(Path(tmp) / name, text)
                env = FakeEnv()
                agent = FakeAgent(env)
                self.arm(ctl, env)
                self.assertIsNone(ctl.deliver(agent), name)
                self.assertEqual((agent.messages, sandbox.calls), ([], []), name)
                self.assertEqual(ctl.record['review_outcome'], 'provider_failure', name)
                self.assertEqual(ctl.record['error_category'], 'invalid_format', name)


# ============================================================================= finalize
class Finalize(unittest.TestCase):
    def test_metrics_after_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl, env = make_strict(tmp, fixed(strict_text())), FakeEnv()
            agent = FakeAgent(env)
            agent.messages = [{'role': 'system'}, {'role': 'user'},
                              {'role': 'assistant', 'content': 'cmd A'}, {'role': 'user', 'content': 'obs'}]
            arm_strict(ctl, env)
            ctl.deliver(agent)
            index = ctl.record['delivered_message_index']
            agent.messages += [
                {'role': 'assistant', 'content': 'cmd A'},                                   # exact repeat
                {'role': 'user', 'content': 'fmt', 'extra': {'interrupt_type': 'FormatError'}},
                {'role': 'assistant', 'content': 'cmd B'},
                {'role': 'user', 'content': 'obs'},
                {'role': 'assistant', 'content': 'cmd B'},                                   # exact repeat
            ]
            trig = sha256_bytes(SRC_BAD)
            events = [{'action': 3, 'source_sha256': trig, 'recognized_public_test': True,
                       'public_status': 'candidate_failure'},
                      {'action': 4, 'command': 'edit'},
                      {'action': 5, 'source_sha256': 'new', 'recognized_public_test': True, 'public_status': 'pass'},
                      {'action': None, 'judge_infrastructure_error': 'x'}]
            rec = ctl.finalize(agent.messages, events)
            self.assertEqual(index, 4)
            expected = {'controller': 'e2-strict', 'trigger_observed': True, 'trigger_kind': 'public_failure',
                        'frontier_requested': True, 'delivered': True, 'local_actions_after': 2,
                        'public_tests_after': 1, 'candidate_changed_after': True, 'public_pass_after': True,
                        'format_errors_after': 1, 'exact_repeats_after': 2, 'repair_mode_declared': 'LOCAL-FIX',
                        'assistant_messages_after': 3}
            self.assertEqual({k: rec[k] for k in expected}, expected)
            self.assertIsInstance(rec['frontier_wait_seconds'], float)
            json.dumps(rec, default=str)

    def test_metrics_when_not_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = make_strict(tmp, fixed(strict_text()))
            rec = ctl.finalize([], [])
            for key in ('controller', 'trigger_observed', 'trigger_kind', 'frontier_requested', 'delivered',
                        'frontier_wait_seconds', 'local_actions_after', 'public_tests_after',
                        'candidate_changed_after', 'public_pass_after', 'format_errors_after',
                        'exact_repeats_after', 'repair_mode_declared'):
                self.assertIn(key, rec)
            self.assertEqual((rec['delivered'], rec['local_actions_after'], rec['frontier_wait_seconds']),
                             (False, None, 0.0))

    def test_stall_finalize_counts_new_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = e2.E2StallController(fixed(STALL_TEXT), STATEMENT, 't', Path(tmp) / 'd', mode='neutral')
            env = FakeEnv()
            agent = FakeAgent(env)
            stall_error(ctl, env)
            ctl.deliver(agent)
            rec = ctl.finalize(agent.messages + [{'role': 'assistant', 'content': 'write'}],
                               [{'action': 4, 'source_sha256': 'abc', 'recognized_public_test': True,
                                 'public_status': 'candidate_failure'}])
            self.assertEqual((rec['controller'], rec['mode'], rec['candidate_changed_after'],
                              rec['public_pass_after'], rec['frontier_requested']),
                             ('e2-stall', 'neutral', True, False, False))


# ============================================================================= runner_v2 integration
class FakeCapture:
    def __init__(self):
        self.responses = []


class FakeModel:
    def __init__(self, script):
        self.script, self.capture = list(script), FakeCapture()

    def next(self):
        kind, payload = self.script.pop(0)
        if kind == 'length':
            from minisweagent.exceptions import FormatError
            self.capture.responses.append({'done_reason': 'length', 'message': {'content': payload}})
            raise FormatError({'role': 'user', 'content': 'format error', 'extra': {'interrupt_type': 'FormatError'}})
        self.capture.responses.append({'done_reason': 'stop', 'message': {'content': 'ok'}})
        return {'role': 'assistant', 'content': payload, 'extra': {'actions': [{'command': payload}]}}


class FakeRuntime:
    TEST_PATTERN = re.compile(r'python -I /public/check\.py')

    class v3:
        @staticmethod
        def limits(name):
            return RuntimeError(name)

    class Agent:
        def __init__(self, *args, instance_template='', model=None, env=None, **kwargs):
            self.model, self.env, self.messages = model, env, []
            self.n_consecutive_format_errors, self._start_time = 0, time.time()

        def add_messages(self, *messages):
            self.messages.extend(messages)
            return list(messages)

        def step(self):
            return self.execute_actions(self.query())

        def query(self):
            message = self.model.next()
            self.add_messages(message)
            return message

        def execute_actions(self, message):
            outs = [self.env.execute(a) for a in message['extra']['actions']]
            return self.add_messages(*({'role': 'user', 'content': o['output']} for o in outs))

        def loop(self, steps):
            from minisweagent.exceptions import FormatError
            for _ in range(steps):
                try:
                    self.step()
                    self.n_consecutive_format_errors = 0
                except FormatError as error:
                    self.n_consecutive_format_errors += 1
                    self.add_messages(*error.messages)

    class Environment:
        def __init__(self, *args, budget=None, deadline=None, container_timeout=None, **kwargs):
            self.budget, self.deadline, self.evidence = budget, deadline, []
            self.source, self.container_timeout = b'', container_timeout

        def snapshot(self):
            return self.source

        def execute(self, action, cwd='', *, timeout=None):
            self.budget.before()
            if action['command'].startswith('write '):
                self.source = action['command'][6:].encode().replace(b'\\n', b'\n')
            return {'output': 'done', 'returncode': 0}


class FakeJudge:
    def __init__(self):
        self.calls = []

    def run(self, task_id, code, timeout=None):
        self.calls.append(code)
        return failure(source=code) | {'task_id': task_id} if code == SRC_BAD else public_pass(code) | {'task_id': task_id}


class RunnerIntegration(unittest.TestCase):
    def setUp(self):
        from enhanced_de import runner_v2
        self.runner = runner_v2

    def build(self, ctl):
        attempts = []
        agent_cls, env_cls = self.runner.make_enhanced_classes(FakeRuntime, judge=FakeJudge(), task_id='t',
                                                               attempts=attempts, public_cases=PUBLIC_CASES,
                                                               e2_controller=ctl)
        env = env_cls(budget=FakeBudget(actions=0), deadline=time.monotonic() + 600, container_timeout='900s')
        return agent_cls, env, attempts

    def test_strict_and_advisory_through_runner_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = make_strict(tmp, fixed(strict_text()))
            agent_cls, env, attempts = self.build(ctl)
            self.assertEqual(env.container_timeout, f'{900 + 300 + 30}s')
            bad = SRC_BAD.decode().replace('\n', '\\n')
            good = SRC_GOOD.decode().replace('\n', '\\n')
            model = FakeModel([('cmd', 'write ' + bad), ('cmd', 'python -I /public/check.py'),
                               ('cmd', 'write ' + good), ('cmd', 'python -I /public/check.py')])
            agent = agent_cls(instance_template='{{task}}', model=model, env=env)
            agent.loop(2)
            self.assertTrue(ctl.record['delivered'])
            self.assertEqual(agent.messages[-1]['extra']['interrupt_type'], 'FrontierDiagnosisV2')
            self.assertEqual(env.evidence[-1]['returncode'], 1)
            agent.loop(2)
            last = env.evidence[-1]
            self.assertEqual((last['public_status'], last['returncode']), ('pass', 0))     # advisory never blocks
            self.assertIn(e2.ADVISORY_LABEL, last['output'])
            self.assertTrue(last['output'].startswith('PUBLIC TESTS: 2/2 passed'))
            rec = ctl.finalize(agent.messages, env.evidence)
            self.assertEqual((rec['public_tests_after'], rec['public_pass_after'], rec['candidate_changed_after']),
                             (1, True, True))
            self.assertEqual(len(attempts), 2)

    def test_stall_through_runner_hooks_keeps_format_error_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctl = e2.E2StallController(fixed(STALL_TEXT), STATEMENT, 't', Path(tmp) / 'd', mode='stall-diag',
                                       sandbox_runner=FakeSandbox())
            agent_cls, env, _ = self.build(ctl)
            model = FakeModel([('length', 'thinking ' * 900), ('length', 'still thinking ' * 900),
                               ('cmd', 'write ' + SRC_GOOD.decode().replace('\n', '\\n'))])
            agent = agent_cls(instance_template='{{task}}', model=model, env=env)
            agent.loop(2)
            self.assertEqual(agent.n_consecutive_format_errors, 2)
            self.assertTrue(ctl.record['trigger_observed'])
            self.assertIsNotNone(ctl.pending)
            self.assertEqual(ctl.pending['deliberation_chars_sent'], 4500)
            agent.loop(1)                         # query() delivers first, then the model writes the program
            self.assertTrue(ctl.record['delivered'])
            kinds = [(m.get('extra') or {}).get('interrupt_type') for m in agent.messages]
            self.assertEqual(kinds.index('FrontierDiagnosisV2'), 2)
            self.assertEqual(agent.n_consecutive_format_errors, 0)   # reset only by the stock clean step

    def test_build_controllers_matches_constructor_signatures(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            plan = plan_artifact(tmp)
            specs = {
                'strict': ({'kind': 'strict', 'provider_spec': {'provider': 'fixed', 'text': 'x'}, 'timeout': 77,
                            'enable_advisory_vchecks': False}, e2.E2StrictController),
                'stall': ({'kind': 'stall', 'provider_spec': {'provider': 'fixed', 'text': 'x'}, 'mode': 'c-late',
                           'plan_path': str(plan), 'enable_public_fallback': True}, e2.E2StallController),
                'review': ({'kind': 'review', 'provider_spec': {'provider': 'fixed', 'text': 'x'}},
                           e2.E2ReviewController),
            }
            for name, (spec, cls) in specs.items():
                _, ctl = self.runner._build_controllers({'e2': spec}, tmp, out, STATEMENT, 't')
                self.assertIsInstance(ctl, cls, name)
                self.assertEqual(ctl.out_dir, out / 'e2_diagnosis')
            _, strict = self.runner._build_controllers({'e2': specs['strict'][0]}, tmp, out, STATEMENT, 't')
            self.assertEqual((strict.max_wait_seconds, strict.enable_advisory_vchecks), (77, False))
            with self.assertRaises(ValueError):
                self.runner._build_controllers({'e2': specs['stall'][0]}, tmp, out, 'different statement', 't')

    def test_hook_signatures(self):
        params = lambda f: set(inspect.signature(f).parameters)  # noqa: E731
        for cls in (e2.E2StrictController, e2.E2StallController, e2.E2ReviewController):
            self.assertTrue({'result', 'source', 'digest', 'budget', 'deadline', 'public_cases', 'now'}
                            <= params(cls.on_public_result))
            self.assertTrue({'done_reason', 'raw_content', 'consecutive_errors', 'has_candidate', 'budget',
                             'deadline', 'now'} <= params(cls.on_format_error))
            self.assertTrue({'action', 'error'} <= params(cls.observe_infrastructure_error))
            self.assertEqual(list(inspect.signature(cls.post_public_advisory).parameters),
                             ['self', 'source', 'digest', 'public_status'])
            self.assertEqual(list(inspect.signature(cls.finalize).parameters), ['self', 'messages', 'events'])


# ============================================================================= real sandbox (opt-in)
@unittest.skipUnless(os.environ.get('CSC2108_DOCKER_TESTS') == '1', 'set CSC2108_DOCKER_TESTS=1 to use Docker')
class DockerSandbox(unittest.TestCase):
    def test_ok_wa_re_tle(self):
        ok = e2.docker_sandbox_runner(SRC_GOOD, '-4 -6\n', 3.0)
        self.assertEqual((ok['verdict'], ok['stdout'].strip()), ('OK', '-10'))
        self.assertEqual(e2.classify_run(e2.docker_sandbox_runner(SRC_BAD, '-4 -6\n', 3.0), '-10\n'), 'WA')
        self.assertEqual(e2.docker_sandbox_runner(b'raise SystemExit(3)\n', '', 3.0)['verdict'], 'RE')
        self.assertEqual(e2.docker_sandbox_runner(b'while True:\n    pass\n', '', 1.0)['verdict'], 'TLE')
        net = e2.docker_sandbox_runner(b'import socket\nsocket.create_connection(("1.1.1.1", 53), 2)\n', '', 3.0)
        self.assertEqual(net['verdict'], 'RE')
        write = e2.docker_sandbox_runner(b'open("/x", "w")\n', '', 3.0)
        self.assertEqual(write['verdict'], 'RE')


class DockerCommand(unittest.TestCase):
    def test_command_flags(self):
        cmd = e2.docker_command('e2-sbx-x', 2)
        joined = ' '.join(cmd[:-2])
        for flag in ('run --rm -i', '--network none', '--read-only', '--user 65534:65534', '--memory 512m',
                     '--pids-limit 64', 'python:3.11-slim-bookworm python -I -c'):
            self.assertIn(flag, joined)
        self.assertEqual(cmd[-1], '2.000')

    def test_missing_docker_is_infra(self):
        with mock.patch.object(e2.subprocess, 'run', side_effect=FileNotFoundError('docker')):
            self.assertEqual(e2.docker_sandbox_runner(b'print(1)', '', 1.0)['verdict'], 'INFRA')

    def test_backstop_timeout_removes_container(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if cmd[1] == 'run':
                raise subprocess.TimeoutExpired(cmd, 1)
            return SimpleNamespace(returncode=0, stdout=b'', stderr=b'')
        with mock.patch.object(e2.subprocess, 'run', side_effect=fake_run):
            out = e2.docker_sandbox_runner(b'print(1)', '', 1.0, backstop=0.1)
        self.assertEqual(out['verdict'], 'INFRA')
        self.assertEqual(calls[1][:3], ['docker', 'rm', '-f'])

    def test_returncode_mapping(self):
        def runner(rc, stderr=b''):
            proc = SimpleNamespace(returncode=rc, stdout=b'1\n', stderr=stderr)
            with mock.patch.object(e2.subprocess, 'run', return_value=proc):
                return e2.docker_sandbox_runner(b'print(1)', '', 1.0)['verdict']
        self.assertEqual(runner(0), 'OK')
        self.assertEqual(runner(1), 'RE')
        self.assertEqual(runner(124, b'[E2-SANDBOX-TLE]'), 'TLE')
        self.assertEqual(runner(124), 'RE')
        self.assertEqual(runner(125), 'INFRA')


if __name__ == '__main__':
    unittest.main()
