"""Offline regression tests for the final-evaluation additions (no model, Docker or network).

    python -m unittest evaluation.test_final

Selection and exposure, plan and freeze binding, scoring completeness and verdict integrity, provenance and cohort
checks, cost / token / latency aggregation, the budget preflight and pass@k.
"""
import hashlib
import itertools
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from evaluation import (budget, efficiency, exposure, judge as judgelib, metrics, passk, plan as planlib, pricing,
                        provenance, selection, validate)
from evaluation.test_evaluation import MAIN, REPO, FakeJudge, fake_run, usd
from guided_agent import integrity

FINAL = REPO / 'judge/manifests/final.json'
PILOT = REPO / 'judge/manifests/pilot.json'


# ----------------------------------------------------------------------------- selection
def synthetic_pool():
    """Six tasks per (difficulty, series) with varied hidden counts; a few with non-exact output semantics."""
    pool, audit = {}, {'tasks': {}}
    for d, s, i in itertools.product(selection.DIFFICULTIES, ('abc', 'arc'), range(6)):
        t = f'lcb-atcoder-{s}{900 + i}_{d[0]}'
        pool[t] = {'task_id': t, 'difficulty': d, 'series': s, 'n_hidden': 40 if i < 5 else 4, 'n_public': 2,
                   'title': t, 'contest_id': s, 'contest_date': '2025-01-01'}
        audit['tasks'][t] = {'category': 'multiple_answers' if i == 4 else 'exact'}
    registry = {'tasks': {t: {'class': 'development', 'sources': []} for t in list(pool)[::3]}}
    return pool, audit, registry


def pick(pool, audit, registry, **kwargs):
    return selection.select(pool, audit=audit, registry=registry, reserved_manifests=(), **kwargs)


class Selection(unittest.TestCase):
    def test_deterministic_and_seeded(self):
        pool, audit, registry = synthetic_pool()
        counts = {'easy': 3, 'medium': 2, 'hard': 4}
        first = pick(pool, audit, registry, counts=counts, seed=2108)
        self.assertEqual(first, pick(pool, audit, registry, counts=counts, seed=2108))
        self.assertEqual(Counter(pool[t]['difficulty'] for t in first['selected']), counts)   # unequal quotas
        other = [pick(pool, audit, registry, counts=counts, seed=s)['selected'] for s in range(1, 6)]
        self.assertTrue(any(o != first['selected'] for o in other))

    def test_eligibility_rules(self):
        pool, audit, registry = synthetic_pool()
        chosen = pick(pool, audit, registry, counts={'easy': 4, 'medium': 4, 'hard': 4})['selected']
        self.assertTrue(all(pool[t]['n_hidden'] >= 40 and audit['tasks'][t]['category'] == 'exact' for t in chosen))
        relaxed = pick(pool, audit, registry, counts={'easy': 10, 'medium': 1, 'hard': 1}, min_hidden_tests=1)
        self.assertTrue(any(pool[t]['n_hidden'] < 40 for t in relaxed['selected']))   # configurable threshold
        with self.assertRaises(ValueError):                                            # semantics never relaxed
            pick(pool, audit, registry, tasks=['lcb-atcoder-abc904_e'], counts={'easy': 1})

    def test_previously_used_allowed_by_default_and_optionally_excluded(self):
        pool, audit, registry = synthetic_pool()
        counts = {'easy': 4, 'medium': 4, 'hard': 4}
        default = pick(pool, audit, registry, counts={'easy': 8, 'medium': 8, 'hard': 8})['selected']
        self.assertTrue(any(t in registry['tasks'] for t in default))
        strict = pick(pool, audit, registry, counts=counts, exclude_previously_used=True)['selected']
        self.assertFalse(any(t in registry['tasks'] for t in strict))
        preferred = pick(pool, audit, registry, counts={'easy': 3, 'medium': 3, 'hard': 3}, prefer_unexposed=True)
        self.assertFalse(any(t in registry['tasks'] for t in preferred['selected']))

    def test_insufficient_pool_is_reported_never_shrunk(self):
        pool, audit, registry = synthetic_pool()
        with self.assertRaises(selection.InsufficientPool) as caught:
            pick(pool, audit, registry, counts={'easy': 20, 'medium': 2, 'hard': 2})
        self.assertEqual(caught.exception.available['easy']['eligible'], 8)
        self.assertIn('hidden tests < 40', caught.exception.available['easy']['ineligible_by_reason'])

    def test_base_replacements_stay_in_their_stratum(self):
        pool, audit, registry = synthetic_pool()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'base.json'
            keep = ['lcb-atcoder-abc900_e', 'lcb-atcoder-arc904_h', 'lcb-atcoder-arc905_h', 'lcb-atcoder-abc901_h']
            planlib.write_json(base, {'tasks': [{'task_id': t, 'difficulty': pool[t]['difficulty']} for t in keep]})
            result = pick(pool, audit, registry, base=base)
            self.assertEqual({r['task_id'] for r in result['removed']}, {'lcb-atcoder-arc904_h', 'lcb-atcoder-arc905_h'})
            for r in result['replacements']:
                self.assertEqual((pool[r['replacement']]['difficulty'], pool[r['replacement']]['series']), ('hard', 'arc'))
            self.assertIn('lcb-atcoder-abc900_e', result['selected'])


