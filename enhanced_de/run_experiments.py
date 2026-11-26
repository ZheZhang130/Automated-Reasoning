"""Unified resumable experiment runner & batch summarizer for enhanced_de Phases 1-3.

All GPU runs execute strictly sequentially via `runner_v2.run_batch_v2` (which acquires
`local_agent.platform_support.model_lock`). Hidden evaluation runs as an explicit
separate step AFTER all attempts finish.

Providers (`codex` isolated replay vs `api` direct OpenAI API) are ALWAYS placed in
distinct batch directories and tagged explicitly in every spec and summary record.
"""

import argparse
import csv
import json
from pathlib import Path

from guided_agent.common import REPO, read_json, utc_now, write_json

from . import runner_v2


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
DEV_COHORTS = REPO / 'enhanced_de' / 'manifests' / 'dev_cohorts.json'
TEST5_MANIFEST = REPO / 'enhanced_de' / 'manifests' / 'test5_val16.json'
FROZEN_PLANS_DIR = REPO / 'results' / 'final-main' / 'guidance' / 'final-plans'
FROZEN_RUNS_CSV = REPO / 'results' / 'final-main' / 'report' / 'runs.csv'


def load_historical_final_main():
    """Map (task_id, condition, seed) -> row dict from results/final-main/report/runs.csv."""
    out = {}
    if not FROZEN_RUNS_CSV.exists():
        return out
    with FROZEN_RUNS_CSV.open('r', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            key = (row['task_id'], row['condition'], int(row['seed']))
            out[key] = row
    return out


def _provider_spec(provider, study, *, model='gpt-6.2-sol', effort='medium', ledger=None, purpose='e2-validation'):
    if provider == 'codex':
        return {'provider': 'codex', 'model': model, 'effort': effort}
    if provider == 'api':
        return {
            'provider': 'api',
            'model': model,
            'effort': effort,
            'purpose': purpose,
            'ledger_path': str(ledger or (Path(study) / 'api-ledger.json')),
        }
    if provider == 'none':
        return {'provider': 'fixed', 'text': ''}
    raise ValueError(f'Unknown provider: {provider!r}')


def make_spec(
    *,
    batch_dir,
    study,
    cohort,
    batch_name,
    task_id,
    seed,
    arm,
    condition,
    d2=None,
    e2=None,
    provider_label='local-only',
):
    short_task = task_id.replace('lcb-atcoder-', '')
    run_id = f'{batch_name}-{short_task}-{arm}-s{seed}'
    spec = {
        'run_id': run_id,
        'task_id': task_id,
        'seed': int(seed),
        'arm': arm,
        'condition': condition,
        'provider_label': provider_label,
        'cohort': cohort,
        'batch': batch_name,
        'study': str(study),
        'output': str(Path(batch_dir) / run_id),
    }
    if d2 is not None:
        spec['d2'] = d2
    if e2 is not None:
        spec['e2'] = e2
    return spec


def build_phase1c_specs(study, *, arms=('E2-stall-neutral', 'E2-stall-clate', 'E2-stall-diag'),
                        provider='codex', limit=None):
    """Phase 1C: E2-Stall dev cohort (12 stratified truncation pairs)."""
    cohorts = read_json(DEV_COHORTS)
    pairs = cohorts['phase1c_e2_stall_truncation_pairs']
    if limit:
        pairs = pairs[:limit]
    batch_name = f'phase1c-e2-stall-{provider}'
    batch_dir = Path(study) / 'runs' / batch_name
    specs = []
    for arm in arms:
        for p in pairs:
            tid, seed = p['task_id'], int(p['seed'])
            if arm == 'E2-stall-neutral':
                e2 = {'kind': 'stall', 'mode': 'neutral', 'provider_spec': {'provider': 'fixed', 'text': ''}}
                prov_lbl = 'local-only'
            elif arm == 'E2-stall-clate':
                plan_path = FROZEN_PLANS_DIR / f'{tid}.plan-v1.api.json'
                if not plan_path.exists():
                    raise FileNotFoundError(f'Missing frozen C plan for {tid}: {plan_path}')
                e2 = {
                    'kind': 'stall',
                    'mode': 'c-late',
                    'plan_path': str(plan_path),
                    'provider_spec': {'provider': 'fixed', 'text': ''},
                }
                prov_lbl = 'frozen-c-plan-api'
            elif arm == 'E2-stall-diag':
                e2 = {
                    'kind': 'stall',
                    'mode': 'stall-diag',
                    'provider_spec': _provider_spec(provider, study, purpose='phase1c-stall'),
                }
                prov_lbl = f'{provider}-replay' if provider == 'codex' else 'openai-api'
            else:
                raise ValueError(f'Unknown Phase 1C arm: {arm}')
            specs.append(make_spec(
                batch_dir=batch_dir, study=study, cohort='dev-phase1c-stall',
                batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                e2=e2, provider_label=prov_lbl,
            ))
    return batch_dir, specs


def build_phase1a_specs(study, *, arms=('D2-inputs-stress', 'D2-oracle', 'E2-review'),
                        provider='codex', include_safety=True, limit=None):
    """Phase 1A: D2 + E2-Review dev cohort (10 PPHF pairs + 6 safety non-regression pairs)."""
    cohorts = read_json(DEV_COHORTS)
    pairs = list(cohorts['phase1a_d2_and_review_pphf_pairs'])
    if include_safety:
        pairs += list(cohorts['phase1a_safety_nonregression_pairs'])
    if limit:
        pairs = pairs[:limit]
    batch_name = f'phase1a-d2-review-{provider}'
    batch_dir = Path(study) / 'runs' / batch_name
    bank_dir = Path(study) / 'd2_banks' / provider
    prov_lbl = f'{provider}-replay' if provider == 'codex' else 'openai-api'
    specs = []
    for arm in arms:
        for p in pairs:
            tid, seed = p['task_id'], int(p['seed'])
            if arm.startswith('D2-'):
                mode = arm[len('D2-'):]
                bank_path = bank_dir / f'{tid}.bank.json'
                if not bank_path.exists():
                    print(f'  [WARN] Skipping {tid} for {arm}: missing compiled bank {bank_path}', flush=True)
                    continue
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='dev-phase1a-d2-review',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='D2',
                    d2={'bank_path': str(bank_path), 'mode': mode, 'trigger': 'public_pass_only'},
                    provider_label=prov_lbl,
                ))
            elif arm == 'E2-review':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='dev-phase1a-d2-review',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={'kind': 'review', 'provider_spec': _provider_spec(provider, study)},
                    provider_label=prov_lbl,
                ))
            else:
                raise ValueError(f'Unknown Phase 1A arm: {arm}')
    return batch_dir, specs


