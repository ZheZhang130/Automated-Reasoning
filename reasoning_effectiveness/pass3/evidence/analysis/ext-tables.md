# Pass-3 extended benchmark tables (generated)

Complete (task, seed) blocks: 24; excluded blocks (infrastructure): none. Cells: hidden ✓/✗, hidden cases passed, T = length truncations; E: trig/untrig.

## Seed 2108

| # | Task | A | C | D | E |
| --- | --- | --- | --- | --- | --- |
| 1 | abc397_e | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 2 | abc388_f | ✗ none (3T) | ✗ none (3T) | ✗ 38/40 (1T) | ✗ none (3T, untrig) |
| 3 | abc395_f | ✓ 40/40 (1T) | ✓ 40/40 | ✗ none (3T) | ✓ 40/40 (1T, trig) |
| 4 | abc389_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 5 | abc397_f | ✗ none (3T) | ✗ 0/40 (1T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 6 | abc391_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 7 | abc390_f | ✗ 8/40 (5T) | ✓ 40/40 (1T) | ✗ 2/40 (1T) | ✗ 13/40 (1T, trig) |
| 8 | arc193_a | ✗ none (3T) | ✗ none (3T) | ✗ 18/40 (2T) | ✗ none (3T, untrig) |
| 9 | arc193_b | ✗ none (3T) | ✓ 40/40 | ✗ 1/40 (2T) | ✗ none (3T, untrig) |
| 10 | arc195_d | ✗ none (3T) | ✗ 0/1 (2T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 11 | arc194_e | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 12 | arc190_c | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |

## Seed 2109

| # | Task | A | C | D | E |
| --- | --- | --- | --- | --- | --- |
| 1 | abc397_e | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 2 | abc388_f | ✗ 21/40 (1T) | ✗ none (3T) | ✗ 38/40 (1T) | ✗ 38/40 (1T, trig) |
| 3 | abc395_f | ✗ 34/40 (2T) | ✓ 40/40 | ✗ 0/40 (2T) | ✓ 40/40 (2T, trig) |
| 4 | abc389_f | ✗ none (3T) | ✓ 40/40 (1T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 5 | abc397_f | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 6 | abc391_f | ✗ none (3T) | ✓ 40/40 (1T) | ✗ 0/40 (3T) | ✗ none (3T, untrig) |
| 7 | abc390_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 8 | arc193_a | ✗ 4/40 (1T) | ✓ 40/40 | ✗ none (3T) | ✓ 40/40 (1T, trig) |
| 9 | arc193_b | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 10 | arc195_d | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 11 | arc194_e | ✓ 40/40 (1T) | ✗ none (3T) | ✗ none (3T) | ✓ 40/40 (1T, untrig) |
| 12 | arc190_c | ✗ 0/40 (2T) | ✗ 0/40 (1T) | ✗ none (3T) | ✗ 34/40 (2T, trig) |

## Accuracy

| Condition | seed 2108 | seed 2109 | pooled |
| --- | --- | --- | --- |
| A | 1/12 | 1/12 | 2/24 |
| C | 6/12 | 7/12 | 13/24 |
| D | 0/12 | 0/12 | 0/24 |
| E | 1/12 | 3/12 | 4/24 |

## Paired comparisons (unit: task × seed)

| Comparison | pairs | gains | harms | both pass | both fail | mean diff | task-cluster 95% | sign test (tasks) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C vs A | 24 | 12 ['abc397_e@2108', 'abc397_e@2109', 'abc395_f@2109', 'abc389_f@2108', 'abc389_f@2109', 'abc391_f@2108', 'abc391_f@2109', 'abc390_f@2108', 'abc390_f@2109', 'arc193_a@2109', 'arc193_b@2108', 'arc193_b@2109'] | 1 ['arc194_e@2109'] | 1 | 10 | 0.458 | (0.167, 0.75) | 7+/1- p=0.0703 |
| D vs A | 24 | 0 [] | 2 ['abc395_f@2108', 'arc194_e@2109'] | 0 | 22 | -0.083 | (-0.208, 0.0) | 0+/2- p=0.5 |
| E vs A | 24 | 2 ['abc395_f@2109', 'arc193_a@2109'] | 0 [] | 2 | 20 | 0.083 | (0.0, 0.208) | 2+/0- p=0.5 |
| C vs D | 24 | 13 ['abc397_e@2108', 'abc397_e@2109', 'abc395_f@2108', 'abc395_f@2109', 'abc389_f@2108', 'abc389_f@2109', 'abc391_f@2108', 'abc391_f@2109', 'abc390_f@2108', 'abc390_f@2109', 'arc193_a@2109', 'arc193_b@2108', 'arc193_b@2109'] | 0 [] | 0 | 11 | 0.542 | (0.25, 0.833) | 7+/0- p=0.0156 |
| C vs E | 24 | 10 ['abc397_e@2108', 'abc397_e@2109', 'abc389_f@2108', 'abc389_f@2109', 'abc391_f@2108', 'abc391_f@2109', 'abc390_f@2108', 'abc390_f@2109', 'arc193_b@2108', 'arc193_b@2109'] | 1 ['arc194_e@2109'] | 3 | 10 | 0.375 | (0.083, 0.667) | 5+/1- p=0.2188 |
| D vs E | 24 | 0 [] | 4 ['abc395_f@2108', 'abc395_f@2109', 'arc193_a@2109', 'arc194_e@2109'] | 0 | 20 | -0.167 | (-0.375, 0.0) | 0+/3- p=0.25 |

## Resources and behaviour (sums over complete blocks)

| Condition | candidate | submitted | public pass | runs w/ trunc | truncations | format errors | calls | completion tokens | median tokens | local s | wall s | frontier wait s | manual self-checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 7 | 1 | 1 | 24 | 64 | 64 | 178 | 313160 | 12288 | 3421.3 | 3437.7 | 0 | 0 |
| C | 16 | 14 | 14 | 14 | 31 | 31 | 121 | 165000 | 10421 | 1929.8 | 1946.4 | 0 | 5 |
| D | 7 | 3 | 3 | 24 | 63 | 63 | 139 | 303947 | 12288 | 3315.7 | 3332.2 | 0 | 5 |
| E | 7 | 6 | 6 | 24 | 60 | 60 | 106 | 277558 | 12288 | 2997.3 | 3093.0 | 78.9 | 0 |

## Failure categories

* A: {'no_program_truncation': 17, 'partial_RE+TLE+WA': 1, 'pass': 2, 'partial_WA': 3, 'wrong_everywhere': 1}
* C: {'pass': 13, 'no_program_truncation': 8, 'wrong_everywhere': 3}
* D: {'no_program_truncation': 17, 'partial_RE+TLE': 2, 'wrong_everywhere': 2, 'partial_WA': 3}
* E: {'no_program_truncation': 17, 'partial_RE+TLE': 1, 'pass': 4, 'partial_WA': 1, 'tle_only': 1}

## Condition E

```
{
 "assigned": 24,
 "triggered": 6,
 "requested": 6,
 "delivered": 6,
 "errors": {},
 "untriggered_reasons": {
  "no_public_test": 17,
  "no_qualifying_failure": 1
 },
 "changed_after": 6,
 "public_pass_after": 5,
 "hidden_pass_triggered": 3,
 "triggered_where_A_failed": 5,
 "recovered_where_A_failed": 2,
 "wait_seconds": [
  13.875,
  15.438,
  12.782,
  13.578,
  12.032,
  11.234
 ]
}
```

## Seed consistency

```
{
 "A": {
  "tasks_with_identical_outcome_across_seeds": 10,
  "tasks_with_both_seeds": 12
 },
 "C": {
  "tasks_with_identical_outcome_across_seeds": 11,
  "tasks_with_both_seeds": 12
 },
 "D": {
  "tasks_with_identical_outcome_across_seeds": 12,
  "tasks_with_both_seeds": 12
 },
 "E": {
  "tasks_with_identical_outcome_across_seeds": 10,
  "tasks_with_both_seeds": 12
 }
}
```
