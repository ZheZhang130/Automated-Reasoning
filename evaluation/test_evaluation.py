"""Offline tests for the evaluation pipeline (no model, Docker or network).

    python -m unittest evaluation.test_evaluation
"""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evaluation import judge as judgelib, metrics, pipeline, plan as planlib, tasks as taskslib
from evaluation.__main__ import main as cli
from guided_agent import integrity
from guided_agent.common import REPO

FIXTURE = REPO / 'guided_agent/fixtures/a_success/measurement.json'
MAIN = REPO / 'judge/manifests/main.json'


def fake_run(batch, item, *, hidden='pass', final_public='pass', public=('pass',), infra=False, overflow=False,
             triggered=None, cost=None, agent_error=None, truncated=0, exit_status=None, responses=(),
             first_candidate_s=None, upfront=None):
    run_dir = batch / integrity.run_name(item)
    run_dir.mkdir(parents=True)
    doc = copy.deepcopy(planlib.read_json(FIXTURE))
    run_id = f"{batch.name}-{run_dir.name}"
    doc['identity'] |= {'run_id': run_id, 'task_id': item['task_id'], 'condition': item['condition'],
                        'seed': item['seed'], 'guidance_artifact_sha256': None}
    doc['correctness'] |= {'hidden_status': hidden, 'final_public_status': final_public,
                           'infrastructure_failure': infra, 'context_overflow': overflow,
                           'candidate_produced': hidden != 'missing_submission',
                           'exit_status': exit_status or ('infra_error' if infra or overflow else 'submitted')}
    doc['local_inference']['truncated_responses'] = truncated
    doc['agent']['seconds_to_first_executable_candidate'] = first_candidate_s
    if responses:  # (eval_count, eval_seconds, total_seconds)
        planlib.write_json(run_dir / f'agent-{run_id}' / 'ollama-responses.json', [
            {'eval_count': n, 'eval_duration': int(e * 1e9), 'total_duration': int(t * 1e9)} for n, e, t in responses])
    if agent_error:
        planlib.write_json(run_dir / f'agent-{run_id}' / 'result.json', {'error': agent_error})
    doc['frontier'] = {'requests': [], 'n_requests': 0, 'provider_failures': 0}
    doc['cost']['api_cost_usd_run'] = None
    if cost is not None:
        doc['frontier'] = {'requests': [{'upfront': False, 'cost_usd': cost, 'input_tokens': 10, 'output_tokens': 5,
                                         'status': 'ok'}], 'n_requests': 1, 'provider_failures': 0}
        doc['cost']['api_cost_usd_run'] = cost
    if upfront:  # (cost, input tokens, output tokens, latency s, artifact sha)
        c, i, o, lat, sha = upfront
        doc['frontier']['requests'].append({'upfront': True, 'cost_usd': c, 'input_tokens': i, 'output_tokens': o,
                                            'latency_seconds': lat, 'status': 'ok'})
        doc['identity']['guidance_artifact_sha256'] = sha
    doc['condition'] = {'guidance': None, 'diagnosis': {'trigger_observed': triggered} if triggered is not None else None}
    planlib.write_json(run_dir / 'measurement.json', doc)
    planlib.write_json(run_dir / 'result.json', {'run_id': run_id})
    (run_dir / 'attempts.jsonl').write_text(''.join(json.dumps({'result': {'status': s}}) + '\n' for s in public))
    planlib.write_json(batch / 'eval' / f'{run_id}.json',
                       {'status': hidden, 'verdict_counts': {'AC': 30, 'WA': 10} if hidden != 'pass' else {'AC': 40}})


