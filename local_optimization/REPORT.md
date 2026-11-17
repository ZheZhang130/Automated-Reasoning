# Qwen3.5 9B local coding-agent optimization

**Status: configuration selection complete; frozen held-out validation running.** Across 12 selection problems and two seeds, the presence/window1024 challenger passes 10/24 versus control 8/24, using 1,687.8 versus 2,073.2 agent seconds and 133,405 versus 171,860 output tokens. The paired accuracy interval remains inconclusive. The two configurations and source hashes were committed in `2c3bb17` before the fixed 80-attempt held-out comparison started. No final improvement is claimed yet. Work remains on `feat/csc2108-qwen-local-optimization`; nothing has been pushed or merged. This report will be completed after held-out validation. [Decision log](DECISIONS.md), [plan](PLAN.md), [reproduction instructions](README.md), [frozen selection](final_selection.json).

## Original baseline and diagnosis

The frozen `heredoc-v6-16k-common` control uses mini-SWE-agent 2.4.6, LiteLLM 1.81.16 and local Ollama 0.40.16, Qwen3.5 9B Q4_K_M, 16K context/4K output, thinking disabled, T=.2, top_k=40/top_p=.9, presence/frequency penalties zero and repeat penalty one. Each attempt allows 20 actions, three recognized-public-failure repair groups, a 600-second task budget and 180-second query timeout. The original runtime and all previous results remain intact.

Prior official correctness was 23/48 (47.9%), including 14/16 easy, 9/20 medium and 0/12 hard attempts. Of 299,459 generated tokens, failed attempts used 288,284 (96.3%). The raw-transport/trajectory audit links all 56 format errors to length-limited responses. Every such response opens a command fence and none closes it. Twelve runs execute no actions; eight have no submission and four preserve an unchanged functional starter. Context truncation affects two runs. These are delivery failures, not evidence that every underlying algorithm was wrong. In contrast, six candidates pass examples but fail official tests, and only one public-failure recovery reaches official success, establishing a separate correctness/generalization limitation.

Repeated identical-source public tests occur five times. None of the 29 runs ever passing public examples changes source after its first passing test; 30 total subsequent actions remain, predominantly submission. Checkpointing or automatic submission therefore offers little demonstrated prior gain, while automatically accepting examples cannot establish private correctness. No such policy has been added. Additional action/repair budgets are lower priorities than generation delivery on these traces.

## Infrastructure and interface findings

