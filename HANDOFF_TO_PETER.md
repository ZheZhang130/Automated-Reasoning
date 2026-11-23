# Handoff to Peter: running and measuring A/B/C/D/E

This branch is the agent implementation, not a benchmark orchestrator. You own the final evaluation pipeline;
this document tells you exactly what to call, what to read, and what not to touch.

## 1. What is ready

* **One CLI:** `python -m guided_agent` runs all five conditions through **one shared mini-SWE-agent** (the original
  frozen runner, Qwen3.5 9B) with one judge (`csc2108-judge:0.2.1`).
* **Every attempt writes the same records:**
  * `result.json`, the full record;
  * `measurement.json`, the stable schema in `MEASUREMENT_SCHEMA.md`;
  * `attempts.jsonl`, the judge-public history;
  * `submission.py`.
* **Hidden scoring** is a separate step after all attempts.
* **Configuration:** the selected per-condition configuration is in `CONDITIONS.md` and its hashes are in
  `FINALIZATION_MANIFEST.json`.

## 2. Setup (once per machine)

Windows (the frozen reference host):

```powershell
. .\local_baseline\env.ps1                          # data root E:\CSC2108Local, project Ollama on 127.0.0.1:11435
$py = 'E:\CSC2108Local\.venv\Scripts\python.exe'   # Python 3.11.9 with local_agent/requirements.txt
& $py -m local_agent verify                         # 38 frozen hashes, packages, images, model digest
```

macOS/Linux use the portable adapter (`--backend portable`; see `docs/MACOS.md`). Keep Mac results a separate
hardware cohort.

Set a study root **outside the checkout**. It holds bundles, judge suites, guidance artifacts, runs and the ledger:

```bash
export CSC2108_STUDY_ROOT=/path/outside/checkout/final-study
export LITELLM_LOCAL_MODEL_COST_MAP=True PYTHONIOENCODING=utf-8
python -m guided_agent prepare-tasks --ids lcb-atcoder-abc394_b ...   # judge suites + agent bundles from the pinned shard
```

`OPENAI_API_KEY` and `FRONTIER_MODEL=openai/gpt-6.2-sol` go in the `.env` file that `guided_agent.providers.env_file()`
reads. That file is never in Git, never printed, and never passed to Codex or to a sandbox.

## 3. Generate guidance once (C and D), before any run

```bash
python -m guided_agent author --provider api --prompt-id plan-v1     --tasks <ids> --label final-plans     --purpose "final benchmark C guidance"
python -m guided_agent author --provider api --prompt-id contract-v1  --tasks <ids> --label final-contracts --purpose "final benchmark D guidance"
```

* **Artifacts:** each is a write-once `guidance/<label>/<task>.<prompt>.api.json`, bound to the statement's sha256.
* **Freeze, never regenerate:** record their hashes in your freeze manifest before the first run. Never regenerate
  one after seeing an outcome; that would be rejection sampling.
* **Reuse:** one artifact serves every seed of that task. Measurement reports the generation cost once per
  artifact (`cost.api_cost_usd_upfront`). You choose one-off or amortized accounting.

## 4. Run attempts

A plan is a JSON list of attempts. Each attempt fixes the task, condition, seed, agent configuration, artifacts,
providers and budgets; budgets are the frozen defaults.

```json
{"batch": "final-s2108", "frozen": true, "outer_timeout": 1000, "attempts": [
  {"task_id": "lcb-atcoder-abc394_b", "condition": "A", "seed": 2108, "agent": "frozen-v6"},
  {"task_id": "lcb-atcoder-abc394_b", "condition": "B", "seed": 2108, "variant": "api",
   "coder": {"provider": "api", "max_requests": 28, "purpose": "final B"}},
  {"task_id": "lcb-atcoder-abc394_b", "condition": "C", "seed": 2108, "agent": "frozen-v6",
   "guidance": "<study>/guidance/final-plans/lcb-atcoder-abc394_b.plan-v1.api.json"},
  {"task_id": "lcb-atcoder-abc394_b", "condition": "D", "seed": 2108, "agent": "frozen-v6",
   "guidance": "<study>/guidance/final-contracts/lcb-atcoder-abc394_b.contract-v1.api.json"},
  {"task_id": "lcb-atcoder-abc394_b", "condition": "E", "seed": 2108, "agent": "frozen-v6",
   "diagnosis": {"provider": "api", "purpose": "final E", "prompt_id": "diagnosis-v1", "delivery": "deliver-v1"}}
]}
```

