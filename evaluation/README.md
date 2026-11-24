# Evaluation pipeline

The evaluation owns everything around the agent: the tasks, the judge, the schedule, hidden scoring and the metrics.
The agent (`guided_agent`) is treated as a black box that receives a task bundle and a plan entry, may call
judge-public while it runs, and leaves `result.json` and `submission.py` behind.

```
evaluation plan -> evaluation tasks -> evaluation judge -> evaluation guidance -> evaluation run
                -> evaluation score -> evaluation metrics
```

Every step after `plan` takes the same plan file, so the task list is decided once.

| Step | Owner | What it does |
| --- | --- | --- |
| `plan` | evaluation | tasks from `judge/manifests/*.json`, conditions, seeds → one plan JSON |
| `tasks` | evaluation | judge suites (public and hidden tests) and the agent's bundles, from `judge/build_data.py`, hash-checked against the manifest |
| `judge` | evaluation | builds `csc2108-judge:0.2.1` from `judge/Dockerfile`, starts judge-public, runs the selftest |
| `guidance` | evaluation schedules, agent executes | authors the missing C/D guidance with `guided_agent author` (paid; needs `--yes`), then freezes it |
| `run` | evaluation schedules, agent executes | checks that tasks, freeze and image are ready, then runs `guided_agent batch` |
| `score` | evaluation | judge-hidden on every finished run → `<batch>/eval/<run_id>.json`, then `guided_agent measure` |
| `metrics` | evaluation | report, statistics, failure categories (definitions below) |

### Why task preparation and hidden scoring moved here

`guided_agent` also has `prepare-tasks` and `evaluate`. They are kept unchanged, and they still work, but the
final pipeline does not use them:

* **Separation.** The agent should not build, hold or score the tests it is evaluated on. Here the only things the
  agent touches are `<study>/bundles/<id>` (statement, public samples, the `check.py` stub) and judge-public. Hidden
  tests are built by the evaluation, loaded into judge-hidden only by `evaluation score`, and never pass through
  agent code.
* **One task list.** The plan is the single source of which tasks run; previously the same IDs were typed for
  `prepare-tasks`, both `author` calls and the plan, and had to agree by hand (a smoke subset could silently differ).
* **Stricter and resumable.** `evaluation tasks` accepts only tasks pinned in `judge/manifests`, re-verifies the
  hashes of tasks already built, and rebuilds a task left half-written by an interrupted build;
  `prepare-tasks` accepts IDs outside the manifests and stops on any existing directory.
* **The judge image.** Nothing in the agent's path built `csc2108-judge:0.2.1`, and `judge/setup.sh` is a POSIX
  shell script; `evaluation judge` builds it on every OS.

The outputs are the same files as before, so the agent reads them unchanged: the task and bundle bytes match
`guided_agent.tasks.prepare`, the judge container names match `guided_agent.backend.judge_client`, and
`evaluation score` writes the same `eval/<run_id>.json` as `guided_agent evaluate`. The tests check all three against
Sam's code, and re-scoring the pilot batches with the real judge reproduces their existing `eval/` files.

## Full run (Windows, the frozen reference host)

Run everything from the repository root in one PowerShell session, with Docker Desktop running.

```powershell
. .\local_baseline\env.ps1
$py = 'E:\CSC2108Local\.venv\Scripts\python.exe'
$env:CSC2108_STUDY_ROOT = 'E:\CSC2108Local\final-study'      # new, empty, outside the checkout
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'; $env:PYTHONIOENCODING = 'utf-8'
& $py -m local_agent verify                                    # 38 frozen hashes, model digest
$plan = "$env:CSC2108_STUDY_ROOT\plans\final-main.json"
```

**1. API key and ceilings.** In the `.env` that `guided_agent.providers.env_file()` reads (default: the folder
*above* the checkout), set `OPENAI_API_KEY` and `FRONTIER_MODEL=openai/gpt-6.2-sol`. The paid-call ceilings are the
constants `MAX_REQUESTS, MAX_USD = 20, 10.00` in `guided_agent/providers.py`, shared by the whole study ledger. A full
run needs far more than 20 requests (B needs at least one per (task, seed), C and D one per task each, plus every E
trigger), so set them to the team-agreed budget, commit that change, and use a new study root (a ledger file can
lower the ceilings but never raise them).

**2. Plan.** One batch holds every (task, condition, seed). Attempts are ordered seed → task → condition, so a
stopped batch still holds whole (task, seed) blocks.

```powershell
& $py -m evaluation plan --batch final-main --seeds 2108 2109 2110 --out $plan --cohort "final windows"
```