class FinalManifest(unittest.TestCase):
    """The committed official benchmark (judge/manifests/final.json)."""

    def setUp(self):
        self.manifest = planlib.read_json(FINAL)
        self.tasks = {e['task_id']: e for e in self.manifest['tasks']}

    def test_shape_and_eligibility(self):
        self.assertEqual(len(self.tasks), 60)
        self.assertEqual(self.manifest['counts'], {'easy': 20, 'medium': 20, 'hard': 20})
        self.assertEqual(self.manifest['hf_revision'], ['0fe84c3912ea0c4d4a78037083943e8f0c4dd505'])
        self.assertTrue(all(e['n_hidden'] == 40 and e['output_semantics'] == 'exact' for e in self.tasks.values()))
        pilot = {e['task_id'] for e in planlib.read_json(PILOT)['tasks']}
        self.assertFalse(pilot & set(self.tasks))
        for removed in ('lcb-atcoder-abc395_a', 'lcb-atcoder-arc195_c', 'lcb-atcoder-abc399_d',
                        'lcb-atcoder-abc400_e', 'lcb-atcoder-abc400_g', 'lcb-atcoder-arc196_b'):
            self.assertNotIn(removed, self.tasks)

    def test_hashes_agree_with_main_and_audit_and_registry(self):
        main = {e['task_id']: e for e in planlib.read_json(MAIN)['tasks']}
        self.assertEqual(len(set(main) & set(self.tasks)), 54)
        for t in set(main) & set(self.tasks):
            self.assertEqual((main[t]['public_sha256'], main[t]['hidden_sha256']),
                             (self.tasks[t]['public_sha256'], self.tasks[t]['hidden_sha256']))
        audit = planlib.read_json(selection.AUDIT)
        self.assertEqual(self.manifest['selection']['output_semantics_audit_sha256'], planlib.sha256_file(selection.AUDIT))
        self.assertEqual(self.manifest['selection']['exposure_registry_sha256'], planlib.sha256_file(exposure.REGISTRY))
        registry = exposure.load()
        for t, e in self.tasks.items():
            self.assertEqual(audit['tasks'][t]['category'], 'exact')
            self.assertEqual(e['exposure'], exposure.classify(t, registry)['class'])

    def test_audit_covers_the_whole_pool(self):
        audit = planlib.read_json(selection.AUDIT)
        self.assertEqual(len(audit['tasks']), 112)
        self.assertEqual(audit['counts'], {'exact': 102, 'tolerance': 1, 'multiple_answers': 6, 'case_insensitive': 3,
                                           'interactive': 0})
        self.assertEqual(audit['tasks']['lcb-atcoder-abc395_a']['category'], 'case_insensitive')
        self.assertEqual(audit['tasks']['lcb-atcoder-arc195_c']['category'], 'multiple_answers')


class Exposure(unittest.TestCase):
    def test_normalization_and_classes(self):
        self.assertEqual(exposure.normalize('atcoder-abc390_a'), 'lcb-atcoder-abc390_a')
        self.assertEqual(exposure.normalize('lcb-atcoder-abc390_a'), 'lcb-atcoder-abc390_a')
        self.assertEqual(exposure.classify_sources([{'class': 'other_scored'}, {'class': 'development'}]), 'development')
        self.assertEqual(exposure.subgroup('selection_holdout'), 'exposed')
        self.assertEqual(exposure.subgroup('none_known'), 'potentially_unseen')
        self.assertEqual(exposure.subgroup('uncertain'), 'uncertain')

    def test_main_manifest_overlap_is_recorded(self):
        registry = exposure.load()
        main = [e['task_id'] for e in planlib.read_json(MAIN)['tasks']]
        exposed = [t for t in main if exposure.classify(t, registry)['class'] in exposure.EXPOSED]
        self.assertEqual(len(exposed), 27)               # at least the 21 of the preliminary audit
        self.assertEqual(exposure.classify('lcb-atcoder-zzz999_a', registry)['class'], 'none_known')