The pinned LiteLLM Ollama serializer converts native assistant calls, but omits them from its outgoing message list; it also omits tool result names. A mock of the real HTTP transport reproduces this. `transport.py` supplies a per-request native message override, preserving function arguments, tool-result links and reasoning history. Installed packages are unchanged. This follows [Ollama's tool-history protocol](https://docs.ollama.com/capabilities/tool-calling). On two existing synthetic fixtures, repair reduces actions 9→5 and 15→8, and output tokens 679→297 and 910→450; all four runs pass. These are mechanism checks, not benchmark accuracy estimates.

Direct checker commands with `2>&1` were missed by the old matcher. The new version recognizes that harmless redirection without accepting compound commands or masked exit status. Merely searching output for a public marker is unsafe because reading the checker source prints its marker too. Post-hoc direct-check recognition is separately counted in derived metrics; original events and repair budgets are unchanged. Pipelines/manual tests remain visible actions but outside the defined trusted-check repair accounting. Three repair groups do not mean three total conceivable manual revisions.

The pinned provider also wraps `httpx.ReadTimeout` as `APIConnectionError`. A typed exception-chain test reproduces and distinguishes it from connection refusal. New runs classify declared resource expiration as `ModelTimeout`; response telemetry remains incomplete when the server reply is absent. One old frozen run receives a separate, hash-linked timeout assessment after its actual traceback and expired wall establish the cause. Its original result is never rewritten or rerun.

Agent programs run only in disposable Docker containers: no network, non-root UID 65534, read-only root, 512 MB memory, one CPU, 64 PIDs, all capabilities dropped, no-new-privileges, and bounded temporary filesystems. The only bind mount is the read-only public task. The official judge runs separately with its existing limits and never returns private feedback to Qwen. A live-container inspection confirms these settings. Candidate source is extracted as bytes and never executed on the host.

## Experimental methodology

Fresh splits are frozen before inference: development 6 (2/2/2 easy/medium/hard), selection 12 (4/4/4), held-out 20 (6/8/6). Every split excludes all 27 previously scored benchmark IDs. Contests are disjoint between splits, with at most two tasks per contest in a split; held-out also excludes contests in the prior primary evaluation. SHA256 ordering and platform round robin select tasks without examining outcomes. Functional interfaces requiring custom node types and image statements remain excluded, as in the existing harness. Complete selection/exclusion details and content hashes are committed in the manifests.

All runs use the same Qwen9 weight digest, dataset source and official evaluator revision. Paired arms share task, seed and execution constraints, except explicitly labelled budget changes. Profiles and source bytes are archived per batch; runtime code executes from that archive. Later engineering cannot alter an active batch. Every wire request verifies actual Ollama sampling/model/thinking fields, including provider-specific options that LiteLLM otherwise filters or aliases. The original control executes its original archived runtime.

Initial compute ceiling is 10 inference hours or 3 million generated tokens, sequential GPU use. The gate includes all attempts and conservatively charges missing timeout replies at their full configured caps. That gate value is an upper bound, not a claim of measured completed-token inference. Runtime/token tables explicitly distinguish captured telemetry from unknown work. Completed attempts resume without inference or judging; interrupted/infra retries preserve separate attempt directories. The completed first screen was actually resumed with zero new jobs.

Official correctness is assessed only after termination. Analyses retain successful/failed runtime distributions, prompt/output counts, actual captured generation/prefill/load durations, actions, calls, repair outcomes, tool errors, public/private disagreement, model allocation/offload and failed-attempt costs. Paired intervals bootstrap problem clusters with both seeds together where repetitions exist. These descriptive intervals cannot remove small-sample, task-selection or training-contamination uncertainty. No composite score is used.

## Development results so far

Different development subsets below must not be pooled as a head-to-head accuracy comparison. Output includes thinking tokens. Timeout totals marked ≥ omit an explicitly unknown reply; the corresponding cap upper bound is retained in JSON.

| Subset | Configuration | Official passes | Agent seconds | Output tokens | Format errors |
| --- | --- | ---: | ---: | ---: | ---: |
| First easy/medium/hard | Original control | 2/3 | 126.6 | 9,259 | 2 |
| Same three | Repaired native, nonthinking | 2/3 | 267.5 | 18,366 | 0 |
| Same three | Repaired native, thinking, 4K output | 1/3 | 285.0 | 25,841 | 6 |
| First medium | Native thinking, 128K/4K | 0/1 | 128.5 | 12,288 | 3 |
| Same medium | Native thinking, 128K/32K, T=.2/presence=0 | 0/1 | 600.1 | ≥32,768 | 1 |
| Other easy/medium/hard | Text nonthinking, presence=0 | 1/3 | 207.5 | 17,362 | 3 |
| Same other three | Text nonthinking, presence=1.5 | 2/3 | 176.0 | 14,189 | 3 |
| First medium | Native thinking, 128K/32K, T=.2/presence=1.5 | 0/1 | 109.6 | 9,601 | 0 |
| Same medium | Native thinking, documented coding preset | 0/1 | 602.1 | ≥43,210 | 1 |

Native tools improve interface reliability but do not improve accuracy in the first paired screen and double total time. A 4K thinking budget truncates internal reasoning before an action on the medium/hard cases. Simply raising it to 32K at low temperature prolongs repetition: the first 32K thinking response repeats a 12-word sequence 68 times and delivers no action. Two unstarted jobs in that weak arm are deliberately stopped; the report preserves 2/4 planned completion rather than claiming a full comparison.

Presence=1.5 improves one nonthinking development outcome and substantially shortens that attempt. Both arms still truncate on the other hard problem, despite fewer repeated sequences under the penalty. The presence-controlled thinking arm fixes delivery on the first medium, then fails hidden judging after passing examples. The coding preset eventually writes a candidate after a truncated first response, but exhausts its wall and remains incorrect. More output and more thinking have not automatically improved correctness.

A separate historical comparison aligns 37 prior Qwen9 attempts: tag-default and common samplers each pass 23, with three successes unique to each; tag defaults use 1,666.8 vs 2,095.7 seconds and 117,663 vs 154,542 tokens. Their text prompts match, but other source/provenance differences mean this remains exploratory evidence motivating fresh explicit-sampler trials. It is not pooled into the new results.

## Context, inference and GPU observations

| Allocated context | Ollama model allocation | GPU allocation | CPU offload |
| ---: | ---: | ---: | --- |
| 32K | 6.718 GB | 6.718 GB | none |
| 64K | 7.683 GB | 7.683 GB | none |
| 128K | 9.897 GB | 9.897 GB | none |

At 128K, total GPU use including desktop/background allocations is 13,262 MiB on the 16,376-MiB RTX 4080 SUPER. These are allocation probes with tiny prompts, not proof of long-input throughput or a need for 128K. Longer measured generations sustain roughly 90–105 tokens/s depending on actual history length. Native nonthinking on the first medium reaches a 16,051-token prompt, so history pressure is real in some traces. Larger allocation fits on GPU, but does not itself fix the small-output-cap reasoning failures.

Cold loads are normally about 3.2–3.5 seconds; the first diagnostic after setup takes 20.6 seconds and is explicitly retained as an outlier. Runs intentionally unload project models for consistent cold-start comparisons. Production use can retain an already loaded model through keep_alive, but no unmeasured warm-start benefit is credited to an accuracy result. Desktop/GPU activity and container noise limit precise latency claims.

## Remaining stages

Finish the final inexpensive candidate screens, compare promising samplers on fresh selection tasks, repeat ambiguous comparisons, freeze a practical default and any justified high-reasoning alternative, then run paired held-out validation. Held-out execution is guarded by a frozen configuration-selection artifact. Add final Pareto/runtime charts, exact provenance, recommendation, unresolved limitations and commit inventory after those stages. No final recommendation is implied by this work-in-progress report.
