"""evaluation command line: owns the tasks, the judge, the schedule, hidden scoring and the metrics.

  python -m evaluation select   --out MANIFEST.json [--counts easy=20 medium=20 hard=20] [--base M] [...]
  python -m evaluation plan     --batch final-main --seeds 2108 2109 2110 --out PLAN.json [--manifest M]
  python -m evaluation tasks    PLAN.json            # build/verify the plan's tasks (judge suites + agent bundles)
  python -m evaluation judge                         # build the judge image, start judge-public, selftest
  python -m evaluation guidance PLAN.json [--yes]    # author missing C/D guidance (paid), then freeze it
  python -m evaluation budget   PLAN.json            # paid-request and reservation estimate against the ledger
  python -m evaluation ready    PLAN.json            # every readiness check; runs nothing
  python -m evaluation run      PLAN.json            # readiness, provenance, then the agent: guided_agent batch
  python -m evaluation status   PLAN.json            # state of every scheduled attempt
  python -m evaluation score    PLAN.json            # hidden scoring after ALL attempts, then guided_agent measure
  python -m evaluation metrics  BATCH_DIR [BATCH_DIR ...] --out REPORT_DIR [--preliminary]

  python -m evaluation freeze | check | exclude | exposure | crosscheck

The study root is CSC2108_STUDY_ROOT or --study (before the command); every step reads the same plan.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from . import metrics, plan as planlib

REPO = Path(__file__).resolve().parents[1]
FINAL = REPO / 'judge/manifests/final.json'
MANIFESTS = [REPO / 'judge/manifests/main.json', REPO / 'judge/manifests/pilot.json', FINAL]


def study_root(args):
    study = args.study or os.environ.get('CSC2108_STUDY_ROOT')
    if not study:
        raise SystemExit('set CSC2108_STUDY_ROOT or pass --study')
    return Path(study).resolve()


def show(value):
    print(json.dumps(value, indent=1, ensure_ascii=False, default=str))


def parse_counts(values):
    counts = {}
    for value in values or ():
        level, _, n = value.partition('=')
        if not n.isdigit():
            raise SystemExit(f'--counts takes difficulty=N, got {value!r}')
        counts[level] = int(n)
    return counts or None


def cmd_select(args):
    from . import selection, tasks as taskslib
    bd = taskslib.build_data()
    shard = taskslib.locate_shard(bd, '0fe84c3912ea0c4d4a78037083943e8f0c4dd505', args.shard)
    pool = selection.load_pool(shard)
    counts = parse_counts(args.counts)
    if args.per_difficulty:
        counts = {d: args.per_difficulty for d in selection.DIFFICULTIES}
    if args.total:
        if args.total % len(selection.DIFFICULTIES):
            raise SystemExit(f'--total {args.total} does not split evenly over {selection.DIFFICULTIES}; use --counts')
        counts = {d: args.total // len(selection.DIFFICULTIES) for d in selection.DIFFICULTIES}
    reserved = [] if args.no_reserve else [Path(p) for p in (args.reserve or selection.RESERVED)]
    config = {'counts': counts, 'tasks': args.tasks or [], 'base': Path(args.base).name if args.base else None,
              'base_sha256': planlib.sha256_file(args.base) if args.base else None, 'seed': args.seed,
              'min_hidden_tests': args.min_hidden_tests, 'exclude_previously_used': args.exclude_previously_used,
              'prefer_unexposed': args.prefer_unexposed, 'reserved_manifests': [p.name for p in reserved]}
    try:
        result = selection.select(pool, counts=counts, tasks=args.tasks or (), base=args.base, seed=args.seed,
                                  min_hidden_tests=args.min_hidden_tests,
                                  exclude_previously_used=args.exclude_previously_used,
                                  prefer_unexposed=args.prefer_unexposed, reserved_manifests=reserved)
    except selection.InsufficientPool as error:
        show({'error': str(error), 'available': error.available})
        raise SystemExit(2)
    if args.dry_run:
        show({k: result[k] for k in ('removed', 'replacements', 'eligible_counts')} | {'selected': len(result['selected'])})
        return
    data = selection.manifest(result, pool, name=args.name, seed=args.seed,
                              revision='0fe84c3912ea0c4d4a78037083943e8f0c4dd505', shard_sha256=bd.SHARDS['test6.jsonl'],
                              config=config)
    selection.write(args.out, data)
    show({'manifest': str(args.out), 'counts': data['counts'], 'removed': len(result['removed']),
          'replacements': result['replacements'], 'exposure': data['selection']['exposure_counts'],
          'hidden_tests': data['selection']['hidden_test_counts']})


def cmd_plan(args):
    study = study_root(args)
    seeds = args.seeds or [args.first_seed + i for i in range(args.repetitions)]
    tasks = planlib.manifest_tasks(args.manifest, args.tasks, args.per_difficulty)
    benchmark = planlib.benchmark_record(args.manifest, tasks, REPO)
    plan = planlib.build_plan(batch=args.batch, task_ids=tasks, seeds=seeds, study=study,
                              conditions=args.conditions, plan_label=args.plan_label,
                              contract_label=args.contract_label, b_max_requests=args.b_max_requests,
                              e_provider=args.e_provider, b_provider=args.b_provider,
                              outer_timeout=args.outer_timeout, cohort=args.cohort, order=args.order,
                              benchmark=benchmark)
    planlib.write_json(args.out, plan)
    show({'plan': str(args.out), 'tasks': len(tasks), 'seeds': seeds, 'conditions': args.conditions,
          'attempts': len(plan['attempts']), 'order': args.order,
          'guidance_artifacts': len(planlib.guidance_artifacts(plan)), 'manifest': benchmark['manifest'],
          'plan_sha256': planlib.plan_sha256(plan)})


def cmd_tasks(args):
    from . import pipeline, tasks
    plan = planlib.read_json(args.plan)
    result = tasks.prepare(study_root(args), pipeline.plan_tasks(plan), shard=args.shard,
                           manifests=pipeline.plan_manifests(plan))
    show({'built': len(result['built']), 'verified': len(result['verified'])})


def cmd_judge(args):
    from . import judge
    study = study_root(args)
    if args.down:
        judge.down(study)
        show({'down': True})
        return
    image = judge.build_image(force=args.rebuild)
    status = judge.up(study) | {'built': image['built']}
    show(status)
    if not status['selftest_ok']:
        raise SystemExit(1)


def cmd_guidance(args):
    from . import pipeline
    show(pipeline.guidance(args.plan, study_root(args), yes=args.yes, backend=args.backend))


def cmd_budget(args):
    from . import budget
    from guided_agent.common import ledger_path
    study = study_root(args)
    ledger = Path(args.ledger) if args.ledger else ledger_path(study)
    if args.init_ledger:
        if args.max_requests is None or args.max_usd is None:
            raise SystemExit('--init-ledger needs --max-requests and --max-usd')
        budget.init_ledger(ledger, args.max_requests, args.max_usd)
    show(budget.assess(args.plan, study, ledger))


def cmd_ready(args):
    from . import pipeline
    report = pipeline.readiness(args.plan, study_root(args), services=not args.offline)
    show(report)
    raise SystemExit(0 if report['ready'] else 1)


def cmd_run(args):
    from . import pipeline
    raise SystemExit(pipeline.run(args.plan, study_root(args), backend=args.backend))


def cmd_status(args):
    from . import pipeline, validate
    study = study_root(args)
    plan = planlib.read_json(args.plan)
    directory = pipeline.batch_dir(plan, study)
    if not (directory / 'plan.json').exists():
        show({'batch': str(directory), 'scheduled': len(plan['attempts']), 'note': 'not started'})
        return
    show(validate.summary(validate.batch_status(directory, study), limit=args.limit))


def cmd_score(args):
    from . import pipeline
    show(pipeline.score(args.plan, study_root(args), backend=args.backend, measure=not args.no_measure,
                        allow_incomplete=args.allow_incomplete, rescore_stale=args.rescore_stale))


def cmd_exclude(args):
    from . import pipeline, validate
    from .judge import utc_now
    plan = planlib.read_json(args.plan)
    blocks = {(a['task_id'], a['seed']) for a in plan['attempts']}
    if (args.task, args.seed) not in blocks:
        raise SystemExit(f'({args.task}, {args.seed}) is not a block of this plan')
    directory = pipeline.batch_dir(plan, study_root(args))
    show(validate.add_exclusion(directory, args.task, args.seed, args.reason, args.by, utc_now()))


def cmd_freeze(args):
    plan = planlib.read_json(args.plan)
    out = Path(args.out or Path(args.plan).with_suffix('.freeze.json'))
    record = planlib.freeze(plan, out)
    show({'freeze': str(out), 'artifacts': len(record['artifacts'])})


def cmd_check(args):
    plan = planlib.read_json(args.plan) if args.plan else None
    problems = planlib.check(args.freeze, plan, study_root(args) if plan and (args.study or
                                                                              os.environ.get('CSC2108_STUDY_ROOT')) else None)
    show({'unchanged': not problems, 'problems': problems})
    raise SystemExit(1 if problems else 0)


def cmd_exposure(args):
    from . import exposure
    if args.build:
        registry = exposure.build(args.study_roots or ())
        exposure.write(registry)
        show({'registry': str(exposure.REGISTRY), 'tasks': len(registry['tasks'])})
        return
    registry = exposure.load()
    show({t: exposure.classify(t, registry) for t in args.tasks} if args.tasks else
         {'tasks': len(registry['tasks']), 'definitions': registry['definitions']})


def cmd_crosscheck(args):
    from . import crosscheck
    show(crosscheck.run(args.batches, study=args.study and Path(args.study), shard=args.shard, out=args.out,
                        limit=args.limit, image=args.image, vendor=args.vendor))


def cmd_metrics(args):
    report, rows = metrics.analyze(args.batches, args.manifests, preliminary=args.preliminary, ledger=args.ledger,
                                   study=args.study and Path(args.study), ks=args.k,
                                   low_coverage_threshold=args.low_coverage_threshold)
    metrics.write(report, rows, args.out)
    print(metrics.markdown(report))


def main(argv=None):
    parser = argparse.ArgumentParser(prog='evaluation', description=__doc__.splitlines()[0])
    parser.add_argument('--study', help='study root (default: CSC2108_STUDY_ROOT)')
    parser.add_argument('--backend', default='auto', choices=['auto', 'windows', 'portable'],
                        help='passed to guided_agent (its host adapter)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('select', help='deterministic, outcome-blind benchmark selection into a judge manifest')
    p.add_argument('--out', required=True)
    p.add_argument('--name', default='custom')
    p.add_argument('--counts', nargs='+', metavar='DIFFICULTY=N', help='per difficulty, e.g. easy=20 medium=20 hard=20')
    p.add_argument('--per-difficulty', type=int, help='the same count for easy, medium and hard')
    p.add_argument('--total', type=int, help='total, split evenly over the three difficulties')
    p.add_argument('--tasks', nargs='+', help='specific task IDs (count toward their difficulty)')
    p.add_argument('--base', help='keep this manifest\'s eligible tasks and replace the others (same difficulty/series)')
    p.add_argument('--seed', type=int, default=2108, help='selection seed for the sha256 order')
    p.add_argument('--min-hidden-tests', type=int, default=40)
    p.add_argument('--exclude-previously-used', action='store_true',
                   help='drop tasks with any recorded historical exposure (default: allowed, and recorded)')
    p.add_argument('--prefer-unexposed', action='store_true',
                   help='fill and replace with tasks without recorded exposure first (exposed tasks stay eligible)')
    p.add_argument('--reserve', nargs='+', help='manifests whose tasks are never selected (default: pilot.json)')
    p.add_argument('--no-reserve', action='store_true')
    p.add_argument('--shard', help='a local copy of the pinned test6.jsonl')
    p.add_argument('--dry-run', action='store_true', help='print the selection, write nothing')
    p = sub.add_parser('plan')
    p.add_argument('--batch', required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--seeds', type=int, nargs='+')
    group.add_argument('--repetitions', type=int, help='seeds --first-seed, --first-seed + 1, ...')
    p.add_argument('--first-seed', type=int, default=2108)
    p.add_argument('--out', required=True)
    p.add_argument('--manifest', default=str(FINAL))
    p.add_argument('--tasks', nargs='+', help='subset of the manifest (default: all of it)')
    p.add_argument('--per-difficulty', type=int, help='first N tasks of each difficulty (smoke batches)')
    p.add_argument('--conditions', nargs='+', default=list(planlib.CONDITIONS))
    p.add_argument('--order', default='balanced', choices=['balanced', 'fixed'],
                   help='condition order within each (task, seed) block (balanced: Williams design)')
    p.add_argument('--plan-label', default='final-plans')
    p.add_argument('--contract-label', default='final-contracts')
    p.add_argument('--b-provider', default='api')
    p.add_argument('--b-max-requests', type=int, default=28)
    p.add_argument('--e-provider', default='api')
    p.add_argument('--outer-timeout', type=int, default=1000)
    p.add_argument('--cohort')
    p = sub.add_parser('tasks')
    p.add_argument('plan')
    p.add_argument('--shard', help='a local copy of the pinned test6.jsonl (default: judge/.cache, else download)')
    p = sub.add_parser('judge')
    p.add_argument('--rebuild', action='store_true', help='rebuild the image even if it exists')
    p.add_argument('--down', action='store_true', help="stop this study's judge containers")
    p = sub.add_parser('guidance')
    p.add_argument('plan')
    p.add_argument('--yes', action='store_true', help='make the paid authoring requests')
    p = sub.add_parser('budget', help='paid-request estimate; optionally create the study ledger with ceilings')
    p.add_argument('plan')
    p.add_argument('--ledger', help='default: CSC2108_API_LEDGER or <study>/api-ledger.json')
    p.add_argument('--init-ledger', action='store_true')
    p.add_argument('--max-requests', type=int)
    p.add_argument('--max-usd', type=float)
    p = sub.add_parser('ready', help='every readiness check, without running anything')
    p.add_argument('plan')
    p.add_argument('--offline', action='store_true', help='skip Ollama and Docker checks')
    p = sub.add_parser('run')
    p.add_argument('plan')
    p = sub.add_parser('status')
    p.add_argument('plan')
    p.add_argument('--limit', type=int, default=20)
    p = sub.add_parser('score')
    p.add_argument('plan')
    p.add_argument('--no-measure', action='store_true')
    p.add_argument('--allow-incomplete', action='store_true', help='score a batch that is still running (preliminary)')
    p.add_argument('--rescore-stale', action='store_true', help='move stale verdicts to eval/stale/ and rescore them')
    p = sub.add_parser('exclude', help='document an intentional exclusion of one (task, seed) block')
    p.add_argument('plan')
    p.add_argument('--task', required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--reason', required=True)
    p.add_argument('--by')
    p = sub.add_parser('freeze')
    p.add_argument('plan')
    p.add_argument('--out')
    p = sub.add_parser('check')
    p.add_argument('freeze')
    p.add_argument('--plan', help='also check the freeze belongs to this plan')
    p = sub.add_parser('exposure', help='show (or rebuild) the historical exposure registry')
    p.add_argument('tasks', nargs='*')
    p.add_argument('--build', action='store_true')
    p.add_argument('--study-roots', nargs='+', help='study roots whose run directory names count as exposure')
    p = sub.add_parser('crosscheck', help='re-judge saved submissions with the official LiveCodeBench evaluator')
    p.add_argument('batches', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--limit', type=int, default=40)
    p.add_argument('--shard')
    p.add_argument('--image', default='csc2108-lcb-judge:v2')
    p.add_argument('--vendor', help='LiveCodeBench checkout at the pinned evaluator revision')
    p = sub.add_parser('metrics')
    p.add_argument('batches', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--manifests', nargs='+', default=[str(m) for m in MANIFESTS])
    p.add_argument('--preliminary', action='store_true',
                   help='report incomplete data, clearly labelled PRELIMINARY (unscored runs are excluded, not failed)')
    p.add_argument('--ledger', help='API ledger for the study-expenditure section (default: <study>/api-ledger.json)')
    p.add_argument('--k', type=int, nargs='+', help='pass@k values (default: 1..repetitions)')
    p.add_argument('--low-coverage-threshold', type=int, default=40)
    args = parser.parse_args(argv)
    globals()['cmd_' + args.command](args)


if __name__ == '__main__':
    sys.exit(main())