class Statistics(unittest.TestCase):
    def test_mcnemar_exact_matches_the_binomial(self):
        self.assertEqual(metrics.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(metrics.mcnemar_exact(5, 0), 2 / 32)
        self.assertAlmostEqual(metrics.mcnemar_exact(3, 1), 2 * 5 / 16)

    def test_sign_flip_is_exact_for_small_samples(self):
        self.assertAlmostEqual(metrics.sign_flip_p([1, 1, 1, 1]), 2 / 16)
        self.assertEqual(metrics.sign_flip_p([0, 0]), 1.0)

    def test_holm_is_monotone_and_capped(self):
        adjusted = metrics.holm({'C': 0.01, 'D': 0.04, 'E': 0.03})
        self.assertAlmostEqual(adjusted['C'], 0.03)
        self.assertAlmostEqual(adjusted['E'], 0.06)
        self.assertAlmostEqual(adjusted['D'], 0.06)

    def test_bootstrap_ci_contains_the_mean_and_is_reproducible(self):
        diffs = [0, 1, 1, 0, 0.5, 1, 0, 1]
        ci = metrics.bootstrap_ci(diffs)
        self.assertLessEqual(ci[0], sum(diffs) / len(diffs))
        self.assertGreaterEqual(ci[1], sum(diffs) / len(diffs))
        self.assertEqual(ci, metrics.bootstrap_ci(diffs))


class Plans(unittest.TestCase):
    def test_full_plan_is_valid_frozen_and_collision_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp)
            tasks = planlib.manifest_tasks(MAIN)
            plan = planlib.build_plan(batch='final-main', task_ids=tasks, seeds=[2108, 2109, 2110], study=study)
            self.assertEqual(len(plan['attempts']), 60 * 3 * 5)
            for path in planlib.guidance_artifacts(plan):  # stand-in artifacts so the frozen validator can read them
                task, prompt = Path(path).name.split('.')[:2]
                planlib.write_json(path, {'task_id': task, 'prompt_id': prompt})
            self.assertEqual(integrity.validate_plan(plan), [])
            first_block = plan['attempts'][:5]
            self.assertEqual([a['condition'] for a in first_block], list('ABCDE'))
            self.assertEqual({a['seed'] for a in first_block}, {2108})

    def test_subset_and_per_difficulty(self):
        self.assertEqual(len(planlib.manifest_tasks(MAIN, per_difficulty=1)), 3)
        with self.assertRaises(ValueError):
            planlib.manifest_tasks(MAIN, tasks=['lcb-atcoder-nope'])

    def test_freeze_detects_changed_and_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp)
            plan = planlib.build_plan(batch='b', task_ids=['t1'], seeds=[1], study=study, conditions=['C', 'D'])
            with self.assertRaises(FileNotFoundError):
                planlib.freeze(plan, study / 'f.json')
            for path in planlib.guidance_artifacts(plan):
                planlib.write_json(path, {'x': 1})
            planlib.freeze(plan, study / 'f.json')
            with self.assertRaises(FileExistsError):
                planlib.freeze(plan, study / 'f.json')
            self.assertEqual(planlib.check(study / 'f.json'), [])
            planlib.write_json(planlib.guidance_artifacts(plan)[0], {'x': 2})
            self.assertEqual(len(planlib.check(study / 'f.json')), 1)


