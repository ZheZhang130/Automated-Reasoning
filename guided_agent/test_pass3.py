"""Reliability tests (pass 3, kept for the final branch): judge semantics, selection, plan integrity, E evidence, ledger, B, privacy, CLI.

All offline (no model, Docker, network or credentials):   python -m unittest guided_agent.test_pass3
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from guided_agent import agent_config, checkers, diagnosis, integrity, output_semantics, privacy, selection_pass3
from guided_agent.common import REPO, sha256_bytes, write_json

REVIEW = REPO / 'guided_agent/data/output-semantics-review.json'


class JudgeSemantics(unittest.TestCase):
    def test_frozen_comparator_is_the_deployed_judge_code(self):
        self.assertEqual(checkers.JUDGE_VERSION, '0.2.1')
        match = checkers.outputs_match
        # the judge's own unit expectations (judge/tests/test_judge.py), run on every host
        self.assertTrue(match('1 2\n3\n', '1 2\n3'))
        self.assertTrue(match('  1 2  \n 3', '1 2\n3\n\n'))
        self.assertTrue(match('1.50', '1.5'))
        self.assertFalse(match('1\n2', '1 2'))
        self.assertFalse(match('Yes', 'yes'))
        self.assertFalse(match('0.333333', '0.3333333'))
        self.assertFalse(match('sNaN', '5'))

    def test_abc392_d_tolerance_false_negative_is_reproduced_and_contained(self):
        expected = '0.333333333333333'                         # public sample 1 output
        python_repr = repr(1 / 3)                               # what a correct program typically prints
        self.assertFalse(checkers.outputs_match(python_repr, expected))   # judge 0.2.1: wrong answer
        self.assertTrue(checkers.tolerance_match(python_repr, expected, '1e-8'))
        self.assertTrue(checkers.tolerance_match('0.33333333', expected, '1e-8'))       # error 3.3e-9
        self.assertFalse(checkers.tolerance_match('0.3333334', expected, '1e-8'))       # error 6.7e-8
        self.assertFalse(checkers.tolerance_match('0.33 1', expected, '1e-8'))          # token count differs
        auto = output_semantics.classify('Print the answer.\nYour answer is considered correct if the absolute or '
                                         'relative error from the true solution does not exceed 10^{-8}.', [expected])
        self.assertEqual(auto['auto_category'], 'tolerance')
        category, how = output_semantics.decide('lcb-atcoder-abc392_d', auto, output_semantics.load_review(REVIEW))
        self.assertEqual((category, how), ('tolerance', 'manual'))
        self.assertFalse(output_semantics.eligible_for_judge_0_2_1(category))

    def test_abc396_e_alternative_minimum_is_rejected_by_exact_and_accepted_by_validator(self):
        case = '2 1\n1 2 1\n'          # A1 xor A2 = 1: (0, 1) and (1, 0) both have the minimum sum 1
        self.assertFalse(checkers.outputs_match('1 0', '0 1'))                         # judge 0.2.1: wrong answer
        self.assertTrue(checkers.xor_min_sum_valid(case, '0 1', '1 0'))
        self.assertFalse(checkers.xor_min_sum_valid(case, '0 1', '2 3'))               # valid but not minimal
        self.assertFalse(checkers.xor_min_sum_valid(case, '0 1', '0 0'))               # violates the constraint
        self.assertFalse(checkers.xor_min_sum_valid(case, '0 1', '-1'))
        sample = '3 2\n1 3 4\n1 2 3'   # public sample 1: (1,2,5) is good but has a larger sum than (0,3,4)
        self.assertTrue(checkers.xor_min_sum_valid(sample, '0 3 4', '0 3 4'))
        self.assertFalse(checkers.xor_min_sum_valid(sample, '0 3 4', '1 2 5'))
        self.assertTrue(checkers.compare('multiple_answers', '1 0', '0 1', task_id='lcb-atcoder-abc396_e', case_input=case))
        with self.assertRaises(NotImplementedError):
            checkers.compare('multiple_answers', '1', '1', task_id='lcb-atcoder-abc397_d', case_input='')

    def test_exact_tasks_are_scored_exactly_as_before(self):
        pairs = [('3\n', '3'), ('Yes', 'Yes'), ('Yes', 'No'), ('1 2 3', '1 2 3'), ('1 2', '1 2 3'), ('10', '1e1'),
                 ('0.5', '0.50'), ('a b', 'a  b'), ('', ''), ('x\n\ny', 'x\ny')]
        for actual, expected in pairs:
            self.assertEqual(checkers.compare('exact', actual, expected), checkers.outputs_match(actual, expected))

    def test_classifier_flags_every_known_non_exact_wording(self):
        cases = {
            'If there are multiple good sequences with the same minimum sum, printing any of them is accepted.':
                'multiple_answers',
            'If it exists, show one example.': 'multiple_answers',                       # arc195_c (no "any")
            'If multiple solutions exist, any of them is accepted.': 'multiple_answers',
            'The judge is case-insensitive; for example, if the correct answer is Fennec, outputs such as fennec '
            'will also be accepted.': 'case_insensitive',
            'This is an interactive problem. Flush the output after each line.': 'interactive',
        }
        for text, category in cases.items():
            auto = output_semantics.classify(text)
            self.assertTrue(auto['needs_review'], text)
            self.assertIn(category, auto['signals'], text)

    def test_ordinary_statements_have_no_signal_but_decimal_samples_need_review(self):
        for text in ('Print the answer.', 'If A is strictly increasing, print Yes; otherwise, print No.',
                     'Print Q lines. The i-th line should contain the answer to the i-th query.'):
            self.assertEqual(output_semantics.classify(text, ['3', 'Yes']),
                             {'auto_category': 'exact', 'signals': {}, 'needs_review': False})
        self.assertTrue(output_semantics.classify('Print the answer.', ['2.5000000'])['needs_review'])

    def test_unreviewed_cue_makes_a_task_ineligible(self):
        auto = output_semantics.classify('Print any of them.')
        self.assertEqual(output_semantics.decide('t', auto, {}), ('unreviewed', 'auto-flagged'))
        self.assertFalse(output_semantics.eligible_for_judge_0_2_1('unreviewed'))

    def test_review_file_covers_the_known_and_main_manifest_cases(self):
        reviews = output_semantics.load_review(REVIEW)
        expected = {'abc392_d': 'tolerance', 'abc396_e': 'multiple_answers', 'arc195_c': 'multiple_answers',
                    'abc395_a': 'case_insensitive', 'arc192_b': 'case_insensitive'}
        for task, category in expected.items():
            self.assertEqual(reviews['lcb-atcoder-' + task]['category'], category)

    def test_build_data_writes_identical_lf_bytes_on_every_os(self):
        from guided_agent.tasks import build_data_module
        bd = build_data_module()
        with tempfile.TemporaryDirectory() as tmp:
            bd.write_cases(Path(tmp) / 'cases', [{'input': '1 2\n3 4\n', 'output': '3\n'}])
            self.assertEqual((Path(tmp) / 'cases/01.in').read_bytes(), b'1 2\n3 4\n')
            self.assertEqual((Path(tmp) / 'cases/01.out').read_bytes(), b'3\n')


class Selection(unittest.TestCase):
    def test_bands_use_only_the_public_contest_letter(self):
        self.assertEqual([selection_pass3.band('lcb-atcoder-' + t) for t in
                          ('abc397_e', 'abc388_f', 'arc193_a', 'abc390_g', 'arc194_d')], [1, 2, 3, 4, 4])

    def test_selection_excludes_non_exact_and_is_deterministic(self):
        def row(qid, text):
            return {'platform': 'atcoder', 'question_id': qid, 'difficulty': 'hard', 'question_title': qid,
                    'contest_date': '2025-03-01T00:00:00', 'question_content': text,
                    'public_test_cases': json.dumps([{'input': '1', 'output': '1'}])}
        rows = {'lcb-atcoder-' + q: row(q, t) for q, t in (
            ('abc397_e', 'Print Yes or No.'), ('abc397_d', 'If there are multiple solutions, print any of them.'),
            ('abc388_f', 'Print the answer.'), ('arc192_b', 'The judge is case-insensitive.'),
            ('arc193_a', 'Print the answer.'), ('abc390_g', 'Print the answer.'), ('abc394_b', 'Print it.'))}
        with tempfile.TemporaryDirectory() as tmp:
            shard = Path(tmp) / 'shard.jsonl'
            shard.write_text('', encoding='utf-8')
            review = Path(tmp) / 'review.json'
            write_json(review, {'reviews': {}})
            with mock.patch.object(selection_pass3, 'rows_by_id', return_value=rows), \
                    mock.patch.object(selection_pass3, 'manifest_entries', return_value={}), \
                    mock.patch.object(selection_pass3, 'exclusion_union', return_value=set()):
                first = selection_pass3.select(shard, review, n=3)
                second = selection_pass3.select(shard, review, n=3)
        self.assertEqual(first['frozen_order'], second['frozen_order'])
        chosen = [t['task_id'][12:] for t in first['frozen_order']]
        self.assertEqual(chosen, ['abc397_e', 'abc388_f', 'arc193_a'])                 # band order
        excluded = {e['task_id'][12:]: e['output_category'] for e in first['excluded_output_semantics']}
        self.assertEqual(excluded, {'abc397_d': 'unreviewed', 'arc192_b': 'unreviewed'})
        self.assertNotIn('abc394_b', chosen + first['not_selected'])                     # pass-2 validation task


class PlanIntegrity(unittest.TestCase):
    def artifact(self, tmp, task, prompt_id):
        path = Path(tmp) / f'{task}.{prompt_id}.json'
        write_json(path, {'task_id': task, 'prompt_id': prompt_id, 'kind': prompt_id.split('-')[0]})
        return str(path)

    def test_valid_frozen_plan_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = agent_config.PRIMARY_AGENT
            plan = {'batch': 'b1', 'frozen': True, 'attempts': [
                {'task_id': 't', 'condition': 'A', 'seed': 2108, 'agent': agent},
                {'task_id': 't', 'condition': 'B', 'seed': 2108, 'coder': {'provider': 'api', 'max_requests': 28,
                                                                            'purpose': 'p'}},
                {'task_id': 't', 'condition': 'C', 'seed': 2108, 'agent': agent,
                 'guidance': self.artifact(tmp, 't', 'plan-v1')},
                {'task_id': 't', 'condition': 'D', 'seed': 2108, 'agent': agent,
                 'guidance': self.artifact(tmp, 't', 'contract-v1')},
                {'task_id': 't', 'condition': 'E', 'seed': 2108, 'agent': agent, 'diagnosis': {'provider': 'codex'}}]}
            self.assertEqual(integrity.validate_plan(plan), [])

    def test_mislabelled_colliding_or_unfrozen_attempts_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            v3 = self.artifact(tmp, 't', 'contract-v3')
            bad = {'batch': 'b1', 'frozen': True, 'attempts': [
                {'task_id': 't', 'condition': 'A', 'seed': 2108},
                {'task_id': 't', 'condition': 'A', 'seed': 2109},                          # same run name
                {'task_id': 't', 'condition': 'C', 'seed': 2108, 'coder': {'provider': 'api'},
                 'guidance': self.artifact(tmp, 't', 'plan-v1'), 'variant': 'x'},
                {'task_id': 't', 'condition': 'A', 'guidance': v3, 'variant': 'g', 'seed': 1},
                {'task_id': 't', 'condition': 'D', 'diagnosis': {'provider': 'codex'}, 'guidance': v3, 'seed': 1},
                {'task_id': 't', 'condition': 'E', 'aci': {'repeat_guard': True}, 'smoke': {'actions': 3}},
                {'task_id': 't', 'condition': 'B'},
                {'task_id': 't', 'condition': 'Z'}]}
            text = '\n'.join(integrity.validate_plan(bad))
        for fragment in ('duplicates attempt 0', 'must not substitute the coding model', 'must not carry upfront guidance',
                         'only condition E may carry', 'contract-v3 is not contract-v1', 'aci is not part of the final configuration', 'smoke budgets',
                         'needs an explicit agent',
                         'explicit integer seed', 'needs a coder', "unknown condition 'Z'"):
            self.assertIn(fragment, text)

    def test_scripted_coder_is_allowed_only_outside_frozen_plans(self):
        item = {'task_id': 't', 'condition': 'E', 'coder': {'provider': 'scripted', 'responses': []}}
        self.assertEqual(integrity.validate_plan({'batch': 'it', 'attempts': [item]}), [])
        self.assertTrue(integrity.validate_plan({'batch': 'it', 'frozen': True, 'attempts': [item | {'seed': 1}]}))

    def test_resumed_batch_must_keep_its_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = {'batch': 'b', 'attempts': [{'task_id': 't', 'condition': 'A'}]}
            write_json(Path(tmp) / 'plan.json', plan | {'plan_path': 'x'})
            self.assertEqual(integrity.check_unchanged(tmp, plan | {'plan_path': 'y'}), [])
            changed = plan | {'attempts': [{'task_id': 't', 'condition': 'C'}]}
            self.assertTrue(integrity.check_unchanged(tmp, changed))

    def test_batch_refuses_an_invalid_plan_before_creating_anything(self):
        from guided_agent import __main__ as cli
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / 'plan.json'
            write_json(plan_path, {'batch': 'refused', 'attempts': [{'task_id': 't', 'condition': 'B'}]})
            args = mock.Mock(plan=str(plan_path), backend='portable')
            with self.assertRaises(SystemExit) as stop:
                cli.cmd_batch(args, mock.Mock(backend='portable'), Path(tmp))
            self.assertEqual(stop.exception.code, 4)
            self.assertFalse((Path(tmp) / 'runs/refused').exists())

    def test_resource_wait_is_bounded_and_reports_unavailability(self):
        from guided_agent import __main__ as cli
        with mock.patch.object(cli, 'foreign_models', return_value=['someone-else:latest']), \
                mock.patch('time.sleep'):
            self.assertIsNone(cli.wait_for_gpu(max_wait=90, poll=30))
        with mock.patch.object(cli, 'foreign_models', return_value=[]):
            self.assertEqual(cli.wait_for_gpu(max_wait=90, poll=30), 0)


class EEvidence(unittest.TestCase):
    def result(self, **extra):
        return {'suite': 'public', 'status': 'candidate_failure', 'first_failure': {'verdict': 'WA'}} | extra

    def test_hidden_suite_results_never_trigger(self):
        self.assertEqual(diagnosis.qualifies(self.result(suite='hidden'), b'print(1)\n'),
                         (False, 'not_public_suite:hidden'))

    def test_the_judged_bytes_must_be_the_candidate_sent_to_the_frontier(self):
        source = b'print(1)\n'
        self.assertEqual(diagnosis.qualifies(self.result(code_sha256=sha256_bytes(source)), source),
                         (True, 'qualifying:WA'))
        self.assertEqual(diagnosis.qualifies(self.result(code_sha256=sha256_bytes(b'other')), source),
                         (False, 'candidate_hash_mismatch'))


class LedgerConcurrency(unittest.TestCase):
    # 20 threads race for a 20-request ceiling: the rule under test, independent of the configured study budget
    @mock.patch('guided_agent.providers.MAX_REQUESTS', 20)
    def test_concurrent_reservations_never_lose_entries_or_exceed_the_ceiling(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            outcomes = []

            def reserve():
                try:
                    outcomes.append(providers.Ledger(path).reserve({'bound_usd_conservative': 0.01}))
                except RuntimeError:
                    outcomes.append('refused')
            threads = [threading.Thread(target=reserve) for _ in range(20)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(len(data['requests']), providers.MAX_REQUESTS)
            self.assertEqual(sorted(o for o in outcomes if o != 'refused'), list(range(providers.MAX_REQUESTS)))
            self.assertFalse(path.with_name('ledger.json.lock').exists())

    @mock.patch('guided_agent.providers.MAX_REQUESTS', 20)
    def test_a_ledger_file_cannot_raise_the_ceilings_in_code(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            write_json(path, {'max_requests': 1000, 'max_usd': 1e6, 'requests': [
                {'bound_usd_conservative': 0.0, 'usage': {'prompt_tokens': 0, 'completion_tokens': 0}}] * providers.MAX_REQUESTS})
            with self.assertRaises(RuntimeError):
                providers.Ledger(path).reserve({'bound_usd_conservative': 0.0})
            write_json(path, {'max_usd': 1e6, 'requests': []})
            with self.assertRaises(RuntimeError):
                providers.Ledger(path).reserve({'bound_usd_conservative': providers.MAX_USD + 1})


class CodexProvenance(unittest.TestCase):
    def test_recorded_command_has_no_machine_paths(self):
        from guided_agent import providers
        events = (json.dumps({'type': 'thread.started', 'thread_id': 'th'}) + '\n' +
                  json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message'}}) + '\n' +
                  json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 1}}) + '\n').encode()

        def fake_run(command, **kwargs):
            if '--version' in command:
                return subprocess.CompletedProcess(command, 0, stdout='codex-cli 9.9', stderr='')
            Path(command[command.index('-o') + 1]).write_text('answer', encoding='utf-8')
            return subprocess.CompletedProcess(command, 0, stdout=events, stderr=b'')
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(providers.shutil, 'which', return_value=str(Path(tmp) / 'bin' / 'codex.CMD')), \
                mock.patch.object(providers.subprocess, 'run', side_effect=fake_run):
            result = providers.codex_infer(system='s', user='u', evidence=Path(tmp) / 'ev', work_root=Path(tmp) / 'w')
        command = result['isolation']['command']
        self.assertEqual(command[0], 'codex.CMD')
        self.assertIn('<isolated-empty-tmpdir>', command)
        self.assertFalse([c for c in command if tmp in c or tmp.replace('\\', '/') in c])


class Privacy(unittest.TestCase):
    IDENTITY = {'<USER>': 'alice', '<HOST>': 'box-17', '<HOME>': r'C:\Users\alice'}

    def test_sanitize_replaces_user_home_host_and_secrets(self):
        record = {'cmd': [r'C:\Users\alice\AppData\Roaming\npm\codex.CMD', '/Users/bob/bin/x', '/home/carol/y'],
                  'host': 'box-17', 'note': 'key sk-proj-abcdefghijklmnopqrstuvwxyz012345',
                  'escaped': 'C:\\\\Users\\\\alice\\\\x'}
        clean = privacy.sanitize(record, self.IDENTITY)
        self.assertEqual(clean['cmd'], [r'<HOME>\AppData\Roaming\npm\codex.CMD', '/Users/<USER>/bin/x',
                                        '/home/<USER>/y'])
        self.assertEqual(clean['host'], '<HOST>')
        self.assertIn('<REDACTED-SECRET>', clean['note'])
        self.assertEqual(privacy.scan(json.dumps(clean), self.IDENTITY), [])
        self.assertTrue(privacy.scan(json.dumps(record), self.IDENTITY))

    def test_committed_docs_and_fixtures_have_no_home_paths_or_secrets(self):
        paths = sorted(REPO.glob('*.md')) + sorted(REPO.glob('*.json')) + sorted((REPO / 'guided_agent/fixtures').rglob('*'))
        findings = []
        for path in paths:
            if path.is_file() and path.suffix in ('.json', '.md', '.txt', '.jsonl'):
                text = path.read_text(encoding='utf-8', errors='replace')
                findings += [(str(path.relative_to(REPO)), f) for f in privacy.scan(text, identity={})]
        self.assertEqual(findings, [])


class Cli(unittest.TestCase):
    def test_cli_help_and_imports(self):
        proc = subprocess.run([sys.executable, '-m', 'guided_agent', '--help'], cwd=REPO, capture_output=True, text=True,
                              timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for command in ('prepare-tasks', 'author', 'batch', 'evaluate', 'summarize', 'measure', 'schema'):
            self.assertIn(command, proc.stdout)
        import guided_agent.analysis  # noqa: F401
        import guided_agent.measurement  # noqa: F401


if __name__ == '__main__':
    unittest.main()
