"""Offline D2 tests plus one end-to-end test using the local Docker image."""

import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

from guided_agent.common import read_json, sha256_bytes, sha256_text

from . import d2_contract as d2


MODULE = dedent('''\
    import math
    from random import Random
    from itertools import accumulate

    def validate_input(inp: str) -> bool:
        try:
            n, *values = map(int, inp.split())
            return 1 <= n <= 1000 and len(values) == n and all(0 <= x <= 9 for x in values)
        except ValueError:
            return False

    def gen_small(seed: int, n: int) -> list[str]:
        rng = Random(seed)
        cases = ['3\\n2 3 4\\n', '1\\n1\\n', '2\\n1 2\\n', '1\\n1\\n',
                 '1\\n-1\\n', ' ', '1\\n0\\n' + ' ' * 4001,
                 f'1\\n{rng.randrange(2, 10)}\\n']
        return cases[:n]

    def gen_stress(seed: int) -> list[str]:
        return ['1000\\n' + '1 ' * 1000 + '\\n', '999\\n' + '0 ' * 999 + '\\n']

    def check_postconditions(inp: str, out: str) -> list[tuple[str, str]]:
        try:
            value = int(out)
            if 0 <= value <= 9 * int(inp.split()[0]):
                return []
        except ValueError:
            pass
        return [('POST-1', 'Expected one integer within the sum bounds')]

    def metamorphic_pairs(seed: int, n: int) -> list[tuple[str, str, str, str]]:
        return [('POST-1', 'equal', '2\\n1 2\\n', '2\\n2 1\\n'),
                ('POST-1', 'le', '1\\n2\\n', '1\\n1\\n'),
                ('POST-1', 'equal', '5\\n0 0 0 0 0\\n', '1\\n0\\n'),
                ('POST-1', 'unknown', '1\\n1\\n', '1\\n1\\n'),
                ('POST-1', 'equal', '1\\n-1\\n', '1\\n1\\n')][:n]

    def reference_small(inp: str) -> str | None:
        n, *values = map(int, inp.split())
        if n > 4:
            return None
        total = list(accumulate(values))[-1]
        assert math.isfinite(total)
        return str(total) + '\\n'
''')
CONTRACT = '- POST-1. Output the sum of all input values as one integer.'
PUBLIC = [{'input': '1\n0\n', 'output': '0\n'}, {'input': '5\n1 2 3 4 5\n', 'output': '15\n'}]
ARTIFACT = {'task_id': 'sum', 'statement_sha256': sha256_text('Add the values.'),
            'contract_md': CONTRACT, 'module_code': MODULE}


def bundle_text(code=MODULE):
    return f'## Contract\n{CONTRACT}\n\n## Verification Module\n```python\n{code.rstrip()}\n```\n'


def ok(value):
    return {'status': 'ok', 'value': value}


def calibration(ref, *, validator=True, property_outcome=None):
    return {'validation': ok(validator), 'property': ok([]) if property_outcome is None else property_outcome,
            'reference': ref}


def case(inp, ref):
    return {'input': inp, 'ref_output': ref}


def pair(relation, first, second):
    return {'post_id': 'POST-1', 'relation': relation, 'input1': first, 'input2': second}


def fixture_bank():
    return ARTIFACT | {'oracle_enabled': True, 'property_enabled': True, 'stress_enabled': True,
                       'small_pools': [[case('long input\n', '3'), case('x\n', '1'), case('skipped\n', None)],
                                       [case('pool two\n', '1')]],
                       'stress_inputs': ['stress input\n'],
                       'metamorphic_pairs': [pair('equal', 'x\n', 'permuted\n')]}


class CandidateRunner:
    """Deterministic test double for both isolated dispatchers; executes no source."""

    def __init__(self, *, outputs=None, statuses=None, properties=None):
        self.outputs = outputs or {}
        self.statuses = statuses or {}
        self.properties = properties or {}
        self.calls = []

    def __call__(self, script, payload, *, timeout):
        self.calls.append((script, payload, timeout))
        inputs = [item['input'] for item in payload['cases']]
        if payload['operation'] == 'candidate':
            return [{'status': self.statuses.get(inp, 'ok'), 'output': self.outputs.get(inp, '0'),
                     'stderr': 'fixture error' if self.statuses.get(inp) == 'error' else ''} for inp in inputs]
        if payload['operation'] == 'properties':
            return [self.properties.get(inp, ok([])) for inp in inputs]
        raise AssertionError(payload['operation'])


