# Quick one-shot ablation

One exploratory pilot, six fresh LiveCodeBench v6 problems (2 easy, 3 medium, 1 hard), one matching seed, two conditions. No tuning or additional benchmark attempts. All work stays on the existing optimization branch; no push or merge.

A invokes the existing `local_eval_v2/runtime.py` implementation and original agent system prompt, with the unchanged `heredoc-v6-16k-common` model profile. It is explicitly a **shortened-budget variant**: 120 seconds outer inference wall, at most 10 actions and 3 repair groups. Interpreter startup and a five-second finalization reserve come from the 120-second cap; the actual remaining internal budget is logged. A memory-only wrapper records typed model exceptions without altering their behavior or changing existing source files.

B calls `litellm.completion` once against the same project Ollama server, with identical model/sampler/seed, no tools, execution feedback or repairs. Both receive exactly the same initial problem, starter and interface text. A additionally has its existing public checker. Both cold-load the model. A single closed Python fence is mechanically removed from B's output, or raw source is accepted; ambiguous/unclosed fences are rejected. Source is never repaired, joined or edited by Codex. All candidate execution occurs in the existing Docker sandbox/judge.

`prepare.py` selects tasks by eligibility/metadata only and refuses an existing artifact directory. The salt and deterministic selection rule, all exclusions and contest fallbacks are in `manifest.json`. Runtime artifacts, frozen source, prompts, candidates and private data stay under `E:\CSC2108Local\one-shot-ablation`; Git contains code, the metadata manifest, aggregate results and the report only.

`run.py` is single-use and refuses a second execution or timer reset. One shared GPU lock covers synthetic sanity, all inference and independent official grading. A 35-minute total ceiling includes sanity and cleanup, with a 25-second shutdown reserve. Each child has an outer timeout. If the global budget would be exceeded, it stops and retains partial evidence; unfinished grading is never counted as a wrong answer. Only recorded owned processes/containers are cleaned up. No foreign workload is unloaded.

From the repository root, in PowerShell:

```powershell
. .\local_baseline\env.ps1
$pilotPython = 'E:\CSC2108Local\.venv\Scripts\python.exe'
& $pilotPython one_shot_ablation\prepare.py   # Once only, before inference
& $pilotPython one_shot_ablation\run.py       # Once only: includes synthetic A/B sanity
& $pilotPython one_shot_ablation\report.py    # Analysis only; never generates solutions
```

Existing frozen sources/results are read-only. Do not rerun the pilot, reuse its scored problems as fresh validation, or reset its timer. Missing timeout replies have unknown exact generation counts; report observed token totals plus explicit bounds rather than inventing complete telemetry. This is not a comparison under matched compute and not a repository-repair benchmark.

Completed: all12 benchmark attempts plus two synthetic checks, in640.2seconds total experimental wall. Agent3/6; one-shot4/6; no agent-only successes. See REPORT.md, metrics.csv and verification.json. One agent timeout reply has unknown exact tokens; its4,096-token bound is explicit. No additional model runs were made. The post-run report generator records its analysis-source hash separately from the original frozen execution source; classification/formatting edits did not change inference or candidates.