class Metrics(unittest.TestCase):
    def batch(self, tmp):
        batch = Path(tmp) / 'final-test'
        tasks = planlib.manifest_tasks(MAIN, per_difficulty=1)  # 1 easy, 1 medium, 1 hard
        plan = planlib.build_plan(batch=batch.name, task_ids=tasks, seeds=[1, 2], study=Path(tmp),
                                  conditions=['A', 'B', 'E'])
        planlib.write_json(batch / 'plan.json', plan)
        items = {(a['task_id'], a['condition'], a['seed']): a for a in plan['attempts']}
        easy, medium, hard = tasks
        for seed in (1, 2):
            fake_run(batch, items[(easy, 'A', seed)])
            fake_run(batch, items[(easy, 'B', seed)], cost=0.01)
            fake_run(batch, items[(easy, 'E', seed)], triggered=False)
            fake_run(batch, items[(medium, 'A', seed)], hidden='candidate_failure', final_public='candidate_failure',
                     public=('candidate_failure',))
            fake_run(batch, items[(medium, 'B', seed)], cost=0.02)
            fake_run(batch, items[(medium, 'E', seed)], public=('candidate_failure', 'pass'), triggered=True)
        fake_run(batch, items[(hard, 'A', 1)], hidden='candidate_failure', overflow=True, public=())
        fake_run(batch, items[(hard, 'B', 1)], hidden='candidate_failure', final_public='pass', cost=0.05)
        fake_run(batch, items[(hard, 'E', 1)], hidden='infrastructure_error')  # excludes (hard, 1) everywhere
        # (hard, seed 2) never ran: excluded everywhere
        return batch, tasks

    def test_report_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, (easy, medium, hard) = self.batch(tmp)
            report, rows = metrics.analyze([batch], [MAIN])
            self.assertEqual(report['scheduled_runs'], 18)
            self.assertEqual(report['included_runs'], 12)
            self.assertEqual({(b['task_id'], b['seed']) for b in report['excluded_blocks']}, {(hard, 1), (hard, 2)})
            a, b, e = (report['summary']['all'][c] for c in 'ABE')
            self.assertEqual((a['runs'], a['passes']), (4, 2))
            self.assertEqual((e['passes'], b['passes']), (4, 4))
            self.assertEqual(e['failure_recovery'], {'runs_with_public_failure': 2, 'recovered': 2, 'rate': 1.0})
            self.assertEqual(a['failure_recovery']['rate'], 0.0)
            self.assertAlmostEqual(b['frontier_cost_usd']['total'], 0.06)
            self.assertAlmostEqual(b['frontier_cost_usd']['per_pass'], 0.015)
            self.assertNotIn('hard', report['summary'])
            pe = report['paired_vs_A']['all']['E']
            self.assertEqual((pe['tasks'], pe['pairs'], pe['difference']), (2, 4, 0.5))
            self.assertEqual(pe['mcnemar']['condition_only'], 2)
            self.assertEqual(set(report['holm_adjusted_p']), {'E'})  # B is exploratory
            self.assertEqual(report['e_subset']['triggered']['pairs'], 2)
            self.assertEqual(report['e_subset']['triggered']['A_pass_rate'], 0.0)
            self.assertEqual(report['e_subset']['trigger_rate'], 0.5)

    def test_context_overflow_is_a_failure_not_an_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            plan = planlib.build_plan(batch='b', task_ids=['lcb-atcoder-abc387_a'], seeds=[1], study=Path(tmp),
                                      conditions=['A'])
            planlib.write_json(batch / 'plan.json', plan)
            fake_run(batch, plan['attempts'][0], hidden='candidate_failure', final_public='none', overflow=True,
                     public=())
            report, rows = metrics.analyze([batch], [MAIN])
            self.assertEqual(report['excluded_blocks'], [])
            self.assertEqual(report['summary']['all']['A']['context_overflow'], 1)
            self.assertEqual(rows[0]['outcome'], 'never_passed_public:none')

    def test_cli_writes_report_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, _ = self.batch(tmp)
            out = Path(tmp) / 'report'
            with mock.patch('sys.stdout'):
                cli(['metrics', str(batch), '--out', str(out), '--manifests', str(MAIN)])
            self.assertTrue((out / 'report.md').read_text().startswith('# Evaluation report'))
            self.assertEqual(len((out / 'runs.csv').read_text().splitlines()), 19)


TIMEOUT = 'litellm.APIConnectionError: Ollama_chatException - litellm.Timeout: Connection timed out after 180.0 seconds.'


