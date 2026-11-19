# Project structure

This is the layout of `feat/csc2108-local-agent-final`, audited against imports, child processes, Docker mounts and configuration reads. The [public interface](../local_agent/README.md) selects frozen Windows execution or the new [portable Mac host adapter](MACOS.md). Older folder names reflect research history; they contain live dependencies as well as historical code.

## Repository map

| Path | Role and ownership |
| --- | --- |
| [README.md](../README.md) | Starting point and one public-task example on the provisioned machine |
| [local_agent/](../local_agent/README.md) | Public CLI; `platform_support.py` selects host paths/locks, `portable.py` adapts the unchanged agent function, and portable provisioning/fixtures/tests live alongside Windows support |
| [local_baseline/](../local_baseline/README.md) | Active sandbox/model helpers and container judge adapter, environment setup, earlier CLIs and tests |
| [local_eval_v2/](../local_eval_v2/README.md) | Active original agent/prompt/profile and shared paths/lock; older batch/report code retained for tests or pins |
| [local_optimization/](../local_optimization/README.md) | Active selector, recommendation/configuration and independent judge monitor; hash-pinned experimental modules remain inactive |
| [evidence/](../evidence/README.md) | Preserved reports, aggregate JSON/CSV, charts, provenance, exclusions and prior handoff validation; not inputs to ordinary agent execution |
| `docs/` | This map and the Mac setup guide; detailed CLI behavior lives with `local_agent/` |
| `.github/workflows/local-agent-portable.yml` | Mac/Windows/Linux dependency, import and host-contract checks; no Docker, model download or inference in CI |
| `local_agent/portable.Dockerfile.dockerignore` | Judge-specific build context allowlist; other Docker builds remain unaffected |
| [orchestration_pilot/](../orchestration_pilot/README.md) | Teammates' separate orchestration loop/tests; not imported by `local_agent` or yet wired to mini-SWE-agent |
| [timeline/](../timeline/orchestration_1113.md) | Teammates' project-history notes; not a runtime dependency |
| [RESULTS_SUMMARY.md](../RESULTS_SUMMARY.md) | Current conclusions and supporting evidence links |
| `.gitattributes`, older-folder `.gitattributes` | Preserve frozen file bytes/line endings across Git checkouts |
| `.gitignore` | Excludes local environments, caches and run directories; runtime artifacts still belong outside the checkout |

Do not invoke the teammate pilot as a substitute for the frozen agent: its task schema, Python environment, guidance adapters and execution loop differ. The `judge` and `orchestration` Git branches are also separate teammate work, not folders to reorganize here.

## Public execution flow

The numbered flow below is the unchanged **Windows default**. Portable execution uses the same original `run` function bytecode, agent/model/environment classes and settings, but enters through `local_agent.portable` rather than the Windows selector. Its isolated function bindings relocate the one hardcoded server-log path, replace the E: output/WSL preflight and NVIDIA-only telemetry requirements, and route API calls to the configured dedicated local endpoint. It does not rewrite source files, agent prompts, shell actions or evaluator code.

1. **Initialize the host.** `local_baseline/env.ps1` sets E: cache/model/config/temp paths. `start_ollama.ps1` sources it and starts the dedicated server if 11435 is unavailable; it does not install models. Desktop endpoint 11434 must separately respond and have no loaded model when the agent starts.
2. **Call `python -m local_agent run`.** The wrapper reads selection/recommendation and both profiles, verifies 38 recorded source hashes and key package versions, checks both Docker image IDs, and queries installed model identity at 11435. It writes outer metadata/invocation records into a fresh output directory.
3. **Launch the selector.** A child runs `local_optimization/selected.py`. Its `optlib.py` inserts `local_eval_v2/` into module lookup and imports `common.py`. The selector repeats source/profile/image checks and invokes `local_eval_v2/runtime.py` with the original model/profile and fixed 600-second/20-action/3-repair budgets.
4. **Run the original agent.** The runtime imports `common.py` and baseline `runner.py`/`probe.py`. `common.py` adds `local_baseline/` to module lookup and supplies the Windows GPU lock. The runtime validates the public bundle, checks Docker isolation/storage and the separate Ollama workload, unloads approved project models before starting, and records model/GPU metadata. mini-SWE-agent uses LiteLLM's `ollama_chat/` adapter to call Ollama.
5. **Execute public actions in Docker.** `runtime.Environment` extends the baseline sandbox; `runner.TaskEnvironment` handles real shell commands, persistent `/workspace`, source snapshots, limits and cleanup. The sole host bind is the trusted public bundle at `/public`, read-only. Agent code goes to `/workspace/solution.py`; public testing runs `/public/check.py`. No private row is mounted or supplied.
6. **Extract and return.** Source bytes are read inside the container without following symlinks or executing candidate code on the host. The child saves available source, trajectory, raw telemetry and runtime result. The wrapper emits structured paths/status/usage. Candidates can be wrong or unchanged starters; missing/incomplete artifacts remain explicit.

