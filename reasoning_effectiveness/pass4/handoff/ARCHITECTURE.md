# Architecture: one shared mini-SWE-agent, five conditions

## 1. Layers

```
python -m guided_agent batch PLAN.json            (guided_agent/__main__.py: validate plan, GPU wait, resume)
 └─ per attempt: child process "run-one SPEC"     (runner.run_child: hard outer timeout, owned-container cleanup)
     └─ runner.run_attempt(spec)
         ├─ agent_config.resolve(spec.agent)                      shared-agent configuration (versioned)
         ├─ local_agent.cli.verify()                              38 frozen file hashes, packages, images, digest
         ├─ guidance.load_for_run()            C, D               statement-hash-bound artifact (teammates' replay classes)
         ├─ contract_checks                    D-active only      parse + benchmark-safe validation of K-checks
         ├─ backend.frozen_runtime()                              local_eval_v2/runtime.py (Windows) or portable adapter
         ├─ backend.judge_client('public').up()                   team judge, public suite only
         ├─ diagnosis.DiagnosisController      E                  one-shot trigger + delivery into the live session
         ├─ frontier_coder                     B                  frontier model substituted for TextModel
         ├─ backend.make_classes()                                GuidedAgent + JudgedEnvironment (below)
         ├─ backend.bound_run()                                   the frozen run() bytecode with rebound globals
         └─ writes result.json, attempts.jsonl, submission.py, measurement.json
python -m guided_agent evaluate BATCH              judge-hidden after all attempts -> eval/<run_id>.json
python -m guided_agent measure BATCH               rebuild measurement.json + measurements.jsonl
```

## 2. The shared agent and its seams

The agent is the original frozen mini-SWE-agent 2.4.6 runner `local_eval_v2/runtime.run`. Its bytecode is executed
unchanged. Conditions and agent configurations differ **only** through globals rebound in `backend.bound_run`:

| Rebound global | Who uses it | Change |
| --- | --- | --- |
| `Agent` → `GuidedAgent` | C, D (guidance template), E (diagnosis delivery), l1 (self-plan block) | first user message template; one extra user message for E |
| `Environment` → `JudgedEnvironment` | all | `python -I /public/check.py` goes to judge-public; l4 receipts; D-active checks |
| `TextModel` → frontier coder | B | the coding model |
| `read` → profile overlay | l2, l3 | thinking / output tokens / context, verified on the wire |
| `exclusive_gpu` → check, then self-plan | l1 | one bounded local planning call |
| `exclusive_gpu`, `api`, `MODELS` | B | no local model is touched |

Everything else is the frozen code: system prompt, the regex action parser, format-error handling, observation
template, sandbox (`python:3.11-slim-bookworm`, network none, read-only, unprivileged, 512 MB, 64 pids), budgets
(20 actions, 3 repair groups, 600 s, 180 s per request), candidate extraction and telemetry. Host differences come
from `local_agent` (Windows: original globals; macOS/Linux: `portable.adapted_run`).

## 3. Condition boundaries

| Condition | Frontier calls | When | Input to the frontier | What the local agent receives |
| --- | --- | --- | --- | --- |
| A | 0 | — | — | the statement (frozen `{{task}}`) |
| B | one per agent turn (frontier is the coder) | during the run | the full agent transcript | — (no local model) |
| C | 1 (plan) | before the run, once per task | statement + plan prompt | statement + plan block |
| D | 1 (contract) | before the run, once per task | statement + contract prompt | statement + contract block (+ D-active: executed check results after each public test) |
| E | 0 or 1 (diagnosis) | at the first qualifying public failure | statement + failed program + its public report | one extra user message; same session, files, counters, budgets |

**Never seen by any model:** hidden tests, reference solutions or earlier experiment outcomes. The frontier never
sees the repository, and Codex runs tool-less in an empty directory.

## 4. Data flow and storage

* **Study root:** everything lives under `CSC2108_STUDY_ROOT` (outside the checkout; `common.study_root` refuses a
  path inside it):
  * `bundles/<task>` holds the agent's public files;
  * `judge/tasks` and `judge/hidden` hold the judge's suites;
  * `guidance/<label>/*.json` holds the write-once artifacts;
  * `runs/<batch>/<run>/` holds attempt outputs;
  * `api-ledger.json` is the paid-request ledger. `CSC2108_API_LEDGER` can share one ledger across roots.
* **Hidden tests:** loaded only into the judge-hidden container, which runs only in `evaluate`, after the attempts.
  Hidden results never reach a model.
* **Paid requests:** a write-ahead reservation in the ledger before every request, a hard request/USD ceiling in
  code, and no retries.

## 5. Reproducibility

* **Frozen agent:** 38 file hashes are verified in every attempt (`identity.frozen_files_verified`).
* **Model:** the digest is recorded; sampler options are verified on the wire (`identity.sampler_wire_verified`).
* **Determinism:** at temperature 0.2 with a fixed seed, reruns are token-identical. Passes 2–4 reproduced
  historical candidates byte for byte, so seeds are the only source of variation.
* **Guidance:** generated once per task, frozen by hash, replayed (never regenerated after outcomes).
* **Plans:** `integrity.validate_plan` refuses mislabelled or colliding attempts. With `"frozen": true` it allows
  only the primary configuration; `check_unchanged` refuses resuming a batch with a different plan.
