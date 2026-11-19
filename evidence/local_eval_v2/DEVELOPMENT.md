# Development evidence

58 finalized development runs, on four synthetic tasks only. These are configuration diagnostics and are excluded from benchmark accuracy. The development tasks test negative-integer aggregation repair, delimiter validation, ASCII case conversion, and a functional distinct-count interface. All held-out development judging remains separate from the model.

The earlier three-task v4 prototype has nine completed records plus a preserved partial attempt under `E:\CSC2108Local\eval-v2\development-experiments`. Its interface was revised before v5; do not pool those trials with v5. Each completed v5/secondary run retains its exact configuration, source hashes and full trajectory. Native v5 initially reused fenced text examples; corrected native v6 uses tool-only instructions, and is the native comparison used for the decision.

## Per-run outcomes

| Model | Profile | Task | Action limit | Official result | Stop | Seconds | Actions | Repairs | Format errors |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| qwen2.5-coder:14b | heredoc-v5-16k | dev-ascii-case | 20 | pass | Submitted | 11.735 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k | dev-balanced-delimiters | 20 | pass | Submitted | 12.344 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k | dev-functional-distinct | 20 | pass | Submitted | 11.171 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k | dev-negative-squares | 20 | candidate_failure | ActionLimit | 36.469 | 20 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-32k | dev-negative-squares | 20 | candidate_failure | ActionLimit | 47.297 | 20 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-8k | dev-negative-squares | 20 | candidate_failure | ActionLimit | 36.625 | 20 | 0 | 1 |
| qwen2.5-coder:14b | native-v5-16k | dev-negative-squares | 20 | candidate_failure | RepeatedFormatError | 11.109 | 0 | 0 | 3 |
| qwen2.5-coder:14b | v3-baseline | dev-negative-squares | 20 | candidate_failure | ActionLimit | 27.891 | 20 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k | dev-ascii-case | 20 | candidate_failure | ActionLimit | 24.469 | 20 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k | dev-balanced-delimiters | 20 | pass | Submitted | 9.968 | 3 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k | dev-functional-distinct | 20 | pass | Submitted | 10.656 | 4 | 0 | 1 |
| qwen2.5-coder:7b | heredoc-v5-16k | dev-negative-squares | 20 | candidate_failure | Submitted | 11.781 | 5 | 1 | 0 |
| qwen2.5-coder:7b | heredoc-v5-32k | dev-negative-squares | 20 | candidate_failure | Submitted | 11.781 | 5 | 1 | 0 |
| qwen2.5-coder:7b | heredoc-v5-8k | dev-negative-squares | 20 | candidate_failure | Submitted | 11.828 | 5 | 1 | 0 |
| qwen2.5-coder:7b | native-v5-16k | dev-negative-squares | 20 | candidate_failure | RepeatedFormatError | 9.234 | 0 | 0 | 3 |
| qwen2.5-coder:7b | v3-baseline | dev-negative-squares | 20 | candidate_failure | ActionLimit | 21.000 | 20 | 1 | 0 |
| qwen3.5:9b | heredoc-v5-16k | dev-ascii-case | 20 | pass | Submitted | 12.250 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k | dev-balanced-delimiters | 20 | pass | Submitted | 12.282 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k | dev-functional-distinct | 20 | pass | Submitted | 11.734 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k | dev-negative-squares | 20 | pass | Submitted | 12.390 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-thinking | dev-ascii-case | 20 | pass | Submitted | 15.860 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-thinking | dev-balanced-delimiters | 20 | pass | Submitted | 24.547 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-thinking | dev-functional-distinct | 20 | pass | Submitted | 14.485 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-thinking | dev-negative-squares | 20 | pass | Submitted | 19.875 | 4 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-32k | dev-negative-squares | 20 | pass | Submitted | 12.110 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-8k | dev-negative-squares | 20 | pass | Submitted | 12.235 | 3 | 0 | 0 |
| qwen3.5:9b | native-v5-16k | dev-negative-squares | 20 | pass | ActionLimit | 49.719 | 20 | 0 | 0 |
| qwen3.5:9b | v3-baseline | dev-negative-squares | 20 | pass | Submitted | 11.500 | 4 | 0 | 0 |
| qwen2.5-coder:14b | heredoc-v5-16k | dev-negative-squares | 40 | candidate_failure | ActionLimit | 65.891 | 40 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k-t02 | dev-ascii-case | 20 | pass | Submitted | 11.579 | 3 | 0 | 0 |
| qwen2.5-coder:14b | heredoc-v5-16k-t02 | dev-balanced-delimiters | 20 | pass | Submitted | 12.453 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k-t02 | dev-functional-distinct | 20 | pass | Submitted | 11.281 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v5-16k-t02 | dev-negative-squares | 20 | candidate_failure | Submitted | 14.078 | 4 | 0 | 1 |
| qwen2.5-coder:14b | native-v6-16k | dev-negative-squares | 20 | candidate_failure | RepeatedFormatError | 11.079 | 0 | 0 | 3 |
| qwen2.5-coder:7b | heredoc-v5-16k | dev-negative-squares | 40 | candidate_failure | Submitted | 11.797 | 5 | 1 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k-t02 | dev-ascii-case | 20 | candidate_failure | ActionLimit | 24.375 | 20 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k-t02 | dev-balanced-delimiters | 20 | pass | Submitted | 9.954 | 3 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k-t02 | dev-functional-distinct | 20 | pass | Submitted | 9.547 | 3 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v5-16k-t02 | dev-negative-squares | 20 | candidate_failure | ActionLimit | 27.078 | 20 | 0 | 0 |
| qwen2.5-coder:7b | native-v6-16k | dev-negative-squares | 20 | candidate_failure | RepeatedFormatError | 9.250 | 0 | 0 | 3 |
| qwen3.5:9b | heredoc-v5-16k | dev-negative-squares | 40 | pass | Submitted | 12.281 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-t02 | dev-ascii-case | 20 | pass | Submitted | 12.281 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-t02 | dev-balanced-delimiters | 20 | pass | Submitted | 12.156 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v5-16k-t02 | dev-functional-distinct | 20 | pass | Submitted | 13.625 | 5 | 0 | 1 |
| qwen3.5:9b | heredoc-v5-16k-t02 | dev-negative-squares | 20 | pass | Submitted | 12.094 | 3 | 0 | 0 |
| qwen3.5:9b | native-v6-16k | dev-negative-squares | 20 | pass | Submitted | 19.219 | 8 | 0 | 0 |
| qwen2.5-coder:14b | heredoc-v6-16k-common | dev-ascii-case | 20 | pass | Submitted | 11.375 | 3 | 0 | 0 |
| qwen2.5-coder:14b | heredoc-v6-16k-common | dev-balanced-delimiters | 20 | pass | Submitted | 12.516 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v6-16k-common | dev-functional-distinct | 20 | pass | Submitted | 11.282 | 3 | 0 | 1 |
| qwen2.5-coder:14b | heredoc-v6-16k-common | dev-negative-squares | 20 | candidate_failure | Submitted | 13.859 | 4 | 0 | 1 |
| qwen2.5-coder:7b | heredoc-v6-16k-common | dev-ascii-case | 20 | candidate_failure | ActionLimit | 24.500 | 20 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v6-16k-common | dev-balanced-delimiters | 20 | pass | Submitted | 9.984 | 3 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v6-16k-common | dev-functional-distinct | 20 | pass | Submitted | 9.641 | 3 | 0 | 0 |
| qwen2.5-coder:7b | heredoc-v6-16k-common | dev-negative-squares | 20 | candidate_failure | ActionLimit | 27.250 | 20 | 0 | 0 |
| qwen3.5:9b | heredoc-v6-16k-common | dev-ascii-case | 20 | pass | Submitted | 11.656 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v6-16k-common | dev-balanced-delimiters | 20 | pass | Submitted | 12.297 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v6-16k-common | dev-functional-distinct | 20 | pass | Submitted | 11.532 | 3 | 0 | 0 |
| qwen3.5:9b | heredoc-v6-16k-common | dev-negative-squares | 20 | pass | Submitted | 11.875 | 3 | 0 | 0 |