# ----------------------------------------------------------------------------- plan and freeze
class PlanAndFreeze(unittest.TestCase):
    def test_williams_design_is_balanced(self):
        rows = planlib.williams(list('ABCDE'))
        self.assertEqual(len(rows), 10)
        for position in range(5):
            self.assertEqual(Counter(r[position] for r in rows), {c: 2 for c in 'ABCDE'})
        pairs = Counter((r[i], r[i + 1]) for r in rows for i in range(4))
        self.assertEqual(set(pairs.values()), {2})        # every ordered pair adjacent equally often
        self.assertEqual(len(planlib.williams(list('ABCD'))), 4)

    def test_plan_is_reproducible_and_bound_to_its_benchmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = planlib.manifest_tasks(FINAL, per_difficulty=1)
            bench = planlib.benchmark_record(FINAL, tasks, REPO)
            a = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1, 2], study=Path(tmp), benchmark=bench)
            b = planlib.build_plan(batch='b', task_ids=tasks, seeds=[1, 2], study=Path(tmp), benchmark=bench)
            self.assertEqual(planlib.plan_sha256(a), planlib.plan_sha256(b))
            self.assertEqual(bench['manifest'], 'judge/manifests/final.json')
            from evaluation import pipeline
            self.assertEqual(pipeline.plan_manifests(a), [FINAL])
            changed = json.loads(json.dumps(a))
            changed['benchmark']['manifest_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                pipeline.plan_manifests(changed)

    def test_freeze_is_bound_to_the_plan_and_the_artifact_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp)
            plan = planlib.build_plan(batch='b', task_ids=['t1', 't2'], seeds=[1], study=study, conditions=['A', 'C'])
            statement = 'Print A+B.'
            for t in ('t1', 't2'):
                planlib.write_json(study / 'bundles' / t / 'task.json', {'statement': statement})
            for path in planlib.guidance_artifacts(plan):
                task = Path(path).name.split('.')[0]
                planlib.write_json(path, {'task_id': task, 'prompt_id': 'plan-v1',
                                          'statement_sha256': hashlib.sha256(statement.encode()).hexdigest()})
            freeze = study / 'f.json'
            planlib.freeze(plan, freeze)
            self.assertEqual(planlib.check(freeze, plan, study), [])
            other = planlib.build_plan(batch='b', task_ids=['t1'], seeds=[1], study=study, conditions=['A', 'C'])
            problems = planlib.check(freeze, other, study)
            self.assertTrue(any('different plan' in p for p in problems))
            self.assertTrue(any('artifact set differs' in p for p in problems))
            planlib.write_json(study / 'bundles/t2/task.json', {'statement': 'something else'})
            self.assertTrue(any('different statement' in p for p in planlib.check(freeze, plan, study)))
            v1 = study / 'v1.json'
            planlib.write_json(v1, {'schema': 'csc2108-guidance-freeze-v1', 'artifacts': {}})
            self.assertTrue(any('not bound to a plan' in p for p in planlib.check(v1, plan)))


# ----------------------------------------------------------------------------- scoring integrity
def scored_batch(tmp, conditions=('A', 'B'), seeds=(1, 2), task_ids=None, **runs):
    tmp = Path(tmp)
    batch = tmp / 'runs' / 'b'
    tasks = task_ids or planlib.manifest_tasks(FINAL, per_difficulty=1)
    plan = planlib.build_plan(batch='b', task_ids=tasks, seeds=list(seeds), study=tmp, conditions=list(conditions),
                              order='fixed')
    planlib.write_json(batch / 'plan.json', plan)
    items = {(a['task_id'], a['condition'], a['seed']): a for a in plan['attempts']}
    return batch, plan, items, tasks


