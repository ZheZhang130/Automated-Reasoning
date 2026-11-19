# Superseded tag-default experiment — not the primary comparison

This partial experiment contains 16 easy, 20 medium and one hard attempt per model. Its aggregate accuracy must not be compared directly with the full corrected primary batch, which includes 12 hard attempts per model.

Stopped deliberately at 111/144 after detecting different model-tag sampler defaults. All 111 completed trajectories and their original frozen source are preserved. Do not resume this plan with the revised source, or pool these results with the explicit common-sampler primary batch. No benchmark solution or hidden feedback was used to make the configuration correction.

# Extended local evaluation: measured comparison

Completed **111/144** planned runs; remaining **33**.

Profile `heredoc-v5-16k-t02`; 2 attempts per problem. All model calls local. No private feedback entered an agent conversation.

| Model | Official passes | Easy | Medium | Hard | Format-error runs | Context-event runs | Total agent seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 23/37 | 14/16 | 9/20 | 0/1 | 8 | 0 | 1666.8 |
| qwen2.5-coder:14b | 18/37 | 12/16 | 6/20 | 0/1 | 26 | 0 | 1327.4 |
| qwen2.5-coder:7b | 15/37 | 9/16 | 6/20 | 0/1 | 1 | 0 | 1110.9 |

qwen3.5:9b: at least one pass on 12/18 fully completed problems; every attempt passed on 11/18. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

qwen2.5-coder:14b: at least one pass on 9/18 fully completed problems; every attempt passed on 9/18. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

qwen2.5-coder:7b: at least one pass on 8/18 fully completed problems; every attempt passed on 7/18. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

## Per-problem paired outcomes

Cells show official passes/completed attempts; ? indicates unfinished work.

| Task | Date | Difficulty | qwen3.5:9b | qwen2.5-coder:14b | qwen2.5-coder:7b |
| --- | --- | --- | ---: | ---: | ---: |
| atcoder-abc400_b | 2025-04-05 | easy | 2/2 | 2/2 | 2/2 |
| leetcode-3773 | 2025-04-05 | easy | 2/2 | 0/2 | 0/2 |
| atcoder-abc400_a | 2025-04-05 | easy | 2/2 | 2/2 | 2/2 |
| leetcode-3832 | 2025-03-29 | easy | 0/2 | 0/2 | 0/2 |
| atcoder-abc399_b | 2025-03-29 | easy | 2/2 | 2/2 | 1/2 |
| leetcode-3811 | 2025-03-29 | easy | 2/2 | 2/2 | 0/2 |
| atcoder-abc399_a | 2025-03-29 | easy | 2/2 | 2/2 | 2/2 |
| leetcode-3817 | 2025-03-22 | easy | 2/2 | 2/2 | 2/2 |
| atcoder-arc195_a | 2025-03-23 | medium | 0/2 | 0/2 | 0/2 |
| leetcode-3793 | 2025-03-29 | medium | 1/2 | 0/2 | 0/2 |
| atcoder-abc398_c | 2025-03-22 | medium | 2/2 | 2/2 | 0/2 |
| leetcode-3805 | 2025-03-29 | medium | 0/2 | 0/2 | 0/2 |
| atcoder-abc398_b | 2025-03-22 | medium | 0/2 | 0/2 | 0/2 |
| leetcode-3809 | 2025-03-22 | medium | 2/2 | 2/2 | 2/2 |
| atcoder-abc397_c | 2025-03-15 | medium | 2/2 | 2/2 | 2/2 |
| leetcode-3795 | 2025-03-15 | medium | 0/2 | 0/2 | 0/2 |
| atcoder-abc397_b | 2025-03-15 | medium | 2/2 | 0/2 | 0/2 |
| leetcode-3750 | 2025-03-15 | medium | 0/2 | 0/2 | 2/2 |
| atcoder-arc196_d | 2025-04-06 | hard | 0/1 ? | 0/1 ? | 0/1 ? |
| leetcode-3777 | 2025-04-05 | hard | 0/0 ? | 0/0 ? | 0/0 ? |
| atcoder-arc196_c | 2025-04-06 | hard | 0/0 ? | 0/0 ? | 0/0 ? |
| leetcode-3784 | 2025-03-15 | hard | 0/0 ? | 0/0 ? | 0/0 ? |
| atcoder-arc195_e | 2025-03-23 | hard | 0/0 ? | 0/0 ? | 0/0 ? |
| leetcode-3789 | 2025-03-08 | hard | 0/0 ? | 0/0 ? | 0/0 ? |

## Workflow reliability and repair

