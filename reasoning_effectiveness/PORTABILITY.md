# Running the integrated A/C/D pipeline on Windows and macOS

One CLI, `python -m guided_agent`, behaves the same in PowerShell and in POSIX shells.
Platform differences are confined to the existing host adapters in `local_agent/`:
`platform_support.Settings` (data root, endpoint, lock) and `portable.adapted_run` (host bindings for the frozen runtime).
The reasoning conditions, guidance artifacts, task bundles, run records and evaluation are
platform-independent JSON/UTF-8 with LF line endings.

## What has actually been validated

| Level | Windows 11 desktop (RTX 4080 SUPER) | macOS |
| --- | --- | --- |
| Software compatibility (imports, CLI, schemas) | ✓ | Code paths are POSIX-clean (no `E:`, no `nvidia-smi`, `fcntl` lock via `local_agent`). **Not executed on a Mac tonight.** |
| Mocked / offline host contracts | ✓ `guided_agent.test_guided` (incl. composition with `portable.adapted_run` using `system='Darwin'` settings) and the existing `local_agent.test_portable` | Same tests are platform-neutral; CI matrix covers `local_agent` only (see below) |
| Portable code path with real Docker + real Qwen | ✓ run on Windows with `--backend portable` (see `EXPERIMENT_LOG.md`, portable smoke) | **Not run** |
| Native model inference | ✓ Windows CUDA, Ollama 0.40.17 | **Not validated — no Mac was available** |
| Benchmark equivalence across hardware | Not established; do not pool | — |

## 1. Requirements (both platforms)

* Python **3.11** with the pinned packages in `local_agent/requirements.txt` (mini-swe-agent 2.4.6, litellm 1.81.16, pydantic 2.12.5); Windows keeps its exact 3.11.9 environment at `E:\CSC2108Local\.venv`.
* Docker Desktop with Linux containers. Images:
  * agent sandbox `python:3.11-slim-bookworm@sha256:a83ba18a…` (multi-arch index: native **arm64** on Apple Silicon, **amd64** on Windows/Intel Macs);
  * Peter's judge `csc2108-judge:0.2.1` built from `judge/Dockerfile` (multi-arch digest-pinned `python:3.12-slim`).
* Ollama serving `qwen3.5:9b` digest `56671c2a…3c90` (Q4_K_M) on a **dedicated** loopback port (default `127.0.0.1:11435`).
* Optional: Codex CLI (for Codex-authored guidance) and an OpenAI key in a `.env` file (for direct API guidance).

## 2. Windows setup (existing desktop — nothing to migrate)

```powershell
Set-Location <checkout>
. .\local_baseline\env.ps1            # E: caches, MSWEA config, TEMP, PYTHONUTF8
& .\local_baseline\start_ollama.ps1   # dedicated server on 11435 (does not pull models)
$py = 'E:\CSC2108Local\.venv\Scripts\python.exe'
docker build -t csc2108-judge:0.2.1 judge      # once
& $py -m local_agent verify                    # frozen sources, model digest, images
```

The Windows backend keeps the historical data root `E:\CSC2108Local` and the shared lock `E:\CSC2108Local\eval-v2\gpu.lock`.
Study artifacts go to `E:\CSC2108Local\reasoning-effectiveness` (override with `CSC2108_STUDY_ROOT`).

## 3. macOS setup

Follow `docs/MACOS.md` sections 1–2 first (virtual environment, `python -m local_agent prepare`, dedicated
`ollama serve` on 11435, `python -m local_agent verify`). `prepare` records native image IDs in
`$CSC2108_ROOT/portable-images.json`, which the portable adapter requires. Then:

```bash
export CSC2108_ROOT="${CSC2108_ROOT:-$HOME/.local/share/csc2108}"
source "$CSC2108_ROOT/.venv/bin/activate"
docker build -t csc2108-judge:0.2.1 judge        # native architecture
python -m unittest guided_agent.test_guided       # offline
```

Defaults on portable hosts: data root `CSC2108_ROOT` (default `~/.local/share/csc2108`), study root
`$CSC2108_ROOT/reasoning-effectiveness`, endpoint `CSC2108_OLLAMA_ENDPOINT` (loopback only, never 11434),
POSIX advisory lock `$CSC2108_ROOT/eval-v2/gpu.lock`. NVIDIA telemetry is recorded as unavailable, not as
a failure. **Only one data root per machine should run inference**: locks are per data root.