class Completeness(unittest.TestCase):
    def test_missing_verdict_blocks_official_and_is_not_a_failure_in_preliminary(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,))
            for key, item in items.items():
                fake_run(batch, item, hidden='pass', score=key != (tasks[0], 'B', 1), cost=0.01 if key[1] == 'B' else None)
            status = validate.batch_status(batch)
            self.assertEqual(status['counts']['awaiting_scoring'], 1)
            with self.assertRaises(metrics.IncompleteEvaluation):
                metrics.analyze([batch], [FINAL])
            report, rows = metrics.analyze([batch], [FINAL], preliminary=True)
            self.assertEqual(report['status'], 'preliminary')
            self.assertTrue(metrics.markdown(report).startswith('# PRELIMINARY'))
            self.assertEqual(report['summary']['all']['A']['pass_rate'], 1.0)   # the unscored B run did not fail A
            self.assertEqual(report['sample_sizes']['excluded_blocks'], 1)
            self.assertEqual(report['summary']['all']['B']['runs'], 2)

    def test_incomplete_batch_refuses_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,))
            first = next(iter(items.values()))
            fake_run(batch, first, score=False)
            (batch / (integrity.run_name(list(items.values())[1]) + '.incomplete-abc123')).mkdir()
            with self.assertRaises(judgelib.ScoringRefused):
                judgelib.score(batch, Path(tmp), judge=FakeJudge({}))
            judgelib.score(batch, Path(tmp), judge=FakeJudge({}), allow_incomplete=True)
            counts = validate.batch_status(batch)['counts']
            # the scored run waits for `guided_agent measure` (pipeline.score runs it): until then it is invalid
            self.assertEqual((counts['invalid'], counts['incomplete'], counts['not_executed']), (1, 1, 4))
            self.assertEqual(len(list((batch / 'eval').glob('*.json'))), 1)

    def test_interrupted_scoring_resumes_without_rejudging(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,))
            for item in items.values():
                fake_run(batch, item, score=False)
            dying = FakeJudge({tasks[1]: 'raise'})
            with self.assertRaises(KeyboardInterrupt):                     # the scoring process is killed
                judgelib.score(batch, Path(tmp), judge=dying)
            done = len(list((batch / 'eval').glob('*.json')))
            self.assertGreater(done, 0)
            again = FakeJudge({})
            judgelib.score(batch, Path(tmp), judge=again)
            self.assertEqual(len(again.calls), len(items) - done)
            self.assertTrue(validate.batch_status(batch)['complete'] is False)   # measurement.json not refreshed yet

    def test_stale_and_mismatched_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A',))
            dirs = [fake_run(batch, item) for item in items.values()]
            self.assertEqual(validate.batch_status(batch)['counts']['scored'], 3)
            # 1: the submission changed after scoring
            (dirs[0] / 'submission.py').write_bytes(b'print("other")\n')
            # 2: a verdict for another run
            verdict_path = next((batch / 'eval').glob(f'*{dirs[1].name}.json'))
            verdict = planlib.read_json(verdict_path) | {'task_id': 'lcb-atcoder-other'}
            planlib.write_json(verdict_path, verdict)
            # 3: the measurement record was not refreshed after scoring
            measurement = planlib.read_json(dirs[2] / 'measurement.json')
            measurement['correctness']['hidden_status'] = None
            planlib.write_json(dirs[2] / 'measurement.json', measurement)
            status = validate.batch_status(batch)
            self.assertEqual(status['counts']['invalid'], 3)
            text = ' '.join(p for a in status['attempts'] for p in a['problems'])
            for phrase in ('stale verdict or changed submission', 'verdict task_id', 'stale measurement'):
                self.assertIn(phrase, text)
            with self.assertRaises(metrics.IncompleteEvaluation):
                metrics.analyze([batch], [FINAL])

    def test_rescoring_a_stale_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A',), task_ids=['t-pass'])
            run_dir = fake_run(batch, next(iter(items.values())), hidden='candidate_failure')
            record = planlib.read_json(run_dir / 'result.json')
            new = b'print(2)\n'
            (run_dir / 'submission.py').write_bytes(new)
            planlib.write_json(run_dir / 'result.json', record | {'submission_sha256': hashlib.sha256(new).hexdigest()})
            with self.assertRaises(judgelib.ScoringRefused):
                judgelib.score(batch, Path(tmp), judge=FakeJudge({}))
            judgelib.score(batch, Path(tmp), judge=FakeJudge({}), rescore_stale=True)
            self.assertEqual(len(list((batch / 'eval/stale').glob('*.json'))), 1)
            verdict = planlib.read_json(batch / 'eval' / f"{record['run_id']}.json")
            self.assertEqual((verdict['status'], verdict['code_sha256']), ('pass', hashlib.sha256(new).hexdigest()))

    def test_hidden_tests_must_be_the_selected_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A',))
            planlib.write_json(Path(tmp) / 'tasks-manifest.json', {'tasks': {
                t: {'hidden_judge_sha256': 'expected-digest', 'n_hidden': 40} for t in tasks}})
            fake_run(batch, items[(tasks[0], 'A', 1)], tests_sha256='expected-digest')
            fake_run(batch, items[(tasks[1], 'A', 1)], tests_sha256='other-tests')
            fake_run(batch, items[(tasks[2], 'A', 1)], tests_sha256='expected-digest')
            status = validate.batch_status(batch)
            self.assertEqual((status['counts']['scored'], status['counts']['invalid']), (2, 1))

    def test_malformed_records_and_documented_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A', 'B'))
            for item in items.values():
                fake_run(batch, item, cost=0.01 if item['condition'] == 'B' else None)
            broken = batch / integrity.run_name(items[(tasks[0], 'A', 1)])
            (broken / 'result.json').write_text('{"run_id": "x"}')
            self.assertEqual(validate.batch_status(batch)['counts']['invalid'], 1)
            with self.assertRaises(metrics.IncompleteEvaluation):
                metrics.analyze([batch], [FINAL])
            validate.add_exclusion(batch, tasks[0], 1, 'result.json corrupted by a disk fault')
            report, _ = metrics.analyze([batch], [FINAL])
            self.assertEqual(report['status'], 'official')
            self.assertEqual(report['excluded_blocks'][0]['task_id'], tasks[0])
            self.assertIn('documented', report['excluded_blocks'][0]['reasons'][0])
            with self.assertRaises(ValueError):
                validate.add_exclusion(batch, tasks[0], 1, 'again')