class BundleTests(unittest.TestCase):
    def test_parse_crlf_and_safe_imports(self):
        contract, code = d2.parse_bundle_response(bundle_text().replace('\n', '\r\n'))
        self.assertEqual((contract, code), (CONTRACT, MODULE.strip()))

    def test_allows_pure_arithmetic_module_constants(self):
        extras = 'LIMIT = 10**18\nMOD = 998_244_353\nBIG = LIMIT + 1\nMASK = 1 << 20\nDIRS = [(-1, 0), (1, 0)]\n'
        contract, code = d2.parse_bundle_response(bundle_text(extras + MODULE))
        self.assertIn('LIMIT = 10**18', code)
        with self.assertRaises(ValueError):
            d2.parse_bundle_response(bundle_text('HUGE = 10**999\n' + MODULE))

    def test_allows_lambda_and_lru_cache_on_helpers_only(self):
        extra = (
            'from functools import lru_cache\n'
            '@lru_cache(maxsize=None)\n'
            'def _helper(n):\n'
            '    return sorted(range(n), key=lambda x: -x)\n'
        )
        _, code = d2.parse_bundle_response(bundle_text(extra + MODULE))
        self.assertIn('lambda', code)
        with self.assertRaises(ValueError):
            d2.parse_bundle_response(bundle_text('@unknown_dec\ndef _h():\n    return 1\n' + MODULE))

    def test_parse_rejects_extra_sections_and_fences(self):
        for text in ('preface\n' + bundle_text(), bundle_text() + 'afterword',
                     bundle_text().replace(CONTRACT, 'No identifiers here.'),
                     bundle_text().replace(CONTRACT, f'{CONTRACT}\n## Extra\nExtra'),
                     bundle_text().replace('```python', '```text')):
            with self.subTest(text=text[:90]), self.assertRaises(ValueError):
                d2.parse_bundle_response(text)

    def test_rejects_syntax_error_and_missing_or_rebound_function(self):
        with self.assertRaises(SyntaxError):
            d2.parse_bundle_response(bundle_text(MODULE + '\ndef bad(:\n    pass\n'))
        with self.assertRaises(SyntaxError):
            d2.parse_bundle_response(bundle_text(MODULE + '\ndef bad():\n    break\n'))
        for code in (MODULE.replace('def validate_input', 'def another_name'),
                     MODULE + '\nvalidate_input = None\n',
                     MODULE + '\nfrom math import sqrt as validate_input\n',
                     MODULE + '\ndef gen_stress(seed):\n    return []\n'):
            with self.subTest(code=code[-130:]), self.assertRaises(ValueError):
                d2.parse_bundle_response(bundle_text(code))

    def test_rejects_unsafe_imports_and_reflection(self):
        unsafe_imports = ('os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'shutil',
                          'pathlib', 'ctypes', 'importlib', 'builtins', 'xml.etree', 're._compiler')
        for imp in unsafe_imports:
            with self.subTest(imp=imp), self.assertRaises(ValueError):
                d2.parse_bundle_response(bundle_text(f'import {imp} as innocent\n{MODULE}'))
        for code in ('from random import SystemRandom', 'from random import *', 'from . import math',
                     'from copy import dispatch_table', 'open("file")', 'VALUE = Random(0)'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                d2.parse_bundle_response(bundle_text(f'{MODULE}\n{code}\n'))
        for expr in ('open("file")', 'exec("pass")', 'eval("0")', '__import__("os")',
                     'getattr(math, "_private")', 'math.__dict__', '(1).__class__',
                     '"{0.__class__}".format(1)', 'globals()', 'setattr(math, "pi", 0)'):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                d2.parse_bundle_response(bundle_text(f'{MODULE}\ndef unsafe():\n    return {expr}\n'))

    def test_fixed_authoring_is_write_once_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'nested' / 'd2.json'
            args = dict(statement='Public statement Ω', task_id='sum', out_path=path,
                        provider='fixed', fixed_response=bundle_text())
            result = d2.author_d2_bundle(**args)
            self.assertEqual(read_json(path), result)
            self.assertEqual(result['statement_sha256'], sha256_text(args['statement']))
            self.assertEqual(result['prompt_sha256'], sha256_text(d2.D2_BUNDLE_V1))
            self.assertEqual(result['response_sha256'], sha256_text(bundle_text()))
            with self.assertRaises(FileExistsError):
                d2.author_d2_bundle(**(args | {'statement': 'Different statement'}))
            self.assertEqual(read_json(path), result)
            self.assertFalse(path.with_name('d2.json.lock').exists())

    def test_guarded_providers_receive_statement_and_one_call(self):
        statement = 'The statement and its public samples only.'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            kwargs = dict(statement=statement, task_id='sum', work_root=root / 'work')
            with patch.object(d2.ledger_guard, 'isolated_codex_infer',
                              return_value={'text': bundle_text(), 'isolation': {'mechanism': 'fixture'}}) as codex:
                d2.author_d2_bundle(**kwargs, out_path=root / 'codex.json')
                codex.assert_called_once()
                self.assertEqual(codex.call_args.kwargs['system'], d2.D2_BUNDLE_V1)
                self.assertEqual(codex.call_args.kwargs['user'], statement)
            result = {'text': bundle_text(), 'finish_reason': 'stop', 'ledger_index': 4}
            with patch.object(d2.ledger_guard, 'guarded_api_chat', return_value=result) as api:
                path = root / 'api.json'
                with self.assertRaisesRegex(ValueError, 'ledger_path'):
                    d2.author_d2_bundle(**kwargs, out_path=path, provider='api')
                api.assert_not_called()
                ledger = root / 'ledger.json'
                artifact = d2.author_d2_bundle(**kwargs, out_path=path, provider='api', ledger_path=ledger)
                api.assert_called_once()
                self.assertEqual(api.call_args.kwargs['ledger_path'], ledger)
                self.assertEqual(api.call_args.kwargs['messages'], [
                    {'role': 'system', 'content': d2.D2_BUNDLE_V1}, {'role': 'user', 'content': statement},
                ])
                self.assertEqual(artifact['ledger_index'], 4)

    def test_incomplete_api_response_and_contention_leave_artifact_intact(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bundle.json'
            lock = path.with_name('bundle.json.lock')
            args = dict(statement='Statement', task_id='sum', out_path=path,
                        provider='api', ledger_path=Path(temp) / 'ledger.json')
            with patch.object(d2.ledger_guard, 'guarded_api_chat', return_value={'finish_reason': 'length'}) as api:
                lock.touch()
                with self.assertRaises(FileExistsError):
                    d2.author_d2_bundle(**args)
                api.assert_not_called()
                lock.unlink()
                with self.assertRaisesRegex(RuntimeError, 'finish_reason=length'):
                    d2.author_d2_bundle(**args)
                api.assert_called_once()
            self.assertFalse(path.exists())
            self.assertFalse(lock.exists())


class DockerCommandTests(unittest.TestCase):
    def test_command_has_isolation_flags_and_passes_payload_only_via_stdin(self):
        script = 'trusted dispatcher'
        payload = {'module_code': 'unicode Ω payload'}
        with patch.object(d2.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, stdout=b'{"ok": true}', stderr=b'')) as run:
            self.assertEqual(d2.run_in_throwaway_docker(script, payload, timeout=9, memory='256m'), {'ok': True})
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ['docker', 'run', '--rm', '-i'])
        self.assertEqual(command[-5:], ['python:3.11-slim-bookworm', 'python', '-I', '-c', script])
        for flag, value in {'--network': 'none', '--user': '65534:65534', '--memory': '256m',
                            '--pull': 'never', '--pids-limit': '64',
                            '--tmpfs': '/tmp:rw,noexec,nosuid,size=64m'}.items():
            self.assertEqual(command[command.index(flag) + 1], value)
        self.assertIn('--read-only', command)
        self.assertTrue({'-v', '--mount', '--privileged'}.isdisjoint(command))
        self.assertEqual(json.loads(run.call_args.kwargs['input']), payload)
        self.assertEqual(run.call_args.kwargs['timeout'], 9)

    def test_docker_timeout_cleans_only_its_own_container(self):
        with patch.object(d2.subprocess, 'run', side_effect=[subprocess.TimeoutExpired('docker', 1),
                                                             subprocess.CompletedProcess([], 0)]) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                d2.run_in_throwaway_docker('script', {}, timeout=1)
        initial, cleanup = [call.args[0] for call in run.call_args_list]
        self.assertEqual(cleanup, ['docker', 'rm', '-f', initial[initial.index('--name') + 1]])

    def test_invalid_dispatcher_output_is_not_a_candidate_failure(self):
        for result in (subprocess.CompletedProcess([], 125, stdout=b'', stderr=b'engine offline'),
                       subprocess.CompletedProcess([], 0, stdout=b'broken JSON', stderr=b'')):
            with self.subTest(result=result), patch.object(d2.subprocess, 'run', return_value=result):
                with self.assertRaisesRegex(RuntimeError, 'dispatcher'):
                    d2.run_in_throwaway_docker('script', {})


