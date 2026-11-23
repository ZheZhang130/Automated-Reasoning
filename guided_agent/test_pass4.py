"""Tests for the final shared-agent configuration, the measurement schema and the finalization manifest.

Offline tests: no model, Docker or network.     python -m unittest guided_agent.test_pass4
Integration tests (real frozen runtime, real Docker sandbox and judge-public, SCRIPTED coder, no inference, no
frontier calls) run only with CSC2108_INTEGRATION=1 and CSC2108_STUDY_ROOT pointing at a prepared study holding
the synthetic fixture (python -m guided_agent prepare-fixture).
"""
import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from guided_agent import agent_config, guidance, integrity, measurement
from guided_agent.common import REPO
from guided_agent.test_pass2 import GOOD, SUBMIT, TEST, WRONG, block

MANIFEST = REPO / 'FINALIZATION_MANIFEST.json'


class SharedAgent(unittest.TestCase):
    def test_configurations_are_versioned_and_validated(self):
        agent_id, definition, digest = agent_config.resolve(None)
        self.assertEqual((agent_id, definition), ('frozen-v6', {}))
        self.assertEqual(len(digest), 64)
        with self.assertRaises(ValueError):
            agent_config.resolve('l9-unknown')
        self.assertIn(agent_config.PRIMARY_AGENT, agent_config.AGENT_CONFIGS)

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
        self.assertEqual(bodies[0]['options'], {'top_k': 40, 'top_p': 0.9, 'num_ctx': 16384, 'num_predict': 4096,
                                                'temperature': 0.2, 'seed': 2109})
        self.assertIs(bodies[0]['think'], False)
        self.assertTrue(text.endswith('[This plan was cut off at the output limit.]'))
        self.assertTrue(saved['truncated'] and saved['delivered'])

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
        self.assertLess(c.index('{{guide}}'), c.index('{{selfplan}}'))


class PlanRules(unittest.TestCase):
    def test_frozen_plans_accept_only_the_primary_configuration(self):
        ok = {'batch': 'b', 'frozen': True, 'attempts': [
            {'task_id': 't', 'condition': 'A', 'seed': 1, 'agent': agent_config.PRIMARY_AGENT}]}
        self.assertEqual(integrity.validate_plan(ok), [])
        other = [k for k in agent_config.AGENT_CONFIGS if k != agent_config.PRIMARY_AGENT][0]
        bad = {'batch': 'b', 'frozen': True, 'attempts': [
            {'task_id': 't', 'condition': 'A', 'seed': 1, 'agent': other},
            {'task_id': 't', 'condition': 'A', 'seed': 2, 'variant': 'x'},
            {'task_id': 't', 'condition': 'A', 'seed': 3, 'variant': 'y', 'agent': 'l9'}]}
        problems = ' | '.join(integrity.validate_plan(bad))
        self.assertIn('frozen plans use the primary shared agent', problems)
        self.assertIn('needs an explicit agent', problems)
        self.assertIn('unknown shared-agent configuration', problems)


