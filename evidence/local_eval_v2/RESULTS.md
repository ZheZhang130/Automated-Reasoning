# Extended local evaluation: measured comparison

Completed **144/144** planned runs; remaining **0**.

Profile `heredoc-v6-16k-common`; 2 attempts per problem. All model calls local. No private feedback entered an agent conversation.

Per-attempt limits: 20 executed actions, 3 repair cycles, 600 agent seconds; context 16384, response ceiling 4096 tokens. T=0.2. Seeds 2108/2109; Qwen3.5 thinking disabled in the primary comparison.

Protocol, commands and full provenance: [README](README.md). Prior-system audit: [AUDIT](AUDIT.md). Configuration experiments: [DEVELOPMENT](DEVELOPMENT.md). Configuration history and sampler correction: [DECISION](DECISION.md).

| Model | Official passes | Easy | Medium | Hard | Format-error runs | Context-event runs | Total agent seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 23/48 | 14/16 | 9/20 | 0/12 | 20 | 2 | 3727.5 |
| qwen2.5-coder:14b | 18/48 | 12/16 | 6/20 | 0/12 | 31 | 0 | 2146.2 |
| qwen2.5-coder:7b | 15/48 | 9/16 | 6/20 | 0/12 | 3 | 0 | 1647.4 |

qwen3.5:9b: at least one pass on 12/24 fully completed problems; every attempt passed on 11/24. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

qwen2.5-coder:14b: at least one pass on 9/24 fully completed problems; every attempt passed on 9/24. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

qwen2.5-coder:7b: at least one pass on 8/24 fully completed problems; every attempt passed on 7/24. These are empirical coverage counts, not independent repetitions or a population pass@k guarantee.

Hardware at freeze: NVIDIA GeForce RTX 4080 SUPER, 16376 MiB GPU memory, driver 610.88. All three model tags use Q4_K_M weights. Official evaluator and dataset revisions, model digests and Docker image IDs are recorded in the frozen plan; the primary source is also archived by hash.

Software at freeze: Ollama 0.40.16; mini-SWE-agent 2.4.6; LiteLLM 1.81.16; Python 3.11.9. The full installed package map is retained in the plan.

Explicit common sampler options: `{"frequency_penalty": 0.0, "min_p": 0.0, "presence_penalty": 0.0, "repeat_last_n": 64, "repeat_penalty": 1.0, "top_k": 40, "top_p": 0.9}`.

Actual request bodies are retained per attempt. Sampler verification counts: qwen3.5:9b 48/48; qwen2.5-coder:14b 48/48; qwen2.5-coder:7b 48/48.

An earlier tag-default batch was stopped at 111 after discovering unequal model-tag overrides. Those observations are archived separately in TAG_DEFAULT_RESULTS.md and are not pooled here. This configuration correction followed metadata inspection; no previous candidate or private feedback was supplied to the agents. The frozen 24-task set was retained, so it is not claimed to be newly unseen in this corrected run.

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
| atcoder-abc398_b | 2025-03-22 | medium | 2/2 | 0/2 | 0/2 |
| leetcode-3809 | 2025-03-22 | medium | 2/2 | 2/2 | 2/2 |
| atcoder-abc397_c | 2025-03-15 | medium | 2/2 | 2/2 | 2/2 |
| leetcode-3795 | 2025-03-15 | medium | 0/2 | 0/2 | 0/2 |
| atcoder-abc397_b | 2025-03-15 | medium | 0/2 | 0/2 | 0/2 |
| leetcode-3750 | 2025-03-15 | medium | 0/2 | 0/2 | 2/2 |
| atcoder-arc196_d | 2025-04-06 | hard | 0/2 | 0/2 | 0/2 |
| leetcode-3777 | 2025-04-05 | hard | 0/2 | 0/2 | 0/2 |
| atcoder-arc196_c | 2025-04-06 | hard | 0/2 | 0/2 | 0/2 |
| leetcode-3784 | 2025-03-15 | hard | 0/2 | 0/2 | 0/2 |
| atcoder-arc195_e | 2025-03-23 | hard | 0/2 | 0/2 | 0/2 |
| leetcode-3789 | 2025-03-08 | hard | 0/2 | 0/2 | 0/2 |

## Workflow reliability and repair

| Model | Actions | Repairs | Format failures | Failed non-test commands | Public-failure runs | Public recoveries | Official passes after public failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 236 | 12 | 56 | 0 | 8 | 4 | 1 |
| qwen2.5-coder:14b | 443 | 13 | 33 | 1 | 20 | 1 | 0 |
| qwen2.5-coder:7b | 708 | 5 | 3 | 0 | 24 | 0 | 0 |

qwen3.5:9b: runs with zero actions: 12; runs without a recognized public test: 15; unchanged official starters: 4. Public passes followed by official failure: 6. Correct preserved candidates with a termination other than Submitted: 0.