class Categories(unittest.TestCase):
    def test_each_category_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            tasks = planlib.manifest_tasks(MAIN)[:10]
            plan = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1], study=Path(tmp), conditions=['A'])
            planlib.write_json(batch / 'plan.json', plan)
            cases = [
                ({}, 'hidden_pass'),
                ({'hidden': 'missing_submission', 'infra': True, 'agent_error': TIMEOUT, 'public': ()},
                 'local_timeout_no_program'),
                ({'hidden': 'missing_submission', 'infra': True, 'public': (),
                  'agent_error': "Command '['docker', 'exec', 'abc']' timed out after 5 seconds"}, 'infrastructure'),
                ({'hidden': 'missing_submission', 'overflow': True, 'agent_error': TIMEOUT, 'public': ()},
                 'context_overflow'),
                ({'hidden': 'missing_submission', 'truncated': 2, 'exit_status': 'action_limit', 'public': ()},
                 'truncated_no_program'),
                ({'hidden': 'missing_submission', 'exit_status': 'action_limit', 'public': ()}, 'budget_limit'),
                ({'hidden': 'missing_submission', 'exit_status': 'format_errors', 'public': ()}, 'format_errors'),
                ({'hidden': 'candidate_failure'}, 'public_pass_hidden_fail'),
                ({'hidden': 'candidate_failure', 'final_public': 'candidate_failure',
                  'public': ('candidate_failure',)}, 'never_passed_public'),
                ({'hidden': 'candidate_failure', 'final_public': 'candidate_failure', 'infra': True,
                  'agent_error': TIMEOUT, 'public': ('candidate_failure',)}, 'local_timeout_with_program'),
            ]
            for item, (kwargs, _) in zip(plan['attempts'], cases):
                if kwargs.get('hidden') == 'missing_submission':
                    kwargs.setdefault('final_public', 'none')
                fake_run(batch, item, **kwargs)
            rows = metrics.load([batch], [MAIN])
            self.assertEqual([r['category'] for r in rows], [c for _, c in cases])
            report, _ = metrics.analyze([batch], [MAIN])
            # only the real infrastructure fault is excluded; a timeout is a failed run
            self.assertEqual(len(report['excluded_blocks']), 1)
            self.assertEqual(report['summary']['all']['A']['local_timeout'], 2)
            self.assertEqual(report['summary']['all']['A']['runs'], 9)
            sens = report['sensitivity_exclude_timeouts']
            self.assertEqual((sens['excluded_blocks'], sens['included_runs']), (2, 7))

    def test_transition_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            tasks = planlib.manifest_tasks(MAIN)[:3]
            plan = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1], study=Path(tmp), conditions=['A', 'C'])
            planlib.write_json(batch / 'plan.json', plan)
            items = {(a['task_id'], a['condition']): a for a in plan['attempts']}
            timeout = {'hidden': 'missing_submission', 'final_public': 'none', 'infra': True, 'agent_error': TIMEOUT,
                       'public': ()}
            fake_run(batch, items[(tasks[0], 'A')], **timeout)
            fake_run(batch, items[(tasks[0], 'C')])
            fake_run(batch, items[(tasks[1], 'A')], **timeout)
            fake_run(batch, items[(tasks[1], 'C')], **timeout)
            fake_run(batch, items[(tasks[2], 'A')])
            fake_run(batch, items[(tasks[2], 'C')], hidden='candidate_failure')
            report, _ = metrics.analyze([batch], [MAIN])
            t = report['transitions_from_A']['C']
            self.assertEqual(t['pairs'], 3)
            self.assertEqual(t['matrix']['local_timeout_no_program'],
                             {'hidden_pass': 1, 'local_timeout_no_program': 1})
            self.assertEqual(t['fixed']['local_timeout_no_program'], {'base_failures': 2, 'passed': 1})
            self.assertEqual(t['broken'], 1)
            self.assertIn('## Transitions A -> C', metrics.markdown(report))


class ProcessAndHosts(unittest.TestCase):
    def test_process_differences_and_host_speed(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            tasks = planlib.manifest_tasks(MAIN)[:2]
            plan = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1], study=Path(tmp), conditions=['A', 'C'])
            planlib.write_json(batch / 'plan.json', plan)
            items = {(a['task_id'], a['condition']): a for a in plan['attempts']}
            fake_run(batch, items[(tasks[0], 'A')], responses=[(4096, 160.0, 170.0), (100, 4.0, 5.0)],
                     first_candidate_s=175.0)
            fake_run(batch, items[(tasks[0], 'C')], responses=[(300, 12.0, 14.0)], first_candidate_s=15.0)
            fake_run(batch, items[(tasks[1], 'A')], hidden='missing_submission', final_public='none', infra=True,
                     agent_error=TIMEOUT, public=())
            fake_run(batch, items[(tasks[1], 'C')], responses=[(500, 20.0, 22.0)], first_candidate_s=23.0)
            report, rows = metrics.analyze([batch], [MAIN])
            p = report['process_vs_A']['C']
            self.assertEqual(p['first_response_tokens'], {'median': -3796, 'pairs': 1})
            self.assertEqual(p['seconds_to_first_candidate'], {'median': -160.0, 'pairs': 1})
            self.assertEqual((p['candidate_only_in_condition'], p['candidate_only_in_base']), (1, 0))
            (host,) = report['host_speed']
            self.assertEqual((host['requests'], host['requests_over_near_s'], host['timed_out_requests']), (4, 1, 1))
            self.assertAlmostEqual(host['near_limit_share'], 0.4)
            self.assertEqual(host['decode_tok_s_median'], 25.0)
            text = metrics.markdown(report)
            for section in ('## Sensitivity', '## Process', '## Host speed'):
                self.assertIn(section, text)
            metrics.write(report, rows, Path(tmp) / 'out')
            self.assertNotIn('_requests', (Path(tmp) / 'out/runs.csv').read_text().splitlines()[0].split(','))