class BankCompilationTests(unittest.TestCase):
    def test_calibration_uses_judge_comparison_and_skips_unknown_references(self):
        outcomes = [calibration(ok('0.0\n')), calibration(ok(None)),
                    calibration({'status': 'timeout'}), calibration({'status': 'error'})]
        generated = {
            'small_pools': [[{'input': 'x', 'reference': ok('1')}, {'input': 'yy', 'reference': ok(None)},
                             {'input': 'zzz', 'reference': {'status': 'timeout'}},
                             {'input': 'wwww', 'reference': {'status': 'error'}}], [], []],
            'metamorphic_pairs': [pair('le', 'a', 'b') | {'references': [ok('1'), ok('2')]},
                                  pair('ge', 'a', 'b') | {'references': [ok('1'), ok('2')]},
                                  pair('equal', 'a', 'c') | {'references': [ok('1'), ok(None)]}],
            'stress_inputs': ['large'], 'stats': {},
        }
        with patch.object(d2, 'run_in_throwaway_docker', side_effect=[outcomes, generated]) as docker:
            bank = d2.compile_d2_bank(ARTIFACT, PUBLIC * 2)
        self.assertTrue(all(bank[key] for key in ('validator_public_ok', 'property_enabled',
                                                 'oracle_enabled', 'stress_enabled')))
        self.assertEqual(bank['small_pools'][0], [case('x', '1'), case('yy', None), case('zzz', None), case('wwww', None)])
        self.assertEqual(bank['metamorphic_pairs'], [pair('le', 'a', 'b')])
        self.assertEqual(bank['compilation_stats']['public'], {
            'cases': 4, 'validator_accepted': 4, 'property_passed': 4, 'reference_matched': 1,
            'reference_mismatched': 0, 'reference_none': 1, 'reference_timeout': 1, 'reference_error': 1,
        })
        self.assertEqual(bank['compilation_stats']['metamorphic'], {
            'accepted': 1, 'reference_mismatched': 1, 'reference_unavailable': 1,
        })
        first, second = [call.args[1] for call in docker.call_args_list]
        self.assertEqual(first['public_cases'], PUBLIC * 2)
        self.assertEqual(second['pool_seeds'], [101, 202, 303])
        self.assertTrue(second['oracle_enabled'])
        self.assertEqual(json.loads(json.dumps(bank)), bank)

    def test_public_failures_disable_only_the_affected_checks(self):
        def runner(script, payload, *, timeout):
            if payload['operation'] == 'calibrate':
                return [calibration(ok('0')), calibration(ok('wrong output'), validator=False,
                                                          property_outcome=ok([['POST-1', 'false alarm']]))]
            self.assertFalse(payload['validator_public_ok'])
            self.assertFalse(payload['oracle_enabled'])
            return {'small_pools': [[{'input': 'unfiltered', 'reference': None}]],
                    'metamorphic_pairs': [pair('equal', 'a', 'b') | {'references': []}],
                    'stress_inputs': [], 'stats': {}}

        bank = d2.compile_d2_bank(ARTIFACT, PUBLIC, pool_seeds=(101,), docker_runner=runner)
        self.assertFalse(any(bank[key] for key in ('validator_public_ok', 'property_enabled',
                                                  'oracle_enabled', 'stress_enabled')))
        self.assertEqual(bank['small_pools'], [[case('unfiltered', None)]])
        self.assertEqual(bank['metamorphic_pairs'], [pair('equal', 'a', 'b')])
        self.assertEqual(bank['compilation_stats']['public']['reference_mismatched'], 1)

    def test_no_public_reference_match_disables_oracle(self):
        generated = {'small_pools': [], 'metamorphic_pairs': [], 'stress_inputs': [], 'stats': {}}
        with patch.object(d2, 'run_in_throwaway_docker', side_effect=[[calibration(ok(None))], generated]):
            bank = d2.compile_d2_bank(ARTIFACT, PUBLIC[:1], pool_seeds=())
        self.assertFalse(bank['oracle_enabled'])
        self.assertTrue(bank['property_enabled'])

    def test_revalidates_artifact_before_any_docker_dispatch(self):
        with patch.object(d2, 'run_in_throwaway_docker') as docker:
            with self.assertRaisesRegex(ValueError, 'Unsafe import'):
                d2.compile_d2_bank(ARTIFACT | {'module_code': MODULE + '\nimport os'}, PUBLIC)
            docker.assert_not_called()


