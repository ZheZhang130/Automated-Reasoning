# CSC2108 extended local comparison

This directory extends the immutable `local_baseline` pilot on branch `feat/csc2108-local-eval-v2`. It keeps the upstream mini-SWE-agent loop, LiteLLM Ollama adapter and existing isolated Docker environment. See [AUDIT.md](AUDIT.md), [DEVELOPMENT.md](DEVELOPMENT.md), [DECISION.md](DECISION.md) and [RESULTS.md](RESULTS.md).

The primary plan is 24 distinct problems × three models × two fresh attempts = **144 runs**. Models are `qwen3.5:9b`, `qwen2.5-coder:14b` and `qwen2.5-coder:7b`. All use the same text workflow, T=0.2, 16K context, 4K response limit, 20 actions, 3 repairs and 600 seconds. Thinking is disabled for Qwen3.5. The development-only thinking experiment is distinct from the primary comparison.

Primary profile: `heredoc-v6-16k-common`. Explicit shared sampler options: top-k 40, top-p 0.9, min-p 0, repeat penalty 1.0, repeat-last-n 64, presence/frequency penalties 0. Actual outgoing request bodies are captured and checked; the runner stops before judging a request-contract mismatch. A complete native `options` block avoids LiteLLM's frequency-to-repeat alias and unsupported OpenAI-parameter filtering.

## Storage and inference

Model manifests and blobs: `E:\OllamaModels`. Inference: the dedicated local Ollama server at `http://127.0.0.1:11435`, reached through LiteLLM's `ollama_chat/` adapter by mini-SWE-agent 2.4.6. LiteLLM is an API adapter, not a model host. Ollama Desktop uses 11434; the runner refuses to start when that endpoint has a loaded model. Project models unload between runs. One runtime owns `E:\CSC2108Local\eval-v2\gpu.lock` at a time.

Python/dependencies: `E:\CSC2108Local\.venv`; existing pins in `../local_baseline/requirements.lock`. Docker disks remain at `E:\DockerDesktop`. Dataset cache, synthetic fixtures, raw trajectories, candidates, judge details, logs and all large artifacts remain under `E:\CSC2108Local\eval-v2`. No weights, reference solutions or raw private feedback are committed.

The exact frozen model digests, quantizations, image IDs, GPU/driver identity, Python version, task/source hashes and configuration are in the batch's `plan.json` and per-attempt configuration/result files. The primary batch is `E:\CSC2108Local\eval-v2\batches\extended-24-v6-common`.

The plan's `git_base` is the prior pilot commit, because the new files were uncommitted when inference was frozen. The 16 source hashes and byte-for-byte source archive identify the actual implementation used. Later local commits do not replace that provenance.

The primary plan records software versions at freeze time: Ollama 0.40.16 on both endpoints, Python 3.11.9, mini-SWE-agent 2.4.6, LiteLLM 1.81.16, Pydantic 2.12.5/core 2.41.5, and all installed package versions. A mid-batch environment snapshot from the superseded v5 experiment remains with that experiment.

## Reproduce and resume

Run from this directory in PowerShell with the existing E: environment and both local Docker/Ollama services available:

```powershell
. ..\local_baseline\env.ps1
$pythonExe = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $pythonExe -m unittest -v test_v2
& $pythonExe -m unittest -v test_analysis
& $pythonExe -m unittest -v test_interruption
& $pythonExe -m unittest -v test_wire
& $pythonExe -m compileall -q .
& $pythonExe verify_manifest.py E:\CSC2108Local\eval-v2\evaluation-24\manifest.json

# Start a NEW, empty batch directory; never reuse the completed primary directory.
& $pythonExe batch.py --manifest E:\CSC2108Local\eval-v2\evaluation-24\manifest.json --batch E:\CSC2108Local\eval-v2\batches\NEW-BATCH --profile heredoc-v6-16k-common --repetitions 2

# Resume the existing primary batch, preserving completed runs and inference outputs.
& $pythonExe batch.py --batch E:\CSC2108Local\eval-v2\batches\extended-24-v6-common --resume
& $pythonExe analyze.py --batch E:\CSC2108Local\eval-v2\batches\extended-24-v6-common --report RESULTS.md
& $pythonExe verify_batch.py E:\CSC2108Local\eval-v2\batches\extended-24-v6-common
```

