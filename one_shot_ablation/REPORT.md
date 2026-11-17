# Quick Qwen one-shot vs mini-SWE-agent pilot

Status: **complete**; total experimental wall including synthetic sanity, inference, grading and cleanup: **640.2 s / 2,100 s**. Hard ceiling respected: True. No parameter tuning or extra benchmark attempts.

Model: `qwen3.5:9b`, Q4_K_M; digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`. mini-SWE-agent 2.4.6 / LiteLLM 1.81.16 / Ollama 0.40.16, endpoint 127.0.0.1:11435. Shared sampler: context 16,384, output 4,096, thinking off, T=.2, top-p=.9, top-k 40, min-p 0, repeat penalty 1, repeat window 64, presence/frequency 0, seed 2108.

A uses the unchanged `heredoc-v6-16k-common` agent prompt and runner: **shortened-budget variant**, not the original 600 s baseline. Outer per-attempt inference wall cap 120 s, at most 10 actions/3 repair groups. Startup and a 5 s finalization reserve come out of this cap; the saved pilot_budget.json gives each active agent budget. B makes exactly one direct LiteLLM completion call with a 120 s outer cap, no tools, tests or repairs. Both start cold and receive byte-identical initial problem/starter/interface text. A additionally has the existing visible checker and execution feedback. Private judging occurs only after inference terminates.

Selection was frozen before sanity or benchmark inference: exclude all 65 scored IDs, prefer unevaluated contests, distinct new contests, platform round robin within difficulty, then SHA256(`CSC2108-one-shot-pilot-v1:`+ID). Existing supported-interface/image exclusions apply; no private tests or solutions were inspected for selection. See [manifest](manifest.json).

| Problem | Difficulty | Prior contest fallback | A: agent | B: one-shot |
| --- | --- | --- | --- | --- |
| atcoder-abc396_b | easy | False | pass | pass |
| leetcode-3753 | easy | False | pass | pass |
| atcoder-abc392_c | medium | False | pass | pass |
| leetcode-3677 | medium | True | candidate_failure | pass |
| atcoder-abc390_d | medium | True | candidate_resource_failure | missing_submission |
| atcoder-arc193_d | hard | False | missing_submission | missing_submission |

| Condition | Correct / completed (6 planned) | Generated tokens captured | Additional uncaptured-token bound | Calls | Inference wall s | Judge wall s | Formatting errors | Missing | Public recoveries | Official failures with source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A: shortened mini-SWE | 3/6 | 29,786 | ≤4,096 | 26 | 409.8 | 22.7 | 5 | 1 | 1 | 2 |
| B: one-shot | 4/6 | 10,178 | ≤0 | 6 | 158.6 | 17.0 | 2 | 2 | 0 | 0 |

Tokens are summed across **all** calls per attempt. If an HTTP reply is interrupted by the 120 s deadline, its exact token count is unavailable: captured counts are lower bounds and each missing reply adds at most 4,096 tokens. No guessed token count is reported as measured. Inference wall includes interpreter/startup, model loading, generation, agent tools and finalization; independent judging is separately timed. Formatting counts are rejected agent replies versus one-shot extraction failures. One-shot has no public recovery by design.

Total wall including independent grading: **A 432.5 s; B 175.6 s**. Synthetic checks and supervisor overhead account for the rest of the experimental clock. Public recovery counts use the unchanged runner's recognized direct checks.

- **both:** atcoder-abc396_b, leetcode-3753, atcoder-abc392_c
- **neither:** atcoder-abc390_d, atcoder-arc193_d
- **agent only:** none
- **one shot only:** leetcode-3677
- **unpaired incomplete:** none

## Failed agent trajectories

- **leetcode-3677:** Deadline; calls: 8, actions: 6, formatting errors: 1, captured length-limited replies: 1. The official evaluator reports Wrong Answer. Visible checks also failed; the saved implementation was incorrect, alongside a length/format failure. Tools and repairs did not resolve it within this shortened budget.
- **atcoder-abc390_d:** Deadline; calls: 4, actions: 1, formatting errors: 2, captured length-limited replies: 2. The written candidate exceeded the unchanged 1 GB judge memory limit (owned Docker OOM evidence). This is a resource/performance failure as well as formatting/budget trouble; no public check ran.
- **atcoder-arc193_d:** ModelTimeout; calls: 3, actions: 0, formatting errors: 2, captured length-limited replies: 2. No candidate delivered; formatting/time/tool delivery failure, not an evaluated algorithm.

## Interpretation

The observed paired outcomes favor one-shot generation (0 agent-only versus 1 one-shot-only successes). This is an exploratory directional observation, not a general effectiveness claim.

Visible-test recovery occurred on atcoder-abc392_c. It produced no agent-only success here. These outcomes are already included above; they are not extra benchmark attempts.

**Only six problems and one seed per problem were used. Inference opportunities are unequal:** the agent may make multiple model calls, execute tests and repair; one-shot makes one call. The 120 s caps do not match generated tokens, prompts or inference compute. The system prompts also differ to request shell actions versus Python source. This pilot is **not a causal estimate under matched compute**, does not evaluate the full 600-second agent baseline, and does not test unrestricted repository-level bug fixing. No settings were changed in response to outcomes.

Both conditions use the same existing official private-test evaluator and pinned Docker images. Generated code executes only in the existing isolated Docker agent/judge containers. One-shot extraction removes a single code fence (or accepts raw output); it never corrects or joins source. Model-authored candidates are never edited by Codex.

Full prompts, raw Ollama requests/responses, candidates, trajectories, exception provenance and official results: `E:\CSC2108Local\one-shot-ablation`. Code/source/image/package pins are in execution.json and frozen-source/. [Per-attempt metrics](metrics.csv), [aggregate results](results.json). Existing source trees and results are preserved. No push or merge.
