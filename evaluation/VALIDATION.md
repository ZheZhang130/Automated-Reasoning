# Final evaluation: pre-launch validation (2026-11-25)

Validation of branch `feat/csc2108-final-evaluation` before the official 900-attempt benchmark (study root
`E:\CSC2108Local\final-study`, batch `final-main`). Runtime artifacts stay outside the checkout; only summaries are here.

## Problem set

`judge/manifests/final.json` (sha256 `6f11cd410028d613a8f28ed4097e78dd45703894ba5b1b352011f1ab0f9f9d44`):

| Property | Value |
| --- | --- |
| Dataset | `livecodebench/code_generation_lite`, shard `test6.jsonl`, revision `0fe84c3912ea0c4d4a78037083943e8f0c4dd505`, shard sha256 `bb4c364f…d1f5` |
| Tasks | 60 unique AtCoder stdin tasks: 20 easy, 20 medium, 20 hard |
| Hidden tests | exactly 40 per task (60 of 60) |
| Output semantics | all `exact` (audit: 112 judgeable, 102 exact, 10 excluded) |
| Historical exposure (allowed, recorded) | 10 development, 10 selection/held-out, 8 other scored, 32 none known (`none_known` = potentially unseen, not verified unseen) |
| Reproducibility | rerunning the documented `evaluation select` command reproduces the manifest byte for byte (same sha256 and git blob) |

## Tests

| Suite | Result |
| --- | --- |
| `evaluation.test_evaluation`, `evaluation.test_final` | 59 passed (58 earlier + 1 new: official ceilings cover the high-usage scenario) |
| `guided_agent.test_guided/_pass2/_pass3/_pass4`, `local_agent.test_portable` | 71 passed, 9 skipped: 8 Docker integration tests (`CSC2108_INTEGRATION=1`; passed in the previous session, not rerun: the only later agent-side change is a constant) and 1 POSIX-only lock test |
| Judge container tests | not rerun (no judge change); previous session: 24 passed |

pass@2/3 are validated offline (`evaluation.test_final.PassAtK`: exact combinatorics, undefined for n < k, matched
differences), not with additional paid runs.

## Smoke end-to-end (`E:\CSC2108Local\final-eval-smoke`, batch `smoke-final`)

3 pilot tasks (`abc390_c` easy, `abc393_a` medium, `abc394_g` hard), seed 2108, conditions A–E, 15 attempts, separate
ledger (60 requests / $6). The batch was paused in the previous session after 7 attempts with one attempt interrupted,
and was resumed (not recreated) under the same provenance binding (a docs-only commit in between does not bind).

* **Resume:** the interrupted `abc393_a-A` was set aside as `*.incomplete-65d20f` and retried; the other finished
  attempts were kept.
* **Completeness:** 15/15 `scored`, 0 incomplete, 0 invalid, 0 orphan verdicts; the official (non-preliminary) report
  was accepted. Verdicts are bound to run ID, task, condition, submission sha256 and the hidden-suite digest.
* **Conditions:** all five ran. E triggered and delivered its diagnosis on the easy and medium tasks (~4 s frontier
  wait each, same session); on the hard task the local model never reached a public test, so E correctly did not
  trigger.
* **Outcomes (not an estimate of anything):** A 2/3, B 3/3, C 2/3, D 2/3, E 2/3 hidden passes. The hard-task failures
  were model failures, classified as such: C `context_overflow` (llama-server closed the connection at 16,383 context
  tokens; recorded as overflow, not infrastructure), A/D/E `truncated_no_program` (three 4,096-token responses).
  No infrastructure exclusions.
* **API:** 17 requests (3 plan, 3 contract, 9 B coder turns, 2 diagnoses), all completed; token-derived $0.083,
  conservative reservation $0.55. The report attributes all 17 ledger requests to included runs (0 unattributed).
  Guidance cost is counted once per artifact.
* **Report sections checked:** cold-start / warm-start / amortized latency (C/D include authoring), matched runtime
  ratios vs A and B, cost/tokens per condition, attempt and pass (cached input and reasoning shown, not double
  counted), ledger reconciliation, failure categories, transitions, E triggered subset; pass@1 only (pass@2/3
  correctly unavailable with one seed).

The smoke is a pipeline check, never pooled with official data.

## Independent judge cross-check

`evaluation crosscheck` on 40 saved hidden-scored submissions from four development batches (`ext-s2108`,
`p4-screen-s2108`, `p4-stageD-agent`, `dev2`; conditions A, C, D, E and agent variants; 10 tasks), re-judged by the
official LiveCodeBench evaluator at revision `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24` (clean vendor checkout) in the
isolated `csc2108-lcb-judge:v2` container (no network, read-only root, 1 GB, 1 CPU, 64 pids, unprivileged, all
capabilities dropped), hidden tests only:

| Our verdict | Runs | Official agrees |
| --- | --- | --- |
| pass | 20 | 20 |
| candidate_failure | 20 | 20 |

40/40 agreement, 0 official infrastructure errors. Differences in configuration: the official evaluator stops at the
first failing test (it reports e.g. 1/2 where ours reports 31/40), so only the verdicts are compared. Limitations: the
sample covers 10 alphabetically early tasks (the selection alternates pass/failure in task order), includes no B
submissions, and agreement does not cover tasks with several acceptable outputs (excluded from the manifest).
`crosscheck.json` (which contains first-failure test data) is kept outside the repository in
`E:\CSC2108Local\final-eval-validation\crosscheck\`.

## Budget change before freeze

`evaluation budget` on the official plan at the then code maximum (1,500 requests / $100): expected 794 requests
(fits), high 1,560 (did **not** fit on requests), stress and worst do not fit. Following the overnight runbook (request
cap at most 2,000, monetary ceiling unchanged), `guided_agent/providers.py` `MAX_REQUESTS` was raised 1500 → 2000
before the official ledger, plan freeze and launch; `MAX_USD` stays $100 and remains the binding limit. The smoke ran
with the 1,500 maximum (its own ledger: 60 / $6), so its code fingerprint differs from the official one only by this
constant.

## Limitations to carry into the report

Mixed historical exposure (not a held-out benchmark) and possible training contamination; one model pair and one
AtCoder subset; hidden tests are not formal verification; C/D guidance is shared across seeds; B and the local
conditions have different budgets; timings are specific to the Windows RTX 4080 SUPER host; costs are token-derived,
not invoiced; contracts are passive and diagnosis is conditional on a public failure.

## Overnight operation

Host-specific helpers in `evaluation/ops/` (copies of `E:\CSC2108Local\ops\`): `ev.ps1` (run any step with the
project environment), `launch.ps1` (one detached step with logs, refuses duplicates), `detach.ps1` (start a process
outside the T3 job object), `watchdog.ps1` (launch/resume `evaluation run`, progress log, project-Ollama restart,
cascade stop, then `score` and `metrics`). The watchdog was exercised on the smoke batch: it adopted the running
batch, detected completion, scored and wrote the report.