The measured primary invocation was `batch.py --manifest E:\CSC2108Local\eval-v2\evaluation-24\manifest.json --batch E:\CSC2108Local\eval-v2\batches\extended-24-v6-common --profile heredoc-v6-16k-common --repetitions 2`, using the Python executable and environment above. Every actual child command, including model, seed, task path and execution budgets, is saved in its `attempt-01.claim.json` file. Existing measured directories require `--resume`; reproduction uses a new directory.

`--models` can restrict a new batch, `--repetitions` changes a new schedule, and `--max-new-runs N` stops cleanly after N newly completed jobs. Existing plans reject changed configuration/source/task/model/image hashes. A clean pinned evaluator checkout is required. Do not edit frozen runtime files during a batch. Completed jobs skip both inference and judging. A runtime result without evaluation resumes with judging only. An incomplete runtime is preserved and requires explicit `--retry-interrupted`; its replacement is a new attempt directory. Infrastructure outcomes are retained and reported separately, not silently retried as new successes.

Run only one batch/development driver at a time. The GPU runtime lock guards agent processes, but parent preflight unload operations are not a scheduler for independent competing batch drivers. Avoid other GPU-heavy applications throughout a measured batch. After an abrupt Windows process termination, let any surviving runtime finish before resuming; live runtime ownership must clear first.

Resume on the same hardware and software versions recorded in the plan. The automatic guards cover source, task, model and image identity; host driver/package changes require restoring the recorded environment or starting a new experiment.

The v6 live resume validation ran two synthetic attempts in separate invocations, then a third no-op resume. The second invocation used the batch's archived source, proving it is self-contained for resumption. All 16 first-attempt files retained identical bytes and modification times. All 16 archived source files matched their frozen hashes. Evidence: `E:\CSC2108Local\eval-v2\resume-common-v6\verification.json`. The earlier v5 resume proof is preserved separately.

The completed 144-run primary batch also passed a real archived-source resume: zero new inference or judging, with all **2,277** run files retaining identical bytes and modification times. Evidence: the batch's `full-resume-verification.json`. `benchmark_metrics.csv`, `benchmark_summary.json` and `benchmark_verification.json` are lightweight repository copies of the numerical results and final integrity checks. `benchmark_provenance.json` exports exact model digests/quantizations, effective settings, prompts, source hashes, package versions, image identities and hardware details without private cases or candidate source. Candidate source, private test contents and raw trajectories remain on E:.

If the repository source later changes, resume using the frozen source rather than mixing implementations:

```powershell
& $pythonExe E:\CSC2108Local\eval-v2\batches\extended-24-v6-common\frozen-source\local_eval_v2\batch.py --batch E:\CSC2108Local\eval-v2\batches\extended-24-v6-common --resume
```

## Superseded tag-default experiment

An initial v5 batch stopped deliberately at **111/144** after a metadata audit identified unequal inherited model-tag sampler settings. Qwen3.5 declared presence penalty 1.5, top-k 20 and top-p 0.95, while the Qwen2.5 tags had no such overrides. Shared client arguments had not fully harmonized sampling. All 111 completed runs were verified against their original source hashes and preserved, with the original source archive, under `E:\CSC2108Local\eval-v2\batches\extended-24-v5-t02`. See `TAG_DEFAULT_RESULTS.md` and `DECISION.md`.

V6 is a new 144-run primary plan with explicit common sampler settings, revalidated on all 12 development model/task combinations. The frozen 24-task selection remains unchanged. These tasks were previously run in v5 and are not claimed as newly unseen in v6. No prior candidate, private case, private feedback or solution-specific advice was supplied to an agent. Neither batch updates model weights. The v5 observations are never pooled with primary v6 accuracy.

## Dataset and evaluator

