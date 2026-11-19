# CSC2108 local coding agent

This component runs **mini-SWE-agent 2.4.6 → LiteLLM 1.81.16 → local Ollama** to solve a trusted public Python task bundle. Qwen writes files, executes real shell commands, runs public tests, and repairs code in a persistent, isolated Docker workspace. It returns the extracted candidate and its complete trajectory. Independent private judging is a separate command.

The supported interface is `python -m local_agent`. The original runtime and prompt remain source-pinned; no experimental challenger or delivery prompt is enabled. See [results](RESULTS_SUMMARY.md), [integration contract](local_agent/README.md), and [research evidence](evidence/README.md).

## Start and run

Use PowerShell from this checkout. Start Docker Desktop and Ollama Desktop (the latter supplies the separate 11434 workload check), then:

```powershell
. .\local_baseline\env.ps1
& .\local_baseline\start_ollama.ps1
$pythonExe = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $pythonExe -m local_agent verify

# Existing synthetic public bundle; choose a NEW output directory each time.
& $pythonExe -m local_agent run `
  --task E:\CSC2108Local\eval-v2\development-v5\public\dev-negative-squares `
  --output E:\CSC2108Local\local-agent-runs\my-task-001 --seed 2108

# Optional, separate private evaluation AFTER the agent finishes.
& $pythonExe -m local_agent evaluate `
  --run E:\CSC2108Local\local-agent-runs\my-task-001 `
  --private-row E:\CSC2108Local\eval-v2\development-v5\private\dev-negative-squares.json `
  --output E:\CSC2108Local\local-agent-runs\my-task-001-judge
```

No downloads or dependency changes are performed by these commands. Ollama serves the installed model at `127.0.0.1:11435` from `E:\OllamaModels`. Keep other GPU inference idle: the original runtime owns `E:\CSC2108Local\eval-v2\gpu.lock` and refuses to run while endpoint 11434 has a loaded model.

## Official configuration

| Setting | Frozen value |
| --- | --- |
| Model | `qwen3.5:9b`, Q4_K_M |
| Model digest | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| Profile / command protocol | `heredoc-v6-16k-common` / original text shell fences |
| Context / maximum output per response | 16,384 / 4,096 tokens |
| Thinking / temperature | disabled / 0.2 |
| top-p / top-k / min-p | 0.9 / 40 / 0 |
| repeat penalty / window | 1.0 / 64 |
| presence / frequency penalties | 0 / 0 |
| Budgets | 20 actions, 3 repair groups, 600 seconds per task, up to 180 seconds per request |
| Default seed | 2108 |

Each request is capped by remaining task time. The frozen 600-second agent deadline includes runtime setup; extraction and cleanup can add invocation wall time. This handoff preserves those semantics.

## Outputs and layout

The command emits a JSON result and saves it as `<output>\result.json`: candidate path, trajectory path, metadata path, termination reason, timings and token usage. `metadata.json` records verified identities and configuration; `runtime\` contains the unchanged agent artifacts, including source, trajectory, raw requests/responses, public-test events and GPU measurements. Missing candidates and incomplete token telemetry remain explicit. `Submitted` means the agent submitted; only independent judging establishes correctness.

| Path | Purpose |
| --- | --- |
| `local_agent/` | Small team CLI, contract, boundary tests and synthetic sanity controls |
| `local_baseline/`, `local_eval_v2/`, `local_optimization/` | Frozen compatibility files, required imports, pins and relevant tests |
| `evidence/` | Original reports, aggregate JSON/CSV, provenance, charts, 75-ID exclusions and cleanup verification |
| `orchestration_pilot/`, `timeline/` | Existing teammate files, unchanged |

Some old optimization drivers must remain because the frozen selection hashes **38 files**, including historical Python modules. They are compatibility material, not the handoff interface. Unneeded historical drivers are available at immutable [archive tags](evidence/README.md). Historical reports retain their original wording and relative links; use their archival commit for the original context.

## Requirements and limits

This is a Windows/E: deployment, not a portable installer: Python 3.11.9 at the path above, pinned dependencies, NVIDIA GPU, Docker Desktop storage at `E:\DockerDesktop`, existing agent/judge images, the dedicated Ollama server/log directory, prepared task bundles, and a clean pinned evaluator checkout at `E:\CSC2108Local\vendor\LiveCodeBench` are required. `verify` checks frozen files, key package versions, model digest and image IDs. Full historical environment versions are retained in `evidence/`. A different machine needs explicit provisioning and validation; do not disable the integrity checks.

Agent containers have no network, read-only roots, an unprivileged user, capped CPU/memory/PIDs and a read-only public bundle mount. Private rows go only to a separate judge after the agent exits. Generated candidate code never runs on Windows. Full artifacts, private tests and weights remain outside Git on E:; their locations are indexed in [evidence/README.md](evidence/README.md).

Future orchestration can supply a trusted public bundle and consume the result JSON. Frontier plans or contracts can become a separately identified task condition with their own provenance; diagnosis can inspect completed public trajectories. Keep the frozen baseline available for comparison and private judge feedback outside every agent/planner input. Frontier assistance is not implemented or validated here.