| Model | Actions | Repairs | Format failures | Failed non-test commands | Public-failure runs | Public recoveries | Official passes after public failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 179 | 12 | 19 | 0 | 8 | 7 | 5 |
| qwen2.5-coder:14b | 307 | 13 | 28 | 0 | 13 | 1 | 0 |
| qwen2.5-coder:7b | 488 | 2 | 1 | 0 | 18 | 0 | 0 |

qwen3.5:9b: 5 runs executed no action; 6 had no recognized public test; 3 retained the official starter unchanged. 7 runs had a public pass but failed official evaluation. 0 preserved candidates passed despite a termination other than Submitted.

Recognized public failures for qwen3.5:9b: 15 wrong-answer events with successful candidate execution, 1 candidate runtime/compile-error events, 0 six-second timeout events, and 0 unclassified failures. These counts are events, so repeated tests of unchanged source can appear many times.

qwen2.5-coder:14b: 1 runs executed no action; 1 had no recognized public test; 0 retained the official starter unchanged. 6 runs had a public pass but failed official evaluation. 0 preserved candidates passed despite a termination other than Submitted.

Recognized public failures for qwen2.5-coder:14b: 116 wrong-answer events with successful candidate execution, 1 candidate runtime/compile-error events, 0 six-second timeout events, and 0 unclassified failures. These counts are events, so repeated tests of unchanged source can appear many times.

qwen2.5-coder:7b: 0 runs executed no action; 4 had no recognized public test; 0 retained the official starter unchanged. 2 runs had a public pass but failed official evaluation. 2 preserved candidates passed despite a termination other than Submitted.

Recognized public failures for qwen2.5-coder:7b: 159 wrong-answer events with successful candidate execution, 1 candidate runtime/compile-error events, 20 six-second timeout events, and 0 unclassified failures. These counts are events, so repeated tests of unchanged source can appear many times.

A repair is a changed candidate after a recognized public failure; repeated identical writes do not count. Public recovery requires a later passing public test. Private correctness is assessed once after termination, including preserved candidates from action/format limits. Private evaluation never informs another agent action.

## Runtime, inference and resources

| Model | Median seconds (correct / failed) | Prompt / output tokens | Generation tok/s | Full token telemetry | Max prompt | Length-limit responses | CPU-offloaded runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 14.0 / 90.6 | 401206 / 117663 | 98.3 | 37/37 | 6652 | 19 | 0 |
| qwen2.5-coder:14b | 12.8 / 41.9 | 676512 / 51655 | 65.1 | 37/37 | 8417 | 3 | 0 |
| qwen2.5-coder:7b | 10.6 / 30.5 | 1045336 / 54859 | 125.3 | 37/37 | 10431 | 0 | 0 |

qwen3.5:9b termination counts: `{"ActionLimit": 2, "RepeatedFormatError": 5, "Submitted": 30}`; official statuses: `{"candidate_failure": 12, "missing_submission": 2, "pass": 23}`. Platform passes: `{"atcoder": {"completed": 19, "passed": 14}, "leetcode": {"completed": 18, "passed": 9}}`.

Total prefill/generation/load seconds: 32.9 / 1197.5 / 119.3. Including failed attempts, output tokens per official pass: 5115.8; agent seconds per official pass: 72.5. Residency snapshots available for 37/37 runs.

qwen2.5-coder:14b termination counts: `{"ActionLimit": 11, "RepairLimit": 1, "RepeatedFormatError": 1, "Submitted": 24}`; official statuses: `{"candidate_failure": 18, "missing_submission": 1, "pass": 18}`. Platform passes: `{"atcoder": {"completed": 19, "passed": 12}, "leetcode": {"completed": 18, "passed": 6}}`.

Total prefill/generation/load seconds: 22.9 / 793.2 / 110.9. Including failed attempts, output tokens per official pass: 2869.7; agent seconds per official pass: 73.7. Residency snapshots available for 37/37 runs.

qwen2.5-coder:7b termination counts: `{"ActionLimit": 22, "Submitted": 15}`; official statuses: `{"candidate_failure": 22, "pass": 15}`. Platform passes: `{"atcoder": {"completed": 19, "passed": 9}, "leetcode": {"completed": 18, "passed": 6}}`.

Total prefill/generation/load seconds: 17.3 / 437.9 / 82.4. Including failed attempts, output tokens per official pass: 3657.3; agent seconds per official pass: 74.1. Residency snapshots available for 37/37 runs.

Agent runtime includes setup, cold model load and public execution; it excludes private judging. Tokens and generation throughput use raw Ollama counts/durations, not wall-clock agent time. Prompt-evaluation counts may reflect cache reuse and are not a count of unique task tokens. Residency comes from post-run allocation snapshots, not continuous peak monitoring. No foreign model workload was permitted at run startup; this is a desktop machine, not a dedicated latency lab.

## Paired uncertainty

