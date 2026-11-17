# Local Qwen optimization

See [PLAN.md](PLAN.md) for the preregistered resource/split policy and [DECISIONS.md](DECISIONS.md) for adaptive decisions. This work is local only and remains on `feat/csc2108-qwen-local-optimization`. Previous baseline/eval-v2 sources and benchmark evidence are unchanged. Full experiment data lives at `E:\CSC2108Local\optimization`, outside Git; small manifests, aggregate results and reports live here.

## Runtime

mini-SWE-agent 2.4.6 → LiteLLM 1.81.16 → dedicated Ollama at `http://127.0.0.1:11435` → `qwen3.5:9b` Q4_K_M, digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`. Weights stay under `E:\OllamaModels`. No model downloads or paid inference are needed. The desktop Ollama endpoint is checked for foreign loaded models; no foreign workload is unloaded.

`runtime_opt.py` versions the v2 runner with an optional native-history transport repair, configurable query budget and GPU sampling. The original control launches the original archived v2 runner. Both retain the existing sandbox, public checker, repair accounting, candidate extraction and official evaluator. `transport.py` repairs the pinned serializer through an explicit per-request body override, without changing installed packages. Every native request is checked for retained assistant calls and linked tool results; every run verifies actual wire sampling and thinking settings.

`batch.py` freezes source bytes, profiles, task hashes, model digest, software versions and Docker image IDs before running. It executes the archived runtime, so later development cannot silently change a batch. Original evidence and failed attempts are retained. A completed inference without a judge result resumes by judging the saved candidate; a completed job is skipped. Interrupted children must exit before retry, and only containers with matching recorded ownership may be cleaned up. Official private outcomes are never sent back into a trajectory.

## Commands (PowerShell, from this directory)

```powershell
. ..\local_baseline\env.ps1
$optimizationPython = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $optimizationPython test_transport.py
& $optimizationPython test_methodology.py
& $optimizationPython -m compileall -q .

# Resume exactly the frozen plan, with no configuration overrides:
& $optimizationPython batch.py --batch E:\CSC2108Local\optimization\batches\dev-interface-thinking --resume
# Explicitly retry an interrupted inference into a NEW attempt directory:
& $optimizationPython batch.py --batch E:\CSC2108Local\optimization\batches\dev-interface-thinking --resume --retry-interrupted
& $optimizationPython analyze.py E:\CSC2108Local\optimization\batches\dev-interface-thinking
```

A new batch needs a fresh E: output directory, an existing frozen manifest, and explicit profile names. Example:

```powershell
& $optimizationPython batch.py --batch E:\CSC2108Local\optimization\batches\NEW-NAME `
  --manifest E:\CSC2108Local\optimization\dataset\development\manifest.json `
  --profiles heredoc-v6-16k-common native-fixed-16k-4k --seeds 2108
```

Never rerun `prepare.py` over the frozen dataset: it deliberately refuses replacement. Never use development/selection outcomes to alter held-out tasks or tune a configuration after held-out starts. The budget gate charges observed generation/prefill/load and conservatively charges missing timeout responses at their declared caps. Agent elapsed time includes preflight, cold model loading and container setup through agent termination; it excludes extraction/cleanup and judging. Later batches additionally record full child-invocation and judge wall times separately. `ollama_ps` reports model allocation/residency; GPU samples also include desktop/background memory and are not process-exclusive measurements.

## Evidence layout

Each batch contains `plan.json`, a `frozen-source/` tree and per-task/profile/seed slots. Each attempt retains the exact task, complete trajectory, raw Ollama request/response arrays, server-log slice, configuration, public-test events, extracted candidate, GPU samples for the new runner and separate judge-attempt logs. `complete.json` points to the accepted completed attempt; it does not delete earlier attempts. Aggregate `analysis.json` and `metrics.csv` are derived, regenerable views. Timeout token/duration totals are lower bounds, with explicit unobserved upper bounds; they are never reported as complete telemetry.

`judge_watch.py` additionally saves the raw official evaluator result, exact owned judge name and Docker OOM events. A confirmed judge-worker OOM is a zero-pass resource failure under the unchanged 1GB allocation, rather than an unexplained harness failure. An older plan can explicitly pin this bookkeeping through `--judge-monitor`; its addendum records the unchanged limits and exact archived wrapper. Unknown infrastructure errors still stop.

## Exporting plots without changing inference dependencies

```powershell
uv --system-certs pip install --python $optimizationPython --no-deps --only-binary :all: `
  --target E:\CSC2108Local\optimization\plotting-packages -r plot-requirements.txt
& $optimizationPython plot.py E:\CSC2108Local\optimization\batches\BATCH-NAME
```

The plotting target is isolated from the inference environment; it shares the existing NumPy/packaging/dateutil/six. Matplotlib cache also stays on E:. SVG, PNG and PDF exports were rendered and visually checked, and the inference package inventory was verified unchanged. `cohort.py` can combine paired seeds or matched subsets using pointers to original attempts, without copying candidates or rerunning inference/judging. Derived comparisons explicitly cannot execute benchmark jobs.

## Final comparison and practical entrypoint

The completed report and machine-readable recommendation are generated after the frozen selection repeat and held-out comparison. The original control remains the fallback when a gain is uncertain. `selected.py --task <trusted-public-bundle> --output <new-E-directory> --seed 2108` verifies the source/configuration/image pins and uses the final recommended profile; `--challenger` explicitly requests the evaluated alternative. It runs the original v2 implementation when the original control is recommended.

```powershell
& $optimizationPython batch.py --batch E:\CSC2108Local\optimization\batches\heldout-final --resume
& $optimizationPython analyze.py E:\CSC2108Local\optimization\batches\heldout-final
& $optimizationPython verify.py E:\CSC2108Local\optimization\batches\heldout-final --baseline
& $optimizationPython finish_report.py
& $optimizationPython plot.py E:\CSC2108Local\optimization\analysis\selection-repeated E:\CSC2108Local\optimization\batches\heldout-final
```

`freeze_final.py` refuses to replace the final selection. Held-out creation additionally requires that selection to be committed. Do not modify the frozen selection or its source files after validation starts. Full telemetry and official outcomes stay outside Git; `results/` exports only aggregate metrics and normalized per-attempt measurements. `final_recommendation.json` implements the preregistered confirmation/fallback rule rather than tuning on validation.

## Completed study

See REPORT.md for all203 measured benchmark attempts and the80-attempt held-out comparison. The experimental challenger passes22/40 versus control19/40, with lower measured wall time/tokens and fewer format errors. Its paired interval touches zero and missing submissions increase9vs8, so the frozen rule retains heredoc-v6-16k-common as the default. selected.py --challenger is the explicitly evaluated experimental alternative. No costly thinking configuration earned a recommendation.

The published report contains editorial interpretation beyond the frozen finish_report.py narrative template. The template's budget uses runtime result.json files; results/allocation_probe_accounting.json separately itemizes three one-token allocation probes (10.7446001seconds). The published compute_budget.json reports both the runtime gate charge and their full sum. Rerunning finish_report.py regenerates the runtime-record totals; add that allocation itemization for the complete study total. Benchmark scores and all statistical calculations come from the unchanged frozen analysis code.

Final integrity, zero-job resume evidence, entrypoint acceptance and the65 scored IDs to exclude from future fresh validation are in results/. Full trajectories remain under E:\CSC2108Local\optimization. No benchmark candidate or private test case is included in Git.