Recognized public-test failure events for qwen3.5:9b: wrong answer after successful candidate execution: 18; candidate runtime or compile error: 3; six-second timeout: 0; unclassified: 0. These counts include repeated tests of unchanged source.

qwen2.5-coder:14b: runs with zero actions: 1; runs without a recognized public test: 1; unchanged official starters: 0. Public passes followed by official failure: 10. Correct preserved candidates with a termination other than Submitted: 0.

Recognized public-test failure events for qwen2.5-coder:14b: wrong answer after successful candidate execution: 166; candidate runtime or compile error: 2; six-second timeout: 10; unclassified: 0. These counts include repeated tests of unchanged source.

qwen2.5-coder:7b: runs with zero actions: 0; runs without a recognized public test: 9; unchanged official starters: 0. Public passes followed by official failure: 2. Correct preserved candidates with a termination other than Submitted: 2.

Recognized public-test failure events for qwen2.5-coder:7b: wrong answer after successful candidate execution: 215; candidate runtime or compile error: 1; six-second timeout: 20; unclassified: 0. These counts include repeated tests of unchanged source.

A repair is a changed candidate after a recognized public failure; repeated identical writes do not count. Public recovery requires a later passing public test. Private correctness is assessed once after termination, including preserved candidates from action/format limits. Private evaluation never informs another agent action.

## Runtime, inference and resources

| Model | Median seconds (correct / failed) | Prompt / output tokens | Generation tok/s | Full token telemetry | Max prompt | Length-limit responses | CPU-offloaded runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 12.9 / 137.0 | 1013509 / 299459 | 99.8 | 48/48 | 15902 | 56 | 0 |
| qwen2.5-coder:14b | 12.6 / 55.6 | 1068949 / 78625 | 63.5 | 48/48 | 8417 | 4 | 0 |
| qwen2.5-coder:7b | 10.6 / 33.2 | 1609120 / 90044 | 120.1 | 48/48 | 11007 | 1 | 0 |

qwen3.5:9b termination counts: `{"ActionLimit": 4, "RepairLimit": 1, "RepeatedFormatError": 14, "Submitted": 29}`; official statuses: `{"candidate_failure": 17, "missing_submission": 8, "pass": 23}`. Platform passes: `{"atcoder": {"completed": 24, "passed": 14}, "leetcode": {"completed": 24, "passed": 9}}`.

Total prefill/generation/load seconds: 62.1 / 2999.3 / 157.0. Including failed attempts, output tokens per official pass: 13020.0; agent seconds per official pass: 162.1. Residency snapshots available for 48/48 runs.

qwen2.5-coder:14b termination counts: `{"ActionLimit": 17, "RepairLimit": 1, "RepeatedFormatError": 1, "Submitted": 29}`; official statuses: `{"candidate_failure": 29, "missing_submission": 1, "pass": 18}`. Platform passes: `{"atcoder": {"completed": 24, "passed": 12}, "leetcode": {"completed": 24, "passed": 6}}`.

Total prefill/generation/load seconds: 33.7 / 1238.9 / 148.7. Including failed attempts, output tokens per official pass: 4368.1; agent seconds per official pass: 119.2. Residency snapshots available for 48/48 runs.

qwen2.5-coder:7b termination counts: `{"ActionLimit": 33, "Submitted": 15}`; official statuses: `{"candidate_failure": 33, "pass": 15}`. Platform passes: `{"atcoder": {"completed": 24, "passed": 9}, "leetcode": {"completed": 24, "passed": 6}}`.

Total prefill/generation/load seconds: 23.4 / 749.6 / 109.7. Including failed attempts, output tokens per official pass: 6002.9; agent seconds per official pass: 109.8. Residency snapshots available for 48/48 runs.

Agent runtime includes setup, cold model load and public execution; it excludes private judging. Tokens and generation throughput use raw Ollama counts/durations, not wall-clock agent time. Prompt-evaluation counts may reflect cache reuse and are not a count of unique task tokens. Residency comes from post-run allocation snapshots, not continuous peak monitoring. No foreign model workload was permitted at run startup; this is a desktop machine, not a dedicated latency lab.

## Paired uncertainty

Bootstrap intervals resample fully completed problem clusters (24 in the full plan, both repetitions kept together), 10,000 draws, seed 2108. Coverage counts above show the number available for each model. These descriptive intervals assume exchangeable problems despite purposive selection. They cannot establish generalization to unseen contests.

| Model | Accuracy | Problem bootstrap 95% interval | Identical candidate pairs |
| --- | ---: | --- | ---: |
| qwen3.5:9b | 47.9% | 29.2% to 66.7% | 1/19 |
| qwen2.5-coder:14b | 37.5% | 20.8% to 58.3% | 6/23 |
| qwen2.5-coder:7b | 31.2% | 14.6% to 50.0% | 8/24 |