class CandidateAndGateTests(unittest.TestCase):
    def test_inputs_stress_reports_only_re_and_tle_with_respective_budgets(self):
        runner = CandidateRunner(statuses={'x\n': 'error', 'stress input\n': 'timeout'})
        result = d2.evaluate_candidate_against_bank(b'fixture-source', fixture_bank(), mode='inputs-stress',
                                                   small_timeout=0.5, stress_timeout=3, docker_runner=runner)
        self.assertFalse(result['passed'])
        self.assertEqual(result['first_failure']['reason'], 'RE')
        self.assertEqual(result['first_failure']['detail'], 'fixture error')
        self.assertEqual(result['counts'], {'small_ran': 3, 'stress_ran': 1, 'meta_ran': 0, 're': 1, 'tle': 1,
                                            'post_fail': 0, 'meta_fail': 0, 'oracle_mismatch': 0})
        ((_, payload, _),) = runner.calls
        self.assertEqual(base64.b64decode(payload['source_b64']), b'fixture-source')
        self.assertNotIn('module_code', payload)
        self.assertEqual({item['input']: item['timeout'] for item in payload['cases']}, {
            'stress input\n': 3, 'long input\n': 0.5, 'x\n': 0.5, 'skipped\n': 0.5,
        })

    def test_oracle_returns_smallest_mismatch_and_skips_unknown_expected_output(self):
        runner = CandidateRunner(outputs={'long input\n': '4', 'x\n': '2', 'skipped\n': 'arbitrary'})
        result = d2.evaluate_candidate_against_bank(b'fixture', fixture_bank(), docker_runner=runner)
        self.assertEqual(result['first_failure'], {'reason': 'oracle_mismatch', 'suite': 'small',
                                                  'input': 'x\n', 'output': '2', 'expected_output': '1'})
        self.assertEqual(result['counts']['oracle_mismatch'], 2)
        self.assertEqual(len(runner.calls), 1)
        bank = fixture_bank() | {'oracle_enabled': False}
        self.assertTrue(d2.evaluate_candidate_against_bank(b'fixture', bank, docker_runner=runner)['passed'])

    def test_property_checks_run_in_separate_dispatcher_and_skip_errors(self):
        runner = CandidateRunner(outputs={'x\n': '-4', 'permuted\n': '5'}, statuses={'skipped\n': 'timeout'},
                                 properties={'x\n': ok([['POST-1', 'out of bounds']]),
                                             'long input\n': {'status': 'error'},
                                             'stress input\n': {'status': 'timeout'}})
        result = d2.evaluate_candidate_against_bank(b'fixture', fixture_bank(), mode='property', docker_runner=runner)
        self.assertEqual(result['first_failure']['reason'], 'postcondition')
        self.assertEqual(result['first_failure']['post_id'], 'POST-1')
        self.assertEqual(result['counts'], {'small_ran': 3, 'stress_ran': 1, 'meta_ran': 1, 're': 0, 'tle': 1,
                                            'post_fail': 1, 'meta_fail': 1, 'oracle_mismatch': 0})
        ((candidate_script, candidate, _), (module_script, properties, _)) = runner.calls
        self.assertNotEqual(candidate_script, module_script)
        self.assertNotIn('source_b64', properties)
        self.assertNotIn('module_code', candidate)
        self.assertEqual(properties['module_code'], MODULE)
        self.assertNotIn('skipped\n', [c['input'] for c in properties['cases']])

    def test_metamorphic_checker_runs_when_postconditions_disabled(self):
        bank = fixture_bank() | {'property_enabled': False}
        runner = CandidateRunner(outputs={'x\n': '2', 'permuted\n': '1'})
        result = d2.evaluate_candidate_against_bank(b'fixture', bank, mode='property', docker_runner=runner)
        failure = result['first_failure']
        self.assertEqual(failure['reason'], 'metamorphic')
        self.assertEqual((failure['relation'], failure['input2'], failure['output2']), ('equal', 'permuted\n', '1'))
        self.assertEqual(len(runner.calls), 1)

    def test_closed_relation_semantics(self):
        for relation, first, second, expected in (
            ('equal', ' 5.0\n', '5', True), ('equal', 'a', 'b', False),
            ('le', '-2', '-1', True), ('le', '2', '1', False), ('ge', '2', '1', True),
            ('ge', '2 1', '1', False), ('le', 'NaN', '1', False), ('ge', 'Infinity', '1', False),
            ('same_yes_no', 'YE s', 'yes', False), ('same_yes_no', 'yes\n', 'YES', True),
            ('same_yes_no', 'no', 'yes', False), ('same_yes_no', 'maybe', 'maybe', False),
            ('unknown', '1', '1', False),
        ):
            with self.subTest(relation=relation, first=first, second=second):
                self.assertEqual(d2._relation_holds(relation, first, second), expected)

    def test_gate_rotates_pools_even_for_same_digest_and_is_silent_on_pass(self):
        runner = CandidateRunner(outputs={'long input\n': '3', 'x\n': '0', 'pool two\n': '1.0'})
        gate = d2.D2GateChecker(fixture_bank(), docker_runner=runner)
        first, warning = gate.on_public_pass(b'fixture', 'same_digest')
        second, silence = gate.on_public_pass(b'fixture', 'same_digest')
        third, _ = gate.on_public_pass(b'fixture', 'same_digest')
        self.assertEqual([entry['pool_index'] for entry in (first, second, third)], [0, 1, 0])
        self.assertEqual(second['source_sha256'], 'same_digest')
        self.assertEqual(silence, '')
        self.assertIn('supplementary, NOT verified; judge-public above is authoritative', warning)
        self.assertIn("Input: 'x\\n'", warning)
        self.assertIn("Expected output: '1'", warning)
        self.assertIn('Fix /workspace/solution.py and retest with python -I /public/check.py.', warning)
        self.assertNotIn('long input', warning)
        self.assertEqual((gate.summary()['checks'], gate.summary()['failed']), (3, 2))

    def test_gate_excerpt_bounds_large_inputs_and_notes_timeouts(self):
        inp = 'y' * 3000
        bank = fixture_bank() | {'small_pools': [], 'stress_inputs': [inp]}
        runner = CandidateRunner(statuses={inp: 'timeout'})
        gate = d2.D2GateChecker(bank, mode='inputs-stress', docker_runner=runner)
        entry, text = gate.on_public_pass(b'fixture', 'digest')
        self.assertEqual(entry['first_failure']['input'], inp)
        self.assertIn('3000 characters total', text)
        self.assertIn('TLE after 4 seconds.', text)
        self.assertLess(len(text), 950)

    def test_gate_records_unavailable_sandbox_without_disturbing_public_pass(self):
        failures = (d2.D2SandboxError('engine offline'), subprocess.TimeoutExpired('docker', 25))
        for failure in failures:
            with self.subTest(failure=failure), patch.object(d2, 'run_in_throwaway_docker', side_effect=failure):
                gate = d2.D2GateChecker(fixture_bank())
                entry, text = gate.on_public_pass(b'fixture', 'digest')
            self.assertEqual(text, '')
            self.assertIsNone(entry['passed'])
            self.assertIsNone(entry['first_failure'])
            self.assertIn('sandbox_error', entry)
            self.assertEqual((gate.summary()['unavailable'], gate.summary()['failed']), (1, 0))

    def test_empty_bank_does_not_start_a_container(self):
        bank = fixture_bank() | {'small_pools': [], 'stress_enabled': False}
        runner = CandidateRunner()
        self.assertTrue(d2.evaluate_candidate_against_bank(b'fixture', bank, docker_runner=runner)['passed'])
        self.assertEqual(runner.calls, [])


