# macOS setup and portable host adapter

The public CLI now selects a **portable host backend on macOS/Linux**, while Windows still defaults to the original frozen selector/runtime. Both use the original mini-SWE-agent loop, prompts, parser, public-test/repair handling, Qwen digest/profile and standard budgets. The adapter changes host plumbing, not the agent algorithm. See [interface settings](../local_agent/README.md#frozen-configuration).

The portability code is tested on Windows and Linux, with a macOS/Windows/Linux host-contract [CI workflow](../.github/workflows/local-agent-portable.yml). See the [validation record](PORTABILITY_VALIDATION.md) for scope and outcomes. A physical Mac/Metal inference run has not been performed during development on this Windows machine. Run the supplied checks on your Mac before collecting results; this is not a claim that the Windows benchmark measurements reproduce on different hardware.

## Requirements

- Python **3.11.x**, Git, Docker Desktop running Linux containers, and the native Ollama CLI. Windows continues to require its original Python 3.11.9 environment.
- [Ollama's macOS requirements](https://docs.ollama.com/macos): macOS 14 or newer; Apple M-series supports CPU/GPU execution, Intel Macs use CPU execution. Enough memory is needed for the 6.55 GB model, its 16K context and Docker; successful execution within the fixed time budget is hardware-dependent.
- [Docker Desktop for your Mac architecture](https://docs.docker.com/desktop/setup/install/mac-install/). Native Linux ARM64 images are selected on Apple Silicon, AMD64 on Intel. The pinned Python base is a multi-architecture index; the adapter rejects an emulated/mismatched agent architecture.

Ollama runs **on the Mac host**, so Apple GPU support comes from Ollama, not Docker. Only shell actions, candidates and judging run inside isolated CPU containers. No OpenAI/frontier key is needed.

## 1. Provision the Python environment and judge

Clone this branch and run these commands from its repository root. Do not reuse your teammates' unrelated virtual environments:

```bash
export CSC2108_ROOT="${CSC2108_ROOT:-$HOME/.local/share/csc2108}"
python3.11 -m venv "$CSC2108_ROOT/.venv"
source "$CSC2108_ROOT/.venv/bin/activate"
python -m pip install -r local_agent/requirements.txt
python -m local_agent verify --offline
python -m local_agent prepare
```

`prepare` explicitly provisions infrastructure: it pulls the pinned native Python image if absent, clones the exact LiveCodeBench evaluator revision if absent, builds `csc2108-lcb-judge:portable-v1` with the original judge dependency lock/deadline, and records actual native image IDs in `$CSC2108_ROOT/portable-images.json`. It does **not** download a model or dataset, start Ollama, or run candidates. An existing evaluator must already be clean at the pinned revision; it is never reset. An existing image manifest is never overwritten.

For an existing evaluator, optionally export `CSC2108_VENDOR=/absolute/path/to/LiveCodeBench` before provisioning/running. For a network requiring a custom trusted CA, `CSC2108_CA_BUNDLE=/absolute/path/to/public-ca.pem` passes that bundle as a Docker build secret; TLS validation stays enabled. Python/Git network trust must also be configured normally on that machine.

Keep the same root and interpreter in all terminals. Run `python -m pip freeze` into your external run records if you need a complete installation snapshot: the portable requirements pin the five core host packages, not every transitive package from the historical Windows installation.

## 2. Start the dedicated Ollama server

In a separate terminal, run the native CLI in the foreground. This uses the usual Mac model directory unless you already set `OLLAMA_MODELS`; it does not change Desktop's global launch configuration. [Ollama documents these server variables and model locations](https://docs.ollama.com/faq).

```bash
export CSC2108_ROOT="${CSC2108_ROOT:-$HOME/.local/share/csc2108}"
export OLLAMA_MODELS="${OLLAMA_MODELS:-$HOME/.ollama/models}"
mkdir -p "$CSC2108_ROOT/logs"
cd "$CSC2108_ROOT"
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NO_CLOUD=1 OLLAMA_NOPRUNE=1 \
  ollama serve >> logs/ollama-project.stdout.log 2>> logs/ollama-project.stderr.log
```

Leave this terminal open. Desktop port 11434 is optional, but if it is running it must have no loaded model; the adapter refuses foreign workloads rather than unloading them. Keep other GPU-heavy applications idle. Do not start another project driver with a different data root to circumvent the shared lock.

In your original terminal, still at the repository root with the virtual environment activated, install the model **only if it is absent on this Mac**, then verify:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen3.5:9b
python -m local_agent verify
```

The pull is an explicit model download, not something `run` performs. The model must match digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` and Q4_K_M. Tags can change upstream: if the digest differs, obtain the matching model from the team instead of editing the frozen digest or accepting a different quantization. Existing Windows weights/configuration are unaffected by Mac provisioning.

## 3. Check isolation, then run a task

The no-inference controls create only trusted synthetic fixtures and execute them in Docker, including independent correct/wrong judging:

```bash
python -m unittest -v local_agent.test_portable
python -m local_agent.portable_sanity --output "$CSC2108_ROOT/checks/sanity-001"
```

For a real mini-SWE-agent task, use an existing trusted bundle or generate the small synthetic example below. Every output directory must be fresh and outside the checkout:

```bash
python -m local_agent fixtures --output "$CSC2108_ROOT/fixtures/sum-001"
python -m local_agent run \
  --task "$CSC2108_ROOT/fixtures/sum-001/public" \
  --output "$CSC2108_ROOT/runs/sum-001" --seed 2108
python -m local_agent evaluate \
  --run "$CSC2108_ROOT/runs/sum-001" \
  --private-row "$CSC2108_ROOT/fixtures/sum-001/private.json" \
  --output "$CSC2108_ROOT/runs/sum-001-judge"
```

`run` calls Qwen; `evaluate` does not generate tokens but still needs the server for identity preflight. `result.json` has the same candidate/trajectory/metadata/status/timing fields as Windows. Hidden test rows enter only the separate offline judge after the agent exits. The CLI does not choose fresh benchmark tasks or expose private feedback to any model.

An additional software integration smoke exercises the real mini-SWE-agent/LiteLLM/Docker stack against a **fake Ollama HTTP server**, verifies the original prompt/options/budgets, and independently judges its synthetic submission. It does not call a real model:

```bash
CSC2108_DOCKER_TESTS=1 python -m unittest -v local_agent.test_portable_integration
```

## What differs from frozen Windows

| Concern | Windows default | Portable backend |
| --- | --- | --- |
| Entry process | Original `selected.py` → original runtime CLI | New isolated worker reuses original `run` bytecode/classes with explicit host bindings |
| Data/output paths | Existing E: paths and output guard | User-writable root; outputs anywhere outside checkout |
| Lock | Historical Windows PID/host lock | POSIX advisory lock in `root/eval-v2/gpu.lock`; persistent inode, automatically released by OS |
| Docker verification | Original image IDs and WSL/VHDX policy | Same pinned multi-architecture base and isolation flags; native image IDs/recipe pinned per installation |
| Telemetry | Original `nvidia-smi` measurements | NVIDIA telemetry if available, otherwise explicitly unavailable; Ollama `/api/ps` remains recorded for Metal/CPU memory information |
| Desktop endpoint | Must respond and be idle | Optional; must be idle if present |
| Server log | Existing hardcoded project log | Relocated under the chosen root; omission is recorded if external server does not write it |

`CSC2108_OLLAMA_ENDPOINT` can select another **dedicated loopback HTTP port** on portable hosts; it defaults to `http://127.0.0.1:11435`, and port 11434/remote servers are rejected. Put `--backend portable` **before** the subcommand to explicitly test this backend on Windows; ordinary Windows commands ignore portable overrides and retain the original behavior. `--backend windows` is rejected on macOS/Linux.

Portable results record backend, host/architecture, data root, actual Docker IDs and serving version. The 38 historical frozen source hashes and original model settings remain checked. Native images, Python patch/transitive versions, hardware and telemetry can differ, so keep portable measurements separate from published Windows evidence. Reprovisioning after a recipe change requires deliberately preserving the previous external manifest and creating a new one; no silent hash bypass or historical evidence rewrite is provided.
