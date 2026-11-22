# CSC2108 local coding agent

Run a local Qwen model through **mini-SWE-agent → LiteLLM → Ollama** to solve a trusted public Python task bundle. The agent writes code, runs public tests and repairs files inside an isolated Docker workspace; it returns the candidate, trajectory and usage records. Official evaluation is a separate command that never feeds private results back to the agent.

Use **`python -m local_agent`** on `feat/csc2108-local-agent-final`. Windows retains the original frozen execution path; macOS selects a portable host adapter. Both use Qwen3.5 9B Q4_K_M and `heredoc-v6-16k-common`: 16K context, 4K response limit, nonthinking mode, 20 actions, 3 repair groups and 600 seconds. [Exact configuration/interface](local_agent/README.md).

## Start here

**On a Mac, follow the [macOS setup guide](docs/MACOS.md)** to create a Python environment, provision native Docker images/evaluator, start local Ollama and run the supplied checks/example. A physical Mac/Metal inference validation remains necessary before collecting research results; development checks cover Windows, POSIX paths/locks and real Docker execution with a fake model server.

The commands below are for the **already provisioned Windows/E: machine** and remain unchanged. Cloning alone installs no packages, models, images, bundles or evaluator. Start Docker Desktop and Ollama Desktop; leave endpoint 11434 free of loaded models.

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

## Frontier guidance (conditions A–E) — integrated backend

**Pass 2** adds three conditions on the same frozen agent and judge:

* **E:** one frontier diagnosis of the first qualifying public-test failure, delivered into the *same running* mini-SWE-agent session.
* **B:** the frontier model as the coding model, through the unchanged action protocol.
* **contract-v3:** an experimental D prompt grounded in Endres et al. and Tufano et al.

Start with [reasoning_effectiveness/pass2/FINAL_REPORT.md](reasoning_effectiveness/pass2/FINAL_REPORT.md). Then read [DIAGNOSIS_INTEGRATION.md](reasoning_effectiveness/pass2/DIAGNOSIS_INTEGRATION.md), [CONTRACT_RESEARCH.md](reasoning_effectiveness/pass2/CONTRACT_RESEARCH.md), [FRONTIER_ONLY.md](reasoning_effectiveness/pass2/FRONTIER_ONLY.md) and [PAPER_ALIGNMENT.md](reasoning_effectiveness/pass2/PAPER_ALIGNMENT.md).

`python -m guided_agent` runs the **same frozen agent** for local-only (A), upfront frontier plan (C) and upfront behavioral contract (D). Guidance is generated once from the public statement, by isolated Codex replay or the direct OpenAI API. Public tests go through Peter's `judge-public`, and hidden scoring is a separate step. Start with [reasoning_effectiveness/FINAL_REPORT.md](reasoning_effectiveness/FINAL_REPORT.md) (results), [PORTABILITY.md](reasoning_effectiveness/PORTABILITY.md) (Windows/macOS commands), [BENCHMARK_READINESS.md](reasoning_effectiveness/BENCHMARK_READINESS.md) and [INTEGRATION_AUDIT.md](reasoning_effectiveness/INTEGRATION_AUDIT.md). The earlier `planning_frontier/plan_once.py` and `contract_frontier/run_contract.py` remain as the teammates' development runners; their prompts and replay classes are reused unchanged.

## Find your way around

| Need | Documentation |
| --- | --- |
| Complete folder map, execution flow, Windows/Mac limits and future integration | [Project structure](docs/PROJECT_STRUCTURE.md) |
| Native Mac installation, model serving, provisioning and smoke checks | [macOS guide](docs/MACOS.md) |
| Task-bundle schema, exact settings, commands, outputs and exit codes | [Integration interface](local_agent/README.md) |
| Which legacy files are active, test support or hash compatibility | [Dependency audit](local_agent/dependencies.md) |
| Experimental conclusions | [Results summary](RESULTS_SUMMARY.md) |
| Original reports, aggregate artifacts, archives and external E: data locations | [Evidence index](evidence/README.md) |

The three older source folders contain active dependencies as well as historical code. Read their role notes before using them: [local_baseline](local_baseline/README.md), [local_eval_v2](local_eval_v2/README.md), [local_optimization](local_optimization/README.md). Their legacy CLIs are not the team interface. Frozen files must stay at their recorded paths and bytes.

`orchestration_pilot/` and `timeline/` belong to teammates and remain separate. Frontier planning/contracts are future integration work. Existing Windows results and frozen source files are preserved; portable measurements must be recorded separately because hardware and native image identities differ.