def build_phase1b_specs(study, *, provider='codex', limit=None):
    """Phase 1B: E2-Strict dev cohort (12 E-v1 triggered-failure pairs)."""
    cohorts = read_json(DEV_COHORTS)
    pairs = list(cohorts['phase1b_e2_strict_triggered_failure_pairs'])
    if limit:
        pairs = pairs[:limit]
    batch_name = f'phase1b-e2-strict-{provider}'
    batch_dir = Path(study) / 'runs' / batch_name
    prov_lbl = f'{provider}-replay' if provider == 'codex' else 'openai-api'
    specs = []
    for p in pairs:
        tid, seed = p['task_id'], int(p['seed'])
        specs.append(make_spec(
            batch_dir=batch_dir, study=study, cohort='dev-phase1b-e2-strict',
            batch_name=batch_name, task_id=tid, seed=seed, arm='E2-strict', condition='E2',
            e2={
                'kind': 'strict',
                'provider_spec': _provider_spec(provider, study),
                'enable_advisory_vchecks': True,
            },
            provider_label=prov_lbl,
        ))
    return batch_dir, specs


def build_phase2_specs(
    study,
    *,
    arms=('A', 'D2-inputs-stress', 'D2-oracle', 'E2-strict', 'E2-stall-neutral', 'E2-stall-full', 'E2-review'),
    provider='codex',
    seed=2108,
    tasks_filter=None,
):
    """Phase 2: Outcome-blind test5_val16 validation cohort (16 tasks x seed 2108)."""
    manifest = read_json(TEST5_MANIFEST)
    task_ids = [t['task_id'] for t in manifest['tasks']]
    if tasks_filter:
        allow = set(tasks_filter)
        task_ids = [t for t in task_ids if t in allow]
    batch_name = f'phase2-test5-{provider}'
    batch_dir = Path(study) / 'runs' / batch_name
    bank_dir = Path(study) / 'd2_banks' / provider
    prov_lbl = f'{provider}-replay' if provider == 'codex' else 'openai-api'
    specs = []
    for arm in arms:
        for tid in task_ids:
            if arm == 'A':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm='A', condition='A',
                    provider_label='local-only',
                ))
            elif arm.startswith('D2-'):
                mode = arm[len('D2-'):]
                bank_path = bank_dir / f'{tid}.bank.json'
                if not bank_path.exists():
                    print(f'  [WARN] Skipping {tid} for {arm}: missing compiled bank {bank_path}', flush=True)
                    continue
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='D2',
                    d2={'bank_path': str(bank_path), 'mode': mode, 'trigger': 'public_pass_only'},
                    provider_label=prov_lbl,
                ))
            elif arm == 'E2-strict':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={
                        'kind': 'strict',
                        'provider_spec': _provider_spec(provider, study),
                        'enable_advisory_vchecks': True,
                    },
                    provider_label=prov_lbl,
                ))
            elif arm == 'E2-stall-neutral':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={'kind': 'stall', 'mode': 'neutral', 'provider_spec': {'provider': 'fixed', 'text': ''}},
                    provider_label='local-only',
                ))
            elif arm == 'E2-stall-diag':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={
                        'kind': 'stall',
                        'mode': 'stall-diag',
                        'enable_public_fallback': False,
                        'provider_spec': _provider_spec(provider, study),
                    },
                    provider_label=prov_lbl,
                ))
            elif arm == 'E2-stall-full':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={
                        'kind': 'stall',
                        'mode': 'stall-diag',
                        'enable_public_fallback': True,
                        'provider_spec': _provider_spec(provider, study),
                    },
                    provider_label=prov_lbl,
                ))
            elif arm == 'E2-review':
                specs.append(make_spec(
                    batch_dir=batch_dir, study=study, cohort='val-test5-16',
                    batch_name=batch_name, task_id=tid, seed=seed, arm=arm, condition='E2',
                    e2={'kind': 'review', 'provider_spec': _provider_spec(provider, study)},
                    provider_label=prov_lbl,
                ))
            else:
                raise ValueError(f'Unknown Phase 2 arm: {arm}')
    return batch_dir, specs


