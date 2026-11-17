# Adaptive decision log

## Before fresh benchmark inference

The 48-run Qwen9 audit found 56 format errors and exactly 56 truncated responses; every rejected turn was length-limited. All 56 raw responses opened a command fence and none closed it. Eight missing submissions occurred with zero executed actions. Thus interface delivery and output budget deserve early priority; a formatting reprimand alone cannot establish an algorithmic failure. Failed attempts consumed 288,284/299,459 output tokens (96.3%). There were also six runs passing examples but failing official tests and only one recovery to official success, so interface repair alone is unlikely to solve the reasoning problem.

A real LiteLLM HTTP-handler mock confirmed that 1.81.16 drops assistant tool calls and tool result names from native history. The versioned `extra_body.messages` override preserves both, reasoning fields and sampling options. No installed package changed. Three transport tests pass. On existing negative/functional synthetic tasks, stock→fixed required 9→5 and 15→8 actions, 679→297 and 910→450 output tokens; all passed public tests. This establishes a mechanism, not benchmark accuracy.

Allocation-only probes at 32K/64K/128K used 6.718/7.683/9.897 GB, respectively, all fully on GPU. Total GPU memory at 128K was 13,262 MiB including desktop/background usage. These short requests do not establish full-length prefill performance or prove the task needs 128K.

Fresh dataset manifests were frozen before any new benchmark inference: development 6, selection 12, held-out 20, all excluding the 27 previously scored IDs. Splits share no contests; held-out also excludes prior primary-evaluation contests. The separate evaluator cache is never agent-mounted.

First screen: three paired development problems (one per difficulty), seed 2108, original v6 vs repaired native tools vs repaired native tools with thinking. All use 16K context/4K output, common sampling, 20 actions/3 repairs/600 seconds and 180-second query timeouts. Original v6 runs its archived original runtime. Native-tool schema/prompt necessarily differs with protocol; the causal interpretation is the complete tool interface, not serialization alone (which the synthetic comparison isolates).

A pre-benchmark launcher typo referenced `runtime.py` rather than `runtime_opt.py`; it failed before any inference. The empty first diagnostic directory is retained, the typo fixed, and the subsequent diagnostic is separately named. The first cold load after GPU probes took 20.6 seconds; subsequent synthetic loads were ~3.2–3.5 seconds. Report load separately rather than attributing that outlier to tool behavior.

## During the first screen

All three arms pass the first easy task. On the medium task, native nonthinking recovers and officially passes, but spends 183.7 seconds/12,885 output tokens/13 actions and reaches a 16,051-token prompt. Thinking at 4K never reaches an action: three capped reasoning responses, 12,288 tokens, missing submission. This supports testing larger output, not concluding that thinking is ineffective. The next budget screen will pair 4K vs 32K at the same 128K context and 480-second query allowance (600-second task wall), and separately compare context at 4K/180 seconds and protocol at 32K/480 seconds. The unchanged original control remains 4K/180 seconds.

Across the 29 prior Qwen9 runs ever passing public tests, none changed the candidate after its final passing test and none ended with a later failed public test. A public-pass checkpoint therefore has no demonstrated prior benefit; avoid adding it now. Repeated identical-source tests occur only five times, so do not impose an untested loop cutoff yet.

Long-output runs can exhaust a declared query/wall budget. Such timeouts are retained as task failures with partial candidate judging, rather than treated as complete responses. Missing response token counts remain explicitly unknown; the compute budget conservatively charges their full output cap and query allowance. Non-timeout infrastructure failures stop the scheduler. No configuration silently shrinks its output limit near a deadline.

## Completed first screen (9 runs)

Control 2/3, native nonthinking 2/3, native thinking 1/3. Total agent seconds: 126.6/267.5/285.0; output tokens 9,259/18,366/25,841. Native nonthinking has zero format errors, but no accuracy gain and twice the total time: eliminate it as a standalone proposed default for now. Keep the repaired native implementation for larger-thinking experiments; correctness of the transport is independently established. The 4K thinking arm is clearly unsuitable on these medium/hard cases, so do not broaden it to selection tasks.

Next batch `dev-output-budget`: the same medium/hard problems, seed 2108; fixed native history, 128K context, 480-second query, 600-second wall, common T=.2 sampling. Only the output cap changes (4K/32K). The 4K arm's larger query allowance is nonbinding; it remains to isolate output at an identical configured context/query budget. This batch explicitly tests the larger-context + larger-output + thinking combination; it does not credit the whole combination to any one component. Once it finishes, decide whether protocol or sampling is the most useful next comparison.

A trajectory review found another small interface-accounting defect: the native hard run executes `python -I /public/check.py 2>&1` and passes examples, but the old exact matcher does not recognize the stderr redirect. Its official failure is a public/private disagreement, not an absence of testing. Also, merely searching output for the public marker would misclassify `cat /public/check.py`, which prints that marker as source. The new runtime version accepts only the same direct Python checker command with optional `2>&1` (and the already-supported stdin redirect), never compound commands or masked exit status. Two focused tests guard this boundary. The already-frozen first screen and output-budget batch retain their old matcher unchanged; later batches archive the new version and report this change. No benchmark-specific content is added to prompts or candidates.
