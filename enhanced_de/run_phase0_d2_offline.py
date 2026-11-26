"""Phase 0 driver: Offline D2 Endres Mutant Benchmark across exposed final-main tasks.

Authors D2 verification bundles (strictly statement-only), compiles isolated Docker
verification banks, and scores all three ablations (inputs-stress, property, oracle)
against passing references (FRR) and public-pass hidden-fail mutants (kill rate).
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time

from guided_agent.common import REPO, read_json, utc_now, write_json

from . import d2_contract
from .runner_v2 import load_public_cases, load_statement


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
DEV_COHORTS = REPO / 'enhanced_de' / 'manifests' / 'dev_cohorts.json'
MUTANT_POOL = REPO / 'enhanced_de' / 'manifests' / 'mutant_pool_final_main.json'


def author_and_compile_task(
    task_id,
    *,
    study,
    provider='codex',
    model='gpt-6.2-sol',
    effort='medium',
    ledger_path=None,
    timeout=300,
    reattempt_errors=False,
):
    """Author a statement-only D2 bundle (if missing) and compile its Docker bank."""
    study = Path(study)
    bundle_dir = study / 'd2_bundles' / provider
    bank_dir = study / 'd2_banks' / provider
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bank_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = bundle_dir / f'{task_id}.bundle.json'
    err_path = bundle_dir / f'{task_id}.error.json'
    bank_path = bank_dir / f'{task_id}.bank.json'

    statement = load_statement(study, task_id)
    public_cases = load_public_cases(study, task_id)

    if not bundle_path.exists():
        if err_path.exists() and not reattempt_errors:
            return {'task_id': task_id, 'status': 'author_error_cached', 'error': read_json(err_path)}
        started = time.monotonic()
        try:
            bundle = d2_contract.author_d2_bundle(
                statement=statement,
                task_id=task_id,
                out_path=bundle_path,
                provider=provider,
                work_root=study / 'work' / f'd2-iso-{provider}',
                ledger_path=ledger_path,
                model=model,
                effort=effort,
                timeout=timeout,
            )
            if err_path.exists():
                err_path.unlink()
        except Exception as exc:
            err_rec = {
                'task_id': task_id,
                'provider': provider,
                'stage': 'author',
                'error_type': type(exc).__name__,
                'error': str(exc),
                'elapsed_seconds': round(time.monotonic() - started, 2),
                'utc': utc_now(),
            }
            write_json(err_path, err_rec)
            return {'task_id': task_id, 'status': 'author_error', 'error': err_rec}
    else:
        bundle = read_json(bundle_path)

    if not bank_path.exists():
        started = time.monotonic()
        try:
            bank = d2_contract.compile_d2_bank(bundle, public_cases)
            bank['provider'] = provider
            bank['compiled_utc'] = utc_now()
            bank['compile_seconds'] = round(time.monotonic() - started, 2)
            write_json(bank_path, bank)
        except Exception as exc:
            err_rec = {
                'task_id': task_id,
                'provider': provider,
                'stage': 'compile',
                'error_type': type(exc).__name__,
                'error': str(exc),
                'elapsed_seconds': round(time.monotonic() - started, 2),
                'utc': utc_now(),
            }
            write_json(bank_dir / f'{task_id}.compile_error.json', err_rec)
            return {'task_id': task_id, 'status': 'compile_error', 'error': err_rec}
    else:
        bank = read_json(bank_path)

    return {
        'task_id': task_id,
        'status': 'compiled',
        'bundle_path': str(bundle_path),
        'bank_path': str(bank_path),
        'validator_public_ok': bank['validator_public_ok'],
        'property_enabled': bank['property_enabled'],
        'oracle_enabled': bank['oracle_enabled'],
        'stress_enabled': bank['stress_enabled'],
        'compilation_stats': bank['compilation_stats'],
        'author_usage': bundle.get('usage'),
        'author_wall_seconds': bundle.get('wall_seconds') or bundle.get('latency_seconds'),
    }


def score_task_offline(task_id, task_entry, *, study, provider='codex', include_public_fail=False):
    """Score one compiled D2 bank on its task's mutant pool entry."""
    study = Path(study)
    bank_path = study / 'd2_banks' / provider / f'{task_id}.bank.json'
    score_dir = study / 'reports' / 'phase0_tasks' / provider
    score_dir.mkdir(parents=True, exist_ok=True)
    score_path = score_dir / f'{task_id}.score.json'
    if score_path.exists():
        return read_json(score_path)
    if not bank_path.exists():
        return {'task_id': task_id, 'status': 'no_bank'}
    bank = read_json(bank_path)
    started = time.monotonic()
    score = d2_contract.evaluate_bank_on_mutant_pool_task(
        bank,
        task_entry,
        include_public_fail_mutants=include_public_fail,
        pool_index=0,
    )
    score['status'] = 'scored'
    score['provider'] = provider
    score['score_seconds'] = round(time.monotonic() - started, 2)
    score['scored_utc'] = utc_now()
    score['bank_flags'] = {
        'validator_public_ok': bank['validator_public_ok'],
        'property_enabled': bank['property_enabled'],
        'oracle_enabled': bank['oracle_enabled'],
        'stress_enabled': bank['stress_enabled'],
        'small_pool0_len': len(bank['small_pools'][0]) if bank['small_pools'] else 0,
        'oracle_labeled_pool0': sum(
            c['ref_output'] is not None for c in (bank['small_pools'][0] if bank['small_pools'] else [])
        ),
        'metamorphic_pairs_len': len(bank['metamorphic_pairs']),
        'stress_inputs_len': len(bank['stress_inputs']),
    }
    write_json(score_path, score)
    return score