def summarize_batch(batch_dir, *, compare_final_main=False):
    """Aggregate result.json + eval/*.json for a batch directory into a structured summary."""
    batch_dir = Path(batch_dir)
    eval_dir = batch_dir / 'eval'
    hist = load_historical_final_main() if compare_final_main else {}

    rows = []
    for res_path in sorted(batch_dir.glob('*/result.json')):
        if '.incomplete-' in res_path.parent.name:
            continue
        rec = read_json(res_path)
        run_id = rec['run_id']
        ev_path = eval_dir / f'{run_id}.json'
        ev = read_json(ev_path) if ev_path.exists() else {}
        g = rec.get('guidance') or {}
        d2g = rec.get('d2_gate') or {}
        e2d = rec.get('e2_diagnosis') or {}
        row = {
            'run_id': run_id,
            'task_id': rec['task_id'],
            'arm': rec.get('arm'),
            'condition': rec.get('condition'),
            'seed': rec.get('seed'),
            'exit_status': rec.get('exit_status'),
            'n_actions': rec.get('n_actions'),
            'n_repairs': rec.get('n_repairs'),
            'wall_seconds': rec.get('wall_seconds'),
            'local_coding_seconds': rec.get('local_coding_seconds'),
            'frontier_wait_seconds': rec.get('frontier_wait_seconds'),
            'triggered': bool(g.get('triggered')),
            'delivered': bool(g.get('delivered')),
            'guidance_error': g.get('error'),
            'd2_checks': d2g.get('checks'),
            'd2_failed': d2g.get('failed'),
            'e2_trigger_kind': e2d.get('trigger_kind'),
            'e2_repair_mode': e2d.get('repair_mode_declared') or e2d.get('repair_mode'),
            'e2_verdict': e2d.get('review_verdict'),
            'e2_review_outcome': e2d.get('review_outcome'),
            'e2_vcheck_alignment': e2d.get('vcheck_alignment'),
            'hidden_status': ev.get('status'),
            'hidden_passed': ev.get('passed'),
            'hidden_total': ev.get('total'),
            'verdict_counts': ev.get('verdict_counts'),
        }
        if compare_final_main:
            for cond in ('A', 'C', 'D', 'E'):
                h = hist.get((rec['task_id'], cond, int(rec['seed'])))
                if h:
                    row[f'hist_{cond}_pass'] = h.get('hidden_status') == 'pass'
                    row[f'hist_{cond}_exit'] = h.get('exit_status')
        rows.append(row)

    by_arm = {}
    for row in rows:
        arm = row['arm'] or 'unknown'
        bucket = by_arm.setdefault(arm, {
            'n': 0, 'evaluated': 0, 'passed': 0, 'triggered': 0, 'delivered': 0,
            'exit_counts': {}, 'hist_A_passed': 0, 'wins_vs_A': 0, 'losses_vs_A': 0,
            'wall_seconds_total': 0.0,
        })
        bucket['n'] += 1
        ex = row['exit_status'] or 'unknown'
        bucket['exit_counts'][ex] = bucket['exit_counts'].get(ex, 0) + 1
        if row['triggered']:
            bucket['triggered'] += 1
        if row['delivered']:
            bucket['delivered'] += 1
        if row['wall_seconds'] is not None:
            bucket['wall_seconds_total'] += float(row['wall_seconds'])
        if row['hidden_status'] is not None:
            bucket['evaluated'] += 1
            is_pass = row['hidden_status'] == 'pass'
            if is_pass:
                bucket['passed'] += 1
            if compare_final_main and 'hist_A_pass' in row:
                ha = bool(row['hist_A_pass'])
                if ha:
                    bucket['hist_A_passed'] += 1
                if is_pass and not ha:
                    bucket['wins_vs_A'] += 1
                elif not is_pass and ha:
                    bucket['losses_vs_A'] += 1

    for arm, b in by_arm.items():
        b['pass_rate'] = round(b['passed'] / b['evaluated'], 4) if b['evaluated'] else None
        b['mean_wall_seconds'] = round(b['wall_seconds_total'] / b['n'], 1) if b['n'] else None

    return {
        'schema': 'csc2108-batch-summary-v1',
        'batch_dir': str(batch_dir),
        'created_utc': utc_now(),
        'by_arm': by_arm,
        'runs': rows,
    }


