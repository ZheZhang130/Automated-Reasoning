# Project structure

This is the layout of `feat/csc2108-local-agent-final`, audited against Python imports, child-process arguments, Docker mounts and configuration reads. The supported interface is [local_agent](../local_agent/README.md). Folder names reflect research history: the three older folders contain both live dependencies and historical code.

## Repository map

| Path | Role and ownership |
| --- | --- |
| [README.md](../README.md) | Starting point and one public-task example on the provisioned machine |
| [local_agent/](../local_agent/README.md) | Public integration boundary: `__main__.py` dispatches to `cli.py`; boundary tests and separately invoked integration sanity controls also live here |
| [local_baseline/](../local_baseline/README.md) | Active sandbox/model helpers and container judge adapter, environment setup, earlier CLIs and tests |
| [local_eval_v2/](../local_eval_v2/README.md) | Active original agent/prompt/profile and shared paths/lock; older batch/report code retained for tests or pins |
| [local_optimization/](../local_optimization/README.md) | Active selector, recommendation/configuration and independent judge monitor; hash-pinned experimental modules remain inactive |
| [evidence/](../evidence/README.md) | Preserved reports, aggregate JSON/CSV, charts, provenance, exclusions and prior handoff validation; not inputs to ordinary agent execution |
| `docs/` | This cross-project map; detailed CLI behavior lives with `local_agent/` |
| [orchestration_pilot/](../orchestration_pilot/README.md) | Teammates' separate orchestration loop/tests; not imported by `local_agent` or yet wired to mini-SWE-agent |
| [timeline/](../timeline/orchestration_1113.md) | Teammates' project-history notes; not a runtime dependency |
| [RESULTS_SUMMARY.md](../RESULTS_SUMMARY.md) | Current conclusions and supporting evidence links |
| `.gitattributes`, older-folder `.gitattributes` | Preserve frozen file bytes/line endings across Git checkouts |
| `.gitignore` | Excludes local environments, caches and run directories; runtime artifacts still belong outside the checkout |

Do not invoke the teammate pilot as a substitute for the frozen agent: its task schema, Python environment, guidance adapters and execution loop differ. The `judge` and `orchestration` Git branches are also separate teammate work, not folders to reorganize here.

## Public execution flow

1. **Initialize the host.** `local_baseline/env.ps1` sets E: cache/model/config/temp paths. `start_ollama.ps1` sources it and starts the dedicated server if 11435 is unavailable; it does not install models. Desktop endpoint 11434 must separately respond and have no loaded model when the agent starts.
2. **Call `python -m local_agent run`.** The wrapper reads selection/recommendation and both profiles, verifies 38 recorded source hashes and key package versions, checks both Docker image IDs, and queries installed model identity at 11435. It writes outer metadata/invocation records into a fresh output directory.
3. **Launch the selector.** A child runs `local_optimization/selected.py`. Its `optlib.py` inserts `local_eval_v2/` into module lookup and imports `common.py`. The selector repeats source/profile/image checks and invokes `local_eval_v2/runtime.py` with the original model/profile and fixed 600-second/20-action/3-repair budgets.
4. **Run the original agent.** The runtime imports `common.py` and baseline `runner.py`/`probe.py`. `common.py` adds `local_baseline/` to module lookup and supplies the Windows GPU lock. The runtime validates the public bundle, checks Docker isolation/storage and the separate Ollama workload, unloads approved project models before starting, and records model/GPU metadata. mini-SWE-agent uses LiteLLM's `ollama_chat/` adapter to call Ollama.
5. **Execute public actions in Docker.** `runtime.Environment` extends the baseline sandbox; `runner.TaskEnvironment` handles real shell commands, persistent `/workspace`, source snapshots, limits and cleanup. The sole host bind is the trusted public bundle at `/public`, read-only. Agent code goes to `/workspace/solution.py`; public testing runs `/public/check.py`. No private row is mounted or supplied.
6. **Extract and return.** Source bytes are read inside the container without following symlinks or executing candidate code on the host. The child saves available source, trajectory, raw telemetry and runtime result. The wrapper emits structured paths/status/usage. Candidates can be wrong or unchanged starters; missing/incomplete artifacts remain explicit.

The standard `local_eval_v2/public_check.py` is an export template: the agent executes the bundle's actual checker. The wrapper does not copy/import that repository file on every run. Similarly, importing `probe.py` does not mean its older model-factory settings or prompt are selected. See the [file audit](../local_agent/dependencies.md).

The agent container is unprivileged, network-disabled and read-only apart from capped temporary/workspace filesystems, with 512 MiB memory, one CPU and 64 PIDs, all capabilities dropped and no new privileges. Its writable workspace persists across actions within the task and is removed with the container afterward.

## Independent evaluation flow

`python -m local_agent evaluate` is a separate invocation after the public run ends. Preflight still requires Docker image inspection and Ollama 11435 identity queries, then verifies the external evaluator checkout is clean at its pinned revision. It does not generate tokens or resume the agent.

For an extracted candidate, the wrapper verifies its saved SHA256, copies the bytes to a fresh directory and imports `local_optimization/judge_watch.py`. That module uses `optlib → common` and `runner.docker` to launch `csc2108-lcb-judge:v2`. The judge mounts the external evaluator read-only at `/opt/lcb` and `local_baseline/judge_lcb.py` at `/judge.py`. Source and the matching official row enter through stdin. The adapter calls LiveCodeBench on public **plus** private cases; the host saves results and owned-container OOM evidence. None of this feedback reaches the agent.

The caller must supply the matching row; the CLI does not check row/task-ID correspondence. Missing candidates report `missing_submission` without launching a judge. Legacy `local_baseline/pilot.py:score` is not this public judge path.

The independent judge is likewise offline/read-only/unprivileged, with 1 GiB memory, one CPU and 64 PIDs. The pinned v2 image has a 175-second container deadline; the host subprocess timeout is 180 seconds, and the official adapter requests six seconds per test. Finalization/telemetry can add time beyond those intervals.

## Runtime state outside Git

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

**The frozen runner cannot run on a Mac as-is.** It requires E: paths, a Windows Python executable, PowerShell setup, process-liveness checks through `ctypes.WinDLL('kernel32')`, Docker Desktop WSL settings/VHDX evidence and `nvidia-smi` GPU telemetry. The recorded installation uses an NVIDIA RTX 4080 SUPER. Installing Ollama and Docker on macOS does not satisfy these implementation requirements.

A Mac user can clone/read the code/evidence, or use an available remote-access method to run commands on the provisioned Windows host; this repository provides no remote execution service. A native macOS port needs a separately versioned implementation/configuration and new platform validation, preserving the frozen Windows baseline rather than editing pinned files or bypassing checks.

## Modification boundaries and future proposals

The [dependency audit](../local_agent/dependencies.md) marks active execution, test support and compatibility independently of hash pins. A compatibility-only file is still required for integrity checks. Keep recorded paths/bytes; a README does not authorize modifying a frozen module. Original reports remain historical observations.

Future orchestration can create a trusted public bundle, invoke the CLI and join its result with a separate judge result. Frontier plans/contracts or diagnosis should be separately identified conditions with logged prompts, inputs, usage and provenance. Preserve the original baseline; keep private feedback out of every model input. The teammate pilot is a separate starting point, not a completed integration.

**Optional future physical reorganization:** after explicitly versioning a new runtime/integrity contract, extract shared sandbox/serving/judging utilities into a package while retaining the complete current archive. A separately validated port could make paths/platform handling configurable. Neither proposal is implemented: this documentation review moves, deletes or changes no runtime files.
