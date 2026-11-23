# Measurement schema `csc2108-run-measurement-v1`

Every attempt writes `<run dir>/measurement.json`. `python -m guided_agent evaluate BATCH` refreshes it with the
hidden verdict, and `python -m guided_agent measure BATCH` rebuilds it for a whole batch and writes
`<batch>/measurements.jsonl`. The builder is `guided_agent/measurement.py`. It **only reads** artifacts the
attempt already wrote, so it can be rerun at any time. The table below is generated from `measurement.FIELDS`
(`python -m guided_agent schema`), the same list the conformance test checks.

## Rules

* **Units** are in the field name: `_seconds`, `_tokens`, `_usd`, `_chars`. Times are wall-clock seconds; costs are
  USD.
* **`null` means "not available from the source"**, never zero. Examples:
  * Ollama does not report thinking tokens separately, so `local_inference.reasoning_tokens` is always `null`.
    `completion_tokens` includes thinking, and `thinking_chars` gives its size.
  * A Codex-replay request has `cost_usd: null`: it is not billed. Its token counts include Codex's own harness
    context (about 9–10K input tokens per request), so they are **not** API-equivalent.
* **Measured, derived, configuration, identity, modelled.** Only `cost.modelled_*` is modelled. It appears only
  when you pass `--watts` (and `--usd-per-kwh`) to `measure`, it is labelled `modelled`, and the assumptions are
  stored next to it.
* **Upfront versus run-time frontier cost.**
  * C and D guidance is generated once per task before any run: `frontier.requests[].upfront = true`, with
    `cost.api_cost_usd_upfront`. The same artifact (same `identity.guidance_artifact_sha256`) can serve several
    seeds. Amortize by counting the attempts that share the hash; for a one-off task the full cost belongs to the
    single attempt.
  * E diagnoses and B coder turns happen during the run: `cost.api_cost_usd_run`.
* **Time.**
  * `time.equal_opportunity_seconds` is the coding time the 600-second budget sees (frontier wait and the l1
    self-plan call excluded).
  * `time.wall_seconds` is the whole attempt including setup.
  * `time.orchestration_seconds` is what remains of `local_coding_seconds` after inference, sandbox tools, public
    tests, frontier waits and the self-plan call. It is derived and approximate.
* **GPU.** `cost.gpu_memory_sample` is two `nvidia-smi` samples (before and after), **not** GPU active time. Use
  `local_inference.total_inference_seconds` as the GPU-busy proxy.
* **Context overflow:** `correctness.context_overflow = true` marks a run whose prompt reached the 16K context, so
  the next model request failed. The runner records `infra_error`, but the failure is deterministic. It is **not**
  an infrastructure failure (`infrastructure_failure = false`); count it as a failed attempt.
* **Authoritative fields for scoring:** `correctness.hidden_status` / `hidden_passed` / `hidden_total` (judge-hidden
  0.2.1, after all attempts). Count `missing_submission` as a failure. Exclude
  `correctness.infrastructure_failure = true` for that task and repeat across all conditions.
* **Timeline fields** (`agent.seconds_to_*`) count from the first local model request, using Ollama's
  response timestamps. They are `null` for B, where there are no local responses.

## Fields

