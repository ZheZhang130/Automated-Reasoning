# Dependency audit

Audited from Python imports, subprocess arguments, configuration reads and Docker mounts in `cli.py`, `selected.py`, `runtime.py`, `runner.py`, `judge_watch.py` and the existing tests. [Project structure](../docs/PROJECT_STRUCTURE.md) owns the execution flow; [the interface contract](README.md) owns commands/settings. The tables cover all current files in the three older folders, including overlapping roles.

## Role definitions

- **Run**: executed, imported or read as operational configuration by public `local_agent run`, including preflight; mere hash-reading does not qualify.
- **Judge**: executed/imported by separate `local_agent evaluate`, beyond shared preflight.
- **Test**: unit-test support or explicitly invoked integration controls, not ordinary public run/judge execution.
- **Compatibility**: retained for frozen hashes or historical reconstruction, without execution on the public path. Reading a file to hash it does not execute its code.
- **Setup/build**: host/image provisioning support rather than per-task execution.

**Pinned** means listed in the unchanged 38-entry `final_selection.json.runtime_sha256` map. Categories overlap: some pinned modules are active, some are imported only for tests, and some are compatibility-only. Selection/recommendation JSON has additional cross-file checks despite not being entries in that map.

## local_baseline

| File(s) | Role | Pinned? | Actual use |
| --- | --- | --- | --- |
| `runner.py` | Run, Judge, Test | Yes | Active runtime subclasses `TaskEnvironment` and uses `Budget`, container arguments, snapshots/cleanup and containment. Judge monitor uses its Docker subprocess helper. Its old `main()` is not invoked. |
| `probe.py` | Run, Judge import, Test | Yes | Imported by `runner`; active runtime calls `unload_project_models()`. Old `make_model()`, prompts and probe CLI are not selected model construction. |
| `models.json` | Run | Yes | Approved-model allowlist read by unload helper; old per-tag defaults do not replace the active v2 profile. |
| `judge_lcb.py` | Judge | Yes | Mounted into the offline container; imports official evaluator there, not on the Windows host. |
| `env.ps1` | Setup, compatibility | Yes | Documented environment initialization; selector verifies bytes. Python CLI does not source it automatically. |
| `start_ollama.ps1` | Setup | No | Sources env, checks/starts dedicated Ollama and sets the user model-location variable; no download. |
| `requirements.lock` | Setup, compatibility | Yes | Recorded host dependencies; checked by selector, not installed during tasks. |
| `judge-requirements.lock` | Build, compatibility | Yes | Original judge dependency lock; checked by selector. |
| `prepare_lcb.py` | Test, compatibility | Yes | `test_runner` calls `export`; imported by legacy `pilot`. Dataset CLI is not used by `local_agent`. |
| `pilot.py` | Test import, compatibility | Yes | V2 test-support modules import its legacy `score` symbol. Old batch/score paths are not the public independent judge. |
| `public_stdio_check.py` | Test/export support | No | Copied into temporary bundles by `prepare_lcb.export` in baseline tests; public wrapper does not copy it. |
| `test_runner.py` | Test | No | Budget, mount/storage and private-field export unit checks. |
| `validate_isolation.py` | Test control | No | Explicit Docker CLI using `fixtures/signed_sum`; not invoked by public wrapper. |
| `fixtures/signed_sum/check.py`, `solution.py`, `task.json` | Test control | No | Synthetic checker, deliberately wrong starter and task for original isolation controls; not benchmark solutions. |
| `requirements.in`, `judge-requirements.in` | Setup/build inputs | No | Earlier direct dependency declarations; not complete provisioning on their own. |
| `judge.Dockerfile`, `build_judge.ps1` | Legacy build support | No | Builds v1 using an E: context/exported public Windows CAs. Not invoked per task; rebuilds can change image identity. |
| `.gitattributes`, `README.md` | Repository support/docs | No | Byte preservation and folder guidance; not Python imports. |

## local_eval_v2

| File(s) | Role | Pinned? | Actual use |
| --- | --- | --- | --- |
| `runtime.py` | Run, Test | Yes | Actual selected child CLI: original prompts, agent/model classes, public-test hooks, trajectory and telemetry. |
| `common.py` | Run, Judge, Test | Yes | Paths, serialization/hashing and Windows GPU lock; appends baseline module lookup; imported via `optlib` too. |
| `profiles.json` | Run/preflight | Yes | Runtime reads original profile; wrapper checks agreement with frozen selection. |
| `public_check.py` | Prepared-checker template, compatibility | Yes | Standard exporter template whose prepared-bundle copy may execute. Public wrapper does not import/copy it anew per task. |
| `dataset.py` | Test import, compatibility | Yes | Retained `batch.py` imports evaluator/dataset constants. Download/selection code is not called by the public path or unit-test imports. |
| `batch.py` | Test, historical driver | No | Scheduling/resume/interruption unit tests call helpers/`run_batch` using temporary records and mocks; not supported task entrypoint. |
| `analyze.py` | Test, historical reporting | No | Accounting tests invoke analysis on temporary synthetic records; not public run/judge logic. |
| `validate_v5.py` | Test, historical control | No | `test_v2` imports `Hooks`; another function contains old v1-judge functional controls. Direct script execution also runs those controls. |
| `test_v2.py`, `test_wire.py`, `test_interruption.py`, `test_analysis.py` | Test | No | Submission/scheduling, adapter serialization with mocked HTTP, interruption preservation and paired accounting. |
| `judge.Dockerfile` | Build support | No | Adds the 175-second timeout entrypoint to existing v1 for judge v2; not built per task. |
| `.gitattributes`, `README.md` | Repository support/docs | No | Byte preservation and folder guidance. |