class Classification(unittest.TestCase):
    def test_infrastructure_is_decided_before_the_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A', 'E'))
            docker = "Command '['docker', 'exec', 'x']' timed out after 5 seconds"
            fake_run(batch, items[(tasks[0], 'A', 1)], hidden='pass', infra=True, agent_error=docker)   # passed anyway
            fake_run(batch, items[(tasks[0], 'E', 1)])
            fake_run(batch, items[(tasks[1], 'A', 1)])
            fake_run(batch, items[(tasks[1], 'E', 1)], diagnosis_error='transport_error')   # provider fault, passed
            fake_run(batch, items[(tasks[2], 'A', 1)])
            fake_run(batch, items[(tasks[2], 'E', 1)], hidden='candidate_failure', final_public='candidate_failure',
                     diagnosis_error='incomplete_response')                                 # an E outcome
            report, rows = metrics.analyze([batch], [FINAL])
            self.assertEqual({(b['task_id'], b['seed']) for b in report['excluded_blocks']}, {(tasks[0], 1), (tasks[1], 1)})
            reasons = ' '.join(r for b in report['excluded_blocks'] for r in b['reasons'])
            self.assertIn('frontier_provider:transport_error', reasons)
            self.assertEqual(report['summary']['all']['E']['runs'], 1)

    def test_frontier_coder_faults(self):
        doc = {'condition': {}}
        self.assertEqual(metrics.frontier_fault(doc, 'FrontierCoderError: RuntimeError: API request ceiling reached'),
                         'frontier_provider:budget_exhausted')
        self.assertEqual(metrics.frontier_fault(doc, 'FrontierCoderError: ApiRequestError: API HTTP 500: x'),
                         'frontier_provider:transport_error')
        self.assertIsNone(metrics.frontier_fault(doc, 'litellm.Timeout: Connection timed out after 180.0 seconds'))
        self.assertIsNone(metrics.frontier_fault({'condition': {'diagnosis': {'error_category': 'no_local_budget'}}}, ''))


