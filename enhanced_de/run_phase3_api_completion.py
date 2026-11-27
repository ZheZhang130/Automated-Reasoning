"""Phase 3 completion: two extra paid-API E2 runs that finish the API rescue side on test5_val16.

After the first 8 API diagnoses, the remaining held-out states where an E2 arm could still rescue an A failure
were arc189_c (stall, no program in A) and abc382_d (public pass, hidden fail).  This adds exactly those two runs
(2 requests; ledger hard caps unchanged: 20 requests / $10 conservative) so the API rows cover every A-failing
test5 task that reaches an E2 trigger.  Same batch directory and spec builders as ``run_phase3_api``.
"""

import argparse
from pathlib import Path

from . import ledger_guard, run_experiments as rexp, runner_v2

STUDY = Path(r'E:\CSC2108Local\enhanced-de-v2-study')
TARGETS = [('lcb-atcoder-arc189_c', 'stall'), ('lcb-atcoder-abc382_d', 'review')]


def build(study, ledger):
    batch_name = 'phase3-api-validation'
    batch_dir = Path(study) / 'runs' / batch_name
    specs = []
    for tid, kind in TARGETS:
        if kind == 'stall':
            e2 = {'kind': 'stall', 'mode': 'stall-diag', 'protocol': 'v2', 'enable_public_fallback': False,
                  'provider_spec': rexp._provider_spec('api', study, ledger=ledger, purpose='phase3-stall:test5')}
            arm = 'E2-stall-diag-api'
        else:
            e2 = {'kind': 'review',
                  'provider_spec': rexp._provider_spec('api', study, ledger=ledger, purpose='phase3-review:test5')}
            arm = 'E2-review-api'
        specs.append(rexp.make_spec(batch_dir=batch_dir, study=study, cohort='phase3-api:test5',
                                    batch_name=batch_name, task_id=tid, seed=2108, arm=arm, condition='E2',
                                    e2=e2, provider_label='openai-api'))
    return batch_dir, specs


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--study', default=str(STUDY))
    args = p.parse_args()
    study = Path(args.study)
    ledger = study / 'api-ledger.json'
    info = ledger_guard.verify_ledger(ledger)
    if info['requests_used'] + len(TARGETS) > info['max_requests']:
        raise SystemExit('ledger ceiling would be exceeded')
    batch_dir, specs = build(study, ledger)
    runner_v2.run_batch_v2(batch_dir, specs)
    runner_v2.evaluate_batch_v2(batch_dir, study)
    summary = rexp.summarize_batch(batch_dir, compare_final_main=False)
    from guided_agent.common import write_json
    write_json(batch_dir / 'summary.json', summary)
    print(ledger_guard.verify_ledger(ledger))


if __name__ == '__main__':
    main()