`evaluation_manifest.json` freezes 8 easy/10 medium/6 hard tasks: 12 AtCoder, 12 LeetCode, 13 contests, maximum two tasks per contest/platform. Source: [official code_generation_lite](https://huggingface.co/datasets/livecodebench/code_generation_lite/tree/0fe84c3912ea0c4d4a78037083943e8f0c4dd505), newest compatible `release_v6`, newest component `test6.jsonl` only. Source SHA256 `bb4c364f71921c4495a6ad15abe1a927350b720009f4933e2e71f8af0f6fd1f5`. This is the latest compatible release found, not a claim that these 2025 problems are contamination-free.

To reconstruct on another machine, run `dataset.py download`, then `dataset.py select` into an absent `evaluation-24` directory and compare its manifest to the committed one. Selection is deterministic: balance platforms within each difficulty, newest date first, max two per contest, supported stdin/JSON functional interfaces, exclude image/custom-node problems and the old pilot tasks. Development tasks are synthetic, have their own IDs, and never enter the evaluation manifest. `verify_manifest.py` checks identities, dates, quotas, exclusions, complete public statements, official starters/public tests, allowlists and all hashes without decoding private tests on the host.

Official evaluator: [LiveCodeBench commit 28fef95](https://github.com/LiveCodeBench/LiveCodeBench/tree/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24), at `E:\CSC2108Local\vendor\LiveCodeBench`. Judge v2 derives from the existing pinned v1 image and adds an internal 175-second deadline (two-second kill grace), retaining the official six-second per-test timeout. Build with `docker build -f judge.Dockerfile -t csc2108-lcb-judge:v2 .`. This prevents an orphan judge from continuing after a host interruption.

Only public files mount inside the agent: task statement, examples, checker and optional official starter. Containers have no network, read-only root, unprivileged user, capped resources and ephemeral writable workspaces. Source extraction does not execute candidates on Windows. After the agent container terminates, a separate offline judge receives the candidate and private row via stdin. Private results never feed back into agents. The functional public checker follows the official method interface with stdlib/typing imports; linked custom node types are excluded.

## Development and verification commands

```powershell
& $pythonExe audit_judge.py --medium-reference E:\CSC2108Local\eval-v2\audit\judge-references\atcoder-abc301_c-reference\solution.py
& $pythonExe make_dev.py
& $pythonExe develop.py --stage memory
& $pythonExe develop.py --stage stress
& $pythonExe develop.py --stage agents
& $pythonExe followup_dev.py
& $pythonExe followup_dev.py --common-sampler
& $pythonExe validate_v5.py
& $pythonExe summarize_development.py
```

Some fixture/audit commands deliberately refuse existing output directories. The first real judge audit used official sample code for old excluded abc301 A and a separate oracle for old excluded C, then tested wrong-answer and syntax candidates. Its later CLI requires `--medium-reference` pointing to an external audit-only reference; none is shipped in Git. Both v1 and v2 passed all six real-task checks. Synthetic functional correct/wrong checks and six scheduling/budget/submission unit checks also passed. Development version prototypes and failures remain on E:; they are not pooled into primary benchmark results.

No frontier assistance was supplied to Qwen for the selected problems, no benchmark candidate was manually repaired, and no paid inference was invoked. This extension does not implement frontier-guided intervention. Nothing on this branch is pushed or merged without approval.

## File map

| Purpose | Files |
| --- | --- |
| Minimal runtime extensions and common settings | `runtime.py`, `common.py`, `profiles.json`, `public_check.py` |
| Frozen scheduling, resumption and judge deadline | `batch.py`, `judge.Dockerfile` |
| Dataset preparation and verification | `dataset.py`, `verify_manifest.py`, `evaluation_manifest.json` |
| Development fixtures and experiments | `make_dev.py`, `develop.py`, `followup_dev.py` |
| Reference and interface audits | `audit_judge.py`, `validate_v5.py` |
| Analysis and artifact verification | `analyze.py`, `verify_batch.py`, `summarize_development.py` |
| Regression/accounting checks | `test_v2.py`, `test_analysis.py`, `test_interruption.py`, `test_wire.py` |
| Decisions, evidence and results | `AUDIT.md`, `DECISION.md`, `DEVELOPMENT.md`, `RESULTS.md`, `TAG_DEFAULT_RESULTS.md`, `development_metrics.csv` |
| Primary numerical exports and provenance | `benchmark_metrics.csv`, `benchmark_summary.json`, `benchmark_verification.json`, `benchmark_provenance.json` |
| Checkout line endings | `.gitattributes` |

Raw source candidates, reference oracles, private rows and trajectories stay outside the repository on E:. The lightweight tables/metrics are review artifacts; the original `local_baseline` directory has no changes.