class Reruns(unittest.TestCase):
    def test_later_batch_replaces_only_infrastructure_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = 'lcb-atcoder-abc387_a'
            first, second = Path(tmp) / 'b1', Path(tmp) / 'b2'
            p1 = planlib.build_plan(batch='b1', task_ids=[task], seeds=[1], study=Path(tmp), conditions=['A', 'B'])
            planlib.write_json(first / 'plan.json', p1)
            fake_run(first, p1['attempts'][0], hidden='infrastructure_error', infra=True)
            fake_run(first, p1['attempts'][1], cost=0.01)
            p2 = planlib.build_plan(batch='b2', task_ids=[task], seeds=[1], study=Path(tmp), conditions=['A'])
            planlib.write_json(second / 'plan.json', p2)
            fake_run(second, p2['attempts'][0])
            report, rows = metrics.analyze([first], [MAIN])
            self.assertEqual(len(report['excluded_blocks']), 1)
            report, rows = metrics.analyze([first, second], [MAIN])
            self.assertEqual(report['excluded_blocks'], [])
            self.assertEqual(report['replaced_by_rerun'][0]['condition'], 'A')
            self.assertEqual(report['summary']['all']['A']['passes'], 1)
            with self.assertRaises(ValueError):  # two valid runs of the same key are ambiguous
                metrics.analyze([first, second, second], [MAIN])


class AnalysisAdditions(unittest.TestCase):
    def test_seed_consistency_and_gap_closed(self):
        def row(task, seed, condition, passed):
            return {'task_id': task, 'seed': seed, 'condition': condition, 'passed': passed}
        rows = []
        # t1: A fails, B passes, C passes -> C closes the gap; t2: all pass; t3: A/C fail, B passes on one seed
        for seed in (1, 2):
            rows += [row('t1', seed, 'A', False), row('t1', seed, 'B', True), row('t1', seed, 'C', True),
                     row('t2', seed, 'A', True), row('t2', seed, 'B', True), row('t2', seed, 'C', True),
                     row('t3', seed, 'A', False), row('t3', seed, 'B', seed == 1), row('t3', seed, 'C', False)]
        k = metrics.seed_consistency([r for r in rows if r['condition'] == 'B'])
        self.assertEqual((k['tasks'], k['all_pass'], k['mixed'], k['all_fail']), (3, 2, 1, 0))
        self.assertAlmostEqual(k['mean_seed_variance'], round(0.25 / 3, 4))
        self.assertIsNone(metrics.seed_consistency([row('t1', 1, 'A', True)]))       # one seed: undefined
        g = metrics.gap_closed(rows, 'C', resamples=2000)
        # task means: A = 1/3, B = (1 + 1 + .5)/3, C = 2/3 -> (2/3 - 1/3) / (2.5/3 - 1/3) = 2/3
        self.assertEqual((g['tasks'], g['gap_closed']), (3, round(2 / 3, 4)))
        self.assertLessEqual(g['ci95'][0], g['gap_closed'])
        self.assertGreaterEqual(g['ci95'][1], g['gap_closed'])
        no_gap = [r | {'passed': True} if r['condition'] == 'A' else r for r in rows]
        self.assertIsNone(metrics.gap_closed(no_gap, 'C', resamples=200)['gap_closed'])

    def test_tokens_split_run_time_from_upfront_counted_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            tasks = ['lcb-atcoder-abc387_a']
            plan = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1, 2], study=Path(tmp),
                                      conditions=['A', 'B', 'C'])
            planlib.write_json(batch / 'plan.json', plan)
            for item in plan['attempts']:
                if item['condition'] == 'A':
                    fake_run(batch, item, hidden='WA', final_public='candidate_failure')
                elif item['condition'] == 'B':
                    fake_run(batch, item, cost=0.01)                              # 10 in / 5 out per run
                else:                                                             # same artifact on both seeds
                    fake_run(batch, item, upfront=(0.02, 700, 400, 9.5, 'artifact-1'))
            report, _ = metrics.analyze([batch], [MAIN])
            b, c = report['summary']['all']['B'], report['summary']['all']['C']
            self.assertEqual(b['frontier_tokens'] | {}, {'run_input': 20, 'run_output': 10, 'upfront_input': 0,
                                                         'upfront_output': 0, 'total': 30, 'per_pass': 15.0})
            self.assertEqual((c['frontier_tokens']['upfront_input'], c['frontier_tokens']['run_input']), (700, 0))
            u = c['upfront_guidance']
            self.assertEqual((u['artifacts'], u['cost_usd'], u['latency_seconds_total']), (1, 0.02, 9.5))
            self.assertEqual(c['seed_consistency']['all_pass'], 1)
            self.assertEqual(report['gap_closed_vs_B']['C']['gap_closed'], 1.0)
            text = metrics.markdown(report)
            for section in ('## Gap closed toward B', '## Seed consistency', '## Frontier usage'):
                self.assertIn(section, text)


