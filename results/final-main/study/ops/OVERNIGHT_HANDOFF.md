# CSC2108 official benchmark — handoff

Updated: 2026-11-25 21:40 UTC. **State: COMPLETE.** The official batch `final-main` finished all 900 attempts, hidden
scoring finished, and the **official** (non-preliminary) report was accepted and written to `report\`.
No user action is required. The project Ollama server (11435) was stopped afterwards, as it was at handoff.

## Results location

`E:\CSC2108Local\final-study\report\` contains `report.md` (human-readable), `report.json` (everything, for plots),
`runs.csv` (one row per attempt) and `tasks.csv` (one row per task and condition). Archive the whole study root with
git commit `a2aa499` before analysis. Never commit the study root, because it contains hidden-test data and run artifacts.

Headline numbers from `report.md`. These are pass@1 on hidden tests, with task-bootstrap 95% CIs. Paired p-values
vs A use a sign-flip permutation test, Holm-adjusted over C, D and E.

| Condition | pass@1 | Δ vs A [95% CI] | Holm p | pass@3 | Cold-start E2E s (median) | Token-derived $ total |
| --- | --- | --- | --- | --- | --- | --- |
| A Local | 0.533 | – | – | 0.567 | 42.0 | 0 (local compute only) |
| B Frontier | 0.967 | +0.433 [0.317, 0.556] | (exploratory) | 0.967 | 12.0 | 1.85 |
| C Planning | 0.717 | +0.183 [0.100, 0.272] | 0.0006 | 0.783 | 25.9 | 0.57 (upfront, once per task) |
| D Contract | 0.544 | +0.011 [-0.017, 0.044] | 1.0 | 0.583 | 36.5 | 0.35 (upfront) |
| E Diagnosis | 0.550 | +0.017 [0.000, 0.044] | 1.0 | 0.583 | 39.3 | 0.26 (run-time) |

By difficulty, pass@1 for A/B/C/D/E was: easy 0.98/1.00/1.00/1.00/1.00, medium 0.53/0.95/0.83/0.55/0.57, and hard
0.08/0.95/0.32/0.08/0.08. Gap closed toward B was 0.42 for C, 0.03 for D and 0.04 for E. E triggered in 18.3% of its
runs; this subset is descriptive only. The report also covers seed consistency, failure categories, transitions,
exposure subgroups, hidden-test coverage (40 tests for every task) and the warm/amortized latency tables.
Interpretation limits are listed in `evaluation/VALIDATION.md`. Among them: mixed historical exposure, one model pair,
shared C/D guidance across seeds, and token-derived costs that are not invoices.

## Repository

* Checkout: `E:\VS Code Projects\CSC2108Project\Automated-Reasoning`, branch `feat/csc2108-final-evaluation`.
* Base at handoff was `50d2e22`. New commits:
  * `bf160d8`: request maximum raised from 1500 to 2000 ($100 unchanged), a focused test, `evaluation/VALIDATION.md`
    and `evaluation/ops/`. The official run used this commit.
  * `a2aa499`: documentation only, recording the official run.
* Both commits were pushed to `origin/feat/csc2108-final-evaluation`. There was no merge and no force-push.
* Working tree: clean except the two user PDFs `papers/2310.01831v2.pdf` and `papers/chong26b.pdf`, which were
  intentionally left untracked.

## Validation and readiness (details: `evaluation/VALIDATION.md`)

* Tests: evaluation 59 passed. Guided and local agent: 71 passed, 9 skipped (8 Docker integration tests passed in
  the previous session; 1 POSIX-only). The judge container tests were not rerun because the judge didn't change.
* Manifest: reproduced byte for byte; 60 unique tasks, 20/20/20, 40 hidden tests each.
* Smoke: `E:\CSC2108Local\final-eval-smoke` was resumed and completed, 15/15 scored, with the official report
  accepted.
* Official LiveCodeBench evaluator cross-check: 40/40 verdicts agree.
* Readiness gate: ready, with no problems and no warnings (`ready-final.json`).

## Official study record

| Item | Value |
| --- | --- |
| Plan | `plans\final-main.json`, sha256 `7342a46fb0b0ff5eb0ea9a9144126f499001e758baa72eebb45ad09bc402d052` |
| Freeze | `plans\final-main.freeze.json`, sha256 `224c492c635ff659f2b546405afac6b16324644907eab7787c642b9ea9b53515` (120 artifacts) |
| Provenance | `runs\final-main\provenance.json`. 2 sessions (05:55 and 20:53 UTC) on commit `bf160d8`, with the same binding sha256 `8822ddd7…805c` |
| Timeline | Launch 05:55 UTC. Seed 2108 done at ~11:00, seed 2109 at ~16:00, seed 2110 at 20:50. Set-aside rerun 20:53. Scoring 20:55–21:30. Report 21:30 UTC. That is ~15 h of execution plus 35 min of scoring |
| Attempts | 900/900 `scored`; 0 excluded blocks; 0 invalid; 0 orphan verdicts |
| API ledger | 725 requests: 724 completed and 1 HTTP error. Breakdown: 120 guidance, 571 B coder turns, 33 E diagnoses, plus the failed diagnosis. $3.03 token-derived, $20.46 conservative reservation; ceilings 2000 / $100 |
| Resources | Disk E: ~376 GB free throughout; Ollama and Docker healthy at every poll; GPU RTX 4080 SUPER |

## Incident and recovery history

* 05:55–07:30 UTC (supervision tooling only). An orphaned `tail -F` held `PROGRESS.log` open, so the watchdog's
  appends to it failed. `ops-logs\watchdog.log` recorded every line. The tail was stopped and `PROGRESS.log` was
  backfilled (those lines are marked `(backfill)`). There was no effect on the experiment.
* 14:23 UTC: frontier provider fault. The diagnosis request for `lcb-atcoder-abc395_e-E-s2109` got API HTTP 503
  (`server_is_overloaded`). Following README §5, outcome-blind and before any hidden scoring, I moved that one run
  (with its `.log` and `.spec.json`) to `set-aside\final-main\` and recorded it in `SET_ASIDE_LOG.jsonl`. It was
  rerun at 20:53 by resuming the same plan, and the rerun's diagnosis was delivered. The failed request is reported
  as `not_attributable` in the report's study-expenditure table. No API retry logic was added.
* No other incidents. The watchdog needed no Ollama restarts or cascade stops, and no blockers occurred.

## Commands (PowerShell)

```powershell
$S = 'E:\CSC2108Local\final-study'; $P = "$S\plans\final-main.json"
& E:\CSC2108Local\ops\ev.ps1 $S status $P                       # 900 scored
& E:\CSC2108Local\ops\ev.ps1 $S --study $S metrics $S\runs\final-main --out $S\report --ledger $S\api-ledger.json   # regenerate the report
& .\local_baseline\start_ollama.ps1                              # project Ollama, only needed to run attempts again
```

Logs: `PROGRESS.log` (summary), `ops-logs\watchdog.log` (authoritative), `ops-logs\run-*.log`, `score-*.log`,
`metrics-*.log`, and `ops-logs\launches.jsonl`.
