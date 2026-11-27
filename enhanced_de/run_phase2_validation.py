"""Phase 2: outcome-blind validation on test5_val16 with trigger-partitioned runs.

Why trigger partitioning is valid here
--------------------------------------
Every D2 / E2 / E-v1 arm is *dormant* until its trigger fires: no prompt change, no extra observation, no change
to format-error counting.  Under the frozen sampler (fixed seed, T 0.2) the local agent is deterministic on this
host, so an arm's trajectory equals A's trajectory up to its trigger.  Development evidence: every untriggered or
silent D2/E2 run of phases 1A-1C produced the byte-identical submission of the official A run at the same
(task, seed) (`reports/determinism_check.json`, written by ``determinism``).  Therefore:

* A is run on all tasks first.
* Each arm is run live only on the tasks whose A trajectory reaches that arm's trigger state.
* On every other task the arm's outcome *is* A's outcome.  Composed tables mark those cells ``from_A``.
* A live arm run that ends up not triggering is kept and checked against A's submission hash (a determinism
  check, reported, never silently replaced).

Trigger states read from A's own records (``result.json`` usage + ``attempts.jsonl``):

* ``stall``: two consecutive length-stopped responses before any public test (E2-stall arms).
* ``fail``: at least one public test whose status is not ``pass`` (E-v1 / E2-strict, first public failure).
* ``pass``: at least one public pass (D2 gates, E2-review).

C (plan-v1) and E-v1 (diagnosis-v1) run through the **official** ``guided_agent`` runner (unchanged frozen code)
with isolated Codex replay as the frontier; everything else runs through ``enhanced_de.runner_v2``.

Providers are never pooled: this module only builds ``codex``-replay batches.  Paid API validation is
``run_phase3_api``.
"""

import argparse
import json
from pathlib import Path

from guided_agent.common import read_json, utc_now, write_json

from . import run_experiments as rx
from . import runner_v2

STUDY = rx.DEFAULT_STUDY
BATCH = 'phase2-test5-codex'
OFFICIAL_BATCH = 'phase2-test5-official-codex'
PLAN_LABEL = 'test5-plans-codex'

STALL_ARMS = ('E2-stall-diag', 'E2-stall-neutral', 'E2-stall-clate')
FAIL_ARMS = ('E2-strict',)                       # E-v1 runs in the official batch
PASS_ARMS = ('D2-oracle', 'D2-property', 'D2-inputs-stress', 'E2-review')
ARM_TRIGGER = {**{a: 'stall' for a in STALL_ARMS}, **{a: 'fail' for a in FAIL_ARMS},
               **{a: 'pass' for a in PASS_ARMS}, 'E1': 'fail'}


def task_ids():
    return [t['task_id'] for t in read_json(rx.TEST5_MANIFEST)['tasks']]


def batch_dir(study, name=BATCH):
    return Path(study) / 'runs' / name


def a_runs(study, seed):
    out = {}
    for res in sorted(batch_dir(study).glob('*/result.json')):
        if '.incomplete-' in res.parent.name:
            continue
        rec = read_json(res)
        if rec.get('arm') == 'A' and int(rec.get('seed')) == seed:
            out[rec['task_id']] = (res.parent, rec)
    return out


