"""Pass-4 tests: versioned shared-agent configurations, D-active contract checks and diagnosis-v2.

Offline tests: no model, Docker or network.     python -m unittest guided_agent.test_pass4
Integration tests (real frozen runtime, real Docker sandbox and judge-public, SCRIPTED coder, no inference, no
frontier calls) run only with CSC2108_INTEGRATION=1 and CSC2108_STUDY_ROOT pointing at a prepared study holding
the synthetic fixture (python -m guided_agent prepare-fixture).
"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from guided_agent import agent_config, contract_checks, guidance, integrity
from guided_agent.common import PROFILE
from guided_agent.test_pass2 import FIX, GOOD, SUBMIT, TEST, WRONG, block

CONTRACT_TEXT = ('## Description\nPrint A+B.\n## Preconditions\nPRE-1 (Unverified) two integers.\n## Postconditions\n'
                 'POST-1 (Unverified) The output equals A+B, sign included.\n## Test suggestions\n'
                 'K-1 (POST-1) — Dropping the sign of a negative operand.\n\n  Stdin\n  ```text\n  -5 1\n  ```\n'
                 '  Expected stdout\n  ```text\n  -4\n  ```\n\n'
                 'K-2 (POST-1) — A deliberately wrong proposal (tests the unverified label).\n\n'
                 '  Stdin\n  ```text\n  2 2\n  ```\n  Expected stdout\n  ```text\n  5\n  ```\n\n'
                 'K-3 (POST-1) — Same input as a public case with a contradicting expectation.\n\n'
                 '  Stdin\n  ```text\n  PUBLIC\n  ```\n  Expected stdout\n  ```text\n  999999\n  ```\n'
                 '## Unspecified behavior\nNone.\n')


class AgentConfigurations(unittest.TestCase):
    def test_frozen_is_empty_and_ids_are_validated(self):
        agent_id, definition, digest = agent_config.resolve(None)
        self.assertEqual((agent_id, definition), ('frozen-v6', {}))
        self.assertEqual(len(digest), 64)
        with self.assertRaises(ValueError):
            agent_config.resolve('l9-unknown')
        # every non-frozen configuration changes exactly one mechanism
        for name, definition in agent_config.AGENT_CONFIGS.items():
            self.assertLessEqual(len(definition), 1, name)

    def test_profile_overlay_touches_only_the_frozen_profile(self):
        profiles = {PROFILE: {'context': 16384, 'output_tokens': 4096, 'thinking': False}, 'other': {'context': 8192}}
        read = agent_config.profile_reader(lambda path: profiles if Path(path).name == 'profiles.json' else {'x': 1},
                                           {'output_tokens': 8192, 'context': 32768})
        changed = read('local_eval_v2/profiles.json')
        self.assertEqual(changed[PROFILE], {'context': 32768, 'output_tokens': 8192, 'thinking': False})
        self.assertEqual(changed['other'], {'context': 8192})
        self.assertEqual(profiles[PROFILE]['output_tokens'], 4096)       # the frozen dict is never mutated
        self.assertEqual(read('task.json'), {'x': 1})

    def test_self_plan_uses_the_frozen_sampler_and_records_truncation(self):
        bodies = []

        def caller(body):
            bodies.append(body)
            return {'message': {'content': '## Observations\n1. x\n## Solution sketch\n1. y'}, 'done_reason': 'length',
                    'eval_count': 4096, 'prompt_eval_count': 300, 'eval_duration': 4e10}
        profile = {'context': 16384, 'temperature': 0.2, 'sampler': {'top_k': 40, 'top_p': 0.9}}
        with tempfile.TemporaryDirectory() as tmp:
            planner = agent_config.SelfPlanner(statement='S', seed=2109, profile=profile, endpoint='http://x', out_dir=tmp,
                                               prompt_text='P', output_tokens=4096, timeout=5, caller=caller)
            text = planner()
            saved = json.loads((Path(tmp) / 'self-plan.json').read_text(encoding='utf-8'))
        body = bodies[0]
        self.assertEqual(body['options'], {'top_k': 40, 'top_p': 0.9, 'num_ctx': 16384, 'num_predict': 4096,
                                           'temperature': 0.2, 'seed': 2109})
        self.assertIs(body['think'], False)
        self.assertEqual(body['messages'][0], {'role': 'system', 'content': 'P'})
        self.assertTrue(text.endswith('[This plan was cut off at the output limit.]'))
        self.assertTrue(saved['truncated'] and saved['delivered'])
        self.assertEqual((saved['completion_tokens'], saved['eval_seconds']), (4096, 40.0))

    def test_self_plan_failure_is_recorded_and_not_retried(self):
        calls = []

        def caller(body):
            calls.append(1)
            raise TimeoutError('simulated')
        with tempfile.TemporaryDirectory() as tmp:
            planner = agent_config.SelfPlanner(statement='S', seed=1, profile={'context': 16384}, endpoint='x',
                                               out_dir=tmp, prompt_text='P', output_tokens=10, timeout=1, caller=caller)
            self.assertIsNone(planner())
        self.assertEqual(len(calls), 1)
        self.assertIn('TimeoutError', planner.record['error'])

    def test_self_plan_template_keeps_the_condition_block(self):
        a = agent_config.self_plan_template(None, None)
        c = agent_config.self_plan_template(guidance.INJECTION['inject-v1']['plan'], 'plan')
        self.assertTrue(a.startswith('{{task}}\n\n## Your own plan') and a.endswith('{{selfplan}}'))
        self.assertIn('{{guide}}', c)
        self.assertLess(c.index('{{guide}}'), c.index('{{selfplan}}'))
        self.assertIn("the stronger model's plan", c)

    def test_receipts_report_state_and_never_repeat_byte_for_byte(self):
        receipts = agent_config.Receipts(20)
        first = receipts.after_command(actions=1, before=None, after=b'print(1)\n', syntax='Python syntax: OK.')
        test = receipts.after_test(actions=2, digest=__import__('hashlib').sha256(b'print(1)\n').hexdigest(),
                                   result={'status': 'candidate_failure', 'passed': 0, 'total': 2})
        same1 = receipts.after_command(actions=3, before=b'print(1)\n', after=b'print(1)\n', syntax='')
        same2 = receipts.after_command(actions=4, before=b'print(1)\n', after=b'print(1)\n', syntax='')
        changed = receipts.after_command(actions=5, before=b'print(1)\n', after=b'print(2)\n', syntax='Python syntax: OK.')
        back = receipts.after_command(actions=6, before=b'print(2)\n', after=b'print(1)\n', syntax='Python syntax: OK.')
        self.assertIn('Action 1/20 done (19 left)', first)
        self.assertIn('now version 1, 1 lines (+1/-0 lines). Python syntax: OK. Version 1 has not been tested.', first)
        self.assertIn('Tested version 1: it failed the public tests (0 of 2 cases passed)', test)
        self.assertIn('was not changed by this command (still version 1', same1)
        self.assertIn('already tested at action 2: it failed', same1)
        self.assertNotEqual(same1, same2)                       # the action count always differs
        self.assertIn('now version 2', changed)
        self.assertIn('byte-identical to that earlier version', back)
        self.assertEqual(receipts.count, 5)


class ContractChecks(unittest.TestCase):
    public = [{'input': '1 2\n', 'output': '3\n'}, {'input': 'PUBLIC\n', 'output': '7\n'}]

    def test_parse_and_benchmark_safe_validation(self):
        checks = contract_checks.parse_checks(CONTRACT_TEXT)
        self.assertEqual([c['id'] for c in checks], ['K-1', 'K-2', 'K-3'])
        self.assertEqual(checks[0]['stdin'], '-5 1\n')
        self.assertEqual(checks[0]['expected'], '-4')
        self.assertEqual(checks[0]['purpose'], 'Dropping the sign of a negative operand.')
        accepted, labelled = contract_checks.validate(checks, self.public)
        self.assertEqual([c['id'] for c in accepted], ['K-1', 'K-2'])
        self.assertEqual([l['status'] for l in labelled], ['unverified', 'unverified', 'contradicts_public'])
        # duplicates, malformed and over-limit checks are dropped explicitly
        many = [{'id': f'K-{i}', 'stdin': f'{i} 0\n', 'expected': str(i)} for i in range(9)] + [checks[0], {'id': 'K-x'}]
        accepted, labelled = contract_checks.validate(many + [dict(many[0])], [])
        self.assertEqual(len(accepted), contract_checks.MAX_CHECKS)
        self.assertEqual(labelled[-1]['status'], 'duplicate')
        self.assertIn('malformed', [l['status'] for l in labelled])
        self.assertIn('over_limit', [l['status'] for l in labelled])

    def test_render_labels_trust_and_inputs_only_hides_expectations(self):
        checks, _ = contract_checks.validate(contract_checks.parse_checks(CONTRACT_TEXT), self.public)
        outputs = [{'rc': 0, 'stdout': '6\n'}, {'rc': 0, 'stdout': '4\n'}]
        active = contract_checks.ContractChecker(checks, 'active')
        text = active.render(outputs, [{'outcome': 'different'}, {'outcome': 'different'}])
        self.assertIn('NOT verified', text)
        self.assertIn('expected (proposed, unverified):\n    -4', text)
        self.assertIn('2 of 2 contract checks differ', text)
        control = contract_checks.ContractChecker(checks, 'inputs-only')
        text = control.render(outputs, [{'outcome': 'ran'}, {'outcome': 'ran'}])
        self.assertNotIn('-4', text)
        self.assertNotIn('expected', text.lower().replace('no expected outputs are given', ''))
        self.assertNotIn('Dropping the sign', text)              # the contract's wording is hidden too
        with self.assertRaises(ValueError):
            contract_checks.ContractChecker(checks, 'oracle')


class PlanRules(unittest.TestCase):
    def test_agent_ids_contract_checks_and_hooks_are_validated(self):
        base = {'task_id': 't', 'condition': 'A', 'seed': 1}
        plan = {'batch': 'b', 'attempts': [base | {'agent': 'l3-out-8k-v1'}]}
        self.assertEqual(integrity.validate_plan(plan), [])
        bad = {'batch': 'b', 'attempts': [
            base | {'agent': 'l9'}, base | {'variant': 'x', 'contract_checks': {'mode': 'active'}},
            {'task_id': 't', 'condition': 'D', 'guidance': 'g.json', 'contract_checks': {'mode': 'oracle'}},
            base | {'variant': 'y', 'test_hooks': {'self_plan_text': 'p'}}]}
        problems = ' | '.join(integrity.validate_plan(bad))
        for text in ('unknown shared-agent configuration', 'apply to condition D only', 'unknown contract-check mode',
                     'test_hooks are only allowed'):
            self.assertIn(text, problems)


class DiagnosisV2(unittest.TestCase):
    def test_v2_is_versioned_and_keeps_the_v1_delivery_contract(self):
        self.assertEqual(guidance.PROMPTS['diagnosis-v2'][0], 'diagnosis')
        self.assertNotEqual(guidance.PROMPTS['diagnosis-v2'][1], guidance.PROMPTS['diagnosis-v1'][1])
        for heading in guidance.HEADINGS['diagnosis']:
            self.assertIn(heading, guidance.PROMPTS['diagnosis-v2'][1])
        sample = ('## Observed failure\nCase 2 expected -1, printed 5.\n## Likely cause\n`abs(a) + abs(b)` drops signs.\n'
                  '## Repair direction\nPrint `a + b`; the sum keeps signs.\n## Verification target\nInput `-5 1` -> -4.\n')
        self.assertEqual(guidance.validate('diagnosis', sample), [])


class MeasurementSchema(unittest.TestCase):
    def test_fields_are_unique_documented_and_units_explicit(self):
        from guided_agent import measurement
        paths = [f[0] for f in measurement.FIELDS]
        self.assertEqual(len(paths), len(set(paths)))
        for path, kind_type, unit, nullable, source, kind, applies in measurement.FIELDS:
            self.assertIn(kind, ('measured', 'derived', 'configuration', 'identity', 'modelled'), path)
            self.assertTrue(source and applies, path)
            if path.endswith('_seconds'):
                self.assertIn('s', unit, path)
            if path.endswith('_usd'):
                self.assertEqual(unit, 'USD', path)
        table = measurement.schema_markdown()
        self.assertEqual(table.count('\n') + 1, len(paths) + 2)
        # unavailable quantities are never reported as zero; modelled costs are labelled as such
        self.assertIn('always null', dict((f[0], f[4]) for f in measurement.FIELDS)['local_inference.reasoning_tokens'])
        self.assertEqual(dict((f[0], f[5]) for f in measurement.FIELDS)['cost.modelled_local_cost_usd'], 'modelled')

    def test_usage_normalization_covers_api_and_codex(self):
        from guided_agent import measurement
        api = measurement._usage({'prompt_tokens': 10, 'completion_tokens': 5, 'prompt_tokens_details': {'cached_tokens': 2},
                                  'completion_tokens_details': {'reasoning_tokens': 3}})
        codex = measurement._usage({'input_tokens': 10, 'cached_input_tokens': 2, 'output_tokens': 5,
                                    'reasoning_output_tokens': 3})
        self.assertEqual(api, codex)
        self.assertEqual(measurement._usage(None), {'input_tokens': None, 'output_tokens': None, 'reasoning_tokens': None,
                                                    'cached_input_tokens': None})


@unittest.skipUnless(os.environ.get('CSC2108_INTEGRATION') == '1', 'set CSC2108_INTEGRATION=1 (Docker + judge image)')
class IntegrationPass4(unittest.TestCase):
    """Real frozen runtime + sandbox + judge-public; scripted coder."""

    def run_spec(self, name, responses, **extra):
        from guided_agent import runner
        study = Path(os.environ['CSC2108_STUDY_ROOT'])
        out = study / 'runs' / 'integration-tests' / f'p4-{name}-{int(time.time() * 1000)}'
        spec = {'task_id': 'fixture-sum-signed', 'condition': 'A', 'run_id': out.name, 'output': str(out),
                'study': str(study), 'backend': os.environ.get('CSC2108_TEST_BACKEND', 'auto'),
                'coder': {'provider': 'scripted', 'responses': [block(r) for r in responses]},
                'batch': 'integration-tests', 'cohort': 'integration (scripted coder)'} | extra
        record = runner.run_attempt(spec)
        messages = json.loads(next(out.glob('agent-*/trajectory.json')).read_text(encoding='utf-8'))['messages']
        from guided_agent import measurement
        document = json.loads((out / 'measurement.json').read_text(encoding='utf-8'))   # written by every attempt
        self.assertEqual(measurement.conforms(document), [])
        self.assertEqual(document['identity']['run_id'], record['run_id'])
        self.assertEqual(document['frontier']['n_requests'], 1 if spec.get('guidance') else 0)  # scripted coder != frontier
        return record, messages, out

    def contract_artifact(self, study):
        from guided_agent.tasks import load_statement
        statement = load_statement(study, 'fixture-sum-signed')
        public = json.loads((study / 'bundles/fixture-sum-signed/public_tests.json').read_text(encoding='utf-8'))
        text = CONTRACT_TEXT.replace('PUBLIC', public[0]['input'].strip())
        record = guidance.artifact(kind='contract', prompt_id='contract-v3', statement=statement, text=text,
                                   task_id='fixture-sum-signed', provider='codex-replay', requested_model='m',
                                   observed_model=None, reasoning_effort='medium', generation={}, label='test')
        return guidance.save_artifact(study / 'guidance/integration' / f'fixture.contract-v3.{time.time_ns()}.json', record)

    def test_1_receipts_reach_the_model_after_writes_and_tests(self):
        record, messages, _ = self.run_spec('receipt', [WRONG, TEST, WRONG, FIX, TEST, SUBMIT], agent='l4-receipt-v1')
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        users = [m['content'] for m in messages if m['role'] == 'user'][1:]
        self.assertIn('now version 1', users[0])
        self.assertIn('Python syntax: OK.', users[0])
        self.assertIn('Tested version 1: it failed the public tests', users[1])
        self.assertIn('was not changed by this command (still version 1', users[2])
        self.assertIn('already tested at action 2', users[2])
        self.assertIn('now version 2', users[3])
        self.assertIn('passed all public tests', users[4])
        self.assertEqual(record['agent_config']['id'], 'l4-receipt-v1')
        self.assertEqual(record['n_actions'], 6)               # receipts add no action

    def test_2_self_plan_is_in_the_first_message_and_time_is_restored(self):
        record, messages, out = self.run_spec('selfplan', [GOOD, TEST, SUBMIT], agent='l1-selfplan-v1',
                                              test_hooks={'self_plan_text': 'SELF-PLAN-MARKER: add the two numbers.'})
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        first = messages[1]['content']
        self.assertIn('## Your own plan, written in a separate planning step', first)
        self.assertIn('SELF-PLAN-MARKER', first)
        self.assertTrue(record['self_plan']['delivered'])
        self.assertTrue((out / 'self-plan.json').exists())

    def test_3_d_active_runs_checks_in_the_sandbox_and_labels_them(self):
        study = Path(os.environ['CSC2108_STUDY_ROOT'])
        path = self.contract_artifact(study)
        record, messages, _ = self.run_spec('d-active', [WRONG, TEST, FIX, TEST, SUBMIT], condition='D',
                                            guidance=str(path), injection='inject-active-v1',
                                            contract_checks={'mode': 'active'})
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        self.assertIn('the harness also runs your program on the K-check inputs', messages[1]['content'])
        reports = [m['content'] for m in messages if m['role'] == 'user' and 'PUBLIC TESTS' in m['content']]
        self.assertEqual(len(reports), 2)
        self.assertIn('[Contract checks: supplementary, NOT verified]', reports[0])
        self.assertIn('2 of 2 contract checks differ', reports[0])       # abs() program: K-1 and K-2 differ
        self.assertIn('1 of 2 contract checks differ', reports[1])       # fixed: only the wrong proposal K-2
        summary = record['contract_checks_summary']
        self.assertEqual((summary['checks'], summary['runs'], summary['errors']), (2, 2, 0))
        self.assertEqual(summary['final_outcomes'], ['same', 'different'])
        self.assertEqual([l['status'] for l in record['contract_checks']['labels']],
                         ['unverified', 'unverified', 'contradicts_public'])
        self.assertEqual(record['n_actions'], 5)               # checks add no action

    def test_4_inputs_only_control_hides_the_contract(self):
        study = Path(os.environ['CSC2108_STUDY_ROOT'])
        path = self.contract_artifact(study)
        record, messages, _ = self.run_spec('d-inputs', [WRONG, TEST, FIX, TEST, SUBMIT], condition='D',
                                            guidance=str(path), contract_checks={'mode': 'inputs-only'})
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        self.assertEqual(messages[1]['content'], json.loads(
            (study / 'bundles/fixture-sum-signed/task.json').read_text(encoding='utf-8'))['statement'])
        transcript = '\n'.join(m['content'] for m in messages)
        self.assertNotIn('Behavioral contract', transcript)
        self.assertNotIn('proposed', transcript)
        self.assertIn('[Extra inputs: supplementary]', transcript)
        self.assertFalse(record['guidance']['delivered'])


if __name__ == '__main__':
    unittest.main()
