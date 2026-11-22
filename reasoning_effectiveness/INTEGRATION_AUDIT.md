# Integration audit: orchestration branch, 2026-11-21

Audit performed before any code was changed on `feat/csc2108-reasoning-effectiveness`.
This document records the starting state and the gaps that the integrated
backend in `guided_agent/` addresses. Later sections are updated at the end of the
session; anything added after the initial audit is marked **(post-integration)**.

## 1. Starting state

| Item | Observed |
| --- | --- |
| Base commit | `origin/orchestration` = `a42aaff85ff43f18e51d4a7ff2e770e4095b4637` (no newer commits after `git fetch` at 22:31 EST) |
| Branch / worktree | `feat/csc2108-reasoning-effectiveness` in a separate worktree `../ar-reasoning`; the original checkout was left on `orchestration` untouched |
| Python | `E:\CSC2108Local\.venv`, Python 3.11.9, mini-swe-agent 2.4.6, litellm 1.81.16, pydantic 2.12.5 |
| Frozen verifier | `python -m local_agent verify` passed: 38 frozen files, profile `heredoc-v6-16k-common`, model digest `56671c2a…3c90` |
| Ollama | Project endpoint `127.0.0.1:11435` (was stopped; started with `local_baseline/start_ollama.ps1`), **version 0.40.17**. Historical baseline records show 0.40.16, so the serving version changed since the measured baseline. |
| Docker | Docker Desktop 29.4.1 (was stopped; started), linux/amd64, 20 CPUs. Images present: `python:3.11-slim-bookworm` (`a83ba18a…`), `csc2108-lcb-judge:v2`, `:v1`, `:portable-v1`. **Peter's `csc2108-judge:0.2.1` image was not built.** |
| Data | Cached LiveCodeBench `test6.jsonl` at `E:\CSC2108Local\eval-v2\cache` matches the judge's pinned sha256 `bb4c364f…f1f5`; no download needed. |

### Existing offline tests (before changes)

| Suite | Result |
| --- | --- |
| `planning_frontier` (`test_planner`, `test_saved_plan`, `test_coding_budget`, run from inside the folder) | 10 passed |
| `contract_frontier.test_contracts` | 4 passed |
| `orchestration` (`python -m unittest`) | 9 passed |
| `local_agent` | 14 passed, 2 skipped |
| `judge/tests` | **Import error on Windows**: `tests/test_judge.py` imports `container/judge.py`, which imports the POSIX-only `fcntl`. The suite only runs on macOS/Linux hosts or inside the container. |

## 2. What teammates implemented

* **`planning_frontier/`** — one-call PlanSearch-inspired planner (`## Observations` + `## Solution sketch` quoting observations), compact variant, `OllamaPlanner` (local substitute), `FrontierPlanner` (LiteLLM), `SavedPlan` (task-bound replay with statement sha256), and `plan_once.py`, which inserts the guide into the first user message and runs a mini-SWE-agent built from `local_eval_v2/runtime.py` classes.
* **`contract_frontier/`** — semi-formal contract prompt (Description / PRE / POST / Test suggestions / Unspecified behaviour; "no code, pseudocode, algorithms or data structures"), `SavedContract`, and `run_contract.py`, which reuses `plan_once.run`.
* **`orchestration/`** — protocol pilot for A–E plus multi-round "guided" schedules using its own JSON `write/test/submit` loop, now wired to Peter's `Judge.public()` and his run-record handoff (`result.json`, `attempts.jsonl`, `submission.py`).
* **`judge/`** — Peter's stdin/stdout judge (one long-lived container per suite, tests streamed in, LiveCodeBench `grade_stdio` comparison), frozen manifests `pilot` (8) and `main` (60), all AtCoder tasks from `test6`.

## 3. What works

* Saved guidance replay with statement-hash binding (`SavedPlan`, `SavedContract`) and offline tests for it.
* Single-call guidance: there is no code path that calls the planner/contract provider twice inside a run.
* Prompts keep the two conditions distinct: the plan asks for an algorithm; the contract forbids algorithms and data structures.
* Real mini-SWE-agent execution in the hardened sandbox (`local_baseline/runner.py` container flags: no network, read-only root, 512 MiB, 1 CPU, 64 PIDs, caps dropped).
* Peter's judge client (`judgekit.Judge`) accepts a custom data `root` and container `name`, so a separate study can run its own task set without touching teammates' containers.