class Cohorts(unittest.TestCase):
    def test_bind_refuses_a_changed_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = Path(tmp) / 'b'
            record = {k: k for k in provenance.BINDING} | {'git': {'commit': 'c1'}}
            self.assertEqual(provenance.bind(batch, record, 't1'), [])
            self.assertEqual(provenance.bind(batch, record | {'git': {'commit': 'c2'}}, 't2'), [])  # docs-only commit
            self.assertEqual(len((batch / 'provenance-sessions.jsonl').read_text().splitlines()), 2)
            problems = provenance.bind(batch, record | {'local_model': 'other digest'}, 't3')
            self.assertTrue(problems and 'local_model' in problems[0])

    def test_incompatible_batches_and_mixed_hosts_are_not_pooled(self):
        base = {k: 'x' for k in provenance.COMPATIBILITY}
        self.assertEqual(provenance.compatible([('a', base), ('b', dict(base))]), [])
        self.assertTrue(provenance.compatible([('a', base), ('b', base | {'hardware_cohort': 'mac'})]))
        rows = [{'condition': 'A', 'host': 'Windows/AMD64/pc'}, {'condition': 'C', 'host': 'Darwin/arm64/mac'}]
        problems, _ = metrics.cohort_problems(rows)
        self.assertTrue(any('hardware hosts' in p for p in problems))
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1,), conditions=('A',))
            for item in items.values():
                fake_run(batch, item)
            planlib.write_json(batch / 'provenance.json', base)
            other_batch = Path(tmp) / 'runs' / 'b2'
            plan2 = planlib.build_plan(batch='b2', task_ids=tasks, seeds=[2], study=Path(tmp), conditions=['A'])
            planlib.write_json(other_batch / 'plan.json', plan2)
            for item in plan2['attempts']:
                fake_run(other_batch, item)
            planlib.write_json(other_batch / 'provenance.json', base | {'local_model': 'other'})
            with self.assertRaises(metrics.IncompleteEvaluation):
                metrics.analyze([batch, other_batch], [FINAL])


# ----------------------------------------------------------------------------- cost, tokens, latency
class Efficiency(unittest.TestCase):
    def test_cache_aware_cost_and_missing_usage(self):
        self.assertAlmostEqual(pricing.request_cost(1000, 500, 600), (400 * 2 + 600 * 0.1 + 500 * 10) / 1e6)
        self.assertAlmostEqual(pricing.request_cost(1000, 500), (1000 * 2 + 500 * 10) / 1e6)
        self.assertIsNone(pricing.request_cost(None, 500))
        self.assertIsNotNone(pricing.price('openai/gpt-6.2-sol'))
        self.assertIsNone(efficiency.total([1.0, None]))
        self.assertEqual(efficiency.ratio(1.0, 0, 'no passing attempt'), {'value': None, 'reason': 'no passing attempt'})

    def test_relative_metrics_and_undefined_values(self):
        self.assertEqual(efficiency.passes_per_dollar(5, 0.0, 3, 0.0)['value'], None)
        neg = efficiency.passes_per_dollar(2, 0.5, 3, 0.0)
        self.assertEqual((neg['value'], neg['note']), (-2.0, 'negative: fewer passes than A'))
        zero_b = {'cost_usd': {'total': 0.0}, 'tokens': {'total': 0}}
        self.assertIsNone(efficiency.relative({'cost_usd': {'total': 1.0}, 'tokens': {'total': 5}}, zero_b)
                          ['cost_reduction']['value'])

    def test_guidance_dedup_cold_warm_amortized_and_matched_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, plan, items, tasks = scored_batch(tmp, seeds=(1, 2, 3), conditions=('A', 'B', 'C'),
                                                     task_ids=planlib.manifest_tasks(FINAL)[:1])
            task = tasks[0]
            for seed in (1, 2, 3):
                fake_run(batch, items[(task, 'A', seed)], hidden='candidate_failure', final_public='candidate_failure',
                         wall=100.0)
                fake_run(batch, items[(task, 'B', seed)], cost=0.01, tokens=(1000, 500, 600), wall=50.0)
                fake_run(batch, items[(task, 'C', seed)], upfront=(0.02, 800, 900, 30.0, 'art-1'), wall=60.0)
            report, rows = metrics.analyze([batch], [FINAL])
            c = report['summary']['all']['C']['efficiency']
            self.assertAlmostEqual(c['cost_usd']['upfront'], usd(800, 900))            # once, not three times
            self.assertEqual(c['requests']['upfront'], 1)
            self.assertEqual(c['latency']['cold_start_seconds']['median'], 90.0)        # 60 + 30
            self.assertEqual(c['latency']['warm_start_seconds']['median'], 60.0)
            self.assertEqual(c['latency']['amortized_seconds']['median'], 70.0)         # 60 + 30 / 3
            self.assertAlmostEqual(c['cost_usd']['amortized_per_attempt']['median'], round(usd(800, 900) / 3, 3), 3)
            b = report['summary']['all']['B']['efficiency']
            self.assertAlmostEqual(b['cost_usd']['total'], 3 * usd(1000, 500, 600))
            self.assertEqual(b['tokens']['total'], 3 * 1500)
            self.assertEqual(b['tokens']['cached_input'], 3 * 600)
            rel = report['relative_efficiency']['C']
            self.assertEqual(rel['runtime']['A']['cold_start_seconds']['ratio']['median'], 0.9)
            self.assertEqual(rel['runtime']['A']['cold_start_seconds']['reduction'], 0.1)
            self.assertEqual(rel['additional_passes_per_usd_vs_A']['additional_passes'], 3)
            self.assertIsNotNone(rel['vs_B']['cost_reduction']['value'])
            row = report['main_table'][2]
            self.assertEqual((row['condition'], row['hidden_pass_rate'], row['e2e_latency_seconds']['median']),
                             ('C', 1.0, 90.0))
            self.assertEqual(report['pass_at_k']['ks'], [1, 2, 3])

    def test_ledger_reconciliation(self):
        ledger = {'requests': [
            {'purpose': 'b B', 'kind': 'coder', 'state': 'completed', 'api_model': 'gpt-6.2-sol',
             'usage': {'prompt_tokens': 1000, 'completion_tokens': 100}},
            {'purpose': 'b B', 'kind': 'coder', 'state': 'http_error', 'bound_usd_conservative': 0.5},
            {'purpose': 'other study', 'kind': 'plan', 'state': 'completed',
             'usage': {'prompt_tokens': 1, 'completion_tokens': 1}}]}
        out = efficiency.ledger_report(ledger, {'b B'}, {0})
        self.assertEqual((out['all']['requests'], out['attributable_to_included_runs']['requests']), (2, 1))
        self.assertEqual(out['not_attributable']['requests_without_usage'], 1)
        self.assertAlmostEqual(out['all']['token_cost_usd_known'], usd(1000, 100))