## local_optimization

| File(s) | Role | Pinned? | Actual use |
| --- | --- | --- | --- |
| `selected.py` | Run | Yes | First child process; verifies source/profile/images and launches original v2 runtime. Direct challenger option is not exposed by `local_agent`. |
| `optlib.py` | Run, Judge, Test | Yes | Prepends v2 module lookup, imports `common`, exposes roots/helpers. Historical source-discovery function is not called by selector. |
| `judge_watch.py` | Judge, Test control | Yes | Independent judge launcher/OOM telemetry; calls `runner.docker` and mounts adapter/vendor checkout. |
| `profiles.json` | Run/preflight | Yes | Selector/wrapper validate original configuration; also contains unselected exploratory profiles. |
| `final_selection.json`, `final_recommendation.json` | Run/preflight | No; cross-checked | Hash map, model/images/settings/budgets and original-control decision; recommendation pins selection SHA. Never change to bypass checks. |
| `runtime_opt.py` | Test import, compatibility | Yes | Alternative runner imported by `test_public_command`; not selected baseline. |
| `transport.py` | Test, compatibility | Yes | Native-history/timeout helpers tested by `test_transport` and imported by alternative runner; not default protocol. |
| `command_transport.py` | Test import, compatibility | Yes | Imported by alternative runner; optional large-command stdin transport is not enabled on public baseline. |
| `test_transport.py`, `test_methodology.py`, `test_public_command.py` | Test | Yes | Serializer/timeouts, frozen control/splits/private separation, checker matching. Methodology checks require historical E: audit/bundles. |
| `development_manifest.json`, `selection_manifest.json`, `heldout_manifest.json` | Test/evidence support | No | Methodology tests read identity/nonoverlap/public hashes; not task selectors used by public CLI. |
| `check_command_transport.py`, `check_judge.py` | Test controls, compatibility | Yes | Explicit Docker transport/resource controls with fixed historical output paths; not ordinary unit discovery or public execution. |
| `analyze.py`, `assess_timeout.py`, `audit.py`, `audit_length_causes.py`, `cohort.py`, `finish_report.py`, `plot.py`, `verify.py` | Compatibility; historical analysis | Yes | Not called/imported by public paths or ordinary unit suites. All hashes remain required; use archival context for old tooling. |
| `batch.py`, `diagnose.py`, `freeze_final.py`, `prepare.py` | Compatibility; experiment drivers | Yes | Not called/imported by public paths or unit suites. Direct execution can run experiments or write research files; not a handoff workflow. |
| `README.md` | Documentation | No | Role note; does not affect frozen `*.py` inventory. |

## Import and subprocess boundaries

Historical flat module names resolve through explicit path changes: `optlib` prepends `local_eval_v2/`; `common` appends `local_baseline/`. Selector/runtime use separate Python processes. They do not import teammates' orchestration loop or archived one-shot/delivery drivers. Names such as `runtime`, `runner`, `probe`, `batch` and `analyze` need their actual process/import context rather than classification by basename alone.

Host subprocesses include Python children, Docker image/info/inspect/exec/run/cleanup/events operations, Git metadata/evaluator checks and `nvidia-smi` telemetry. Docker launches isolated Linux shells/Python. Candidate/official evaluator execution is inside containers; `judge_lcb.py` imports `lcb_runner.evaluation.compute_code_generation_metrics` there. Host `evaluate` copies source bytes but never executes the candidate.

External dependencies include the existing Python environment, mini-SWE-agent, LiteLLM, requests and locked transitive dependencies, Docker CLI/daemon, Ollama services, Git and NVIDIA telemetry. Offline verification needs Python/package identity but no running services. Host/judge locks and [provenance exports](../evidence/README.md#provenance-and-external-artifacts) record versions; installing latest dependencies or rebuilding images is not part of this cleanup.

## Integrity and historical layout

Selection checks **38 frozen file hashes**, including inactive modules, before a baseline task. Active and compatibility files must keep their exact locations/bytes. Additional checks link selection/recommendation and match profiles/images. Existing attributes preserve measured line endings: the host lock was measured with CRLF, and optimization/evidence files use byte-preserving attributes. Do not normalize frozen files or edit expected hashes.

The earlier packaging commit `5d07e6326c3a45be7fd2896c9364048fc8047601` relocated 102 report/data/chart files to `evidence/` and removed 24 historical Python drivers from the active tree. That was a separate completed cleanup; this documentation review relocates/deletes nothing. [layout.json](../evidence/layout.json) records original paths/measured hashes; [archive commits](../evidence/README.md#reports-and-archives) preserve complete research trees. Some old drivers still reference former report paths or write research outputs: presence does not imply a supported current CLI.