**3. Tasks, judge, guidance.** Each step can be rerun; finished work is verified and kept.

```powershell
& $py -m evaluation tasks $plan              # 60 tasks: judge suites + agent bundles, hashes checked
& $py -m evaluation judge                    # build csc2108-judge:0.2.1 if missing, start judge-public, selftest
& $py -m evaluation guidance $plan           # dry run: how many C/D artifacts are missing (= paid requests)
& $py -m evaluation guidance $plan --yes     # author them, then write final-main.freeze.json
```

The freeze holds the sha256 of every guidance artifact. Commit or archive it before step 4.

**4. Run.** Refuses to start while a task, the freeze or the judge image is missing, or a guidance artifact changed.

```powershell
& $py -m evaluation run $plan                # guided_agent batch; resumable: rerun the same command
```

**5. Score and report**, only after every attempt has finished.

```powershell
& $py -m evaluation score $plan              # judge-hidden, then guided_agent measure
& $py -m evaluation check "$env:CSC2108_STUDY_ROOT\plans\final-main.freeze.json"   # no artifact changed
& $py -m evaluation metrics "$env:CSC2108_STUDY_ROOT\runs\final-main" --out "$env:CSC2108_STUDY_ROOT\report"
```

`metrics` writes `report.md`, `report.json` and `runs.csv` (one row per scheduled run). It can take several
batch directories, for example a rerun batch next to the main one.

**Smoke first.** The same steps with `--per-difficulty 1 --seeds 2108` (3 tasks, 15 attempts) and a separate
`--batch` name check the whole path, including the API, before the full run.

`--study` and `--backend` go before the command (`python -m evaluation --study D:\s run $plan`); `--backend` is passed
to `guided_agent`.

## Metric definitions

| Metric | Definition |
| --- | --- |
| Final pass rate (primary) | hidden status `pass` / included runs. A missing submission or a context overflow is a failure |
| Public–hidden gap | final public status `pass` but hidden not `pass`, over included runs |
| Failure recovery | among runs with at least one public `candidate_failure`, the fraction that pass hidden |
| E triggered subset | (task, seed) pairs where E's diagnosis triggered: E vs A pass rate, also restricted to pairs whose A run had a public failure; plus E's trigger rate |
| Frontier cost | run-time requests (B, E) plus upfront guidance (C, D) counted once per artifact; per pass. `null` when any request has no measured cost (for example Codex replay) |
| Runtime, tokens | median and IQR of `wall_seconds`, local inference seconds, local prompt/completion tokens |
| Budget usage | mean actions and repairs, repair distribution, exit status counts, outcome categories |

**Exclusions.** A (task, seed) block is dropped from every condition when any of its runs was an infrastructure
failure (`correctness.infrastructure_failure`, or a hidden `infrastructure_error` / `malformed_record`) or was never
run. The report lists every excluded block. To rerun an infrastructure failure, move its run directory aside and
rerun the batch; guidance errors stay in their condition (intent to treat).

**Comparisons.** B, C, D and E against A on the same tasks. The task is the unit: the mean pass over the seeds
both conditions have. The report gives the mean difference, a 95% bootstrap CI (10,000 resamples of tasks, seed 2108),
a paired sign-flip permutation p-value (exact up to 16 non-zero tasks), and McNemar's exact test on (task, seed)
pairs. Holm adjusts C, D and E only; B and the by-difficulty tables are exploratory.

**Failure categories** (first that applies): `hidden_pass`; `infrastructure` (excluded); `context_overflow`;
`local_timeout_no_program` / `local_timeout_with_program` (a LiteLLM/Ollama request timeout, before or after a
candidate program existed; other timeouts, such as Docker, are infrastructure); `truncated_no_program` (responses hit
the 4096-token cap and no candidate was ever extracted); `budget_limit` (action, repair or deadline limit);
`format_errors`; `public_pass_hidden_fail`; `never_passed_public`; `no_submission`. The report also gives a
transition table against A (which runs a condition fixed or broke), a sensitivity analysis without timeout runs,
process metrics and per-host decode speed.

## macOS notes

Mac results are a separate hardware cohort. On Apple Silicon, `ollama pull qwen3.5:9b` now returns an MLX nvfp4
build with a different digest. Pull the frozen GGUF instead and give it the name the runtime uses:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen3.5:9b-q4_K_M        # digest 56671c2a…, Q4_K_M
OLLAMA_HOST=127.0.0.1:11435 ollama cp qwen3.5:9b-q4_K_M qwen3.5:9b
```

## Tests

```bash
python -m unittest evaluation.test_evaluation
```