TASK = 'lcb-atcoder-zzz001_a'
REVISION = '0fe84c3912ea0c4d4a78037083943e8f0c4dd505'


def fake_shard(directory):
    """One LiveCodeBench-shaped row, and the manifest entry with its true hashes (built once by build_data)."""
    row = {'platform': 'atcoder', 'question_id': 'zzz001_a', 'question_title': 'Add',
           'question_content': 'Print A+B.\n\nSample Input 1\n\n1 2\n\nSample Output 1\n\n3\n',
           'public_test_cases': json.dumps([{'input': '1 2\n', 'output': '3\n', 'testtype': 'stdin'}]),
           'private_test_cases': json.dumps([{'input': f'{i} 1\n', 'output': f'{i + 1}\n', 'testtype': 'stdin'}
                                             for i in range(3)]),
           'difficulty': 'easy', 'contest_id': 'zzz001', 'contest_date': '2026-01-01T00:00:00'}
    shard = Path(directory) / 'shard.jsonl'
    shard.write_text(json.dumps(row) + '\n', encoding='utf-8')
    bd = taskslib.build_data()
    scratch = Path(directory) / 'scratch'
    bd.TASKS_DIR, bd.HIDDEN_DIR = taskslib._LFPath(scratch / 'tasks'), taskslib._LFPath(scratch / 'hidden')
    entry = {'task_id': TASK, 'version': '1', 'n_hidden': 3, 'public_sha256': None, 'hidden_sha256': None}
    bd.build(row, entry, 'test6.jsonl', REVISION, True)
    entry |= {'public_sha256': bd.sha256_dir(scratch / 'tasks' / TASK / 'tests/public'),
              'hidden_sha256': bd.sha256_dir(scratch / 'hidden' / TASK), 'manifest': 'test'}
    return shard, entry