Bootstrap intervals resample the 24 problem clusters (both repetitions kept together), 10,000 draws, seed 2108. These descriptive intervals assume exchangeable problems despite purposive selection. They cannot establish generalization to unseen contests.

| Model | Accuracy | Problem bootstrap 95% interval | Identical candidate pairs |
| --- | ---: | --- | ---: |
| qwen3.5:9b | 62.2% | 41.7% to 83.3% | 1/17 |
| qwen2.5-coder:14b | 48.6% | 27.8% to 72.2% | 5/18 |
| qwen2.5-coder:7b | 40.5% | 19.4% to 63.9% | 6/18 |

qwen3.5:9b minus qwen2.5-coder:14b: mean per-problem accuracy difference 0.1388888888888889; bootstrap 95% interval [0.0, 0.3055555555555556]; 18 paired problems. At-least-one-success discordants 3 versus 0; exploratory two-sided exact p=0.25. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

qwen3.5:9b minus qwen2.5-coder:7b: mean per-problem accuracy difference 0.2222222222222222; bootstrap 95% interval [0.0, 0.4444444444444444]; 18 paired problems. At-least-one-success discordants 5 versus 1; exploratory two-sided exact p=0.2188. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

qwen2.5-coder:14b minus qwen2.5-coder:7b: mean per-problem accuracy difference 0.08333333333333333; bootstrap 95% interval [-0.1111111111111111, 0.2777777777777778]; 18 paired problems. At-least-one-success discordants 2 versus 1; exploratory two-sided exact p=1. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

## Representative trajectories

Examples are selected deterministically as the first completed run matching each diagnostic category in schedule order. They illustrate observed behavior rather than establish causes. No candidate source, private input or expected answer is reproduced.

| Diagnostic | Task | Model | Repetition | Agent stop | Official status | Actions | Format errors |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| No action after format failures | leetcode-3832 | qwen3.5:9b | 1 | RepeatedFormatError | candidate_failure | 0 | 3 |
| Public pass / official failure | atcoder-arc195_a | qwen2.5-coder:7b | 2 | Submitted | candidate_failure | 3 | 0 |
| Correct candidate / unfinished workflow | atcoder-abc397_c | qwen2.5-coder:7b | 1 | ActionLimit | pass | 20 | 0 |
| Missing candidate | atcoder-arc195_a | qwen3.5:9b | 1 | RepeatedFormatError | missing_submission | 0 | 3 |
| Officially correct after public failure | leetcode-3773 | qwen3.5:9b | 1 | Submitted | pass | 5 | 0 |

## Recommendation and uncertainty

Provisional default: **qwen3.5:9b** under the measured `heredoc-v5-16k-t02` configuration, prioritizing official correctness. Reliability and runtime are secondary; short unsuccessful runs do not establish efficiency.

The two attempts use fresh environments with seeds 2108/2109 and temperature 0.2. Shared tasks, prompts and potentially identical candidates make them dependent. Do not treat 48 attempts as 48 independent problems.

This is a purposive 24-problem infrastructure/capability study, not a statistically conclusive population ranking. The newest compatible official slice dates from 2025; model-training contamination cannot be ruled out. Problems from the same contest may also be correlated. Hard-task and platform subgroups are small. Context truncation, execution budgets, public-feedback semantics and workflow compliance remain potential confounders. More fresh tasks and repeated trials are needed before a broad scientific claim.

The old three-problem pilot and this 24-problem set do not overlap and use different configurations. Their aggregate accuracies are not a controlled scaffold ablation. The development set is also small and selected for interface/repair diagnostics; it does not establish an optimal configuration. The thinking-enabled 9B result is development-only, not an alternate configuration mixed into this primary table.

Difficulty labels come from the dataset and are not independently calibrated across platforms. This benchmark measures standalone Python programming through mini-SWE-agent. Repository bug repair, multi-file changes and frontier-guided interventions require separate evaluation before transferring this operational recommendation to those settings.

Raw private evaluator details and reference audits stay on E: outside agent-visible bundles and Git. `metrics.csv` and `analysis.json` contain complete numerical metrics; trajectories, raw Ollama responses and context logs are retained per attempt.

Compared with qwen2.5-coder:14b, qwen3.5:9b produced 5 additional official passes across 37 attempts per model. It had 8 runs with format errors versus 26; median time on correct runs was 14.0 versus 12.8 seconds. The operational choice follows the observed correctness lead, with these reliability/runtime tradeoffs retained explicitly.

Compared with qwen2.5-coder:7b, qwen3.5:9b produced 8 additional official passes across 37 attempts per model. It had 8 runs with format errors versus 1; median time on correct runs was 14.0 versus 10.6 seconds. The operational choice follows the observed correctness lead, with these reliability/runtime tradeoffs retained explicitly.