```bash
python -m guided_agent batch PLAN.json       # sequential, GPU lock, waits politely for foreign models, resumable
python -m guided_agent evaluate <study>/runs/final-s2108     # judge-hidden after ALL attempts; writes eval/<run_id>.json
python -m guided_agent measure  <study>/runs/final-s2108     # (re)build measurement.json + measurements.jsonl
```

These are the primary configurations of `CONDITIONS.md`. In a `"frozen": true` plan every local attempt must name `"agent": "frozen-v6"` (`agent_config.PRIMARY_AGENT`).

**What `"frozen": true` refuses:** a missing or non-primary `agent`, smoke budgets, test hooks, non-primary prompts or
injections, and attempts without an explicit seed.

**Run identity:** the run directory name is `<task>-<condition>[-<variant>]`, so give every seed a variant (for
example `"variant": "s2109"`). The plan validator refuses collisions.

## 5. Integration boundaries

**Call these:**

* **CLI:** `prepare-tasks`, `author`, `batch`, `evaluate`, `measure`, `schema`;
* **in Python:** `guided_agent.runner.run_attempt(spec)` (one attempt) and `guided_agent.measurement.build(run_dir)`.

**Do not modify:**

* `local_eval_v2/`, `local_baseline/`, `local_optimization/`: frozen; 38 hashes are verified on every attempt;
* `local_agent/`: host adapters and verify;
* `judge/`: your judge; version changes need a new version string and regression tests *before* a cohort is frozen;
* `planning_frontier/`, `contract_frontier/`: teammates' prompts and replay classes, imported unchanged;
* `guided_agent/guidance.py` prompts and templates: any change is a new versioned ID, never an edit.

**Authoritative fields:**

* **hidden correctness:** `eval/<run_id>.json` → `measurement.correctness.hidden_*`;
* **costs:** the API ledger → `frontier.requests[].cost_usd`;
* **configuration identity:** `identity.agent_config_id` / `_sha256`, `identity.guidance_artifact_sha256`, prompt
  IDs, `identity.frozen_files_verified`;
* `result.json` holds more detail, but its field names are not a stable contract.

**How E gets its diagnosis live:**

* The judged environment arms a pending diagnosis at the first qualifying public failure (WA/RE/TLE/CE of a
  non-empty candidate; never an infrastructure error).
* The agent then makes **one** provider call, before its next model query, with an evidence packet: statement,
  exact judged bytes and that report, bound by sha256.
* It appends one user message. Local deadlines are suspended for exactly the wait, and nothing is reset.

**Frozen-configuration verification:** `local_agent.cli.verify` runs inside every attempt, and its result is
recorded. A changed frozen file stops the attempt before inference.

**Storage:** everything stays under the study root. Hidden suites exist only inside the judge-hidden container
loaded by `evaluate`.

**Independent hidden judging:** only `evaluate`, only after the batch. It never runs inside an agent process.

**Resuming interrupted batches:**

* Rerun the same `batch PLAN.json`. Finished attempts (with `result.json`) are skipped.
* An interrupted attempt's directory is kept as `*.incomplete-<id>` and redone under a new run ID.
* Changing the plan of an existing batch is refused.
* Infrastructure failures (`correctness.infrastructure_failure`) are rerun; candidate failures never are.

**Preventing double billing:**

* Every paid request is reserved in the ledger (write-ahead) before it is sent; ceilings are enforced in code and
  file.
* There are no retries anywhere. A failed request is recorded and the run continues (E) or ends (B).
* B's per-run `max_requests` caps one attempt.
* Use one ledger for the whole study (`CSC2108_API_LEDGER` if you split study roots).
* Set the ceilings for the final run in `guided_agent/providers.py` (`MAX_REQUESTS`, `MAX_USD`) as a team
  decision, and record them.

**Keeping hidden tests away from agents:**

* The agent container mounts only `bundles/<task>` (statement, public tests, check stub), read-only.
* Judge-public holds only public suites.
* No frontier prompt contains hidden data; packets contain only public evidence.