class MutantStudyTests(unittest.TestCase):
    def test_scores_all_references_and_mutants_in_each_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def submission(name, verdict):
                source = name.encode()
                path = root / (name + '.py')
                path.write_bytes(source)
                return {'rel_path': path.name, 'submission_sha256': sha256_bytes(source), 'dominant_verdict': verdict}

            task = {'task_id': 'sum', 'references': [submission('good', 'AC'), submission('false', 'AC')],
                    'public_pass_mutants': [submission('wrong', 'WA'), submission('slow', 'TLE'),
                                             submission('crash', 'RE'), submission('meta', 'WA')],
                    'public_fail_mutants': [submission('format', 'WA')]}
            reasons = {b'false': {'property': 'postcondition'}, b'wrong': {'oracle': 'oracle_mismatch'},
                       b'slow': dict.fromkeys(d2._MODES, 'TLE'), b'crash': dict.fromkeys(d2._MODES, 'RE'),
                       b'meta': {'property': 'metamorphic'}, b'format': {'property': 'postcondition'}}

            def evaluate(source, bank, *, mode, pool_index, **kwargs):
                self.assertEqual(pool_index, 1)
                reason = reasons.get(source, {}).get(mode)
                failure = {'reason': reason, 'input': 'example'} if reason else None
                return {'passed': failure is None, 'first_failure': failure}

            with patch.object(d2, 'REPO', root), patch.object(d2, 'evaluate_candidate_against_bank',
                                                            side_effect=evaluate) as run:
                report = d2.evaluate_bank_on_mutant_pool_task(fixture_bank(), task, include_public_fail_mutants=True,
                                                              pool_index=1)
                self.assertEqual(run.call_count, 21)
                run.reset_mock()
                default = d2.evaluate_bank_on_mutant_pool_task(fixture_bank(), task, pool_index=1)
                self.assertEqual(run.call_count, 18)
                self.assertNotIn('public_fail_mutants', default['modes']['property'])

            prop = report['modes']['property']
            self.assertEqual(prop['references'], {'total': 2, 'false_rejected': 1, 'false_rejection_rate': 0.5,
                                                  'false_rejections': [{
                                                      'submission_sha256': sha256_bytes(b'false'),
                                                      'counterexample': {'reason': 'postcondition', 'input': 'example'},
                                                  }]})
            self.assertEqual(prop['public_fail_mutants']['kill_rate'], 1.0)
            self.assertEqual(prop['public_fail_mutants']['kill_rate_by_reason']['postcondition'], 1.0)
            self.assertEqual(report['modes']['inputs-stress']['public_pass_mutants']['kill_rate'], 0.5)
            oracle = report['modes']['oracle']['public_pass_mutants']
            self.assertEqual((oracle['killed'], oracle['survived'], oracle['kill_rate']), (3, 1, 0.75))
            self.assertEqual(oracle['by_reason']['oracle_mismatch'], 1)
            self.assertEqual(oracle['by_hidden_verdict']['WA']['kill_rate'], 0.5)
            self.assertEqual(oracle['by_hidden_verdict']['TLE']['by_reason']['TLE'], 1)
            self.assertEqual(oracle['by_hidden_verdict']['RE']['kill_rate_by_reason']['RE'], 1.0)
            self.assertEqual(prop['public_pass_mutants']['by_reason']['metamorphic'], 1)

    def test_digest_and_task_mismatch_do_not_run_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'mutant.py'
            path.write_bytes(b'changed')
            task = {'task_id': 'sum', 'references': [{'rel_path': path.name, 'submission_sha256': 'fixture-digest'}]}
            with patch.object(d2, 'REPO', root), patch.object(d2, 'evaluate_candidate_against_bank') as run:
                with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                    d2.evaluate_bank_on_mutant_pool_task(fixture_bank(), task)
                with self.assertRaisesRegex(ValueError, 'same task'):
                    d2.evaluate_bank_on_mutant_pool_task(fixture_bank(), task | {'task_id': 'other'})
                run.assert_not_called()