## Context allocation probes

Nine short-prompt allocation probes use the same hardware. Reported model allocation and GPU allocation are Ollama snapshots, not process peak memory. A short probe does not exercise the full context window.

| Model | Context | Seconds | Model bytes | GPU bytes | CPU offload bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen3.5:9b | 8192 | 3.766 | 5862210928 | 5862210928 | 0 |
| qwen3.5:9b | 16384 | 3.781 | 6147423600 | 6147423600 | 0 |
| qwen3.5:9b | 32768 | 3.796 | 6717848944 | 6717848944 | 0 |
| qwen2.5-coder:14b | 8192 | 3.562 | 10425372507 | 10425372507 | 0 |
| qwen2.5-coder:14b | 16384 | 3.531 | 11909086575 | 11909086575 | 0 |
| qwen2.5-coder:14b | 32768 | 4.625 | 15720911993 | 14589414604 | 1131497389 |
| qwen2.5-coder:7b | 8192 | 2.485 | 5148633988 | 5148633988 | 0 |
| qwen2.5-coder:7b | 16384 | 2.438 | 5635173252 | 5635173252 | 0 |
| qwen2.5-coder:7b | 32768 | 2.688 | 6608251780 | 6608251780 | 0 |

## Long-input stress probes

The inert prompt is about 20K tokens, with a 32-token output ceiling. Smaller windows truncate deliberately. Prompt token counts below are raw Ollama values; allocation is the requested context. This does not measure coding capability. Some probes hit the deliberately tiny output limit. The initial 7B/16K request returned HTTP 500; it was not recorded as a successful row and its successful retry is listed here. The failed command/traceback remains in the session history; no failure body was captured by the original helper.

