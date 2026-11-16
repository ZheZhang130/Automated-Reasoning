# Setup and measured results — 2026-11-16

**The local coding-agent baseline and nine-run pilot are complete.** Qwen3.5 9B and Qwen2.5-Coder 14B passed the controlled repair task; 7B failed it. Official LiveCodeBench scoring gave 9B **1/3**, 14B **0/3**, and 7B **0/3**. Seven failures were wrong answers and one had no submission. Format errors and logged context truncation limit capability conclusions. No infrastructure-error result occurred in the nine-run batch.

## Git and machine

- Initial checkout: clean `master`, commit `e68d33d`, one worktree, origin `https://github.com/ZheZhang130/Automated-Reasoning.git`; origin/HEAD targets master. Other remote branch: judge.
- Feature branch: `feat/csc2108-mini-swe-local-pilot`. No extra worktree was needed because the checkout was clean. Initial measurements were performed before committing or publishing this work. No resets, stashes or unrelated edits were performed; publication uses this dedicated branch.
- Changes: new `local_baseline/` source/configuration/documentation and appended `.gitignore` rules. Existing orchestration and timeline files are unchanged.
- GPU: NVIDIA GeForce RTX 4080 SUPER, 16,376 MiB, driver 610.88; CUDA reported by nvidia-smi 13.3. Initial display/application usage: 1,694 MiB.
- Initial free space: E: 429,249,531,904 bytes (~399.8 GiB); C: 55,996,895,232 bytes (~52.2 GiB). Current free space and installed versions are recorded in external environment.json.
- Python 3.11.9; uv 0.13.5; Ollama 0.40.16; mini-SWE-agent 2.4.6; LiteLLM 1.81.16; Pydantic 2.12.5 / core 2.41.5; OpenAI client dependency 3.51.0 (no OpenAI endpoint used). Full pins: requirements.lock.
- Docker Desktop 4.71.0; Docker CLI/engine 29.4.1, Linux daemon running. Following user approval, both data and control VHDX files were relocated to `E:\DockerDesktop`, before image downloads/builds. Effective WSL storage, registry base path and disk files were verified. Existing images/volumes match their pre-move inventories; Open WebUI was preserved and resumed.

Relocation evidence and checksum-verified pre-start backup: `E:\CSC2108Local\backups\docker-before-relocation-20261116`. The 10,205,790,208-byte backup SHA256 is `95f14dc6296a22f417dcb71e0a36882c5f429c803ba9f5a13163942d72367974`. Docker's native settings interface performed the move. Its response transport encountered a short-read error, so success was established independently with a subsequent settings read, disk inspection, registry base path and matching image/volume inventories. The account's previously absent `.wslconfig` now places swap at `E:\CSC2108Local\wsl-swap.vhdx`; that file was verified after a controlled restart. No existing model weights were moved or deleted.

Task image digest: `python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39`. Judge image ID: `sha256:62c34bb4ecf3296a832bee7b633edec69c13ae8b5a56cec39ddc451ff0ba9b50`; its base digest and six dependencies are pinned. The initial judge build failed TLS verification; exporting public Windows trust certificates into the E: build context fixed it while retaining verification. No security policy or certificate checks were disabled.

## Model storage and inventory

Persistent account `OLLAMA_MODELS=E:\OllamaModels`; effective project server `http://127.0.0.1:11435`. Its startup log explicitly confirms that path. The original server at 11434 retains its old C: setting until it is restarted; its qwen3.5:9b-q8_0 and qwen3-coder:30b files were left untouched. Automatic approval review rejected stopping the original processes without giving a specific reason. The project server was started separately and left running.

The following downloads completed sequentially in the requested order. All model and projector blobs were verified to exist with manifest-declared sizes beneath `E:\OllamaModels\blobs`; manifests are beneath `E:\OllamaModels\manifests\registry.ollama.ai\library`. Evidence: `E:\CSC2108Local\artifacts\environment.json` and `E:\CSC2108Local\logs\ollama-project.stderr.log`. Total reported installed model size: 20,222,037,409 bytes (~18.8 GiB).

