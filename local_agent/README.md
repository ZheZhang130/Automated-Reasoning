# Public integration interface

Use `E:\CSC2108Local\.venv\Scripts\python.exe -m local_agent` from the checkout root after initializing [env.ps1](../local_baseline/env.ps1). The [root quick start](../README.md#start-here) assumes the existing installation; [project structure](../docs/PROJECT_STRUCTURE.md) explains paths and platform requirements. No editable install is needed on that machine.

The CLI wraps the existing [selected.py](../local_optimization/selected.py) and [runtime.py](../local_eval_v2/runtime.py) without patching prompts, model parameters, parsing, budgets or action handling. The [dependency audit](dependencies.md) distinguishes those active components from historical modules.

## Commands and preflight

| Command | Behavior |
| --- | --- |
| `verify --offline` | Checks all 38 frozen file hashes, selection/recommendation consistency, original profile identity, Python 3.11.9 and five package pins; parses the prompt without importing the runtime. No service calls or inference. |
| `verify` | Adds inspection of both Docker image IDs and Ollama 11435 model digest/quantization/version. No inference. |
| `run --task PUBLIC_DIRECTORY --output NEW_E_DIRECTORY [--seed 2108]` | Performs `verify`, then invokes the frozen selector/runtime as child processes; the runtime acquires the shared GPU lock and performs isolation/GPU preflight before inference. |
| `evaluate --run COMPLETED_RUN --private-row OFFICIAL_ROW_JSON --output NEW_E_DIRECTORY` | Performs service-enabled `verify` plus a clean evaluator-revision check, then independently judges an extracted candidate. No inference or agent resumption. |

`verify` alone does **not** prove all run prerequisites: it does not check endpoint 11434, GPU availability, Docker disk settings, prepared bundles, the runtime server log or the evaluator checkout. In particular, **`evaluate` currently requires Ollama 11435 to be reachable for preflight even though judging makes no model generation call**. The ordinary `verify` command does not check the evaluator revision; `evaluate` does.

Output directories must be new, on E: and outside this checkout. The CLI never reuses them, downloads a model or automatically retries a run. No model/profile/budget override is exposed through this public interface.

## Trusted public task bundle

| File | Contract |
| --- | --- |
| `task.json` | Required: exactly `task_id`, `version`, `statement`, `submission_path`; the last value must be `solution.py` |
| `check.py` | Trusted public checker executed inside Docker; needed for public testing |
| `public_tests.json` | Public examples consumed by the prepared checker |
| `solution.py` | Optional starter; never a reference solution |

The runtime rejects extra entries, subdirectories and symlinks; the allowlist itself does not guarantee that a checker and its examples exist or agree. Supply a **complete prepared bundle**, with the full problem, interface and any starter requirements in `statement`. This is a Python task-bundle interface, not arbitrary repository repair or a standalone problem-to-bundle converter.

The standard [public_check.py](../local_eval_v2/public_check.py) uses cases with `input` and `output` strings and optional `fn_name`. Stdin/stdout comparison splits whitespace; function-call cases parse JSON input lines as arguments and compare JSON values. The prepared `/public/check.py` is executed, not the repository file automatically: it may be a trusted synthetic checker or an exported copy of the standard checker. Private rows must never be put in the public bundle.

## Frozen configuration

| Setting | Value |
| --- | --- |
| Agent / adapter | mini-SWE-agent 2.4.6 / LiteLLM 1.81.16 |
| Serving endpoint | Ollama `http://127.0.0.1:11435` |
| Model / quantization | `qwen3.5:9b` / Q4_K_M |
| Model digest | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| Profile / protocol | `heredoc-v6-16k-common` / text command fences with literal-heredoc file writes |
| Context / maximum output per response | 16,384 / 4,096 tokens |
| Thinking / temperature | disabled / 0.2 |
| top-p / top-k / min-p | 0.9 / 40 / 0 |
| repeat penalty / repeat_last_n | 1.0 / 64 |
| presence / frequency penalties | 0 / 0 |
| Actions / repair groups / task time | 20 / 3 / 600 seconds |
| Request timeout / retries | Up to 180 seconds, capped by remaining task time / 0 |
| Default seed / keep_alive | 2108 / `10m` |

Source of truth: [final_selection.json](../local_optimization/final_selection.json), [final_recommendation.json](../local_optimization/final_recommendation.json), [profiles.json](../local_eval_v2/profiles.json) and the original runtime. The original `PROMPT` and `FORMAT_ERROR` strings remain in `runtime.py`; historical rendered prompts are in [benchmark provenance](../evidence/local_eval_v2/benchmark_provenance.json).

The 600-second deadline begins before runtime setup; it is not an outer wall-time guarantee for the wrapper. Model loading, setup and actions consume the budget; source extraction, process startup and cleanup add invocation time. The wrapper's `invocation_wall_seconds` measures its child-process interval and envelope creation, excluding the wrapper's preceding identity preflight. Shell actions have their own roughly 27-second inner/30-second host caps, also limited by remaining time. Repair groups count changed source after a recognized failed public check; unchanged rewrites do not count. Compound checker commands can execute tests without entering those counters, a preserved [baseline limitation](../RESULTS_SUMMARY.md).

## Outputs and exit codes

A completed `run` prints one JSON object and saves it as `<output>\result.json`; child console output is redirected to logs. The schema version is 1. Main fields are `run_id`, `status`, `termination_reason`, `candidate_path`, `trajectory_path`, `metadata_path`, `runtime_result_path`, `process_returncode`, `task_id`, `model`, `profile`, `timings`, `usage` and `error`. Paths are absolute; missing candidate/trajectory/result paths are `null`. The wrapper's `run_id` is the outer output directory name; the frozen child's internal `run_id` is `runtime`, so preserve the full paths and outer record when joining results.

| Output | Contents |
| --- | --- |
| `result.json` | Structured interface result, paths, termination reason and usage/timings |
| `metadata.json`, `invocation.json` | Verified identities/image IDs, profile, packages, seed, checkout commit, wrapper hash, task path and child arguments/start time |
| `stdout.log`, `stderr.log` | Child console output |
| `runtime/result.json` | Original action/test/repair events, hashes, GPU measurements, errors and inference counters |
| `runtime/solution.py` | Extracted candidate when available; can be an unchanged starter |
| `runtime/trajectory.json`, `runtime/configuration.json`, `runtime/task.json` | Conversation, serialized effective configuration and public task |
| `runtime/ollama-requests.json`, `runtime/ollama-responses.json`, `runtime/ollama-server.log` | Captured wire traffic and server-log segment; may be absent/partial on early failure |
| `runtime/container.json` | Owned agent container identity recorded during setup |

`Submitted` and candidate-file presence do not prove authorship or correctness. Inspect the original record and independently evaluate. `usage.observed_generated_tokens` sums captured replies; `usage.unobserved_generated_tokens_upper_bound` adds at most 4,096 tokens per uncaptured call, rather than estimating measured tokens. Ollama generation/prefill/load durations are separate from child-process wall time and private judging time.

`run` returns 2 for a child process failure or exact `InfrastructureError` status; other retained agent terminations return 0, including a missing submission. Preflight/unhandled exceptions normally return 1 and can occur before output creation. Interruptions can leave partial artifacts; there is no automatic resume. Always inspect the JSON and logs, rather than treating exit code 0 as a successful solution.

## Independent evaluation

After the public run has finished, use its matching official row in a distinct invocation. From the repository root, with `$pythonExe` set as in the quick start:

```powershell
& $pythonExe -m local_agent evaluate `
  --run E:\CSC2108Local\local-agent-runs\my-task-001 `
  --private-row E:\CSC2108Local\eval-v2\development-v5\private\dev-negative-squares.json `
  --output E:\CSC2108Local\local-agent-runs\my-task-001-judge
```

The wrapper verifies the extracted source hash, copies its bytes to the fresh judge directory, and passes source plus the row through stdin to a separate offline Docker judge. The official adapter evaluates **the row's public cases plus its private cases**. No private feedback is delivered to Qwen. A caller must provide the matching row: the CLI does not validate task-ID correspondence between that row and the completed public task.

Judge output includes `result.json` (summary), `evaluation.json`, the candidate copy, `official-evaluator.json`, `judge-launch.json`, stdout/stderr and `resource-events.json`. A missing candidate produces only the summary/evaluation files. Candidate wrong answers and resource failures are evaluated outcomes; exact `infrastructure_error` returns 2, other returned statuses return 0, and unhandled exceptions return 1. See [evidence provenance](../evidence/README.md#provenance-and-external-artifacts) for image/evaluator identities.

## Validation commands

For a documentation-only review, use only static checks and `verify --offline`; CLI help also performs no inference:

```powershell
& $pythonExe -m local_agent --help
& $pythonExe -m local_agent verify --offline
```

Separately, the repository contains `test_interface.py` and legacy unit suites, plus `python -m local_agent.sanity --output NEW_E_DIRECTORY` for integration controls. The latter **executes synthetic code in Docker and invokes the evaluator**, although it makes no model calls; it is not a static check. The prior [handoff validation](../evidence/handoff/README.md) already records those tests and its one synthetic model run. They are not rerun as part of this documentation review.
