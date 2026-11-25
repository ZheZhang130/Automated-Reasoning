# Evaluation report

Scheduled runs: 900; included: 900; excluded (task, seed) blocks: 0.


## Sample sizes and exclusions

Tasks included: 60; seeds: [2108, 2109, 2110]; attempt states: {'scored': 900}; excluded-block reasons: none.

| Condition | Scheduled | Included |
| --- | --- | --- |
| A | 180 | 180 |
| B | 180 | 180 |
| C | 180 | 180 |
| D | 180 | 180 |
| E | 180 | 180 |

## Main results (all tasks)

| Condition | Hidden pass rate | E2E latency s, median (IQR) | Frontier cost | Cost/pass | Frontier tokens | Gap closed |
| --- | --- | --- | --- | --- | --- | --- |
| A — Local | 53.3% | 42.0 (13.3–128.2) | $0.0000 | $0.0000 | 0 | – |
| B — Frontier | 96.7% | 12.0 (10.3–18.0) | $1.8496 | $0.0106 | 650978 | – |
| C — Planning | 71.7% | 25.9 (19.0–72.8) | $0.5707 | $0.0044 | 84463 | 0.423 |
| D — Contract | 54.4% | 36.5 (19.9–136.7) | $0.3524 | $0.0036 | 65993 | 0.026 |
| E — Diagnosis | 55.0% | 39.3 (13.3–128.2) | $0.2594 | $0.0026 | 81944 | 0.038 |

E2E latency is cold-start (C, D include their upfront guidance authoring); frontier cost is token-derived (usage x list price), not invoiced; frontier tokens are input + output (reasoning included in output).

## pass@k (primary: pass@1; pass@2 and pass@3 secondary)

| Condition | Pass@1 | Pass@2 | Pass@3 | All attempts successful | Tasks |
| --- | --- | --- | --- | --- | --- |
| A — Local | 0.533 [0.4111, 0.6556] | 0.561 [0.4333, 0.6833] | 0.567 [0.45, 0.6833] | 48.3% | 60 |
| B — Frontier | 0.967 [0.9167, 1.0] | 0.967 [0.9167, 1.0] | 0.967 [0.9167, 1.0] | 96.7% | 60 |
| C — Planning | 0.717 [0.6111, 0.8222] | 0.761 [0.6556, 0.8611] | 0.783 [0.6833, 0.8833] | 65.0% | 60 |
| D — Contract | 0.544 [0.4222, 0.6667] | 0.572 [0.45, 0.6944] | 0.583 [0.4667, 0.7] | 50.0% | 60 |
| E — Diagnosis | 0.550 [0.4278, 0.6667] | 0.578 [0.4556, 0.7] | 0.583 [0.4667, 0.7] | 50.0% | 60 |

pass@k, easy:

| Condition | Pass@1 (tasks) | Pass@2 (tasks) | Pass@3 (tasks) |
| --- | --- | --- | --- |
| A | 0.983 (20) | 1.000 (20) | 1.000 (20) |
| B | 1.000 (20) | 1.000 (20) | 1.000 (20) |
| C | 1.000 (20) | 1.000 (20) | 1.000 (20) |
| D | 1.000 (20) | 1.000 (20) | 1.000 (20) |
| E | 1.000 (20) | 1.000 (20) | 1.000 (20) |

pass@k, hard:

| Condition | Pass@1 (tasks) | Pass@2 (tasks) | Pass@3 (tasks) |
| --- | --- | --- | --- |
| A | 0.083 (20) | 0.100 (20) | 0.100 (20) |
| B | 0.950 (20) | 0.950 (20) | 0.950 (20) |
| C | 0.317 (20) | 0.383 (20) | 0.400 (20) |
| D | 0.083 (20) | 0.100 (20) | 0.100 (20) |
| E | 0.083 (20) | 0.100 (20) | 0.100 (20) |

pass@k, medium:

| Condition | Pass@1 (tasks) | Pass@2 (tasks) | Pass@3 (tasks) |
| --- | --- | --- | --- |
| A | 0.533 (20) | 0.583 (20) | 0.600 (20) |
| B | 0.950 (20) | 0.950 (20) | 0.950 (20) |
| C | 0.833 (20) | 0.900 (20) | 0.950 (20) |
| D | 0.550 (20) | 0.617 (20) | 0.650 (20) |
| E | 0.567 (20) | 0.633 (20) | 0.650 (20) |

Matched pass@k difference vs A (95% task-bootstrap CI):

| Condition | Δ pass@1 | Δ pass@2 | Δ pass@3 |
| --- | --- | --- | --- |
| B | +0.433 [0.3167, 0.5556] | +0.406 [0.2833, 0.5278] | +0.400 [0.2833, 0.5167] |
| C | +0.183 [0.1, 0.2778] | +0.200 [0.1056, 0.3056] | +0.217 [0.1167, 0.3333] |
| D | +0.011 [-0.0167, 0.0444] | +0.011 [-0.0222, 0.0556] | +0.017 [-0.0333, 0.0833] |
| E | +0.017 [0.0, 0.0444] | +0.017 [0.0, 0.05] | +0.017 [0.0, 0.05] |

Gap closed toward B per k, (X − A) / (B − A):

| Condition | pass@1 | pass@2 | pass@3 |
| --- | --- | --- | --- |
| C | 0.423 [0.2571, 0.597] | 0.493 [0.3059, 0.6857] | 0.542 [0.3333, 0.75] |
| D | 0.026 [-0.0465, 0.1014] | 0.027 [-0.0678, 0.1235] | 0.042 [-0.1053, 0.1852] |
| E | 0.038 [0.0, 0.1053] | 0.041 [0.0, 0.1385] | 0.042 [0.0, 0.1429] |

* pass@1 is the primary outcome; pass@2 and pass@3 are secondary (the benefit of repeated attempts)
* confidence intervals resample tasks; repeated attempts on one task are not independent problems
* C and D reuse one upfront guidance artifact per task across seeds: their pass@k describes repeated local execution given shared guidance, not independently regenerated frontier guidance
* pass@k counts a task as solved when any of k attempts passes the hidden tests; it does not imply that an agent could identify the correct submission without the hidden tests

## Final pass rate: all

| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | Frontier $ total | $ per pass | Wall s median (IQR) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 180 | 96 | 53.3% | 10.0% | 11/33 | 3 | $0.0000 | $0.0000 | 42.0 (13.3–128.2) |
| B | 180 | 174 | 96.7% | 3.3% | 0/0 | 0 | $1.8496 | $0.0106 | 12.0 (10.3–18.0) |
| C | 180 | 129 | 71.7% | 10.6% | 11/39 | 4 | $0.5707 | $0.0044 | 15.8 (12.9–44.2) |
| D | 180 | 98 | 54.4% | 9.4% | 8/35 | 1 | $0.3524 | $0.0036 | 29.5 (13.3–128.8) |
| E | 180 | 99 | 55.0% | 11.7% | 14/33 | 2 | $0.2594 | $0.0026 | 39.3 (13.3–128.2) |

## Final pass rate: easy

| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | Frontier $ total | $ per pass | Wall s median (IQR) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 60 | 59 | 98.3% | 0.0% | 0/1 | 0 | $0.0000 | $0.0000 | 12.4 (11.9–13.6) |
| B | 60 | 60 | 100.0% | 0.0% | 0/0 | 0 | $0.3114 | $0.0052 | 10.0 (9.5–10.4) |
| C | 60 | 60 | 100.0% | 0.0% | 3/3 | 0 | $0.0855 | $0.0014 | 12.5 (11.9–13.1) |
| D | 60 | 60 | 100.0% | 0.0% | 2/2 | 0 | $0.0949 | $0.0016 | 12.5 (11.9–13.5) |
| E | 60 | 60 | 100.0% | 0.0% | 1/1 | 0 | $0.0038 | $0.0001 | 12.4 (11.9–13.8) |

## Final pass rate: hard

| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | Frontier $ total | $ per pass | Wall s median (IQR) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 60 | 5 | 8.3% | 18.3% | 4/15 | 3 | $0.0000 | $0.0000 | 128.2 (94.4–128.6) |
| B | 60 | 57 | 95.0% | 5.0% | 0/0 | 0 | $1.0579 | $0.0186 | 20.8 (16.6–37.7) |
| C | 60 | 19 | 31.7% | 21.7% | 5/29 | 4 | $0.3270 | $0.0172 | 101.7 (26.6–173.5) |
| D | 60 | 5 | 8.3% | 20.0% | 0/15 | 1 | $0.1344 | $0.0269 | 128.8 (125.4–129.8) |
| E | 60 | 5 | 8.3% | 21.7% | 4/15 | 0 | $0.1488 | $0.0298 | 128.2 (126.5–128.9) |

## Final pass rate: medium

| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | Frontier $ total | $ per pass | Wall s median (IQR) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 60 | 32 | 53.3% | 11.7% | 7/17 | 0 | $0.0000 | $0.0000 | 61.2 (15.9–128.3) |
| B | 60 | 57 | 95.0% | 5.0% | 0/0 | 0 | $0.4803 | $0.0084 | 11.9 (10.9–13.9) |
| C | 60 | 50 | 83.3% | 10.0% | 3/7 | 0 | $0.1583 | $0.0032 | 15.2 (13.9–22.6) |
| D | 60 | 33 | 55.0% | 8.3% | 6/18 | 0 | $0.1230 | $0.0037 | 43.6 (14.6–128.8) |
| E | 60 | 34 | 56.7% | 13.3% | 9/17 | 2 | $0.1068 | $0.0031 | 64.9 (16.4–127.9) |

## Paired vs A: all (primary: C, D, E with Holm)

| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p (exploratory) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 60 | 180 | 96.7% | 53.3% | +0.433 | [0.3167, 0.5556] | 0.0001 | – | 78/0, 0.0 |
| C | 60 | 180 | 71.7% | 53.3% | +0.183 | [0.1, 0.2722] | 0.0002 | 0.0006 | 34/1, 0.0 |
| D | 60 | 180 | 54.4% | 53.3% | +0.011 | [-0.0167, 0.0444] | 0.72656 | 1.0 | 6/4, 0.75391 |
| E | 60 | 180 | 55.0% | 53.3% | +0.017 | [0.0, 0.0444] | 0.5 | 1.0 | 3/0, 0.25 |

## Paired vs A: easy (exploratory)

| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p (exploratory) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 20 | 60 | 100.0% | 98.3% | +0.017 | [0.0, 0.05] | 1.0 | – | 1/0, 1.0 |
| C | 20 | 60 | 100.0% | 98.3% | +0.017 | [0.0, 0.05] | 1.0 | – | 1/0, 1.0 |
| D | 20 | 60 | 100.0% | 98.3% | +0.017 | [0.0, 0.05] | 1.0 | – | 1/0, 1.0 |
| E | 20 | 60 | 100.0% | 98.3% | +0.017 | [0.0, 0.05] | 1.0 | – | 1/0, 1.0 |

## Paired vs A: hard (exploratory)

| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p (exploratory) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 20 | 60 | 95.0% | 8.3% | +0.867 | [0.7167, 1.0] | 0.0001 | – | 52/0, 0.0 |
| C | 20 | 60 | 31.7% | 8.3% | +0.233 | [0.0667, 0.4167] | 0.03125 | – | 15/1, 0.00052 |
| D | 20 | 60 | 8.3% | 8.3% | +0.000 | [0.0, 0.0] | 1.0 | – | 1/1, 1.0 |
| E | 20 | 60 | 8.3% | 8.3% | +0.000 | [0.0, 0.0] | 1.0 | – | 0/0, 1.0 |

## Paired vs A: medium (exploratory)

| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p (exploratory) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 20 | 60 | 95.0% | 53.3% | +0.417 | [0.2167, 0.6333] | 0.00195 | – | 25/0, 0.0 |
| C | 20 | 60 | 83.3% | 53.3% | +0.300 | [0.1333, 0.4833] | 0.00391 | – | 18/0, 1e-05 |
| D | 20 | 60 | 55.0% | 53.3% | +0.017 | [-0.0667, 0.1] | 1.0 | – | 4/3, 1.0 |
| E | 20 | 60 | 56.7% | 53.3% | +0.033 | [0.0, 0.1] | 1.0 | – | 2/0, 0.5 |

## Runtime (all): seconds, median (IQR)

| Condition | Cold-start E2E | Warm-start | Amortized | Upfront authoring | Frontier wait in run | Local inference |
| --- | --- | --- | --- | --- | --- | --- |
| A | 42.0 (13.3–128.2) | 42.0 (13.3–128.2) | 42.0 (13.3–128.2) | – | 0.0 (0.0–0.0) | 30.3 (6.2–120.1) |
| B | 12.0 (10.3–18.0) | 12.0 (10.3–18.0) | 12.0 (10.3–18.0) | – | 7.2 (5.5–13.1) | – |
| C | 25.9 (19.0–72.8) | 15.8 (12.9–44.2) | 18.9 (15.1–53.9) | 9.0 (5.8–13.6) | 0.0 (0.0–0.0) | 8.7 (5.8–36.5) |
| D | 36.5 (19.9–136.7) | 29.5 (13.3–128.8) | 31.8 (15.6–131.5) | 7.3 (6.1–7.8) | 0.0 (0.0–0.0) | 20.1 (6.2–120.7) |
| E | 39.3 (13.3–128.2) | 39.3 (13.3–128.2) | 39.3 (13.3–128.2) | – | 0.0 (0.0–0.0) | 29.6 (6.1–120.1) |

Matched runtime vs A and B (cold-start E2E): median paired ratio X/ref (IQR), reduction = 1 − median ratio:

| Condition | vs A ratio | vs A reduction | vs B ratio | vs B reduction |
| --- | --- | --- | --- | --- |
| A | – | – | 2.32 (1.28–5.94) | -1.320 |
| B | 0.43 (0.17–0.78) | +0.569 | – | – |
| C | 1.32 (0.50–1.45) | -0.316 | 1.94 (1.72–3.04) | -0.944 |
| D | 1.33 (1.05–1.52) | -0.332 | 2.21 (1.83–6.53) | -1.212 |
| E | 1.00 (1.00–1.00) | +0.000 | 2.21 (1.28–6.33) | -1.209 |

## Frontier cost, requests and tokens (all; token-derived cost, not invoiced)

| Condition | Total $ | Upfront $ | Run-time $ | $/attempt | $/pass | Cold-start $/attempt (median) | Amortized $/attempt (median) | Cost reduction vs B | Extra passes per $ vs A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | +1.000 | – |
| B | $1.8496 | $0.0000 | $1.8496 | $0.0103 | $0.0106 | $0.0070 | $0.0070 | – | +42.17 |
| C | $0.5707 | $0.5707 | $0.0000 | $0.0032 | $0.0044 | $0.0070 | $0.0020 | +0.691 | +57.82 |
| D | $0.3524 | $0.3524 | $0.0000 | $0.0020 | $0.0036 | $0.0060 | $0.0020 | +0.809 | +5.68 |
| E | $0.2594 | $0.0000 | $0.2594 | $0.0014 | $0.0026 | $0.0000 | $0.0000 | +0.860 | +11.56 |

| Condition | Requests (upfront / run-time) | Failed | Missing usage | Requests/attempt | Requests/pass | Input tokens | Cached input | Output (incl. reasoning) | Reasoning | Tokens/pass | Token reduction vs B | Local calls | Local in/out tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 (0 / 0) | 0 | 0 | 0.00 | 0.00 | 0 | 0 | 0 | 0 | 0 | +1.000 | 931 | 2626693/1073418 |
| B | 571 (0 / 571) | 0 | 0 | 3.17 | 3.28 | 546374 | 152194 | 104604 | 42919 | 3741 | – | 0 | None/None |
| C | 60 (60 / 0) | 0 | 0 | 0.33 | 0.47 | 34240 | 0 | 50223 | 11488 | 655 | +0.870 | 1006 | 4802027/613108 |
| D | 60 (60 / 0) | 0 | 0 | 0.33 | 0.61 | 38440 | 0 | 27553 | 36 | 673 | +0.899 | 1006 | 3658579/1082328 |
| E | 33 (0 / 33) | 0 | 0 | 0.18 | 0.33 | 70001 | 0 | 11943 | 2849 | 828 | +0.874 | 858 | 2393183/1069530 |

