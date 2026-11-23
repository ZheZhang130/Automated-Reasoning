# CSC2108: Frontier-guided local coding agents (final agent implementation)

**Research question.** When and how should a stronger (frontier) model provide reasoning to a small local coding
agent?

**What this branch contains.** One shared coding agent and five experimental conditions, ready for the final
benchmark:

| | Condition | Frontier role |
| --- | --- | --- |
| A | local only | none |
| B | frontier only | the frontier model is the coder, through the same agent interface |
| C | frontier plan | one upfront natural-language plan |
| D | frontier contract | one upfront behavioural contract (see `CONDITIONS.md` for the selected variant) |
| E | frontier diagnosis | one diagnosis at the first failed public test, delivered into the same session |

**Shared components.**

* **Local agent:** mini-SWE-agent 2.4.6 with Qwen3.5 9B (Q4_K_M) on Ollama; see `CONDITIONS.md` for the selected
  shared-agent configuration.
* **Frontier:** `gpt-6.2-sol` via the OpenAI API. Isolated Codex replay is the free development substitute.
* **Judge:** the team judge `csc2108-judge:0.2.1` (LiveCodeBench exact comparison).

## Quick start

```bash
export CSC2108_STUDY_ROOT=/path/outside/checkout/study LITELLM_LOCAL_MODEL_COST_MAP=True PYTHONIOENCODING=utf-8
python -m local_agent verify                       # frozen agent identity (38 hashes, packages, model digest)
python -m guided_agent prepare-fixture             # synthetic task; no LiveCodeBench data needed
python -m guided_agent batch PLAN.json             # attempts (see HANDOFF_TO_PETER.md for plan examples)
python -m guided_agent evaluate <study>/runs/<batch>
python -m guided_agent measure  <study>/runs/<batch>
python -m unittest guided_agent.test_guided guided_agent.test_pass2 guided_agent.test_pass3 guided_agent.test_pass4
```

## Documents

| File | For |
| --- | --- |
| `HANDOFF_TO_PETER.md` | running the final evaluation: commands, boundaries, billing, resuming, fixtures |
| `ARCHITECTURE.md` | how the shared agent and the conditions fit together |
| `CONDITIONS.md` | one specification per condition: frontier calls, inputs, outputs, triggers, budgets |
| `MEASUREMENT_SCHEMA.md` | every field of `measurement.json`: type, unit, nullability, source |
| `FINALIZATION_MANIFEST.json` | commits, configuration IDs, prompt and source hashes, versions, test results |

## Layout

| Path | Role |
| --- | --- |
| `guided_agent/` | the integrated A/B/C/D/E runner, providers, measurement, tests and fixtures |
| `local_agent/` | host adapters (Windows frozen, portable macOS/Linux) and identity verification |
| `local_eval_v2/`, `local_baseline/`, `local_optimization/` | the **frozen** original agent and its selection (hash-verified; do not edit) |
| `judge/` | the team judge (public and hidden suites) |
| `planning_frontier/`, `contract_frontier/` | the teammates' plan and contract prompts and replay classes (used unchanged) |
| `orchestration/`, `timeline/`, `papers/`, `docs/` | teammates' and project material |

## History

The full development history lives on `feat/csc2108-contract-diagnosis-pass2`: passes 1–4, every experiment,
diagnostic script, intermediate report and alternative configuration. This branch keeps only what the final system
needs.
