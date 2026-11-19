# Local Qwen3.5 optimization, 2026-11-17

All work stays on `feat/csc2108-qwen-local-optimization`; no push or merge is authorized. The prior baseline and eval-v2 sources/results are immutable controls. Only local Qwen inference authors candidates. Codex supplies infrastructure and aggregate diagnosis, never task solutions, candidate edits, or algorithm hints. Private judging is separate and never returned to the agent.

## Budget and selection policy

Initial ceiling: 10 hours of recorded inference (generation + prefill + load) or 3 million generated tokens. Sequential inference, the existing cross-project GPU lock, no foreign workload unloading. This is a ceiling, not a target. Stop weak arms early; spend additional runs on ambiguity and promising combinations. Record decisions before the next stage.

Freeze fresh task splits before inference: development 6 (2/2/2 easy/medium/hard), selection 12 (4/4/4), held-out 20 (6/8/6). Deterministic SHA256 ordering, platform balance where feasible, at most two tasks per contest in a split, contest-disjoint splits. Exclude every discovered previously scored benchmark ID from ALL new splits, and prior evaluation contests from held-out where feasible. Interface eligibility follows eval-v2; dataset/evaluator pins stay unchanged. No task selection by outcome. Keep held-out statements out of analysis until configuration selection is frozen.

1. Audit all 48 prior Qwen9 trajectories and raw transports, including truncated/invalid turns, source repetition, recovery and public/private disagreement.
2. Reproduce the pinned LiteLLM native-history omission with a mocked real transport; test a versioned fix on existing synthetic fixtures. Probe 32K/64K/128K context allocation and actual GPU residency.
3. Controlled development: preserve exact v6 control; vary protocol, thinking, output/context budgets, then explicitly test promising combinations. Include 32K output; enlarge further only if useful work remains capped. Keep task/seed/judge/action/repair/wall budgets paired except explicitly labelled budget comparisons. Avoid extra architecture unless logs justify a measured test.
4. Compare leading arms on fresh selection tasks, repeat if ambiguous. Use official pass count first, then runtime/tokens/reliability and problem-paired uncertainty; no composite score. Prefer established simpler behavior if improvement is uncertain.
5. Freeze final configurations, source hashes, task hashes, model/image digests and judge provenance before held-out. Plan 20 tasks x 2 seeds x control/default = 80 runs, needed to separate seed variance from problem effects. Add a high-reasoning arm only if selection shows a useful Pareto tradeoff and the budget allows it. Never tune on held-out.
6. Report successful/failed runtime distributions, tokens, inference/prefill/load, model calls/actions, tool failures, submission/recovery, wasted failed work, GPU allocation/offload, paired uncertainty and Pareto plots. Preserve raw evidence and safe resume behavior.

Safety uses the unchanged eval-v2 sandbox and official judge: network disabled, read-only root, non-root user, capped memory/CPU/PIDs, trusted public bundle only, source extracted as bytes and never executed on the host. Large artifacts go to `E:\CSC2108Local\optimization`; weights remain `E:\OllamaModels`; Docker remains `E:\DockerDesktop`.

## External rationale

The [Qwen model card](https://huggingface.co/Qwen/Qwen3.5-9B) recommends 32,768 output for ordinary uses, more for demanding reasoning, and at least 128K context for thinking. These are hypotheses to measure on this GPU, not presumed optima. Its coding-thinking sampling preset is another controlled candidate. [Ollama's native tool protocol](https://docs.ollama.com/capabilities/tool-calling) retains assistant calls and links results using `tool_name`. The installed LiteLLM 1.81.16 adapter appears to omit both in its outgoing message construction; a transport test must establish this before performance comparisons.