The standard `local_eval_v2/public_check.py` is an export template: the agent executes the bundle's actual checker. The wrapper does not copy/import that repository file on every run. Similarly, importing `probe.py` does not mean its older model-factory settings or prompt are selected. See the [file audit](../local_agent/dependencies.md).

The agent container is unprivileged, network-disabled and read-only apart from capped temporary/workspace filesystems, with 512 MiB memory, one CPU and 64 PIDs, all capabilities dropped and no new privileges. Its writable workspace persists across actions within the task and is removed with the container afterward.

## Independent evaluation flow

`python -m local_agent evaluate` is separate after the public run ends. Preflight requires image inspection and project Ollama identity queries, then checks the clean external evaluator revision. Windows uses the original image IDs and v2 tag; portable uses explicitly provisioned native image IDs and the same judge dependency lock/deadline. It does not generate tokens or resume the agent.

For an extracted candidate, the wrapper verifies its saved SHA256, copies the bytes to a fresh directory and imports `local_optimization/judge_watch.py`. That module uses `optlib → common` and `runner.docker` to launch `csc2108-lcb-judge:v2`. The judge mounts the external evaluator read-only at `/opt/lcb` and `local_baseline/judge_lcb.py` at `/judge.py`. Source and the matching official row enter through stdin. The adapter calls LiveCodeBench on public **plus** private cases; the host saves results and owned-container OOM evidence. None of this feedback reaches the agent.

The caller must supply the matching row; the CLI does not check row/task-ID correspondence. Missing candidates report `missing_submission` without launching a judge. Legacy `local_baseline/pilot.py:score` is not this public judge path.

The independent judge is likewise offline/read-only/unprivileged, with 1 GiB memory, one CPU and 64 PIDs. The pinned v2 image has a 175-second container deadline; the host subprocess timeout is 180 seconds, and the official adapter requests six seconds per test. Finalization/telemetry can add time beyond those intervals.

## Runtime state outside Git

The table describes the existing Windows deployment. Portable defaults to `~/.local/share/csc2108`, configurable with `CSC2108_ROOT`; model files stay in the Mac Ollama location or the user's `OLLAMA_MODELS`. Portable image pins, caches/config/logs, vendor checkout, fixtures and outputs are external, not copied into this repository. See [Mac configuration](MACOS.md#what-differs-from-frozen-windows).

| Location | Use |
| --- | --- |
| `E:\CSC2108Local\.venv` | Existing Python 3.11.9 environment and dependencies |
| `E:\OllamaModels` | Ollama model manifests/blobs |
| `E:\DockerDesktop` | Docker Desktop WSL disks/images/volumes |
| `E:\CSC2108Local\eval-v2\gpu.lock` | Shared runtime ownership |
| `E:\CSC2108Local\logs\ollama-project.stderr.log` | Existing server log read into per-run evidence |
| `E:\CSC2108Local\config`, `cache`, `tmp` | mini-SWE-agent global configuration, caches and temporary files |
| `E:\CSC2108Local\vendor\LiveCodeBench` | Clean pinned external evaluator |
| Caller-selected fresh E: directory | Outer interface records plus `runtime/`; judging uses another directory |

[Evidence locations](../evidence/README.md#provenance-and-external-artifacts) index completed studies. Full trajectories, benchmark solutions, private cases, weights and mutable state remain outside Git. A clone supplies code/documentation and aggregate evidence, not a complete installation.

## Platform requirements and macOS

The public CLI now supports a portable Mac host path; follow [MACOS.md](MACOS.md) for Python, native Docker and Ollama setup. Windows continues to use E:, PowerShell, its original process lock, WSL/VHDX storage checks and NVIDIA telemetry. The historical Windows CLI itself remains Windows-specific; users do not invoke that CLI directly on Mac.

The portable adapter uses POSIX advisory locking, native-architecture Linux containers, host Ollama (including Metal where available), external per-machine image pins and explicit host provenance. All 38 frozen source hashes still pass. Hardware/performance and native image identities differ; published Windows accuracy/timing is not revalidated for Mac. Unit/POSIX and fake-server Docker checks do not substitute for a physical Mac/Metal model run, which remains a deployment acceptance check.

## Modification boundaries and future proposals

The [dependency audit](../local_agent/dependencies.md) marks active execution, test support and compatibility independently of hash pins. A compatibility-only file is still required for integrity checks. Keep recorded paths/bytes; a README does not authorize modifying a frozen module. Original reports remain historical observations.

Future orchestration can create a trusted public bundle, invoke the CLI and join its result with a separate judge result. Frontier plans/contracts or diagnosis should be separately identified conditions with logged prompts, inputs, usage and provenance. Preserve the original baseline; keep private feedback out of every model input. The teammate pilot is a separate starting point, not a completed integration.

**Optional future physical reorganization:** extract shared sandbox/serving/judging utilities into a versioned package while retaining the complete frozen archive. The current port deliberately keeps all historical paths and source files; only new adapter code and the unpinned public wrapper change. No teammate code or historical evidence is reorganized.