| Model | Context | Prompt eval tokens | Seconds | Done reason |
| --- | ---: | ---: | ---: | --- |
| qwen3.5:9b | 8192 | 4098 | 4.406 | stop |
| qwen3.5:9b | 16384 | 8194 | 5.000 | stop |
| qwen3.5:9b | 32768 | 20025 | 6.937 | stop |
| qwen2.5-coder:14b | 8192 | 4098 | 5.156 | length |
| qwen2.5-coder:14b | 16384 | 8194 | 13.031 | length |
| qwen2.5-coder:14b | 32768 | 20041 | 78.485 | length |
| qwen2.5-coder:7b | 8192 | 4098 | 3.281 | stop |
| qwen2.5-coder:7b | 16384 | 8194 | 3.656 | length |
| qwen2.5-coder:7b | 32768 | 20041 | 5.563 | length |

## Decision and limits

The common 16K text workflow passed 4/4 (9B), 3/4 (14B), and 2/4 (7B) at both temperatures 0 and 0.2. The four-task sample is too small for a statistical configuration claim. The 14B and 7B negative-squares failures persisted at 40 actions/5 repairs; their repeated identical/wrong code does not automatically count as multiple repair cycles. Corrected native v6 worked for 9B but both Qwen2.5 models emitted no native action. Qwen3.5 thinking-on passed 4/4 but was slower than thinking-off on these easy tasks. It was not silently enabled in the primary benchmark.

The 32K 14B model allocation offloaded 1,131,497,389 bytes in the allocation probe and the long-input run was much slower. 16K was chosen as a common GPU-resident allocation, not an assertion that no long trajectory can exhaust it. Raw context logs and length-limit reasons are retained in every main run. See DECISION.md for the pre-benchmark freeze.

The final 12 v6 trials explicitly harmonize native Ollama sampler options and verify each actual request body. They passed 4/4, 3/4 and 2/4 (9B, 14B, 7B), matching the observed small-set correctness with tag defaults. They are separate from the earlier v5 trials. The v6 correction followed a model-metadata audit during an initial benchmark batch; that batch stopped at 111 and is retained separately, not pooled into primary v6 results. See DECISION.md.

Artifacts: `E:\CSC2108Local\eval-v2\development-v5-experiments`, `development-secondary`, `development-common-v6`, and `development-experiments/{memory,stress}.json`. `development_metrics.csv` exports numerical outcomes without candidate source or held-out cases.
