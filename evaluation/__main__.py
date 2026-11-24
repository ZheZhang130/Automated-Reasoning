"""evaluation command line: owns the tasks, the judge, the schedule, hidden scoring and the metrics.

  python -m evaluation plan     --batch final-main --seeds 2108 2109 2110 --out PLAN.json
  python -m evaluation tasks    PLAN.json            # build/verify the plan's tasks (judge suites + agent bundles)
  python -m evaluation judge                         # build the judge image, start judge-public, selftest
  python -m evaluation guidance PLAN.json [--yes]    # author missing C/D guidance (paid), then freeze it
  python -m evaluation run      PLAN.json            # preflight, then the agent: guided_agent batch
  python -m evaluation score    PLAN.json            # hidden scoring after ALL attempts, then guided_agent measure
  python -m evaluation metrics  BATCH_DIR [BATCH_DIR ...] --out REPORT_DIR

  python -m evaluation freeze | check                # the guidance freeze on its own (guidance does both)

The study root is CSC2108_STUDY_ROOT or --study (before the command); every step reads the same plan.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from . import metrics, plan as planlib

REPO = Path(__file__).resolve().parents[1]
MANIFESTS = [REPO / 'judge/manifests/main.json', REPO / 'judge/manifests/pilot.json']


def study_root(args):
    study = args.study or os.environ.get('CSC2108_STUDY_ROOT')
    if not study:
        raise SystemExit('set CSC2108_STUDY_ROOT or pass --study')
    return Path(study).resolve()


def show(value):
    print(json.dumps(value, indent=1, ensure_ascii=False))


def cmd_plan(args):
    study = study_root(args)
    tasks = planlib.manifest_tasks(args.manifest, args.tasks, args.per_difficulty)
    plan = planlib.build_plan(batch=args.batch, task_ids=tasks, seeds=args.seeds, study=study,
                              conditions=args.conditions, plan_label=args.plan_label,
                              contract_label=args.contract_label, b_max_requests=args.b_max_requests,
                              e_provider=args.e_provider, b_provider=args.b_provider,
                              outer_timeout=args.outer_timeout, cohort=args.cohort)
    planlib.write_json(args.out, plan)
    show({'plan': str(args.out), 'tasks': len(tasks), 'seeds': args.seeds, 'attempts': len(plan['attempts']),
          'guidance_artifacts': len(planlib.guidance_artifacts(plan))})


def cmd_tasks(args):
    from . import pipeline, tasks
    plan = planlib.read_json(args.plan)
    result = tasks.prepare(study_root(args), pipeline.plan_tasks(plan), shard=args.shard)
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


def cmd_run(args):
    from . import pipeline
    raise SystemExit(pipeline.run(args.plan, study_root(args), backend=args.backend))


def cmd_score(args):
    from . import pipeline
    show(pipeline.score(args.plan, study_root(args), backend=args.backend, measure=not args.no_measure))


def cmd_freeze(args):
    plan = planlib.read_json(args.plan)
    out = Path(args.out or Path(args.plan).with_suffix('.freeze.json'))
    record = planlib.freeze(plan, out)
    show({'freeze': str(out), 'artifacts': len(record['artifacts'])})


def cmd_check(args):
    problems = planlib.check(args.freeze)
    show({'unchanged': not problems, 'problems': problems})
    raise SystemExit(1 if problems else 0)


def cmd_metrics(args):
    report, rows = metrics.analyze(args.batches, args.manifests)
    metrics.write(report, rows, args.out)
    print(metrics.markdown(report))


def main(argv=None):
    parser = argparse.ArgumentParser(prog='evaluation', description=__doc__.splitlines()[0])
    parser.add_argument('--study', help='study root (default: CSC2108_STUDY_ROOT)')
    parser.add_argument('--backend', default='auto', choices=['auto', 'windows', 'portable'],
                        help='passed to guided_agent (its host adapter)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--batch', required=True)
    p.add_argument('--seeds', type=int, nargs='+', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--manifest', default=str(MANIFESTS[0]))
    p.add_argument('--tasks', nargs='+', help='subset of the manifest (default: all of it)')
    p.add_argument('--per-difficulty', type=int, help='first N tasks of each difficulty (smoke batches)')
    p.add_argument('--conditions', nargs='+', default=list(planlib.CONDITIONS))
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
    p = sub.add_parser('run')
    p.add_argument('plan')
    p = sub.add_parser('score')
    p.add_argument('plan')
    p.add_argument('--no-measure', action='store_true')
    p = sub.add_parser('freeze')
    p.add_argument('plan')
    p.add_argument('--out')
    p = sub.add_parser('check')
    p.add_argument('freeze')
    p = sub.add_parser('metrics')
    p.add_argument('batches', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--manifests', nargs='+', default=[str(m) for m in MANIFESTS])
    args = parser.parse_args(argv)
    globals()['cmd_' + args.command](args)


if __name__ == '__main__':
    sys.exit(main())