class MeasurementSchema(unittest.TestCase):
    def test_fields_are_unique_documented_and_units_explicit(self):
        paths = [f[0] for f in measurement.FIELDS]
        self.assertEqual(len(paths), len(set(paths)))
        for path, kind_type, unit, nullable, source, kind, applies in measurement.FIELDS:
            self.assertIn(kind, ('measured', 'derived', 'configuration', 'identity', 'modelled'), path)
            self.assertTrue(source and applies, path)
            if path.endswith('_seconds'):
                self.assertIn('s', unit, path)
            if path.endswith('_usd'):
                self.assertEqual(unit, 'USD', path)
        self.assertIn('always null', dict((f[0], f[4]) for f in measurement.FIELDS)['local_inference.reasoning_tokens'])
        self.assertEqual(dict((f[0], f[5]) for f in measurement.FIELDS)['cost.modelled_local_cost_usd'], 'modelled')

    def test_usage_normalization_covers_api_and_codex(self):
        api = measurement._usage({'prompt_tokens': 10, 'completion_tokens': 5, 'prompt_tokens_details': {'cached_tokens': 2},
                                  'completion_tokens_details': {'reasoning_tokens': 3}})
        codex = measurement._usage({'codex_reported': {'input_tokens': 10, 'cached_input_tokens': 2, 'output_tokens': 5,
                                                       'reasoning_output_tokens': 3}})
        self.assertEqual(api, codex)

    def test_every_fixture_conforms_and_is_sanitized(self):
        from guided_agent import privacy
        fixtures = REPO / 'guided_agent/fixtures'
        index = json.loads((fixtures / 'INDEX.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(index), 10)
        for entry in index:
            document = json.loads((fixtures / entry['role'] / 'measurement.json').read_text(encoding='utf-8'))
            self.assertEqual(measurement.conforms(document), [], entry['role'])
            for path in (fixtures / entry['role']).iterdir():
                self.assertEqual(privacy.scan(path.read_text(encoding='utf-8'), identity={}), [], str(path))


@unittest.skipUnless(MANIFEST.exists(), 'FINALIZATION_MANIFEST.json is written on the final branch')
class Manifest(unittest.TestCase):
    def test_prompt_template_and_source_hashes_match(self):
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        for pid, digest in manifest['prompt_sha256'].items():
            self.assertEqual(hashlib.sha256(guidance.PROMPTS[pid][1].encode('utf-8')).hexdigest(), digest, pid)
        for key, digest in manifest['injection_template_sha256'].items():
            iid, kind = key.split('/')
            self.assertEqual(hashlib.sha256(guidance.INJECTION[iid][kind].encode('utf-8')).hexdigest(), digest, key)
        for name, digest in manifest['agent_configurations'].items():
            self.assertEqual(agent_config.resolve(name)[2], digest, name)
        self.assertEqual(manifest['selected']['shared_agent'], agent_config.PRIMARY_AGENT)
        selection = REPO / 'local_optimization/final_selection.json'
        self.assertEqual(hashlib.sha256(selection.read_bytes()).hexdigest(), manifest['frozen_agent']['selection_sha256'])


@unittest.skipUnless(os.environ.get('CSC2108_INTEGRATION') == '1', 'set CSC2108_INTEGRATION=1 (Docker + judge image)')
class IntegrationFinal(unittest.TestCase):
    """Real frozen runtime + sandbox + judge-public; scripted coder."""

    def run_spec(self, name, responses, **extra):
        from guided_agent import runner
        study = Path(os.environ['CSC2108_STUDY_ROOT'])
        out = study / 'runs' / 'integration-tests' / f'final-{name}-{int(time.time() * 1000)}'
        spec = {'task_id': 'fixture-sum-signed', 'condition': 'A', 'run_id': out.name, 'output': str(out),
                'study': str(study), 'backend': os.environ.get('CSC2108_TEST_BACKEND', 'auto'),
                'coder': {'provider': 'scripted', 'responses': [block(r) for r in responses]},
                'batch': 'integration-tests', 'cohort': 'integration (scripted coder)'} | extra
        record = runner.run_attempt(spec)
        messages = json.loads(next(out.glob('agent-*/trajectory.json')).read_text(encoding='utf-8'))['messages']
        document = json.loads((out / 'measurement.json').read_text(encoding='utf-8'))   # written by every attempt
        self.assertEqual(measurement.conforms(document), [])
        self.assertEqual(document['identity']['run_id'], record['run_id'])
        return record, messages, out

    def test_1_self_plan_is_in_the_first_message_and_time_is_restored(self):
        record, messages, out = self.run_spec('selfplan', [GOOD, TEST, SUBMIT], agent='l1-selfplan-v1',
                                              test_hooks={'self_plan_text': 'SELF-PLAN-MARKER: add the two numbers.'})
        self.assertEqual(record['exit_status'], 'submitted', record.get('setup_error'))
        self.assertIn('## Your own plan, written in a separate planning step', messages[1]['content'])
        self.assertIn('SELF-PLAN-MARKER', messages[1]['content'])
        self.assertTrue(record['self_plan']['delivered'])
        self.assertEqual(record['agent_config']['id'], 'l1-selfplan-v1')

    def test_2_action_budget_is_enforced_with_a_program_on_disk(self):
        record, messages, out = self.run_spec('action-limit', [WRONG] + ['pwd'] * 22)
        self.assertEqual(record['exit_status'], 'action_limit', record.get('setup_error'))
        self.assertEqual(record['n_actions'], 20)
        self.assertIsNotNone(record['submission_sha256'])
        document = json.loads((out / 'measurement.json').read_text(encoding='utf-8'))
        self.assertEqual((document['correctness']['exit_status'], document['agent']['actions']), ('action_limit', 20))


if __name__ == '__main__':
    unittest.main()