A has zero frontier API spend, not zero computational cost (local inference above). Upfront guidance is counted once per artifact, not once per seed.

## Study expenditure (API ledger)

Ledger: E:\CSC2108Local\final-study\api-ledger.json. Observed frontier models: ['gpt-6.2-sol'].

| Requests | Count | States | Token-derived $ (known) | Without usage | Reservation $ |
| --- | --- | --- | --- | --- | --- |
| all | 725 | {'completed': 724, 'http_error': 1} | $3.0322 | 1 | 20.4594 |
| attributable_to_included_runs | 724 | {'completed': 724} | $3.0322 | 0 | 19.928 |
| not_attributable | 1 | {'http_error': 1} | $0.0000 | 1 | 0.5314 |

not_attributable = failed or incomplete calls, excluded or rerun runs, and requests of runs not in this report

## Historical exposure subgroups (descriptive)

| Subgroup | Tasks | Condition | Runs | Pass rate | Δ vs A (CI) |
| --- | --- | --- | --- | --- | --- |
| exposed | 28 | A | 84 | 61.9% | – |
| exposed | 28 | B | 84 | 96.4% | +0.345 [0.1786, 0.5238] |
| exposed | 28 | C | 84 | 81.0% | +0.191 [0.0714, 0.3333] |
| exposed | 28 | D | 84 | 61.9% | -0.000 [-0.0476, 0.0476] |
| exposed | 28 | E | 84 | 64.3% | +0.024 [0.0, 0.0714] |
| potentially_unseen | 32 | A | 96 | 45.8% | – |
| potentially_unseen | 32 | B | 96 | 96.9% | +0.510 [0.3438, 0.6771] |
| potentially_unseen | 32 | C | 96 | 63.5% | +0.177 [0.0729, 0.3021] |
| potentially_unseen | 32 | D | 96 | 47.9% | +0.021 [-0.0208, 0.0625] |
| potentially_unseen | 32 | E | 96 | 46.9% | +0.010 [0.0, 0.0312] |

"exposed": the agent ran on the task during development; "potentially_unseen": no recorded exposure (not verified unseen).

## Hidden-test coverage: {'40': 60} (hidden tests: tasks)

every included task has at least 40 hidden tests

## E triggered subset (descriptive)

Trigger rate: 18.3%
* triggered: 33 pairs, E 42.4% vs A 33.3%
* triggered_and_A_failed_public: 33 pairs, E 42.4% vs A 33.3%
* descriptive: selecting on whether the diagnosis triggered is not a randomized comparison

## Gap closed toward B: (X − A) / (B − A)

| Condition | Tasks | Rate | A rate | B rate | Gap closed | 95% CI | resamples without a gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 60 | 71.7% | 53.3% | 96.7% | 0.4231 | [0.2609, 0.5926] | 0 |
| D | 60 | 54.4% | 53.3% | 96.7% | 0.0256 | [-0.0471, 0.1] | 0 |
| E | 60 | 55.0% | 53.3% | 96.7% | 0.0385 | [0.0, 0.1045] | 0 |

## Seed consistency (all): tasks with every seed passing, mixed, or failing

| Condition | Tasks | All pass | Mixed | All fail | Mean seed variance p(1−p) |
| --- | --- | --- | --- | --- | --- |
| A | 60 | 29 | 5 | 26 | 0.0185 |
| B | 60 | 58 | 0 | 2 | 0.0 |
| C | 60 | 39 | 8 | 13 | 0.0296 |
| D | 60 | 30 | 5 | 25 | 0.0185 |
| E | 60 | 30 | 5 | 25 | 0.0185 |

