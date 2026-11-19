# Integration contract

Run from the repository root using `E:\CSC2108Local\.venv\Scripts\python.exe -m local_agent`. Initialize the environment with `local_baseline/env.ps1` first. No editable install or new dependency is needed.

`run --task PUBLIC_DIRECTORY --output NEW_E_DIRECTORY [--seed 2108]` launches the existing `local_optimization/selected.py`, which retains its source/image/configuration checks and runs the original `local_eval_v2/runtime.py`. The original runtime acquires the shared GPU lock. No prompt, sampler, parser, budget or action handling is patched. Preflight identity checks and a structured result envelope are the only new runtime behavior.

The public directory is **trusted input** with this exact allowlist:

| File | Contract |
| --- | --- |
| `task.json` | Exactly `task_id`, `version`, `statement`, `submission_path`; last field must be `solution.py` |
| `public_tests.json` | Public examples in the existing checker's format |
| `check.py` | Trusted public checker, run inside Docker |
| `solution.py` | Optional starter, not a reference solution |

Only regular files are allowed, with no symlinks or extra entries. Use existing prepared public bundles. The statement contains the full original problem and interface/starter requirements. This interface handles Python task bundles, not arbitrary repository repair. Checker formatting follows `local_eval_v2/public_check.py`. Bundle export helpers remain for compatibility; they are not new dataset selectors.

On a completed invocation, stdout is one JSON object (child console output is saved in logs). `result.json` has schema version 1:

```json
{
  "schema_version": 1,
  "status": "Submitted",
  "candidate_path": "E:\\...\\runtime\\solution.py",
  "trajectory_path": "E:\\...\\runtime\\trajectory.json",
  "metadata_path": "E:\\...\\metadata.json",
  "runtime_result_path": "E:\\...\\runtime\\result.json",
  "termination_reason": "Submitted",
  "timings": {"invocation_wall_seconds": 0, "agent_elapsed_seconds": 0},
  "usage": {"observed_generated_tokens": 0, "unobserved_generated_tokens_upper_bound": 0}
}
```

Paths are absolute. Missing candidate/trajectory paths are `null`. An unchanged starter may still be extracted; consumers must not infer authorship or correctness from file presence. `runtime/result.json` is authoritative for raw action/public-test events, implementation/task/source hashes, GPU snapshots, format errors, token completeness and errors. `runtime/configuration.json` and `runtime/trajectory.json` retain the exact effective system/instance/format-error prompts and observations. Request/response JSON and `ollama-server.log` retain inference telemetry. `metadata.json` records the verified model digest, environment versions, images' check outcome, profile, budgets, seed, checkout and wrapper hash.

`run` returns exit code 2 for a child process failure or `InfrastructureError`; a normal agent termination such as `Deadline`, `ActionLimit`, `RepairLimit` or `RepeatedFormatError` is a retained attempt with exit code 0. Inspect `status`, candidate presence and independent evaluation. Preflight failures raise before inference, typically exit code 1, and may occur before the output directory exists. Existing output directories are never reused. A crashed host process can leave partial logs/artifacts; no automatic resumption, inference retry or model download occurs.

Token totals are observed lower bounds when telemetry is incomplete. The separate upper-bound field charges up to 4,096 additional tokens per uncaptured call. Times separate end-to-end wrapper wall time, runtime time, and Ollama generation/prefill/load durations. Private judging has its own wall time and output directory.

`evaluate --run COMPLETED_RUN --private-row OFFICIAL_ROW_JSON --output NEW_E_DIRECTORY` verifies evaluator revision/image/source identity, checks the extracted candidate hash and copies its bytes into a separate offline judge. The private row is supplied through stdin to the existing official LiveCodeBench wrapper. `evaluation.json`, raw official output, launch arguments, stdout/stderr and owned-container OOM evidence are retained. A missing candidate reports `missing_submission`; an infrastructure failure returns code 2. A wrong candidate is an evaluated outcome, not an infrastructure error. This command never resumes an agent or sends feedback to a model.

`verify [--offline]` checks identities without inference. `python -m local_agent.sanity --output NEW_E_DIRECTORY` runs no-inference isolation, parser, feedback/repair/submission and official evaluator controls. It uses existing synthetic fixtures and writes all control candidates outside Git. Boundary tests: `python -m unittest -v local_agent.test_interface`.

The import chain is documented in [dependencies](dependencies.md). Fixed paths and known baseline limitations are listed in the top-level README/results summary. Additional frontier plans/contracts must be identified and logged as a new condition; preserve a run of the unchanged baseline and keep private feedback out of planners and agents.
