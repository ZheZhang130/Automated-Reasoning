"""Phase 3 runner: Direct OpenAI API (`gpt-6.2-sol`) validation under strict v2 ledger.

Strictly separated from isolated Codex replay (`runs/phase3-api-validation/`).
Targets <= 12 total paid requests across the entire v2 study (4 D2 banks already
authored + 8 live E2 API calls = 12/20 requests; hard cap 20 req / $10.00 conservative).
"""

import argparse
import json
from pathlib import Path

from guided_agent.common import REPO, read_json, utc_now, write_json

from . import ledger_guard, run_experiments as rexp, runner_v2


DEFAULT_STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
API_D2_TASKS = [
    'lcb-atcoder-abc384_c',
    'lcb-atcoder-abc383_c',
    'lcb-atcoder-abc379_g',
    'lcb-atcoder-abc376_e',
]


def select_phase3_targets(study, seed=2108):
    """Deterministically pick live API targets from the Phase 2 test5 trigger states (dev fallbacks labelled).

    Eligibility comes from the recorded A trajectory (``reports/phase2_trigger_states_s<seed>.json``, written by
    ``run_phase2_validation triggers``), the same evidence the trigger-partitioned Codex arms use:

    - D2-oracle (API bank): the 4 pre-authored test5 API banks, only where A reaches a public pass (0 new calls;
      elsewhere the gate cannot fire and the run would equal A)
    - E2-strict (API): up to 4 test5 tasks whose A run reaches a public failure, A-hidden-failures first
    - E2-stall-diag (API): up to 2 test5 stall states
    - E2-review (API): up to 2 test5 public-pass states whose A run failed hidden (PPHF), then other public passes
    Development fallbacks (consumed final-main states) fill any shortfall and are labelled ``dev-*``.
    """
    study = Path(study)
    states = read_json(study / 'reports' / f'phase2_trigger_states_s{seed}.json')['states']
    a_pass = {}
    for ev in sorted((study / 'runs' / 'phase2-test5-codex' / 'eval').glob('*-A-s*.json')):
        rec = read_json(ev)
        if rec.get('arm') == 'A' and int(rec.get('seed') or 0) == seed:
            a_pass[rec['task_id']] = rec.get('status') == 'pass'
    order = sorted(states)
    fail = sorted((t for t in order if states[t]['fail']), key=lambda t: (a_pass.get(t) is True, t))
    stall = sorted((t for t in order if states[t]['stall']), key=lambda t: (a_pass.get(t) is True, t))
    review = sorted((t for t in order if states[t]['pass']), key=lambda t: (a_pass.get(t) is not False, t))

    def fill(chosen, want, fallbacks):
        out = [(t, seed, 'test5') for t in chosen[:want]]
        for fb in fallbacks:
            if len(out) >= want:
                break
            out.append(fb)
        return out

    return {
        'd2_oracle_api': [(t, seed, 'test5') for t in API_D2_TASKS if states.get(t, {}).get('pass')],
        'e2_strict_api': fill(fail, 4, [('lcb-atcoder-abc400_c', 2109, 'dev-phase1b'),
                                        ('lcb-atcoder-arc194_c', 2109, 'dev-phase1b'),
                                        ('lcb-atcoder-abc398_g', 2108, 'dev-phase1b'),
                                        ('lcb-atcoder-abc394_e', 2110, 'dev-phase1b')]),
        'e2_stall_api': fill(stall, 2, [('lcb-atcoder-abc390_d', 2108, 'dev-phase1c'),
                                        ('lcb-atcoder-abc394_e', 2108, 'dev-phase1c')]),
        'e2_review_api': fill(review, 2, [('lcb-atcoder-abc387_c', 2108, 'dev-phase1a'),
                                          ('lcb-atcoder-abc400_c', 2109, 'dev-phase1a')]),
    }