| Model | Actual size (bytes) | Quantization | Full manifest digest |
| --- | ---: | --- | --- |
| qwen3.5:9b | 6,550,825,550 | Q4_K_M | `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90` |
| qwen2.5-coder:14b | 8,988,124,298 | Q4_K_M | `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849` |
| qwen2.5-coder:7b | 4,683,087,561 | Q4_K_M | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` |

## Real connection/protocol probes

All probes used actual local GPU inference through mini-SWE-agent's supported model adapters. **Zero generated shell actions were dispatched.** The only requested action printed a fixed connection token. No benchmark solutions, repair advice or private cases were supplied.

| Model | Initial native parser | Initial minimal text prompt | Common explicit-fence-v2 text prompt |
| --- | --- | --- | --- |
| Qwen3.5 9B | Parsed action (18.985 s) | FormatError: command on opening fence line (8.453 s) | Parsed action (4.797 s) |
| Qwen2.5-Coder 14B | FormatError: JSON content, no tool call (22.218 s) | Parsed action (4.859 s) | Parsed action (7.578 s) |
| Qwen2.5-Coder 7B | FormatError: JSON content, no tool call (6.172 s) | FormatError (4.656 s) | Parsed action (6.750 s) |

The native check used the stock LitellmModel parser; text checks used stock LitellmTextbasedModel and its stock action regex. These are connection diagnostics, not stock end-to-end agent runs. The common v2 prompt adds a multiline `pwd` fence example and explicit newline rules. Every model received the same revised text interface. No parser was relaxed and no algorithmic guidance was added. All earlier failures remain on disk.

Post-probe GPU evidence for v2 (one project model loaded at a time; context 8,192):

| Model | Ollama model allocation | Ollama size_vram | Total GPU usage snapshot | CPU offload reported |
| --- | ---: | ---: | ---: | --- |
| Qwen3.5 9B | 5,862,210,928 B | 5,862,210,928 B | 8,434 MiB | None; allocation equals VRAM |
| Qwen2.5-Coder 14B | 10,425,372,507 B | 10,425,372,507 B | 11,898 MiB | None; allocation equals VRAM |
| Qwen2.5-Coder 7B | 5,148,633,988 B | 5,148,633,988 B | 6,864 MiB | None; allocation equals VRAM |

These are snapshots, not peak-memory measurements. They include display/other application usage. Different warm/load states make probe latency unsuitable for a performance ranking.

Artifacts: `E:\CSC2108Local\artifacts\probe-qwen35-native-01`, `probe-qwen35-text-01`, `probe-qwen35-text-v2`; analogous `probe-qwen14b-*` and `probe-qwen7b-*` directories. Each contains probe.json with complete prompts, responses/errors, model metadata, options and GPU/API snapshots.

## Coding tasks and benchmark status

Before Docker relocation, `fixture-sum-signed` run `20261116T110958-b2477d7e` refused execution because `E:\DockerDesktop` did not exist. It records `infrastructure_error`, zero model-driven actions and no submission. This is **not** a programming failure.

Preflight check `20261116T112107-3a7abec3` repeated that safe refusal. Both records remain intact.

After isolation validation, all three models ran the same controlled task with the common v2 profile. The 7B model's multiple-command responses prompted a workflow-only revision applied to every model: `single-step-v3` explicitly requires one action at a time, noninteractive edits and waiting for feedback; its format-error message repeats the interface syntax. The parser, inference settings, task and budgets did not change. All three were rerun before the pilot. No algorithmic guidance or manual candidate repair was supplied.

| Profile / model | Run ID | Agent seconds | Actions | Repairs | Format errors | Recognized failed tests | Independent correctness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| v2 / Qwen3.5 9B | 20261116T120617-81800222 | 29.000 | 5 | 1 | 0 | 1 | Pass |
| v2 / Qwen2.5-Coder 14B | 20261116T120710-59482dc5 | 14.750 | 7 | 1 | 0 | 1 | Pass |
| v2 / Qwen2.5-Coder 7B | 20261116T120727-dd8a9daa | 10.953 | 1 | 0 | 4 | 1 | Fail; RepeatedFormatError |
| v3 / Qwen3.5 9B | 20261116T120838-4666229a | 12.562 | 5 | 1 | 0 | 1 | Pass |
| v3 / Qwen2.5-Coder 14B | 20261116T120854-a0e402e9 | 11.703 | 4 | 0 | 0 | 0 | Pass |
| v3 / Qwen2.5-Coder 7B | 20261116T120909-2a7e9f5f | 25.610 | 20 | 0 | 0 | 4 | Fail; ActionLimit / invalid Python |

The Qwen3.5 trajectories show inspection → actual failed test → edit → passing test → submission. The 14B v2 run also demonstrates recovery; its v3 run solved the task without a recognized initial failed test. The 7B v3 run shows executable actions and actual feedback but repeated invalid source writes; zero repairs reflects the defined change-after-recognized-failure rule, not success. These are individual observations with different load/warm states, not latency rankings. All sources/trajectories/results are under `E:\CSC2108Local\artifacts\runs\<run ID>`.

Additional real budget diagnostic `20261116T121004-e9bb2ddf` used Qwen3.5/v3 with two actions. It stopped at ActionLimit, preserved the unfinished candidate, and independent evaluation correctly failed it. Trusted containment validation `d54ae8d09320482fa2390310d1663d38` passed resource/mount, read-only-root, failure-feedback, wrong-candidate evaluation and timeout/container-cleanup checks. Judge validation `d2bfa3c26a264f818211ca7e89a6cb34` passed all five synthetic cases: correct, wrong answer, syntax error, timeout, and encoded private tests.

Fixed LiveCodeBench problems, all run once per model:

| ID | Difficulty |
| --- | --- |
| atcoder-abc301_a | easy |
| atcoder-abc301_c | medium |
| atcoder-abc301_e | hard |

Dataset: `livecodebench/code_generation_lite`, `release_v1`, revision `0fe84c3912ea0c4d4a78037083943e8f0c4dd505`. Source test.jsonl SHA256: `2bd02b38beb48e8c46b5b9987095d999ff38cd8efc255ea5d58974317c48f63f` (1,252,609,773 bytes on E:). Evaluator source commit: `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`. Public manifests are frozen before any measured run. Private rows were saved separately without host-side pickle decoding. No reference solutions were generated or supplied for these problems.

The adapter uses the official evaluator in a separate resource-limited container after agent termination. Completed batch: `E:\CSC2108Local\artifacts\pilots\20261116T121253-720e27b2`. It records source hashes, exact task hashes, image identity, complete trajectories, public outputs, candidates and private evaluator results. Every model received the same v3 text workflow, T=0, seed 2108, context 8192, 2048 generated tokens/response, 20 actions, 3 repairs and 600 seconds; Qwen3.5 thinking was disabled. A final source audit confirmed that all frozen implementation hashes remained unchanged. The older release is an infrastructure pilot, not evidence of contamination-free model capability. No generated benchmark output is tracked in Git.

| Model | Problem | Agent seconds | Actions | Repairs | Format errors | Recognized failed public tests | Agent stop | Official evaluation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Qwen3.5 9B | abc301_a | 61.859 | 10 | 2 | 0 | 3 | Submitted | Pass (15 official cases) |
| Qwen3.5 9B | abc301_c | 118.954 | 17 | 2 | 4 | 2 | RepeatedFormatError | Wrong answer |
| Qwen3.5 9B | abc301_e | 149.141 | 8 | 1 | 5 | 4 | RepeatedFormatError | Wrong answer |
| Qwen2.5-Coder 14B | abc301_a | 43.156 | 20 | 0 | 0 | 0 | ActionLimit | Wrong answer |
| Qwen2.5-Coder 14B | abc301_c | 8.969 | 1 | 0 | 0 | 0 | Submitted | Missing submission |
| Qwen2.5-Coder 14B | abc301_e | 88.031 | 20 | 3 | 0 | 10 | ActionLimit | Wrong answer |
| Qwen2.5-Coder 7B | abc301_a | 13.922 | 5 | 0 | 1 | 0 | Submitted | Wrong answer |
| Qwen2.5-Coder 7B | abc301_c | 30.735 | 20 | 0 | 1 | 8 | ActionLimit | Wrong answer |
| Qwen2.5-Coder 7B | abc301_e | 24.937 | 20 | 0 | 1 | 9 | ActionLimit | Wrong answer |

All seven scored failures have the official wrong-answer code -2; the eighth failure has no extracted solution.py. No candidate was manually repaired, no reference solution was supplied, and private feedback never re-entered an agent conversation. Submitted status demonstrably does not imply correctness. Missing submissions count as failures in the denominator of three scheduled problems per model. These individual runtimes include setup/model loading and exclude post-run judging; shorter failed runs do not establish greater efficiency.

Aggregate agent time / actions / repairs / format errors / recognized public failures: 9B = 329.954 s / 35 / 5 / 9 / 9; 14B = 140.156 s / 41 / 3 / 0 / 10; 7B = 69.594 s / 45 / 0 / 3 / 17. Exact run IDs and rows are in metrics.csv and summary.json, reproducible with `summarize.py <batch>`. Individual result.json files retain command failures separately. Full Ollama/API VRAM snapshots are saved per run; the saved server log includes context-truncation events. Available model history therefore became an additional limit despite the complete client histories being retained.

## Verification and remaining work

Passed: six new unittest checks; all four existing orchestration tests; Python compile checks; uv dependency compatibility check; E: blob/manifest inventory; nine real protocol probes (including four preserved parsing failures); pilot refusal of the blocked smoke record. Existing scripted orchestration tests use only their built-in deterministic fixture and do not establish local-model coding success.

Remaining work before full experimentation: improve and separately validate workflow/file-editing adherence, choose and freeze an explicit context/truncation policy, validate repair counting when models combine commands or skip recognized tests, and use a larger fresh selection with repeated trials. Preserve the current batch as the v3 local-only pilot; future changes need new configuration IDs and independent runs. No frontier integration was implemented. Changes are isolated to the dedicated feature branch; the existing master and judge branches are unchanged.