## 4. Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `CSC2108_ROOT` | Portable data root (Windows backend is fixed to `E:\CSC2108Local`) | `~/.local/share/csc2108` |
| `CSC2108_STUDY_ROOT` | Where tasks, guidance, runs and ledgers are written | `<root>/reasoning-effectiveness` |
| `CSC2108_OLLAMA_ENDPOINT` | Dedicated Ollama endpoint (portable) | `http://127.0.0.1:11435` |
| `CSC2108_VENDOR` | LiveCodeBench evaluator checkout used by `local_agent prepare` | `<root>/vendor/LiveCodeBench` |
| `CSC2108_LCB_SHARD` | Path to the pinned `test6.jsonl` (sha256 `bb4c364f…`); otherwise downloaded into `judge/.cache` | auto |
| `CSC2108_ENV_FILE` | `.env` containing `OPENAI_API_KEY` and `FRONTIER_MODEL` | `<checkout parent>/.env` |
| `JUDGE_IMAGE` | Override judge image tag | `csc2108-judge:0.2.1` |

## 5. Synthetic smoke test (no LiveCodeBench data, no frontier)

```bash
python -m guided_agent prepare-fixture
python -m guided_agent batch plans/smoke.json        # {"batch":"smoke","attempts":[{"task_id":"fixture-sum-signed","condition":"A"}]}
python -m guided_agent evaluate "$CSC2108_STUDY_ROOT/runs/smoke"
```

On Windows add `--backend portable` *before* the subcommand to exercise the portable adapter on the same host.
Expected: `submitted` after ~3 actions; hidden fixture `pass`.

## 6. Running A/C/D

```bash
python -m guided_agent prepare-tasks --ids lcb-atcoder-abc396_a lcb-atcoder-abc392_d
# Codex-authored guidance (isolated, model-only; see EXPERIMENT_LOG.md for the isolation evidence)
python -m guided_agent author --provider codex --prompt-id plan-v1 --tasks lcb-atcoder-abc392_d --label mine
python -m guided_agent author --provider codex --prompt-id contract-v1 --tasks lcb-atcoder-abc392_d --label mine
# Direct API guidance (paid; ledger enforces 12 requests / $10 per study root)
python -m guided_agent author --provider api --prompt-id plan-v1 --tasks lcb-atcoder-abc392_d --label api --purpose "why"
python -m guided_agent batch plan.json               # sequential, under the GPU lock, hard outer timeout per attempt
python -m guided_agent evaluate <study>/runs/<batch>  # hidden judge, after all attempts
python -m guided_agent summarize <study>/runs/<batch>
```

A batch plan lists attempts: `{"task_id", "condition": "A"|"C"|"D", "guidance": <artifact path for C/D>,
"variant"?, "seed"?, "aci"?, "injection"?}`. Guidance artifacts are bound to the task statement hash and
are replayed through the teammates' `SavedPlan` / `SavedContract` classes.

## 7. Provenance recorded per attempt

`result.json` (Peter's handoff fields plus): host OS/release/machine/node, host backend
(`windows-frozen-globals` or `portable.adapted_run`), model digest and details, Ollama version, agent image ID,
judge image ID / version / tests sha256, frozen-file verification (38 hashes), sampler wire verification,
source commit and dirty state, guidance provider/model/prompt/hash, GPU telemetry (or its absence),
per-call token usage. `attempts.jsonl` holds every judge-public call; `eval/<run_id>.json` holds the hidden outcome.

## 8. Remaining native Mac validation (team action)

1. `docs/MACOS.md` §1–3 on an Apple Silicon Mac (confirms `portable-images.json`, arm64 images, digest-matched model).
2. `python -m unittest guided_agent.test_guided local_agent.test_portable`.
3. Section 5 synthetic smoke with real inference; confirm `host_adapter = portable.adapted_run`,
   `sampler_wire_verified = true`, a `submitted` exit and hidden `pass`.
4. One dev task under A and C with the saved Codex guidance from this pass, to compare trajectories with Windows.
   Record results as a **separate hardware cohort**.