def trigger_states(run_dir, rec):
    coding = (rec.get('usage') or {}).get('coding') or []
    attempts = []
    att_path = Path(run_dir) / 'attempts.jsonl'
    if att_path.exists():
        attempts = [json.loads(line) for line in att_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    statuses = [((a.get('result') or {}).get('status')) for a in attempts if a.get('delivered', True)]
    reasons = [c.get('done_reason') for c in coding]
    first_test_call = None
    if attempts:
        first_test_call = min(int(a.get('action') or 0) for a in attempts)
    # Inclusive on purpose: any two consecutive length stops make the task a stall candidate.  The live arm
    # records whether its exact trigger (2nd consecutive format error, length stop, no candidate) really fired;
    # a candidate that does not fire costs compute but reproduces A (checked in ``compose``).
    stall = any(reasons[i - 1] == 'length' and reasons[i] == 'length' for i in range(1, len(reasons)))
    return {
        'stall': stall,
        'fail': any(s not in (None, 'pass') for s in statuses),
        'pass': any(s == 'pass' for s in statuses),
        'public_statuses': statuses,
        'done_reasons': reasons,
        'first_test_action': first_test_call,
        'exit_status': rec.get('exit_status'),
        'submission_sha256': rec.get('submission_sha256'),
    }


def cmd_triggers(study, seed):
    runs = a_runs(study, seed)
    missing = [t for t in task_ids() if t not in runs]
    if missing:
        raise SystemExit(f'A is missing for {len(missing)} tasks at seed {seed}: {missing}')
    states = {t: trigger_states(*runs[t]) for t in task_ids()}
    doc = {'schema': 'csc2108-enhanced-de-phase2-triggers-v1', 'created_utc': utc_now(), 'seed': seed,
           'batch': str(batch_dir(study)), 'states': states,
           'counts': {k: sum(1 for s in states.values() if s[k]) for k in ('stall', 'fail', 'pass')}}
    out = Path(study) / 'reports' / f'phase2_trigger_states_s{seed}.json'
    write_json(out, doc)
    print(json.dumps(doc['counts']), str(out))
    return doc


def build_triggered_specs(study, seed, arms):
    doc = read_json(Path(study) / 'reports' / f'phase2_trigger_states_s{seed}.json')
    specs = []
    for arm in arms:
        kind = ARM_TRIGGER[arm]
        tasks = [t for t, s in doc['states'].items() if s[kind]]
        if not tasks:
            continue
        if arm == 'E2-stall-clate':
            _, base = rx.build_phase2_specs(study, arms=('E2-stall-neutral',), seed=seed, tasks_filter=tasks)
            for spec in base:
                tid = spec['task_id']
                plan = Path(study) / 'guidance' / PLAN_LABEL / f'{tid}.plan-v1.codex.json'
                if not plan.exists():
                    raise FileNotFoundError(plan)
                spec['arm'] = 'E2-stall-clate'
                spec['run_id'] = spec['run_id'].replace('E2-stall-neutral', 'E2-stall-clate')
                spec['output'] = spec['output'].replace('E2-stall-neutral', 'E2-stall-clate')
                spec['e2'] = {'kind': 'stall', 'mode': 'c-late', 'plan_path': str(plan),
                              'protocol': spec['e2'].get('protocol', 'v1'),
                              'provider_spec': {'provider': 'fixed', 'text': ''}}
                spec['provider_label'] = 'frozen-c-plan-codex'
                specs.append(spec)
        else:
            _, base = rx.build_phase2_specs(study, arms=(arm,), seed=seed, tasks_filter=tasks)
            specs.extend(base)
    return specs


def official_plan(study, seed, include_c=True, include_e1=True):
    doc = read_json(Path(study) / 'reports' / f'phase2_trigger_states_s{seed}.json')
    attempts = []
    if include_c:
        for tid in task_ids():
            plan = Path(study) / 'guidance' / PLAN_LABEL / f'{tid}.plan-v1.codex.json'
            if not plan.exists():
                raise FileNotFoundError(plan)
            attempts.append({'task_id': tid, 'condition': 'C', 'seed': seed, 'agent': 'frozen-v6',
                             'variant': f's{seed}', 'guidance': str(plan)})
    if include_e1:
        for tid, s in doc['states'].items():
            if s['fail']:
                attempts.append({'task_id': tid, 'condition': 'E', 'seed': seed, 'agent': 'frozen-v6',
                                 'variant': f's{seed}',
                                 'diagnosis': {'provider': 'codex', 'prompt_id': 'diagnosis-v1',
                                               'delivery': 'deliver-v1'}})
    plan = {'batch': f'{OFFICIAL_BATCH}-s{seed}', 'frozen': True, 'outer_timeout': 1000,
            'cohort': 'val-test5-16', 'attempts': attempts,
            'note': 'Official guided_agent runner; C uses isolated Codex plan-v1 artifacts; E (E-v1) runs only on '
                    'tasks whose A trajectory reaches a public failure (trigger partitioning).'}
    out = Path(study) / 'plans' / f'{OFFICIAL_BATCH}-s{seed}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, plan)
    print(out, len(attempts))
    return out


def _hidden(batch, run_id):
    ev = Path(batch) / 'eval' / f'{run_id}.json'
    return read_json(ev) if ev.exists() else None


def compose(study, seed):
    """Per-arm task outcomes with A filled in where the arm cannot trigger, plus determinism checks."""
    doc = read_json(Path(study) / 'reports' / f'phase2_trigger_states_s{seed}.json')
    tasks = task_ids()
    a = a_runs(study, seed)
    cells = {}

    def put(arm, tid, rec, run_dir, batch, source):
        ev = _hidden(batch, rec['run_id'])
        g = rec.get('guidance') or {}
        cells.setdefault(arm, {})[tid] = {
            'source': source, 'run_id': rec['run_id'], 'exit_status': rec.get('exit_status'),
            'hidden_status': (ev or {}).get('status'), 'hidden_passed': (ev or {}).get('passed'),
            'hidden_total': (ev or {}).get('total'), 'pass': (ev or {}).get('status') == 'pass' if ev else None,
            'triggered': bool(g.get('triggered')), 'delivered': bool(g.get('delivered')),
            'submission_sha256': rec.get('submission_sha256'),
            'same_submission_as_A': rec.get('submission_sha256') == a[tid][1].get('submission_sha256'),
            'wall_seconds': rec.get('wall_seconds'),
        }

    for tid, (rd, rec) in a.items():
        put('A', tid, rec, rd, batch_dir(study), 'live')
    for res in sorted(batch_dir(study).glob('*/result.json')):
        if '.incomplete-' in res.parent.name:
            continue
        rec = read_json(res)
        if rec.get('arm') in (None, 'A') or int(rec.get('seed')) != seed:
            continue
        put(rec['arm'], rec['task_id'], rec, res.parent, batch_dir(study), 'live')
    ob = batch_dir(study, f'{OFFICIAL_BATCH}-s{seed}')
    for res in sorted(ob.glob('*/result.json')) if ob.exists() else []:
        if '.incomplete-' in res.parent.name:
            continue
        rec = read_json(res)
        arm = {'C': 'C', 'E': 'E1'}.get(rec.get('condition'))
        if arm:
            put(arm, rec['task_id'], rec, res.parent, ob, 'live-official')
    # fill dormant cells from A
    for arm, kind in ARM_TRIGGER.items():
        for tid in tasks:
            if tid in cells.get(arm, {}):
                continue
            if not doc['states'][tid][kind]:
                cells.setdefault(arm, {})[tid] = dict(cells['A'][tid], source='from_A (trigger state not reached)')
            elif arm.startswith('D2-') and not (Path(study) / 'd2_banks' / 'codex' / f'{tid}.bank.json').exists():
                # D2 abstains when its statement-only bank failed compilation: the gate never exists, so A.
                cells.setdefault(arm, {})[tid] = dict(cells['A'][tid], source='from_A (D2 bank abstained)')
    # composed E2-stall-full: stall-diag where a stall occurs, otherwise strict at the first public failure
    full = {}
    for tid in tasks:
        st = doc['states'][tid]
        src = 'E2-stall-diag' if st['stall'] else ('E2-strict' if st['fail'] else 'A')
        cell = (cells.get(src) or {}).get(tid)
        if cell is not None:
            full[tid] = dict(cell, source=f"composed from {src}: {cell['source']}")
    cells['E2-stall-full (composed)'] = full
    # composed maximal-coverage single-intervention E2: first trigger reached among stall, public failure, public pass
    widest = {}
    for tid in tasks:
        st = doc['states'][tid]
        src = ('E2-stall-diag' if st['stall'] else 'E2-strict' if st['fail'] else 'E2-review' if st['pass'] else 'A')
        cell = (cells.get(src) or {}).get(tid)
        if cell is not None:
            widest[tid] = dict(cell, source=f"composed from {src}: {cell['source']}")
    cells['E2-adaptive (composed: stall > fail > review)'] = widest

    table = {}
    for arm, by_task in cells.items():
        done = [c for c in by_task.values() if c['pass'] is not None]
        table[arm] = {
            'tasks_covered': len(by_task), 'scored': len(done), 'passes': sum(1 for c in done if c['pass']),
            'live_runs': sum(1 for c in by_task.values() if c['source'].startswith('live')),
            'triggered_live': sum(1 for c in by_task.values() if c['source'].startswith('live') and c['triggered']),
            'delivered_live': sum(1 for c in by_task.values() if c['source'].startswith('live') and c['delivered']),
            'wins_vs_A': sum(1 for t, c in by_task.items() if c['pass'] and cells['A'][t]['pass'] is False),
            'losses_vs_A': sum(1 for t, c in by_task.items() if c['pass'] is False and cells['A'][t]['pass']),
            'untriggered_live_not_same_as_A': [t for t, c in by_task.items()
                                               if c['source'].startswith('live') and arm != 'A'
                                               and not c['triggered'] and not c['same_submission_as_A']],
        }
    out = {'schema': 'csc2108-enhanced-de-phase2-composed-v1', 'created_utc': utc_now(), 'seed': seed,
           'provider': 'codex-replay (never pooled with openai-api)', 'trigger_counts': doc['counts'],
           'table': table, 'cells': cells}
    path = Path(study) / 'reports' / f'phase2_composed_s{seed}.json'
    write_json(path, out)
    for arm, row in table.items():
        print(f"{arm:28s} {row['passes']:>2}/{row['scored']:<2} live={row['live_runs']:<2} "
              f"trig={row['triggered_live']:<2} deliv={row['delivered_live']:<2} "
              f"+{row['wins_vs_A']}/-{row['losses_vs_A']}  nondet={row['untriggered_live_not_same_as_A']}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--study', default=str(STUDY))
    p.add_argument('--seed', type=int, default=2108)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('run-a')
    sub.add_parser('triggers')
    r = sub.add_parser('run-arms')
    r.add_argument('--arms', default=','.join(STALL_ARMS + FAIL_ARMS + PASS_ARMS))
    r.add_argument('--skip-eval', action='store_true')
    o = sub.add_parser('official-plan')
    o.add_argument('--no-c', action='store_true')
    o.add_argument('--no-e1', action='store_true')
    sub.add_parser('evaluate')
    sub.add_parser('compose')
    args = p.parse_args()
    study = Path(args.study)
    if args.cmd == 'run-a':
        bdir, specs = rx.build_phase2_specs(study, arms=('A',), seed=args.seed)
        runner_v2.run_batch_v2(bdir, specs)
        runner_v2.evaluate_batch_v2(bdir, study)
    elif args.cmd == 'triggers':
        cmd_triggers(study, args.seed)
    elif args.cmd == 'run-arms':
        arms = [a.strip() for a in args.arms.split(',') if a.strip()]
        specs = build_triggered_specs(study, args.seed, arms)
        print(f'=== phase2 triggered arms: {len(specs)} runs ===', flush=True)
        runner_v2.run_batch_v2(batch_dir(study), specs)
        if not args.skip_eval:
            runner_v2.evaluate_batch_v2(batch_dir(study), study)
    elif args.cmd == 'official-plan':
        official_plan(study, args.seed, include_c=not args.no_c, include_e1=not args.no_e1)
    elif args.cmd == 'evaluate':
        runner_v2.evaluate_batch_v2(batch_dir(study), study)
    elif args.cmd == 'compose':
        compose(study, args.seed)


if __name__ == '__main__':
    main()
