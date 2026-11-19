# CSC2108 local coding agent

Run a local Qwen model through **mini-SWE-agent → LiteLLM → Ollama** to solve a trusted public Python task bundle. The agent writes code, runs public tests and repairs files inside an isolated Docker workspace; it returns the candidate, trajectory and usage records. Official evaluation is a separate command that never feeds private results back to the agent.

Use **`python -m local_agent`** on `feat/csc2108-local-agent-final`. The default remains Qwen3.5 9B Q4_K_M with the frozen `heredoc-v6-16k-common` profile: 16K context, 4K response limit, nonthinking mode, 20 actions, 3 repair groups and a 600-second task budget. [Exact configuration and interface](local_agent/README.md).

## Start here

These instructions assume the **already provisioned Windows/E: machine**. Cloning the repository does not install Python packages, models, Docker images, prepared bundles or the external evaluator. Start Docker Desktop and Ollama Desktop; leave endpoint 11434 free of loaded models.

From this checkout's root in PowerShell:

```powershell
. .\local_baseline\env.ps1
& .\local_baseline\start_ollama.ps1
$pythonExe = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $pythonExe -m local_agent verify

# Runs the existing synthetic public task. Choose a NEW output directory.
& $pythonExe -m local_agent run `
  --task E:\CSC2108Local\eval-v2\development-v5\public\dev-negative-squares `
  --output E:\CSC2108Local\local-agent-runs\my-task-001 --seed 2108
```

Read `<output>\result.json` for the candidate/trajectory paths, termination reason, timings and token usage. `Submitted` does not establish correctness: use the [separate evaluation command](local_agent/README.md#independent-evaluation) afterward if you have the matching official row. No command above downloads a model or changes dependencies; `run` performs inference.

## Find your way around

| Need | Documentation |
| --- | --- |
| Complete folder map, execution flow, Windows/Mac limits and future integration | [Project structure](docs/PROJECT_STRUCTURE.md) |
| Task-bundle schema, exact settings, commands, outputs and exit codes | [Integration interface](local_agent/README.md) |
| Which legacy files are active, test support or hash compatibility | [Dependency audit](local_agent/dependencies.md) |
| Experimental conclusions | [Results summary](RESULTS_SUMMARY.md) |
| Original reports, aggregate artifacts, archives and external E: data locations | [Evidence index](evidence/README.md) |

The three older source folders contain active dependencies as well as historical code. Read their role notes before using them: [local_baseline](local_baseline/README.md), [local_eval_v2](local_eval_v2/README.md), [local_optimization](local_optimization/README.md). Their legacy CLIs are not the team interface. Frozen files must stay at their recorded paths and bytes.

`orchestration_pilot/` and `timeline/` belong to teammates; they are separate from this runner. Frontier planning/contracts are future integration work. **The current runner does not run on macOS as-is**; a Mac can read the repository/results or be used to access the provisioned Windows host. See [platform requirements](docs/PROJECT_STRUCTURE.md#platform-requirements-and-macos).