## Frontier usage (all): tokens, and the one-off guidance cost

| Condition | Run-time tokens in/out | Upfront tokens in/out | Tokens per pass | Guidance artifacts | Upfront $ | Authoring s median (total) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0/0 | 0/0 | 0.0 | 0 | $0.0000 | – |
| B | 546374/104604 | 0/0 | 3741.3 | 0 | $0.0000 | – |
| C | 0/0 | 34240/50223 | 654.8 | 60 | $0.5707 | 9.045 (800.09) |
| D | 0/0 | 38440/27553 | 673.4 | 60 | $0.3524 | 7.26 (422.85) |
| E | 70001/11943 | 0/0 | 827.7 | 0 | $0.0000 | – |

## Sensitivity: local timeouts excluded (0 (task, seed) blocks dropped, 900 runs kept)

| Condition | Runs | Pass | Pass rate | Δ vs A | 95% CI | p (perm) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 180 | 96 | 53.3% | – | – | – |
| B | 180 | 174 | 96.7% | +0.433 | [0.3167, 0.5556] | 0.0001 |
| C | 180 | 129 | 71.7% | +0.183 | [0.1, 0.2722] | 0.0002 |
| D | 180 | 98 | 54.4% | +0.011 | [-0.0167, 0.0444] | 0.72656 |
| E | 180 | 99 | 55.0% | +0.017 | [0.0, 0.0444] | 0.5 |

## Process (all): what the local agent did

| Condition | Runs with a program | Runs truncated | First response tokens median | Local tokens median | s to first program median |
| --- | --- | --- | --- | --- | --- |
| A | 132/180 | 84 | 1124.0 | 2771.0 | 9.805 |
| B | 180/180 | 0 | – | – | – |
| C | 175/180 | 35 | 415.0 | 552.5 | 9.768 |
| D | 136/180 | 80 | 947.5 | 1697.0 | 9.076 |
| E | 132/180 | 84 | 1124.0 | 2742.5 | 9.74 |

| Paired vs A | Pairs | Δ local tokens (median) | Δ first response tokens | Δ s to first program | program only here / only in A |
| --- | --- | --- | --- | --- | --- |
| B | 180 | – | – | – | 48 / 0 |
| C | 180 | -110.5 (180) | -55.5 (180) | -0.42 (126) | 46 / 3 |
| D | 180 | +0.0 (180) | +0.0 (180) | -0.01 (117) | 18 / 14 |
| E | 180 | +0.0 (180) | +0.0 (180) | -0.01 (130) | 0 / 0 |

## Host speed (local requests)

| Host | Model | Runs | Requests | tok/s median | tok/s p10 | ≥150 s | timed out | near-limit share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Windows/AMD64/<HOST> | qwen3.5:9b | 720 | 3801 | 105.8 | 100.8 | 0 | 0 | 0.0% |

## Failure categories (all)

| Condition | hidden_pass | infrastructure | local_timeout_no_program | local_timeout_with_program | context_overflow | truncated_no_program | budget_limit | format_errors | public_pass_hidden_fail | never_passed_public | no_submission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 96 | 0 | 0 | 0 | 3 | 48 | 0 | 3 | 18 | 12 | 0 |
| B | 174 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| C | 129 | 0 | 0 | 0 | 4 | 5 | 0 | 3 | 19 | 20 | 0 |
| D | 98 | 0 | 0 | 0 | 1 | 44 | 0 | 3 | 17 | 17 | 0 |
| E | 99 | 0 | 0 | 0 | 2 | 48 | 0 | 1 | 21 | 9 | 0 |

## Transitions A -> B (180 pairs; rows: A, columns: B; A passes that B lost: 0)