## 4. Verification of the nine known integration issues

| # | Claim | Verified state |
| --- | --- | --- |
| 1 | `plan_once.py` builds its own mini-SWE-agent instead of invoking the frozen baseline | **Confirmed.** It reuses runtime classes but not `runtime.run`, so it skips the frozen preflight, telemetry, model verification and sampler wiring. |
| 2 | Coding output 4,000 vs 4,096 | **Confirmed** (`DEFAULT_CODING_OUTPUT_TOKENS = 4000`). |
| 3 | Sampler not reproduced | **Confirmed.** Only `temperature=0.2` is sent. `top_k/top_p/min_p/repeat_penalty/repeat_last_n/penalties` and `seed` are missing, so Ollama/Modelfile defaults apply (Ollama's default `repeat_penalty` is 1.1, not the frozen 1.0). `keep_alive` is also absent. |
| 4 | Request timeout and step limit differ | **Partly false.** The model kwarg says 120 s, but `runtime.Agent.query` overwrites it with `min(180, remaining)`; `step_limit=28` equals the frozen `actions + 8`. Effective values match. |
| 5 | Logging, model verification, GPU lock, deadline differ | **Confirmed.** There is no GPU lock, no `exclusive_gpu`, no `/api/show` model identity, no server-log capture, no sampler wire verification, no container label and no isolation preflight. Live planning also runs **inside** the 600-second task deadline, while saved replay does not, so live and replayed guidance get different coding time. |
| 6 | Uses the earlier local public checker | **Confirmed.** It requires Sam's bundle schema (`check.py`, `public_tests.json`); public feedback does not come from Peter's judge. |
| 7 | Orchestration uses a separate JSON loop | **Confirmed.** `orchestrate.py` never runs mini-SWE-agent; its README and `MERGED_INTEGRATION.md` say so. |
| 8 | Smoke results do not establish benefit | **Confirmed.** Two synthetic tasks per module, on a Mac MLX Qwen with 2,000–4,000 output tokens, no matched baseline and no hidden evaluation. The planning Codex smoke ended `RepeatedFormatError` after 3 length-truncated responses. |
| 9 | Guidance runners bypass the portable host adapter | **Confirmed.** `plan_once.py` bypasses `local_agent.platform_support.Settings`, the portable image manifest and `model_lock`. |

## 5. Further findings

* **Live API path risk.** `FrontierPlanner` calls `litellm.completion(max_tokens=…)` with no reasoning-effort control. LiteLLM 1.81.16 predates `gpt-6.2-sol`, so whether it maps `max_tokens` to `max_completion_tokens` is unknown. Its cost lookup will probably return `None`. A failed paid request would still count against tonight's 12-request cap, so the integrated backend uses a direct, explicitly parameterized OpenAI client with a ledger instead.
* **Judge task pool.** After removing the pilot and main manifests (68 IDs) and the 75-ID scored union, `test6` AtCoder leaves **0 easy, 2 medium (abc392_d, abc396_d) and 32 hard** tasks. 28 of the 75 previously scored IDs are also in the judge's main/pilot manifests (for example abc387_c, abc390_a, arc195_a). The team should know the main cohort is partly previously scored.
* **Task ID normalization.** Earlier evaluator IDs are `atcoder-abc397_b`; judge IDs are `lcb-atcoder-abc397_b`. Exclusion checks must strip the `lcb-` prefix.
* **Judge portability.** `judge/setup.sh` is POSIX `sh`, calls `python3`, and its unit tests need `fcntl`. On Windows it needs Git Bash/WSL, and only the container-side code runs there. The Docker image itself is multi-arch (digest-pinned `python:3.12-slim`).
* **Version drift.** Ollama 0.40.17 is not the 0.40.16 measured in the frozen baseline. Tonight's integrated A runs must not be pooled with historical A results.
* **Python mismatch.** The judge runs candidates under Python 3.12, while the agent sandbox uses 3.11. The judge timeline recommends 3.12 but does not enforce it. The integrated backend keeps the frozen 3.11 agent image to preserve the measured agent environment and records both versions.
* **Two statement formats.** Sam's bundles use raw `question_content`; Peter's `problem.md` adds the title and a stdin/stdout submission note. The integrated backend uses Peter's `problem.md` text for the agent and the frontier alike, so guidance and coding see identical statements.

## 6. Paper-alignment assessment

| Paper | Teammate adaptation | Gap |
| --- | --- | --- |
| PlanSearch (Wang et al., ICLR 2025) | One request producing observations and a solution sketch with quoted observations | No observation-subset combination, no second-order observations, no diversity search, no pseudocode stage. This matches the proposal's "single-plan transfer" scope. The paper's own finding is that solve rates polarize on sketch correctness (§3.3), which predicts that C helps exactly when the sketch is right. |
| Spec-driven test generation (Tufano et al., SpecOps 2026) | PRE/POST/test-suggestion/unspecified sections from the public statement | The paper extracts contracts from **existing code** to drive **test generation**, with Tested/Untested states. Our adaptation derives them from requirements to guide **implementation**, and every condition is Unverified. This is consistent with the proposal ("natural-language contracts to guide code implementation"). |
| SWE-agent (Yang et al., NeurIPS 2024) | mini-SWE-agent bash-only ACI, heredoc writes, format-error recovery | No linter guardrail on edits, no special empty-output message, no history collapsing. These are ACI features the paper credits with gains. The frozen agent is a thin bash ACI. |

## 7. Original baseline vs. teammate guidance runner

| Setting | Frozen `heredoc-v6-16k-common` | `plan_once.py` |
| --- | --- | --- |
| Entry point | `local_eval_v2/runtime.run` (via `local_agent`) | Own construction of `runtime` classes |
| Output tokens | 4,096 | 4,000 |
| Sampler | temp 0.2, top_k 40, top_p 0.9, min_p 0, repeat 1.0/64, penalties 0, seed 2108 (wire-verified) | temp 0.2 only, no seed |
| Request timeout | min(180, remaining) | same in effect (overwritten by `Agent.query`) |
| Step limit / actions / repairs / seconds | 28 / 20 / 3 / 600 | 28 / 20 / 3 / 600 (planning time counted inside the 600 s for live providers) |
| GPU lock, exclusive GPU, model identity, server log | yes | no |
| Image | `python:3.11-slim-bookworm` verified by ID | same tag, unverified |
| Public feedback | bundle `check.py` | bundle `check.py` |
| Instance template | `{{task}}` | `{{task}}\n\nUpfront {{guidance_label}}:\n{{guide}}` |

## 8. Portability support found

`local_agent/platform_support.py` selects `windows` (fixed `E:\CSC2108Local`, historical lock) or `portable` (`CSC2108_ROOT`, `CSC2108_OLLAMA_ENDPOINT`, `CSC2108_VENDOR`, `fcntl` advisory lock). `local_agent/portable.py` runs the **unchanged** `runtime.run` bytecode with rebound host globals (server-log path, output-root check, Ollama endpoint, NVIDIA telemetry, image identity). CI runs `test_portable` plus an offline import on macOS, Ubuntu and Windows. That is the right abstraction to extend. The integrated guided backend composes with it rather than adding a second portability layer.

Discovered platform-specific problems: `local_eval_v2/common.py` hardcodes `E:` paths (adapted by the bindings), `runtime.run` calls `nvidia-smi` (adapted), the judge setup is POSIX-only, and the judge tests import `fcntl`.

## 9. What requires modification (plan)

1. A new adapter (`guided_agent/`) that runs the frozen `runtime.run` bytecode for A, C and D alike. It overrides only the agent's instance template (guidance block, empty for A) and the environment's recognized public-test command, which is routed to Peter's `judge-public`. Frozen files stay untouched and hash-verified.
2. A task builder that reuses `judge/build_data.py` to create judge-format tasks and the agent's public bundle under the data root, outside Git.
3. Guidance providers: Codex-authored replay (isolated `codex exec`, artifact compatible with `SavedPlan`/`SavedContract`) and a direct OpenAI client with a request/cost ledger.
4. Peter's run-record handoff per attempt and a separate hidden-evaluation command.
