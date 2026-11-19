# Baseline helpers retained by the final component

This folder is **partly active**, despite its historical name. Use [python -m local_agent](../local_agent/README.md), starting with the [root README](../README.md). The [dependency audit](../local_agent/dependencies.md#local_baseline) lists every retained file and its pin/test status.

| Important files | Role today |
| --- | --- |
| `runner.py` | Active sandbox base classes, budgets, source extraction, Docker helper and containment checks |
| `probe.py`, `models.json` | Active approved-project-model unload helper/allowlist; the old probe/model factory is not the selected configuration |
| `judge_lcb.py` | Active adapter mounted into the independent offline official judge |
| `env.ps1`, `start_ollama.ps1` | Documented host initialization and dedicated Ollama startup |
| `requirements.lock`, `judge-requirements.lock` | Recorded dependencies/hash compatibility; not automatically installed per task |
| `prepare_lcb.py`, `pilot.py`, `public_stdio_check.py` | Earlier export/judge tooling used by tests/imports or kept for pins; not the public run/evaluate workflow |
| `test_runner.py`, `validate_isolation.py`, `fixtures/signed_sum/` | Unit and explicitly invoked Docker isolation controls |
| Build scripts, Dockerfile and `.in` files | Legacy provisioning inputs; the old build script produces judge v1, while current evaluation uses an existing pinned v2 image |

**Do not directly modify frozen helpers or invoke their legacy agent/pilot/probe CLIs for team tasks.** They can use different prompts/settings, start inference or write historical output locations. The two setup scripts above belong to manual startup; use the public wrapper for tasks/judging. Rebuilding images or installing dependencies needs a separately planned environment change.

Original documentation/results are preserved under [evidence/local_baseline](../evidence/local_baseline/RESULTS.md); they describe their original date/configuration. [Project structure](../docs/PROJECT_STRUCTURE.md) explains the current flow. These role notes move or change no runtime files.
