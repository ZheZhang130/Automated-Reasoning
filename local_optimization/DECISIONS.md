# Adaptive decision log

## Before fresh benchmark inference

The 48-run Qwen9 audit found 56 format errors and exactly 56 truncated responses; every rejected turn was length-limited. All 56 raw responses opened a command fence and none closed it. Eight missing submissions occurred with zero executed actions. Thus interface delivery and output budget deserve early priority; a formatting reprimand alone cannot establish an algorithmic failure. Failed attempts consumed 288,284/299,459 output tokens (96.3%). There were also six runs passing examples but failing official tests and only one recovery to official success, so interface repair alone is unlikely to solve the reasoning problem.

A real LiteLLM HTTP-handler mock confirmed that 1.81.16 drops assistant tool calls and tool result names from native history. The versioned `extra_body.messages` override preserves both, reasoning fields and sampling options. No installed package changed. Three transport tests pass. On existing negative/functional synthetic tasks, stock→fixed required 9→5 and 15→8 actions, 679→297 and 910→450 output tokens; all passed public tests. This establishes a mechanism, not benchmark accuracy.

Allocation-only probes at 32K/64K/128K used 6.718/7.683/9.897 GB, respectively, all fully on GPU. Total GPU memory at 128K was 13,262 MiB including desktop/background usage. These short requests do not establish full-length prefill performance or prove the task needs 128K.

Fresh dataset manifests were frozen before any new benchmark inference: development 6, selection 12, held-out 20, all excluding the 27 previously scored IDs. Splits share no contests; held-out also excludes prior primary-evaluation contests. The separate evaluator cache is never agent-mounted.

First screen: three paired development problems (one per difficulty), seed 2108, original v6 vs repaired native tools vs repaired native tools with thinking. All use 16K context/4K output, common sampling, 20 actions/3 repairs/600 seconds and 180-second query timeouts. Original v6 runs its archived original runtime. Native-tool schema/prompt necessarily differs with protocol; the causal interpretation is the complete tool interface, not serialization alone (which the synthetic comparison isolates).

A pre-benchmark launcher typo referenced `runtime.py` rather than `runtime_opt.py`; it failed before any inference. The empty first diagnostic directory is retained, the typo fixed, and the subsequent diagnostic is separately named. The first cold load after GPU probes took 20.6 seconds; subsequent synthetic loads were ~3.2–3.5 seconds. Report load separately rather than attributing that outlier to tool behavior.