class Tasks(unittest.TestCase):
    def prepare(self, study, shard, entry, ids=(TASK,)):
        with mock.patch.object(taskslib, 'pinned_tasks', return_value=({TASK: entry}, REVISION)), \
                mock.patch.object(taskslib, 'locate_shard', return_value=shard):
            return taskslib.prepare(study, list(ids))

    def test_build_is_byte_identical_to_the_agent_side_builder(self):
        from guided_agent import tasks as agent_tasks
        self.assertEqual(taskslib.CHECK_STUB, agent_tasks.CHECK_STUB)
        with tempfile.TemporaryDirectory() as tmp:
            shard, entry = fake_shard(tmp)
            ours, theirs = Path(tmp) / 'ours', Path(tmp) / 'theirs'
            self.assertEqual(self.prepare(ours, shard, entry), {'built': [TASK], 'verified': []})
            with mock.patch.object(agent_tasks, 'manifest_entries', return_value={TASK: entry}), \
                    mock.patch.object(agent_tasks, 'locate_shard', return_value=shard):
                agent_tasks.prepare([TASK], theirs, host_settings=None)
            files = sorted(p.relative_to(theirs) for p in theirs.rglob('*') if p.is_file()
                           and p.name != 'tasks-manifest.json')
            self.assertEqual(files, sorted(p.relative_to(ours) for p in ours.rglob('*') if p.is_file()
                                           and p.name != 'tasks-manifest.json'))
            for rel in files:
                self.assertEqual((ours / rel).read_bytes(), (theirs / rel).read_bytes(), rel)
                self.assertNotIn(b'\r', (ours / rel).read_bytes(), rel)
            a = planlib.read_json(theirs / 'tasks-manifest.json')['tasks'][TASK]
            b = planlib.read_json(ours / 'tasks-manifest.json')['tasks'][TASK]
            self.assertEqual({k: v for k, v in b.items() if a.get(k) != v}, {})

    def test_rebuild_verifies_repairs_partial_and_refuses_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            shard, entry = fake_shard(tmp)
            study = Path(tmp) / 'study'
            self.prepare(study, shard, entry)
            self.assertEqual(self.prepare(study, shard, entry), {'built': [], 'verified': [TASK]})
            (study / 'bundles' / TASK / 'check.py').unlink()          # interrupted build: rebuilt from the shard
            self.assertEqual(self.prepare(study, shard, entry)['built'], [TASK])
            (study / 'judge/hidden' / TASK / '01.out').write_text('wrong\n')
            with self.assertRaises(RuntimeError):
                self.prepare(study, shard, entry)
            with self.assertRaises(ValueError):                         # only manifest tasks
                self.prepare(study, shard, entry, ids=[TASK, 'lcb-atcoder-not_pinned'])

    def test_every_manifest_task_is_accepted(self):
        entries, revision = taskslib.pinned_tasks()
        self.assertEqual(len(entries), 68)
        self.assertEqual(revision, REVISION)


class FakeJudge:
    def __init__(self, verdicts):
        self.verdicts, self.calls = verdicts, []

    def up(self):
        return {'tests_sha256': 'suite-hash'}

    def run(self, task_id, code):
        self.calls.append(task_id)
        status = self.verdicts.get(task_id, 'pass')
        return {'status': status, 'passed': 3 if status == 'pass' else 1, 'total': 3, 'judge_version': '0.2.1',
                'verdict_counts': {'AC': 3} if status == 'pass' else {'AC': 1, 'WA': 2}, 'tests_sha256': 't',
                'code_sha256': hashlib.sha256(code).hexdigest(), 'error': None, 'cases': ['not copied']}


def finished_batch(batch):
    """Four finished runs (pass, fail, no submission, tampered submission) and one malformed record."""
    for name, task, code, tamper in (('r1', 't-pass', b'print(1)\n', False), ('r2', 't-fail', b'print(2)\n', False),
                                     ('r3', 't-none', None, False), ('r4', 't-pass', b'print(4)\n', True)):
        run = batch / name
        run.mkdir(parents=True)
        record = {'run_id': f'b-{name}', 'task_id': task, 'condition': 'A',
                  'submission_sha256': hashlib.sha256(code).hexdigest() if code else None}
        planlib.write_json(run / 'result.json', record)
        if code:
            (run / 'submission.py').write_bytes(code + (b'#' if tamper else b''))
    (batch / 'r5').mkdir()
    (batch / 'r5/result.json').write_text('{"run_id": "b-r5"}')            # no task_id: malformed