def build_phase3_specs(study, *, ledger_path=None):
    study = Path(study)
    ledger = Path(ledger_path or (study / 'api-ledger.json'))
    ledger_guard.verify_ledger(ledger)
    targets = select_phase3_targets(study)
    batch_name = 'phase3-api-validation'
    batch_dir = study / 'runs' / batch_name
    specs = []

    for tid, seed, src in targets['d2_oracle_api']:
        bank_path = study / 'd2_banks' / 'api' / f'{tid}.bank.json'
        if not bank_path.exists():
            raise FileNotFoundError(f'Missing compiled API D2 bank: {bank_path}')
        specs.append(rexp.make_spec(
            batch_dir=batch_dir, study=study, cohort=f'phase3-api:{src}',
            batch_name=batch_name, task_id=tid, seed=seed, arm='D2-oracle-api', condition='D2',
            d2={'bank_path': str(bank_path), 'mode': 'oracle', 'trigger': 'public_pass_only'},
            provider_label='openai-api',
        ))

    for tid, seed, src in targets['e2_strict_api']:
        specs.append(rexp.make_spec(
            batch_dir=batch_dir, study=study, cohort=f'phase3-api:{src}',
            batch_name=batch_name, task_id=tid, seed=seed, arm='E2-strict-api', condition='E2',
            e2={
                'kind': 'strict',
                'enable_advisory_vchecks': True,
                'provider_spec': rexp._provider_spec('api', study, ledger=ledger, purpose=f'phase3-strict:{src}'),
            },
            provider_label='openai-api',
        ))

    for tid, seed, src in targets['e2_stall_api']:
        specs.append(rexp.make_spec(
            batch_dir=batch_dir, study=study, cohort=f'phase3-api:{src}',
            batch_name=batch_name, task_id=tid, seed=seed, arm='E2-stall-diag-api', condition='E2',
            e2={
                'kind': 'stall',
                'mode': 'stall-diag',
                'protocol': 'v2',
                'enable_public_fallback': False,
                'provider_spec': rexp._provider_spec('api', study, ledger=ledger, purpose=f'phase3-stall:{src}'),
            },
            provider_label='openai-api',
        ))

    for tid, seed, src in targets['e2_review_api']:
        specs.append(rexp.make_spec(
            batch_dir=batch_dir, study=study, cohort=f'phase3-api:{src}',
            batch_name=batch_name, task_id=tid, seed=seed, arm='E2-review-api', condition='E2',
            e2={
                'kind': 'review',
                'provider_spec': rexp._provider_spec('api', study, ledger=ledger, purpose=f'phase3-review:{src}'),
            },
            provider_label='openai-api',
        ))

    return batch_dir, specs, targets


def main():
    p = argparse.ArgumentParser(description='Run Phase 3 Direct OpenAI API live validation')
    p.add_argument('--study', default=str(DEFAULT_STUDY))
    p.add_argument('--ledger', default=None)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    study = Path(args.study)
    ledger_path = Path(args.ledger or (study / 'api-ledger.json'))
    batch_dir, specs, targets = build_phase3_specs(study, ledger_path=ledger_path)
    info = ledger_guard.verify_ledger(ledger_path)
    print(f'=== Phase 3 Direct OpenAI API Validation ({len(specs)} live runs; ledger {info["requests_used"]}/{info["max_requests"]}) ===', flush=True)
    print(json.dumps(targets, indent=2), flush=True)
    if args.dry_run:
        return

    runner_v2.run_batch_v2(batch_dir, specs)
    print(f'--- Hidden evaluation for {batch_dir} ---', flush=True)
    runner_v2.evaluate_batch_v2(batch_dir, study)
    summary = rexp.summarize_batch(batch_dir, compare_final_main=True)
    # Attach exact ledger reconciliation
    led = read_json(ledger_path)
    tot_std = tot_cons = tot_reason = 0.0
    for req in led.get('requests') or []:
        u = req.get('usage') or {}
        pt, ct = u.get('prompt_tokens') or 0, u.get('completion_tokens') or 0
        rt = (u.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0
        tot_std += (pt * 2.0 + ct * 10.0) / 1e6
        tot_cons += (pt * 12.0 + ct * 60.0) / 1e6
        tot_reason += rt
    summary['ledger_reconciliation'] = {
        'requests_used': len(led.get('requests') or []),
        'max_requests': led.get('max_requests'),
        'max_usd': led.get('max_usd'),
        'total_reasoning_tokens': int(tot_reason),
        'total_standard_usd': round(tot_std, 6),
        'total_conservative_usd': round(tot_cons, 6),
    }
    write_json(batch_dir / 'summary.json', summary)
    print(json.dumps(summary['by_arm'], indent=2), flush=True)
    print('LEDGER:', json.dumps(summary['ledger_reconciliation'], indent=2), flush=True)


if __name__ == '__main__':
    main()