class Budget(unittest.TestCase):
    def test_assessment_and_ledger_ceilings(self):
        from guided_agent import providers
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp)
            tasks = planlib.manifest_tasks(FINAL)
            plan_path = study / 'plans/p.json'
            planlib.write_json(plan_path, planlib.build_plan(batch='p', task_ids=tasks, seeds=[2108, 2109, 2110],
                                                             study=study))
            ledger = study / 'api-ledger.json'
            out = budget.assess(plan_path, study, ledger)
            self.assertEqual(out['paid_runs_remaining'], {'B': 180, 'E': 180})
            self.assertEqual(out['missing_guidance'], {'C': 60, 'D': 60})
            expected, worst = out['scenarios']['expected'], out['scenarios']['worst']
            self.assertEqual(expected['requests']['total'], 60 + 60 + 584 + 90)
            self.assertGreater(worst['reservation_usd'], expected['reservation_usd'])
            self.assertFalse(out['fits_within_ceilings']['worst'])
            self.assertEqual(out['ceilings']['code_maximum'], {'max_requests': providers.MAX_REQUESTS,
                                                               'max_usd': providers.MAX_USD})
            with self.assertRaises(ValueError):
                budget.init_ledger(ledger, providers.MAX_REQUESTS + 1, 1.0)
            budget.init_ledger(ledger, 40, 5.0)
            with self.assertRaises(FileExistsError):
                budget.init_ledger(ledger, 40, 5.0)
            small = budget.assess(plan_path, study, ledger)
            self.assertEqual(small['ceilings']['max_requests'], 40)
            self.assertFalse(small['fits_within_ceilings']['expected'])
            data = planlib.read_json(ledger)
            self.assertEqual(providers.Ledger(ledger).data['max_requests'], data['max_requests'])