| Field | Type | Unit | Nullable | Source / computation | Kind | Applies to |
| --- | --- | --- | --- | --- | --- | --- |
| `schema` | str |  | no | constant | identity | all |
| `identity.run_id` | str |  | no | result.json | identity | all |
| `identity.task_id` | str |  | no | result.json | identity | all |
| `identity.condition` | str | A|B|C|D|E | no | result.json | identity | all |
| `identity.seed` | int |  | no | result.json | configuration | all |
| `identity.batch` | str |  | yes | result.json | identity | all |
| `identity.agent_config_id` | str |  | no | result.json agent_config | configuration | all |
| `identity.agent_config_sha256` | str | sha256 | yes | agent_config definition | configuration | all |
| `identity.guidance_prompt_id` | str |  | yes | guidance artifact | configuration | C, D |
| `identity.injection` | str |  | yes | spec | configuration | C, D |
| `identity.diagnosis_prompt_id` | str |  | yes | spec | configuration | E |
| `identity.diagnosis_delivery` | str |  | yes | spec | configuration | E |
| `identity.source_commit` | str | git sha | yes | git rev-parse at run time | identity | all |
| `identity.source_dirty` | bool |  | yes | git status of agent paths | identity | all |
| `identity.coding_model` | str |  | no | result.json | identity | all |
| `identity.coding_model_digest` | str | sha256 | yes | Ollama /api/tags (local only) | measured | A, C, D, E |
| `identity.profile` | str |  | no | result.json | configuration | all |
| `identity.profile_config` | object |  | yes | frozen record profile_config (overlay applied) | configuration | A, C, D, E |
| `identity.frontier_provider` | str | openai-api|codex-replay|... | yes | guidance/diagnosis/coder records | identity | B, C, D, E |
| `identity.frontier_requested_model` | str |  | yes | guidance/diagnosis/coder records | identity | B, C, D, E |
| `identity.frontier_observed_model` | str |  | yes | API response model field | measured | B, C, D, E (API) |
| `identity.dataset_revision` | str | git sha | no | common.LCB_REVISION | identity | all |
| `identity.judge_version` | str |  | yes | judge-public info | identity | all |
| `identity.judge_public_tests_sha256` | str | sha256 | yes | judge-public info | identity | all |
| `identity.guidance_artifact_sha256` | str | sha256 | yes | artifact file | identity | C, D |
| `identity.frozen_files_verified` | int | files | yes | local_agent verify | measured | all |
| `identity.sampler_wire_verified` | bool |  | yes | captured Ollama requests | measured | A, C, D, E |
| `identity.host` | object |  | no | platform | identity | all |
| `identity.host_backend` | str | windows|portable | no | result.json | identity | all |
| `correctness.candidate_produced` | bool |  | no | submission_sha256 present | measured | all |
| `correctness.submitted` | bool |  | no | raw exit = Submitted | measured | all |
| `correctness.public_tests_invoked` | int | count | no | attempts.jsonl | measured | all |
| `correctness.public_pass` | bool |  | no | any public test passed | measured | all |
| `correctness.final_public_status` | str | pass|candidate_failure|none | no | last public test | measured | all |
| `correctness.public_runtime_error_cases` | int | cases | no | sum of RE verdicts over public tests | measured | all |
| `correctness.hidden_status` | str | pass|candidate_failure|missing_submission|... | yes | eval/<run_id>.json | measured | all |
| `correctness.hidden_passed` | int | cases | yes | eval/<run_id>.json | measured | all |
| `correctness.hidden_total` | int | cases | yes | eval/<run_id>.json | measured | all |
| `correctness.exit_status` | str | submitted|action_limit|repair_limit|deadline|agent_error|infra_error | no | runner.exit_status | measured | all |
| `correctness.raw_exit_status` | str |  | yes | mini-SWE-agent exit | measured | all |
| `correctness.infrastructure_failure` | bool |  | no | exit infra_error or setup error, excluding context_overflow | derived | all |
| `correctness.setup_error` | str |  | yes | result.json | measured | all |
| `correctness.context_overflow` | bool |  | no | the model request failed (Ollama connection error) when the last prompt plus output was within 1,024 tokens of num_ctx: the agent exhausted its context; recorded by the runner as infra_error but deterministic, so not an infrastructure failure | derived | A, C, D, E |
| `local_inference.calls` | int | requests | no | ollama-responses.json | measured | A, C, D, E (0 for B) |
| `local_inference.prompt_tokens` | int | tokens | yes | prompt_eval_count | measured | A, C, D, E |
| `local_inference.completion_tokens` | int | tokens | yes | eval_count (includes thinking) | measured | A, C, D, E |
| `local_inference.reasoning_tokens` | int | tokens | yes | not reported by Ollama: always null | measured | A, C, D, E |
| `local_inference.thinking_chars` | int | characters | yes | message.thinking | measured | A, C, D, E |
| `local_inference.max_prompt_tokens` | int | tokens | yes | max prompt_eval_count | measured | A, C, D, E |
| `local_inference.context_tokens_limit` | int | tokens | yes | profile num_ctx | configuration | A, C, D, E |
| `local_inference.output_tokens_limit` | int | tokens | yes | profile num_predict | configuration | A, C, D, E |
| `local_inference.prompt_eval_seconds` | float | s | yes | prompt_eval_duration | measured | A, C, D, E |
| `local_inference.eval_seconds` | float | s | yes | eval_duration | measured | A, C, D, E |
| `local_inference.load_seconds` | float | s | yes | load_duration | measured | A, C, D, E |
| `local_inference.total_inference_seconds` | float | s | yes | sum of total_duration | measured | A, C, D, E |
| `local_inference.truncated_responses` | int | responses | no | done_reason == 'length' | measured | all |
| `local_inference.format_errors` | int | responses | no | trajectory FormatError messages | measured | all |
| `local_inference.self_plan` | object |  | yes | self-plan.json (agent l1 only) | measured | l1 configurations |
| `agent.actions` | int | actions | no | Budget | measured | all |
| `agent.repairs` | int | repair groups | no | Budget | measured | all |
| `agent.model_calls` | int | requests | no | mini-SWE-agent n_calls | measured | all |
| `agent.source_writes` | int | commands | no | commands writing solution.py | derived | all |
| `agent.distinct_sources` | int | versions | no | distinct snapshot hashes | derived | all |
| `agent.unchanged_writes` | int | commands | no | write left the snapshot unchanged | derived | all |
| `agent.rewrites_of_failed_candidate` | int | commands | no | write produced a source that already failed public tests | derived | all |
| `agent.repeated_responses` | int | responses | no | assistant message identical to the previous one | derived | all |
| `agent.public_test_attempts` | int | count | no | attempts.jsonl | measured | all |
| `agent.seconds_to_first_valid_action` | float | s from first model request | yes | Ollama created_at/total_duration | derived | A, C, D, E |
| `agent.seconds_to_first_executable_candidate` | float | s from first model request | yes | first public test with an AC or WA case | derived | A, C, D, E |
| `agent.seconds_to_first_public_test` | float | s from first model request | yes | Ollama timestamps | derived | A, C, D, E |
| `frontier.requests` | list |  | no | see frontier.requests[] fields below | measured | all ([] for A) |
| `frontier.requests[].type` | str | guidance|diagnosis|coder_turn | no | record | identity | B, C, D, E |
| `frontier.requests[].prompt_id` | str |  | yes | record | configuration | C, D, E |
| `frontier.requests[].provider` | str |  | yes | record | identity | B, C, D, E |
| `frontier.requests[].utc` | str | ISO 8601 UTC | yes | record | measured | B, C, D, E |
| `frontier.requests[].input_tokens` | int | tokens | yes | provider usage (Codex: includes its harness context) | measured | B, C, D, E |
| `frontier.requests[].output_tokens` | int | tokens | yes | provider usage | measured | B, C, D, E |
| `frontier.requests[].reasoning_tokens` | int | tokens | yes | provider usage | measured | B, C, D, E |
| `frontier.requests[].cached_input_tokens` | int | tokens | yes | provider usage | measured | B, C, D, E |
| `frontier.requests[].latency_seconds` | float | s | yes | provider call wall time | measured | B, C, D, E |
| `frontier.requests[].cost_usd` | float | USD | yes | API ledger (null for Codex replay) | measured | B, C, D, E (API) |
| `frontier.requests[].status` | str | ok|error category | no | record | measured | B, C, D, E |
| `frontier.requests[].request_sha256` | str | sha256 | yes | artifact/packet hashes | identity | C, D, E |
| `frontier.requests[].response_sha256` | str | sha256 | yes | guidance/diagnosis text hash | identity | C, D, E |
| `frontier.requests[].upfront` | bool |  | no | generated before the run (C/D) | identity | C, D |
| `frontier.n_requests` | int | requests | no | len(requests) | derived | all |
| `frontier.cost_usd` | float | USD | yes | sum of request costs; null if any request has no measured cost | measured | all |
| `frontier.wait_seconds_during_run` | float | s | no | E diagnosis wait + B coder latency | measured | B, E |
| `frontier.provider_failures` | int | requests | no | requests with status != ok | measured | B, C, D, E |
| `condition.guidance` | object |  | yes | generated, delivered, sha256, generation cost/latency | measured | C, D |
| `condition.diagnosis` | object |  | yes | trigger, hashes, delivery, after-effects | measured | E |
| `time.wall_seconds` | float | s | no | run_attempt wall (setup included) | measured | all |
| `time.local_coding_seconds` | float | s | yes | frozen run() duration | measured | all |
| `time.local_inference_seconds` | float | s | yes | = local_inference.total_inference_seconds | measured | A, C, D, E |
| `time.frontier_seconds` | float | s | no | frontier.wait_seconds_during_run (upfront guidance excluded) | measured | all |
| `time.public_test_seconds` | float | s | no | judge-public calls | measured | all |
| `time.sandbox_tool_seconds` | float | s | no | other sandbox commands | measured | all |
| `time.orchestration_seconds` | float | s | yes | local_coding - inference - tools - tests - frontier - self-plan | derived | all |
| `time.equal_opportunity_seconds` | float | s | yes | local_coding minus frontier wait and self-plan (the 600 s budget clock) | derived | all |
| `cost.api_cost_usd_run` | float | USD | yes | frontier requests made during the run | measured | B, E (API) |
| `cost.api_cost_usd_upfront` | float | USD | yes | guidance generation (one-off; amortize over attempts sharing the artifact) | measured | C, D (API) |
| `cost.gpu_memory_sample` | object |  | yes | nvidia-smi before/after (not GPU active time) | measured | A, C, D, E |
| `cost.modelled_local_energy_kwh` | float | kWh | yes | local_inference_seconds x assumed watts; only if assumptions given | modelled | A, C, D, E |
| `cost.modelled_local_cost_usd` | float | USD | yes | energy x assumed price; only if assumptions given | modelled | A, C, D, E |
| `cost.modelling_assumptions` | object |  | yes | watts and price supplied by the caller | configuration | A, C, D, E |

## Other files per attempt

| File | Content | Authoritative for |
| --- | --- | --- |
| `result.json` | the full run record (superset of the measurement; field names may change between versions) | provenance details |
| `attempts.jsonl` | every judge-public call: result, action number, judged-source hash | public-test history |
| `submission.py` | the final candidate (the frozen agent's last snapshot) | hidden scoring input |
| `agent-<run_id>/` | frozen agent output: `trajectory.json`, `ollama-requests.json`, `ollama-responses.json`, `result.json` | raw telemetry |
| `diagnosis/` (E) | evidence packet, provider log, delivered message | E audit |
| `coder/` (B) | per-turn coder log | B audit |
| `self-plan.json` (`l1-selfplan-v1`) | the local planning call and its text | self-plan audit |
| `<batch>/eval/<run_id>.json` | hidden verdict | **hidden correctness** |

Never copy hidden-test contents, statements or candidate programs into reports; the measurement record contains
none of them.