qwen3.5:9b minus qwen2.5-coder:14b: mean per-problem accuracy difference 0.10416666666666667; bootstrap 95% interval [0.0, 0.22916666666666666]; 24 paired problems. At-least-one-success discordants 3 versus 0; exploratory two-sided exact p=0.25. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

qwen3.5:9b minus qwen2.5-coder:7b: mean per-problem accuracy difference 0.16666666666666666; bootstrap 95% interval [0.0, 0.3541666666666667]; 24 paired problems. At-least-one-success discordants 5 versus 1; exploratory two-sided exact p=0.2188. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

qwen2.5-coder:14b minus qwen2.5-coder:7b: mean per-problem accuracy difference 0.0625; bootstrap 95% interval [-0.08333333333333333, 0.20833333333333334]; 24 paired problems. At-least-one-success discordants 2 versus 1; exploratory two-sided exact p=1. This p-value tests the binary any-success outcome, is unadjusted for three comparisons, and does not test the mean accuracy difference.

## Representative trajectories

Examples are selected deterministically as the first completed run matching each diagnostic category in schedule order. They illustrate observed behavior rather than establish causes. No candidate source, private input or expected answer is reproduced.

| Diagnostic | Task | Model | Repetition | Agent stop | Official status | Actions | Format errors |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| No action after format failures | leetcode-3832 | qwen3.5:9b | 2 | RepeatedFormatError | candidate_failure | 0 | 3 |
| Public pass / official failure | atcoder-arc195_a | qwen3.5:9b | 1 | Submitted | candidate_failure | 5 | 0 |
| Correct candidate / unfinished workflow | atcoder-abc397_c | qwen2.5-coder:7b | 1 | ActionLimit | pass | 20 | 0 |
| Missing candidate | atcoder-arc195_a | qwen3.5:9b | 2 | RepeatedFormatError | missing_submission | 0 | 3 |
| Officially correct after public failure | leetcode-3809 | qwen3.5:9b | 1 | Submitted | pass | 8 | 0 |

## Recommendation and uncertainty

Primary operational recommendation: **qwen3.5:9b** under the measured `heredoc-v6-16k-common` configuration, prioritizing official correctness. Reliability and runtime are secondary; short unsuccessful runs do not establish efficiency.


On the same 48 attempts per model, qwen3.5:9b passed 23 and qwen2.5-coder:14b passed 18. Format-error runs were 20 versus 31; median time on correct runs was 12.9 versus 12.6 seconds. qwen2.5-coder:14b solved 0 fully paired problems on which the recommended model had no pass. The choice prioritizes observed correctness while retaining these reliability, runtime and task-coverage tradeoffs.

On the same 48 attempts per model, qwen3.5:9b passed 23 and qwen2.5-coder:7b passed 15. Format-error runs were 20 versus 3; median time on correct runs was 12.9 versus 10.6 seconds. qwen2.5-coder:7b solved 1 fully paired problem on which the recommended model had no pass. The choice prioritizes observed correctness while retaining these reliability, runtime and task-coverage tradeoffs.

The recommendation carries substantial failure costs: 14 repeated-format terminations, 8 missing candidates and 56 length-limited responses. Its total agent time was 62.1 minutes. Including failed runs, agent seconds per official pass were 162.1; the other models' values are reported above. The observed correctness lead does not imply reliable completion on every task.

No model passed any of the 36 completed hard-task attempts. The observed correctness advantage comes from easy/medium problems. Hard-task performance needs additional configuration research and fresh evaluation; these failures do not establish capability under other workflows or budgets.

The two attempts use fresh environments with seeds 2108/2109 and temperature 0.2. Shared tasks, prompts and potentially identical candidates make them dependent. Do not treat 48 attempts as 48 independent problems.

This is a purposive 24-problem infrastructure/capability study, not a statistically conclusive population ranking. The newest compatible official slice dates from 2025; model-training contamination cannot be ruled out. Problems from the same contest may also be correlated. Hard-task and platform subgroups are small. Context truncation, execution budgets, public-feedback semantics and workflow compliance remain potential confounders. More fresh tasks and repeated trials are needed before a broad scientific claim.

The old three-problem pilot and this 24-problem set do not overlap and use different configurations. Their aggregate accuracies are not a controlled scaffold ablation. The development set is also small and selected for interface/repair diagnostics; it does not establish an optimal configuration. The thinking-enabled 9B result is development-only, not an alternate configuration mixed into this primary table.

Difficulty labels come from the dataset and are not independently calibrated across platforms. This benchmark measures standalone Python programming through mini-SWE-agent. Repository bug repair, multi-file changes and frontier-guided interventions require separate evaluation before transferring this operational recommendation to those settings.

Raw private evaluator details and reference audits stay on E: outside agent-visible bundles and Git. `metrics.csv` and `analysis.json` contain complete numerical metrics; trajectories, raw Ollama responses and context logs are retained per attempt.
