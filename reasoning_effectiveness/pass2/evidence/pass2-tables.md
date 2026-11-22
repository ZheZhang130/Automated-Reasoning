# Pass-2 tables (generated)

Cells: ✓/✗ hidden pass, hidden cases passed, then format errors (fmt), actions and manual self-checks. Pass-1 columns are the pass-1 runs at the same seed (2108) on the same frozen agent.

### Development: contract versions (seed 2108)

| Task | A (pass 1) | C plan-v1 (pass 1) | D-v1 (pass 1) | D-v1 Codex (pass 2) | D-v3 Codex (pass 2) |
| --- | --- | --- | --- | --- | --- |
| arc192_a | ✗ no program (3 fmt, 0 act) | ✓ 40/40 (3 act) | ✗ 20/40 (2 fmt, 4 act) | — | ✗ no program (3 fmt, 0 act) |
| arc195_a | ✗ 39/40 (2 fmt, 16 act) | ✓ 40/40 (7 act) | ✗ no program (3 fmt, 0 act) | — | ✗ no program (3 fmt, 0 act) |
| abc393_d | ✗ 9/40 (2 fmt, 11 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) |
| abc394_c | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (1 fmt, 3 act) | — | ✗ 39/40 (1 fmt, 20 act) |
| abc390_c | ✓ 40/40 (5 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | — | ✓ 40/40 (3 act) |
| abc388_g | ✗ no program (3 fmt, 0 act) | ✓ 40/40 (3 act) | ✗ no program (3 fmt, 0 act) | — | ✗ no program (3 fmt, 0 act) |
| abc391_e | ✗ no program (3 fmt, 0 act) | ✗ 5/40 (1 fmt, 20 act) | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) |
| abc391_a | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | — | ✓ 40/40 (3 act) |

### Development: E (seed 2108)

| Task | A (pass 1) | E-v1 Codex | E-v1 API |
| --- | --- | --- | --- |
| arc195_a | ✗ 39/40 (2 fmt, 16 act) | ✗ 39/40 (1 fmt, 19 act) | ✗ 39/40 (2 fmt, 5 act) |
| abc393_d | ✗ 9/40 (2 fmt, 11 act) | ✓ 40/40 (5 act) | ✓ 40/40 (5 act) |
| abc390_c | ✓ 40/40 (5 act) | ✓ 40/40 (5 act) | — |
| arc192_a | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) | — |

### E mechanism details

| Run | trigger | at action | local s left | wait s | delivered | actions after | public tests after | changed | public pass after | hidden |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abc390_c | True | 2 | 586.03 | 12.782 | True | 3 | 1 | True | True | pass |
| abc393_d | True | 2 | 580.5 | 8.141 | True | 3 | 1 | True | True | pass |
| arc192_a | False | None | None | 0.0 | False | None | None | None | None | missing_submission |
| arc195_a | True | 2 | 548.34 | 8.281 | True | 17 | 7 | True | False | candidate_failure |
| abc393_d (API) | True | 2 | 580.59 | 4.907 | True | 3 | 1 | True | True | pass |
| arc195_a (API) | True | 2 | 547.97 | 5.718 | True | 3 | 1 | True | True | candidate_failure |
| abc388_e | False | None | None | 0.0 | False | None | None | None | None | missing_submission |
| abc394_b | False | None | None | 0.0 | False | None | None | None | None | pass |
| abc396_f | False | None | None | 0.0 | False | None | None | None | None | missing_submission |
| abc398_d | True | 2 | 547.01 | 9.078 | True | 9 | 4 | True | True | candidate_failure |
| abc399_f | False | None | None | 0.0 | False | None | None | None | None | pass |

### Validation (fresh, outcome-blind; Codex guidance; seed 2108)