class Scoring(unittest.TestCase):
    def test_container_names_match_the_agents(self):
        from guided_agent import backend
        kit = judgelib.judgekit()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(kit, 'docker_bin', return_value='docker'):
            for suite in ('public', 'hidden'):
                self.assertEqual(judgelib.client(Path(tmp), suite).name, backend.judge_client(Path(tmp), suite).name)
                self.assertEqual(judgelib.client(Path(tmp), suite).root, Path(tmp) / 'judge')

    def test_score_matches_the_agent_side_evaluate(self):
        from guided_agent import runner
        with tempfile.TemporaryDirectory() as tmp:
            ours, theirs = Path(tmp) / 'ours', Path(tmp) / 'theirs'
            finished_batch(ours)
            finished_batch(theirs)
            judgelib.score(ours, Path(tmp), judge=FakeJudge({'t-fail': 'WA'}))
            with mock.patch.object(runner.backend, 'judge_client', return_value=FakeJudge({'t-fail': 'WA'})):
                runner.evaluate(theirs, Path(tmp))

            def outcomes(batch):
                return {p.name: {k: v for k, v in planlib.read_json(p).items() if k != 'evaluated_utc'}
                        for p in sorted((batch / 'eval').glob('*.json'))}
            self.assertEqual(outcomes(ours), outcomes(theirs))
            got = outcomes(ours)
            self.assertEqual([got[f'b-r{i}.json']['status'] for i in (1, 2, 3, 4)],
                             ['pass', 'WA', 'missing_submission', 'infrastructure_error'])
            self.assertEqual(got['malformed-r5.json']['status'], 'malformed_record')

    def test_scored_runs_are_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            finished_batch(batch)
            judgelib.score(batch, Path(tmp), judge=FakeJudge({}))
            again = FakeJudge({'t-pass': 'WA'})
            results = judgelib.score(batch, Path(tmp), judge=again)
            self.assertEqual(again.calls, [])
            self.assertEqual(results['b-r1']['status'], 'pass')


class Pipeline(unittest.TestCase):
    def test_guidance_authors_only_what_is_missing_then_freezes(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp).resolve()
            plan = planlib.build_plan(batch='b', task_ids=['t1', 't2'], seeds=[1], study=study,
                                      conditions=['A', 'C', 'D'])
            plan_path = study / 'plans/b.json'
            planlib.write_json(plan_path, plan)
            existing = Path(plan['attempts'][1]['guidance'])                # t1 C already authored
            existing.parent.mkdir(parents=True)
            existing.write_text('{}')
            calls = []

            def author(_study, *args, backend='auto'):
                calls.append(args)
                label, tasks_ = args[args.index('--label') + 1], args[args.index('--tasks') + 1:]
                prompt = args[args.index('--prompt-id') + 1]
                for t in tasks_:
                    out = study / 'guidance' / label / f'{t}.{prompt}.api.json'
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text('{}')
                return 0
            with mock.patch.object(pipeline, 'agent', side_effect=author):
                dry = pipeline.guidance(plan_path, study)
                self.assertEqual((dry['requests'], dry['authored'], calls), (3, False, []))
                done = pipeline.guidance(plan_path, study, yes=True)
            self.assertEqual(sorted((c[c.index('--prompt-id') + 1], c[c.index('--tasks') + 1:]) for c in calls),
                             [('contract-v1', ('t1', 't2')), ('plan-v1', ('t2',))])
            self.assertEqual(done['artifacts'], 4)
            self.assertTrue(pipeline.freeze_path(plan_path).exists())
            existing.write_text('{"changed": true}')
            with mock.patch.object(pipeline, 'agent', side_effect=author), self.assertRaises(RuntimeError):
                pipeline.guidance(plan_path, study, yes=True)

    def test_preflight_names_what_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp).resolve()
            plan_path = study / 'p.json'
            planlib.write_json(plan_path, planlib.build_plan(batch='b', task_ids=['t1'], seeds=[1], study=study,
                                                             conditions=['A', 'C']))
            with mock.patch.object(judgelib, 'image_id', return_value=None), \
                    mock.patch.object(pipeline, 'ollama_up', return_value=False):
                problems = pipeline.preflight(plan_path, study)
            self.assertEqual(len(problems), 4)
            for word in ('tasks not built', 'freeze', 'judge image', 'Ollama'):
                self.assertTrue(any(word in p for p in problems), word)
            with mock.patch.object(judgelib, 'image_id', return_value=None), self.assertRaises(RuntimeError), \
                    mock.patch.object(pipeline, 'agent') as agent:
                pipeline.run(plan_path, study)
            agent.assert_not_called()


if __name__ == '__main__':
    unittest.main()