# ----------------------------------------------------------------------------- pass@k
class PassAtK(unittest.TestCase):
    def test_three_attempts_table(self):
        expected = {0: (0, 0, 0), 1: (1 / 3, 2 / 3, 1), 2: (2 / 3, 1, 1), 3: (1, 1, 1)}
        for c, values in expected.items():
            for k, value in zip((1, 2, 3), values):
                self.assertAlmostEqual(passk.pass_at_k(3, c, k), value)

    def test_arbitrary_repetitions_and_insufficient_attempts(self):
        self.assertAlmostEqual(passk.pass_at_k(5, 2, 2), 1 - 3 / 10)
        self.assertEqual(passk.pass_at_k(5, 5, 5), 1.0)
        self.assertIsNone(passk.pass_at_k(2, 1, 3))
        rows = [{'task_id': 't', 'condition': 'A', 'seed': s, 'passed': s == 1} for s in (1, 2)]
        summary = passk.summary(rows, 'A', [1, 2, 3], metrics.bootstrap_ci)
        self.assertEqual(summary['pass@3'], {'value': None, 'ci95': None, 'eligible_tasks': 0,
                                             'note': 'no task has 3 valid attempts'})
        self.assertEqual(summary['pass@2']['value'], 1.0)

    def test_matched_comparison_uses_common_seeds(self):
        rows = [{'task_id': 't', 'condition': 'A', 'seed': s, 'passed': False} for s in (1, 2, 3)]
        rows += [{'task_id': 't', 'condition': 'C', 'seed': s, 'passed': s == 3} for s in (1, 2, 3)]
        rows = [r for r in rows if not (r['condition'] == 'A' and r['seed'] == 3)]     # A lost seed 3
        v1 = passk.versus(rows, 'C', 'A', 1, metrics.bootstrap_ci)
        self.assertEqual((v1['tasks'], v1['difference']), (1, 0.0))                     # C's seed-3 pass not counted
        self.assertEqual(passk.versus(rows, 'C', 'A', 3, metrics.bootstrap_ci)['tasks'], 0)

    def test_report_levels_exclusions_and_pass1_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = planlib.manifest_tasks(FINAL, per_difficulty=2)
            batch, plan, items, _ = scored_batch(tmp, seeds=(1, 2, 3), conditions=('A', 'B', 'C'), task_ids=tasks)
            for (task, cond, seed), item in items.items():
                index = tasks.index(task)
                passed = {'A': seed == 1 and index % 2 == 0, 'B': True, 'C': seed <= 2}[cond]
                infra = cond == 'B' and index == 5 and seed == 3
                fake_run(batch, item, hidden='infrastructure_error' if infra else 'pass' if passed else 'candidate_failure',
                         final_public='pass' if passed else 'candidate_failure', cost=0.01 if cond == 'B' else None)
            report, rows = metrics.analyze([batch], [FINAL])
            pk = report['pass_at_k']
            self.assertEqual(pk['ks'], [1, 2, 3])
            c_all = pk['by_level']['all']['C']
            self.assertAlmostEqual(c_all['pass@1']['value'], round((5 * 2 / 3 + 1.0) / 6, 4))   # task 5 kept 2 seeds
            self.assertEqual(c_all['pass@3']['eligible_tasks'], 5)                               # task 5 has only 2
            self.assertEqual(c_all['pass@2']['value'], 1.0)
            for level in ('easy', 'medium', 'hard'):
                self.assertEqual(pk['by_level'][level]['C']['tasks'], 2)
            self.assertEqual(pk['versus_A']['all']['C']['pass@3']['tasks'], 5)
            self.assertIsNotNone(pk['gap_closed_vs_B']['all']['C']['pass@1']['gap_closed'])
            self.assertIn('C and D reuse one upfront guidance artifact', ' '.join(pk['notes']))
            self.assertEqual(report['summary']['all']['A']['runs'], 17)      # the infrastructure block left every condition
            text = metrics.markdown(report)
            self.assertIn('| A — Local |', text)
            self.assertIn('All attempts successful', text)
            metrics.write(report, rows, Path(tmp) / 'out')
            per_task = (Path(tmp) / 'out/tasks.csv').read_text().splitlines()
            self.assertEqual(len(per_task), 1 + 6 * 3)

    def test_pass1_equals_pass_rate_with_equal_repetitions(self):
        rows = [{'task_id': f't{t}', 'condition': 'A', 'seed': s, 'passed': (t + s) % 3 == 0}
                for t in range(7) for s in (1, 2, 3)]
        summary = passk.summary(rows, 'A', [1], metrics.bootstrap_ci)
        self.assertAlmostEqual(summary['pass@1']['value'], round(sum(r['passed'] for r in rows) / len(rows), 4))


if __name__ == '__main__':
    unittest.main()