def aggregate_phase0(task_ids, compile_records, score_records, *, provider):
    """Aggregate offline Endres mutant benchmark results across all tasks."""
    compiled = [r for r in compile_records.values() if r.get('status') == 'compiled']
    scored = [r for r in score_records.values() if r.get('status') == 'scored']

    modes_agg = {}
    for mode in ('inputs-stress', 'property', 'oracle'):
        ref_total = ref_fr = tasks_with_fr = 0
        pp_total = pp_killed = tasks_with_kill = 0
        by_reason = {k: 0 for k in ('RE', 'TLE', 'postcondition', 'metamorphic', 'oracle_mismatch')}
        by_verdict = {}
        false_rejections = []
        per_task = []

        for sc in scored:
            tid = sc['task_id']
            m = sc['modes'][mode]
            refs = m['references']
            pp = m['public_pass_mutants']
            ref_total += refs['total']
            ref_fr += refs['false_rejected']
            if refs['false_rejected'] > 0:
                tasks_with_fr += 1
                for fr in refs['false_rejections']:
                    ce = fr.get('counterexample') or {}
                    false_rejections.append({
                        'task_id': tid,
                        'submission_sha256': fr['submission_sha256'],
                        'reason': ce.get('reason'),
                        'suite': ce.get('suite'),
                        'post_id': ce.get('post_id'),
                        'detail': (ce.get('detail') or '')[:200],
                        'input_preview': (ce.get('input') or '')[:200],
                        'output_preview': (ce.get('output') or '')[:120],
                        'expected_preview': (ce.get('expected_output') or '')[:120],
                    })
            pp_total += pp['total']
            pp_killed += pp['killed']
            if pp['killed'] > 0:
                tasks_with_kill += 1
            for r_key, r_cnt in pp['by_reason'].items():
                by_reason[r_key] = by_reason.get(r_key, 0) + r_cnt
            for v_key, v_bucket in pp['by_hidden_verdict'].items():
                agg_v = by_verdict.setdefault(
                    v_key, {'total': 0, 'killed': 0, 'by_reason': dict.fromkeys(by_reason, 0)}
                )
                agg_v['total'] += v_bucket['total']
                agg_v['killed'] += v_bucket['killed']
                for r_key, r_cnt in v_bucket['by_reason'].items():
                    agg_v['by_reason'][r_key] = agg_v['by_reason'].get(r_key, 0) + r_cnt

            per_task.append({
                'task_id': tid,
                'ref_total': refs['total'],
                'ref_false_rejected': refs['false_rejected'],
                'pp_total': pp['total'],
                'pp_killed': pp['killed'],
                'pp_by_reason': pp['by_reason'],
                'flags': sc.get('bank_flags'),
            })

        for v_bucket in by_verdict.values():
            v_bucket['kill_rate'] = round(v_bucket['killed'] / v_bucket['total'], 4) if v_bucket['total'] else None

        modes_agg[mode] = {
            'tasks_scored': len(scored),
            'references': {
                'total_programs': ref_total,
                'false_rejected_programs': ref_fr,
                'program_frr': round(ref_fr / ref_total, 4) if ref_total else None,
                'tasks_with_any_fr': tasks_with_fr,
                'task_frr': round(tasks_with_fr / len(scored), 4) if scored else None,
            },
            'public_pass_mutants': {
                'total_mutants': pp_total,
                'killed_mutants': pp_killed,
                'mutant_kill_rate': round(pp_killed / pp_total, 4) if pp_total else None,
                'tasks_with_any_kill': tasks_with_kill,
                'task_detection_rate': round(tasks_with_kill / len(scored), 4) if scored else None,
                'by_reason': by_reason,
                'by_hidden_verdict': by_verdict,
            },
            'false_rejections': false_rejections,
            'per_task': per_task,
        }

    return {
        'schema': 'csc2108-phase0-d2-offline-report-v1',
        'provider': provider,
        'created_utc': utc_now(),
        'n_target_tasks': len(task_ids),
        'n_compiled': len(compiled),
        'n_scored': len(scored),
        'calibration_summary': {
            'validator_public_ok': sum(bool(r['validator_public_ok']) for r in compiled),
            'property_enabled': sum(bool(r['property_enabled']) for r in compiled),
            'oracle_enabled': sum(bool(r['oracle_enabled']) for r in compiled),
            'stress_enabled': sum(bool(r['stress_enabled']) for r in compiled),
            'failed_tasks': [
                {'task_id': tid, 'status': r.get('status'), 'error': r.get('error')}
                for tid, r in compile_records.items()
                if r.get('status') != 'compiled'
            ],
        },
        'modes': modes_agg,
    }