| A \ B | hidden_pass | context_overflow | truncated_no_program | format_errors | public_pass_hidden_fail | never_passed_public | fixed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hidden_pass | 96 | 0 | 0 | 0 | 0 | 0 | – |
| context_overflow | 3 | 0 | 0 | 0 | 0 | 0 | 3/3 |
| truncated_no_program | 47 | 0 | 0 | 0 | 1 | 0 | 47/48 |
| format_errors | 3 | 0 | 0 | 0 | 0 | 0 | 3/3 |
| public_pass_hidden_fail | 13 | 0 | 0 | 0 | 5 | 0 | 13/18 |
| never_passed_public | 12 | 0 | 0 | 0 | 0 | 0 | 12/12 |

## Transitions A -> C (180 pairs; rows: A, columns: C; A passes that C lost: 1)

| A \ C | hidden_pass | context_overflow | truncated_no_program | format_errors | public_pass_hidden_fail | never_passed_public | fixed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hidden_pass | 95 | 0 | 0 | 0 | 0 | 1 | – |
| context_overflow | 0 | 0 | 1 | 0 | 0 | 2 | 0/3 |
| truncated_no_program | 20 | 4 | 2 | 2 | 8 | 12 | 20/48 |
| format_errors | 1 | 0 | 0 | 1 | 1 | 0 | 1/3 |
| public_pass_hidden_fail | 7 | 0 | 1 | 0 | 8 | 2 | 7/18 |
| never_passed_public | 6 | 0 | 1 | 0 | 2 | 3 | 6/12 |

## Transitions A -> D (180 pairs; rows: A, columns: D; A passes that D lost: 4)

| A \ D | hidden_pass | context_overflow | truncated_no_program | format_errors | public_pass_hidden_fail | never_passed_public | fixed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hidden_pass | 92 | 0 | 2 | 0 | 1 | 1 | – |
| context_overflow | 0 | 0 | 2 | 0 | 0 | 1 | 0/3 |
| truncated_no_program | 2 | 0 | 30 | 3 | 7 | 6 | 2/48 |
| format_errors | 2 | 0 | 1 | 0 | 0 | 0 | 2/3 |
| public_pass_hidden_fail | 1 | 0 | 5 | 0 | 8 | 4 | 1/18 |
| never_passed_public | 1 | 1 | 4 | 0 | 1 | 5 | 1/12 |

## Transitions A -> E (180 pairs; rows: A, columns: E; A passes that E lost: 0)

| A \ E | hidden_pass | context_overflow | truncated_no_program | format_errors | public_pass_hidden_fail | never_passed_public | fixed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hidden_pass | 96 | 0 | 0 | 0 | 0 | 0 | – |
| context_overflow | 0 | 0 | 0 | 0 | 0 | 3 | 0/3 |
| truncated_no_program | 0 | 0 | 48 | 0 | 0 | 0 | 0/48 |
| format_errors | 0 | 1 | 0 | 0 | 2 | 0 | 0/3 |
| public_pass_hidden_fail | 2 | 0 | 0 | 0 | 16 | 0 | 2/18 |
| never_passed_public | 1 | 1 | 0 | 1 | 3 | 6 | 1/12 |

## Outcomes (all)

* A: hidden_pass 96, never_passed_public:WA 17, never_passed_public:none 1, no_submission:agent_error 48, public_pass_hidden_fail:RE 5, public_pass_hidden_fail:TLE 4, public_pass_hidden_fail:WA 9
* B: hidden_pass 174, public_pass_hidden_fail:RE 3, public_pass_hidden_fail:WA 3
* C: hidden_pass 129, never_passed_public:RE 4, never_passed_public:WA 23, no_submission:agent_error 5, public_pass_hidden_fail:RE 3, public_pass_hidden_fail:TLE 3, public_pass_hidden_fail:WA 13
* D: hidden_pass 98, never_passed_public:WA 21, no_submission:agent_error 44, public_pass_hidden_fail:RE 4, public_pass_hidden_fail:TLE 3, public_pass_hidden_fail:WA 10
* E: hidden_pass 99, never_passed_public:WA 11, never_passed_public:none 1, no_submission:agent_error 48, public_pass_hidden_fail:RE 6, public_pass_hidden_fail:TLE 4, public_pass_hidden_fail:WA 11