| Task | A | C plan-v1 | D-v1 | D-v3 | E-v1 |
| --- | --- | --- | --- | --- | --- |
| abc394_b | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) |
| abc388_e | ✗ no program (3 fmt, 0 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✗ 31/40 (3 act) | ✗ no program (3 fmt, 0 act) |
| abc396_f | ✗ no program (3 fmt, 0 act) | ✗ 5/40 (1 fmt, 17 act) | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) |
| abc398_d | ✗ 36/40 (1 fmt, 5 act) | ✓ 40/40 (3 act) | ✗ 36/40 (3 act) | ✗ 36/40 (5 act) | ✗ 36/40 (1 fmt, 11 act) |
| abc399_f | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✗ 0/40 (15 act) | ✗ 20/40 (10 act) | ✓ 40/40 (3 act) |

### Development, second seed (2109)

| Task | A s2109 | E-v1 Codex s2109 | D-v3 Codex s2109 |
| --- | --- | --- | --- |
| abc393_d | ✓ 40/40 (1 fmt, 3 act) | ✓ 40/40 (1 fmt, 3 act) | ✓ 40/40 (11 act) |
| abc390_c | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (1 fmt, 3 act) |
| abc394_c | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) |
| arc195_a | ✓ 40/40 (2 fmt, 9 act) | ✓ 40/40 (2 fmt, 5 act) | ✗ 37/40 (1 fmt, 20 act) |

### Direct-API comparison at the same frozen states (seed 2108)

| Task | A | E Codex | E API | D-v3 Codex | D-v3 API |
| --- | --- | --- | --- | --- | --- |
| abc398_d | ✗ 36/40 (1 fmt, 5 act) | ✗ 36/40 (1 fmt, 11 act) | ✗ 36/40 (2 fmt, 5 act) | ✗ 36/40 (5 act) | — |
| abc399_f | ✓ 40/40 (3 act) | ✓ 40/40 (3 act) | — | ✗ 20/40 (10 act) | ✗ 1/40 (14 act) |
| abc388_e | ✗ no program (3 fmt, 0 act) | ✗ no program (3 fmt, 0 act) | — | ✗ 31/40 (3 act) | ✗ no program (3 fmt, 0 act) |

### E mechanism details (second seed and API validation)

| Run | trigger | at action | wait s | delivered | actions after | public pass after | hidden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| abc390_c s2109 | False | None | 0.0 | False | None | None | pass |
| abc393_d s2109 | False | None | 0.0 | False | None | None | pass |
| abc394_c s2109 | False | None | 0.0 | False | None | None | pass |
| arc195_a s2109 | True | 2 | 8.375 | True | 3 | True | pass |
| abc398_d api | True | 2 | 4.438 | True | 3 | True | candidate_failure |

### Resources by condition (pass-2 runs)

| Cohort / condition | runs | hidden pass | completion tokens | format errors | local s (net) | frontier wait s |
| --- | --- | --- | --- | --- | --- | --- |
| dev-e E | 4 | 2 | 28087 | 4 | 353.0 | 29.2 |
| dev-e-api E/api | 2 | 1 | 10392 | 2 | 130.6 | 10.6 |
| dev-d A | 2 | 0 | 22715 | 4 | 265.6 | 0 |
| dev-d D/v1codex | 2 | 1 | 13741 | 3 | 154.6 | 0 |
| dev-d D/v3 | 8 | 3 | 52739 | 13 | 608.2 | 0 |
| val A | 5 | 2 | 30876 | 7 | 352.2 | 0 |
| val C | 5 | 4 | 8832 | 1 | 334.2 | 0 |
| val D/v1 | 5 | 2 | 26583 | 3 | 332.3 | 0 |
| val D/v3 | 5 | 1 | 26022 | 3 | 319.6 | 0 |
| val E | 5 | 2 | 37095 | 7 | 423.0 | 9.1 |
| dev-s2109 A/s2109 | 3 | 3 | 6203 | 1 | 92.6 | 0 |
| dev-s2109 D/v3-s2109 | 4 | 3 | 12001 | 2 | 177.9 | 0 |
| dev-s2109 E/s2109 | 4 | 4 | 15829 | 3 | 205.7 | 8.4 |
| val-api D/v3-api | 2 | 0 | 20895 | 3 | 243.4 | 0 |
| val-api E/api | 1 | 0 | 9556 | 2 | 110.8 | 4.4 |
