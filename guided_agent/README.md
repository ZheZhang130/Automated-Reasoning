# guided_agent — integrated A/B/C/D/E backend

Every condition runs on **one** coding agent: the unchanged frozen `local_eval_v2/runtime.run` (mini-SWE-agent
2.4.6 + Qwen3.5 9B, `heredoc-v6-16k-common`). Public tests go through Peter's `judge-public`, and hidden scoring is
a separate step.

| Condition | What differs from A | Where |
| --- | --- | --- |
| A local only | — (frozen `{{task}}` first message) | — |
| B frontier only | The coding model: frozen `TextModel` → frontier provider (same parser, sandbox, judge, budgets) | `frontier_coder.py` |
| C plan | Upfront plan appended to the first message (`plan-v1`, `inject-v1`) | `guidance.py` |
| D contract | Upfront behavioral contract (`contract-v1` + `inject-v1`; pass-2 experimental `contract-v3` + `inject-v3-contract`) | `guidance.py` |
| E diagnosis | One frontier diagnosis of the first qualifying public failure, delivered into the **same running session** | `diagnosis.py`, hooks in `backend.py` |

Pass-1 documentation: [`../reasoning_effectiveness/`](../reasoning_effectiveness/).
Pass-2 documentation (B, contract-v3, E): [`../reasoning_effectiveness/pass2/`](../reasoning_effectiveness/pass2/).
Commands, platforms and environment variables: [`../reasoning_effectiveness/PORTABILITY.md`](../reasoning_effectiveness/PORTABILITY.md).

| Module | Role | Status |
| --- | --- | --- |
| `backend.py` | Rebinds `Agent` (first-message template; E delivery after the triggering observation) and `Environment` (recognized `python -I /public/check.py` → judge-public; E trigger observation; E container lifetime) in the frozen function. Composes with `local_agent.portable.adapted_run`. | **Active** |
| `runner.py` | One attempt → Peter's run record (`result.json`, `attempts.jsonl`, `submission.py`) + provenance (incl. `diagnosis` / `coder` blocks); hard outer timeout; separate hidden `evaluate` | **Active** |
| `guidance.py` | Versioned prompts (`plan-v1`, `contract-v1` = teammates' prompts; `contract-v2`, `contract-v3`, `diagnosis-v1`), injection and delivery templates, format/leakage validation, task-bound artifacts replayed via `SavedPlan`/`SavedContract` | **Active** (`contract-v2/v3`: experimental) |
| `diagnosis.py` | E: trigger policy, evidence packet, live Codex / API / fixed / replay providers, at-most-once controller with deadline suspension | **Active (pass 2)** |
| `frontier_coder.py` | B: API (ledgered, per-run cap) / Codex-per-turn / scripted coders as a model substitution | **Active (pass 2), functional only** |
| `providers.py` | Isolated Codex single-response inference; direct OpenAI client with write-ahead request/cost ledger (12 requests / $10 per study root) | **Active** |
| `tasks.py`, `selection.py`, `selection_pass2.py` | Build judge tasks + agent bundles (LF-safe on Windows); deterministic, outcome-blind selection | **Active** |
| `analysis.py`, `report.py` | Per-attempt metrics (incl. E trigger/delivery/recovery, manual self-checks); per-cohort tables | **Active** |
| `aci` options in `backend.py` | `truncation_note`, `unchanged_source_note`, `repeat_guard` | **Experimental — off; not promoted** |
| `test_guided.py`, `test_pass2.py` | Offline tests; `test_pass2.IntegrationE` (real runtime + Docker + judge, scripted coder) with `CSC2108_INTEGRATION=1` | `python -m unittest guided_agent.test_guided guided_agent.test_pass2` |

Batch plan items: `{"task_id", "condition": "A"|"B"|"C"|"D"|"E", "guidance"?: artifact (C/D), "injection"?,
"variant"?, "seed"?, "diagnosis"?: {"provider": "codex"|"api"|"fixed"|"replay", "timeout", "purpose" (api)},
"coder"?: {"provider": "api"|"codex"|"scripted", "max_requests", "purpose" (api)}, "smoke"?: {"actions", "seconds"}}`.
`smoke` budgets are for labelled functional smokes only.

Condition F (plan + contract) remains reserved (`common.FUTURE_CONDITIONS`): one injection template with two artifacts.