## 6. Test fixtures for your pipeline

`guided_agent/fixtures/<role>/` holds sanitized records of 12 roles: A success, self-plan success, truncation
without a program, action-budget exhaustion, C success, D contract, E triggered with repair, E untriggered, E
provider error, B API with repair, context overflow, infrastructure error. Each has `result.json`,
`measurement.json`, `attempts.jsonl` and `eval.json`. There are no programs, statements or model texts;
`INDEX.json` and `fixtures/README.md` list them. Use them to test
ingestion without running any model.

**Context overflow** (`correctness.context_overflow`): the prompt reached the 16K window and the next model request
failed. The runner records `infra_error`, but the failure is deterministic: the same seed reproduces it. Count it
as a failed attempt; do not rerun it as infrastructure.

## 7. Tests (what proves what)

```bash
python -m unittest guided_agent.test_guided guided_agent.test_pass2 guided_agent.test_pass3 guided_agent.test_pass4 local_agent.test_portable
CSC2108_INTEGRATION=1 python -m unittest guided_agent.test_pass2.IntegrationE guided_agent.test_pass4.IntegrationFinal   # Docker + judge
```

| Required property | Test(s) |
| --- | --- |
| A runs without frontier guidance | `test_guided.Backend.test_agent_template_unchanged_for_a`, `test_pass2.IntegrationE.test_6_a_is_unchanged_by_the_e_machinery` |
| B codes through the same interface | `test_pass2.FrontierCoder.test_actions_use_the_frozen_text_protocol`, `test_non_ollama_globals_never_touch_the_gpu_or_ollama_metadata` |
| C injects its plan once | `test_guided.GuidanceArtifacts.*` (statement-bound replay, write-once, parallel templates) |
| D delivers its contract | `test_guided.GuidanceArtifacts.test_plan_and_contract_templates_are_parallel`, `test_replay_through_teammate_classes` |
| E triggers once on a qualifying public failure | `test_pass2.TriggerPolicy.*`, `IntegrationE.test_5_only_first_of_multiple_failures_triggers` |
| E preserves the same session | `IntegrationE.test_1_diagnosis_then_same_session_repair_passes` (history only grows, one action counter) |
| E does not trigger on infrastructure failures | `IntegrationE.test_4_judge_infrastructure_error_requests_nothing`, `test_pass3.EEvidence.*` |
| Budgets are enforced | `IntegrationFinal.test_2_action_budget_is_enforced_with_a_program_on_disk`, `test_pass2.FrontierCoder.test_request_cap_stops_cleanly_and_errors_are_never_retried`, `test_pass2.Delivery.test_frontier_wait_is_excluded_from_local_time` |
| API request accounting and caps | `test_guided.Providers.*`, `test_pass3.LedgerConcurrency.*`, `test_pass2.FrontierCoder.test_api_coder_respects_the_ledger_without_network` |
| Judge interface and candidate extraction | `test_guided.Backend.test_recognized_test_goes_to_judge_and_counts_an_action`, `test_pass3.JudgeSemantics.*`, `IntegrationFinal.test_2` (submission extracted) |
| Run records follow the measurement schema | `test_pass4.MeasurementSchema.*` (fields, units, every fixture conforms), `IntegrationFinal` (each attempt writes a conforming `measurement.json`) |
| Windows/Linux/macOS software paths | `test_guided.Backend.test_composes_with_portable_host_adapter`, `local_agent.test_portable`, CI matrix (macOS, Ubuntu, Windows) |
| Frozen configuration and provenance hashes | `test_pass4.Manifest` (prompts, templates, agent configurations, frozen selection), `local_agent verify` (38 hashes) in every attempt |

## 8. Still yours to decide or do

See `CONDITIONS.md` §"Open decisions". Before the final freeze:

* decide those items;
* generate and freeze all C and D guidance with the API;
* set the ledger ceilings;
* run a small smoke batch of all five conditions on the synthetic fixture and one real task.

The final benchmark design options (60/90/120 tasks, seeds, strata, costs) are on the development branch
(`reasoning_effectiveness/pass3/FINAL_BENCHMARK_OPTIONS.md`, updated by `pass4/FINAL_REPORT.md`).