def main():
    p = argparse.ArgumentParser(description='Run and summarize enhanced_de live GPU experiments')
    p.add_argument('--study', default=str(DEFAULT_STUDY))
    sub = p.add_subparsers(dest='cmd', required=True)

    p1c = sub.add_parser('phase1c')
    p1c.add_argument('--arms', default='E2-stall-neutral,E2-stall-clate,E2-stall-diag')
    p1c.add_argument('--provider', default='codex', choices=['codex', 'api'])
    p1c.add_argument('--limit', type=int, default=None)
    p1c.add_argument('--skip-eval', action='store_true')

    p1a = sub.add_parser('phase1a')
    p1a.add_argument('--arms', default='D2-inputs-stress,D2-oracle,E2-review')
    p1a.add_argument('--provider', default='codex', choices=['codex', 'api'])
    p1a.add_argument('--no-safety', action='store_true')
    p1a.add_argument('--limit', type=int, default=None)
    p1a.add_argument('--skip-eval', action='store_true')

    p1b = sub.add_parser('phase1b')
    p1b.add_argument('--provider', default='codex', choices=['codex', 'api'])
    p1b.add_argument('--limit', type=int, default=None)
    p1b.add_argument('--skip-eval', action='store_true')

    p2 = sub.add_parser('phase2')
    p2.add_argument('--arms', default='A,D2-inputs-stress,D2-oracle,E2-strict,E2-stall-neutral,E2-stall-full')
    p2.add_argument('--provider', default='codex', choices=['codex', 'api'])
    p2.add_argument('--seed', type=int, default=2108)
    p2.add_argument('--tasks', default=None)
    p2.add_argument('--skip-eval', action='store_true')

    ps = sub.add_parser('summarize')
    ps.add_argument('batch_dir', type=Path)
    ps.add_argument('--compare-final-main', action='store_true')

    args = p.parse_args()
    study = Path(args.study)

    if args.cmd == 'summarize':
        summary = summarize_batch(args.batch_dir, compare_final_main=args.compare_final_main)
        out = args.batch_dir / 'summary.json'
        write_json(out, summary)
        print(json.dumps(summary['by_arm'], indent=2), flush=True)
        return

    compare_fm = False
    if args.cmd == 'phase1c':
        arms = [a.strip() for a in args.arms.split(',') if a.strip()]
        batch_dir, specs = build_phase1c_specs(study, arms=arms, provider=args.provider, limit=args.limit)
        compare_fm = True
    elif args.cmd == 'phase1a':
        arms = [a.strip() for a in args.arms.split(',') if a.strip()]
        batch_dir, specs = build_phase1a_specs(
            study, arms=arms, provider=args.provider, include_safety=not args.no_safety, limit=args.limit
        )
        compare_fm = True
    elif args.cmd == 'phase1b':
        batch_dir, specs = build_phase1b_specs(study, provider=args.provider, limit=args.limit)
        compare_fm = True
    elif args.cmd == 'phase2':
        arms = [a.strip() for a in args.arms.split(',') if a.strip()]
        tfilt = [t.strip() for t in args.tasks.split(',')] if args.tasks else None
        batch_dir, specs = build_phase2_specs(
            study, arms=arms, provider=args.provider, seed=args.seed, tasks_filter=tfilt
        )
    else:
        raise ValueError(args.cmd)

    print(f'=== {args.cmd}: {len(specs)} runs -> {batch_dir} ===', flush=True)
    runner_v2.run_batch_v2(batch_dir, specs)
    if not args.skip_eval:
        print(f'--- Hidden evaluation for {batch_dir} ---', flush=True)
        runner_v2.evaluate_batch_v2(batch_dir, study)
    summary = summarize_batch(batch_dir, compare_final_main=compare_fm)
    write_json(batch_dir / 'summary.json', summary)
    print(f'=== Summary ({batch_dir / "summary.json"}) ===', flush=True)
    print(json.dumps(summary['by_arm'], indent=2), flush=True)


if __name__ == '__main__':
    main()
