# guided_agent — integrated A/C/D backend

Runs local-only (A), upfront frontier plan (C) and upfront behavioral contract (D) on **one** coding
agent: the unchanged frozen `local_eval_v2/runtime.run` (mini-SWE-agent 2.4.6 + Qwen3.5 9B,
`heredoc-v6-16k-common`). Public tests go through Peter's `judge-public`, and hidden scoring is a separate step.
Commands, platforms and environment variables: [`../reasoning_effectiveness/PORTABILITY.md`](../reasoning_effectiveness/PORTABILITY.md).
Results: [`../reasoning_effectiveness/FINAL_REPORT.md`](../reasoning_effectiveness/FINAL_REPORT.md).

| Module | Role | Status |
| --- | --- | --- |
| `backend.py` | Rebinds only `Agent` (guidance block in the first user message) and `Environment` (recognized `python -I /public/check.py` → judge-public) in the frozen function. Composes with `local_agent.portable.adapted_run` on portable hosts. | **Active** |
| `runner.py` | One attempt → Peter's run record (`result.json`, `attempts.jsonl`, `submission.py`) + provenance; hard outer timeout per attempt; separate hidden `evaluate` | **Active** |
| `guidance.py` | Versioned prompts (`plan-v1`, `contract-v1` = teammates' prompts, imported unchanged), task-bound artifacts replayed via `SavedPlan`/`SavedContract`, format/leakage validation, injection templates | **Active** (`contract-v2`, `inject-v2-contract-checks`: experimental, not promoted) |
| `providers.py` | Isolated Codex single-response authoring; direct OpenAI client with write-ahead request/cost ledger (12 requests / $10 per study) | **Active** |
| `tasks.py`, `selection.py` | Build judge tasks + agent bundles from the pinned LCB shard (LF-safe on Windows); deterministic outcome-blind selection | **Active** |
| `analysis.py`, `report.py` | Per-attempt reliability metrics; per-cohort tables (cohorts never pooled) | **Active** |
| `aci` options in `backend.py` | `truncation_note`, `unchanged_source_note`, `repeat_guard` | **Experimental — off by default; not promoted** |
| `test_guided.py` | Offline tests (no model, Docker or network) | Run: `python -m unittest guided_agent.test_guided` |

Condition hooks for future work: E (diagnosis) belongs at `JudgedEnvironment._public_judge` after the first
recognized failure, delivered once as the next user message. B (frontier-only) is a different coder model on the same
ACI. F combines two artifacts in one injection template. `common.FUTURE_CONDITIONS` reserves their labels.