class DockerIsolationSmokeTest(unittest.TestCase):
    def test_offline_bundle_compilation_reference_and_mutant(self):
        # Only this test uses real Docker. All code below travels in JSON stdin to docker run.
        actual_run = d2.subprocess.run
        docker_calls = []

        def audited_run(command, **kwargs):
            self.assertEqual(command[:2], ['docker', 'run'])
            self.assertEqual(command[command.index('--network') + 1], 'none')
            self.assertEqual(command[command.index('--user') + 1], '65534:65534')
            self.assertIn('--read-only', command)
            self.assertTrue({'--mount', '-v'}.isdisjoint(command))
            payload = json.loads(kwargs['input'])
            docker_calls.append((command[command.index('--name') + 1], payload['operation']))
            self.assertNotIn(MODULE.strip(), command[-1])
            return actual_run(command, **kwargs)

        source = dedent('''\
            import os
            import sys
            from pathlib import Path

            assert sys.platform == 'linux' and os.getuid() == 65534 and os.getgid() == 65534
            assert os.statvfs('/').f_flag & os.ST_RDONLY
            assert set(os.listdir('/sys/class/net')) == {'lo'}
            assert Path.cwd().parent == Path('/tmp')
            n, *values = map(int, sys.stdin.buffer.read().split())
            print(sum(values))
        ''').encode()
        mutant = source.replace(b'sum(values)', b'sum(values) if n != 1 or values[0] == 0 else 0')
        with patch.object(d2.subprocess, 'run', side_effect=audited_run):
            bank = d2.compile_d2_bank(ARTIFACT, PUBLIC, pool_seeds=(101,), cases_per_pool=8)
            reference = d2.evaluate_candidate_against_bank(source, bank, mode='property')
            result = d2.evaluate_candidate_against_bank(mutant, bank, mode='oracle')

        self.assertEqual([operation for _, operation in docker_calls],
                         ['calibrate', 'materialize', 'candidate', 'properties', 'candidate'])
        self.assertEqual(len({name for name, _ in docker_calls}), len(docker_calls))
        self.assertTrue(bank['oracle_enabled'])
        self.assertTrue(bank['property_enabled'])
        self.assertEqual(len(bank['stress_inputs']), 2)
        pool = bank['small_pools'][0]
        self.assertEqual(len(pool), 4)
        self.assertEqual([len(c['input']) for c in pool], sorted(len(c['input']) for c in pool))
        self.assertEqual(bank['metamorphic_pairs'], [pair('equal', '2\n1 2\n', '2\n2 1\n')])
        self.assertEqual(bank['compilation_stats']['metamorphic']['reference_mismatched'], 1)
        self.assertEqual(bank['compilation_stats']['metamorphic']['reference_unavailable'], 1)
        self.assertTrue(reference['passed'], reference)
        self.assertEqual(reference['counts']['meta_ran'], 1)
        self.assertFalse(result['passed'])
        self.assertEqual(result['first_failure']['reason'], 'oracle_mismatch')
        self.assertEqual(result['first_failure']['input'], '1\n1\n')
        self.assertEqual(result['first_failure']['expected_output'], '1\n')


if __name__ == '__main__':
    unittest.main()