def main():
    parser = argparse.ArgumentParser(description='Run Phase 0 offline D2 mutant benchmark')
    parser.add_argument('--study', default=str(DEFAULT_STUDY))
    parser.add_argument('--provider', default='codex', choices=['codex', 'api'])
    parser.add_argument('--model', default='gpt-6.2-sol')
    parser.add_argument('--effort', default='medium')
    parser.add_argument('--ledger', default=None)
    parser.add_argument('--tasks', default=None, help='Comma-separated subset of task_ids')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--score-workers', type=int, default=2)
    parser.add_argument('--include-public-fail', action='store_true')
    parser.add_argument('--reattempt-errors', action='store_true')
    parser.add_argument('--author-only', action='store_true')
    args = parser.parse_args()

    study = Path(args.study)
    cohorts = read_json(DEV_COHORTS)
    pool = read_json(MUTANT_POOL)
    raw_tasks = pool['tasks']
    task_map = raw_tasks if isinstance(raw_tasks, dict) else {t['task_id']: t for t in raw_tasks}
    task_ids = [t.strip() for t in args.tasks.split(',')] if args.tasks else cohorts['phase0_offline_mutant_pool_tasks']

    print(f'=== Phase 0 D2 Offline Benchmark ({len(task_ids)} tasks, provider={args.provider}) ===', flush=True)
    compile_records = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {
            ex.submit(
                author_and_compile_task,
                tid,
                study=study,
                provider=args.provider,
                model=args.model,
                effort=args.effort,
                ledger_path=args.ledger,
                reattempt_errors=args.reattempt_errors,
            ): tid
            for tid in task_ids
        }
        for fut in as_completed(futs):
            tid = futs[fut]
            rec = fut.result()
            compile_records[tid] = rec
            if rec['status'] == 'compiled':
                print(
                    f"  [COMPILED] {tid}: val={rec['validator_public_ok']} prop={rec['property_enabled']} "
                    f"oracle={rec['oracle_enabled']} stress={rec['stress_enabled']} "
                    f"oracle_small={rec['compilation_stats'].get('oracle_labeled_small')} "
                    f"meta={rec['compilation_stats'].get('metamorphic', {}).get('accepted')}",
                    flush=True,
                )
            else:
                print(f"  [FAIL]     {tid}: {rec['status']} -> {rec.get('error', {}).get('error')}", flush=True)

    if args.author_only:
        print('Author/compile stage complete (--author-only).', flush=True)
        return

    score_records = {}
    compiled_ids = [tid for tid in task_ids if compile_records[tid].get('status') == 'compiled' and tid in task_map]
    print(f'\n--- Scoring {len(compiled_ids)} compiled banks on mutant pool ---', flush=True)
    with ThreadPoolExecutor(max_workers=max(1, args.score_workers)) as ex:
        futs = {
            ex.submit(
                score_task_offline,
                tid,
                task_map[tid],
                study=study,
                provider=args.provider,
                include_public_fail=args.include_public_fail,
            ): tid
            for tid in compiled_ids
        }
        for fut in as_completed(futs):
            tid = futs[fut]
            sc = fut.result()
            score_records[tid] = sc
            if sc.get('status') == 'scored':
                parts = []
                for mode in ('inputs-stress', 'property', 'oracle'):
                    m = sc['modes'][mode]
                    parts.append(
                        f"{mode}: FR={m['references']['false_rejected']}/{m['references']['total']} "
                        f"KILL={m['public_pass_mutants']['killed']}/{m['public_pass_mutants']['total']}"
                    )
                print(f"  [SCORED]   {tid} ({sc.get('score_seconds')}s): " + ' | '.join(parts), flush=True)
            else:
                print(f"  [SKIP]     {tid}: {sc.get('status')}", flush=True)

    report = aggregate_phase0(task_ids, compile_records, score_records, provider=args.provider)
    out_path = study / 'reports' / f'phase0_d2_offline_{args.provider}.json'
    write_json(out_path, report)
    print(f'\n=== Phase 0 Aggregate Summary ({out_path}) ===', flush=True)
    print(
        f"Compiled: {report['n_compiled']}/{report['n_target_tasks']} | "
        f"val_ok={report['calibration_summary']['validator_public_ok']} "
        f"prop_ok={report['calibration_summary']['property_enabled']} "
        f"oracle_ok={report['calibration_summary']['oracle_enabled']} "
        f"stress_ok={report['calibration_summary']['stress_enabled']}",
        flush=True,
    )
    for mode, stats in report['modes'].items():
        r = stats['references']
        p = stats['public_pass_mutants']
        print(
            f"  {mode:14s}: Ref FRR={r['false_rejected_programs']}/{r['total_programs']} "
            f"({r['program_frr']}) [tasks {r['tasks_with_any_fr']}/{stats['tasks_scored']}] | "
            f"PP-Mutant Kill={p['killed_mutants']}/{p['total_mutants']} ({p['mutant_kill_rate']}) "
            f"[tasks {p['tasks_with_any_kill']}/{stats['tasks_scored']}] | "
            f"reasons={p['by_reason']}",
            flush=True,
        )


if __name__ == '__main__':
    main()
