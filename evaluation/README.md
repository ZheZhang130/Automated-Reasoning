# Evaluation pipeline

The evaluation owns everything around the agent: the benchmark selection, the tasks, the judge, the schedule, hidden
scoring, integrity checks and the metrics. The agent (`guided_agent`) is treated as a black box that receives a task
bundle and a plan entry, may call judge-public while it runs, and leaves `result.json` and `submission.py` behind.

```
evaluation select -> plan -> tasks -> judge -> guidance -> [budget, ready] -> run -> [status] -> score -> metrics
```

Every step after `plan` takes the same plan file, so the task list is decided once. Contents:

1. [Official benchmark launch (consolidated)](#1-official-benchmark-launch-consolidated)
2. [Environment and host setup](#2-environment-and-host-setup)
3. [Steps in detail](#3-steps-in-detail)
4. [Benchmark selection](#4-benchmark-selection)
5. [Interruption, resume, infrastructure failures, exclusions](#5-interruption-resume-infrastructure-failures-exclusions)
6. [Scoring completeness and integrity](#6-scoring-completeness-and-integrity)
7. [API budget](#7-api-budget)
8. [Measurement definitions](#8-measurement-definitions)
9. [Results preservation and provenance](#9-results-preservation-and-provenance)
10. [Judge cross-validation](#10-judge-cross-validation)
11. [Troubleshooting](#11-troubleshooting)
12. [macOS notes](#12-macos-notes)
13. [Tests](#13-tests)

## 1. Official benchmark launch (consolidated)

The preferred official experiment: the 60 tasks of `judge/manifests/final.json` (20 easy, 20 medium, 20 hard, 40
hidden tests each), conditions A–E, seeds 2108, 2109 and 2110: **900 attempts**. Run everything from the repository
root in one PowerShell session on the Windows reference host. Paths marked *example* can be changed; the study root must
be new, empty and outside the checkout.

```powershell
# --- environment (cheap) -----------------------------------------------------------------------------------------
. .\local_baseline\env.ps1                                       # data root E:\CSC2108Local, OLLAMA_HOST 127.0.0.1:11435
$py = 'E:\CSC2108Local\.venv\Scripts\python.exe'                 # example: the project Python 3.11.9 environment
$env:CSC2108_STUDY_ROOT = 'E:\CSC2108Local\final-study'          # example: NEW and empty
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'; $env:PYTHONIOENCODING = 'utf-8'
$env:CSC2108_LCB_SHARD = 'E:\CSC2108Local\eval-v2\cache\test6.jsonl'   # optional local copy of the pinned shard
$plan = "$env:CSC2108_STUDY_ROOT\plans\final-main.json"
git status --short                                               # execution paths must be committed (ready refuses otherwise)
& $py -m local_agent verify                                      # 38 frozen hashes, packages, model digest

# --- preparation (no paid requests) --------------------------------------------------------------------------------
& $py -m evaluation plan --batch final-main --seeds 2108 2109 2110 --out $plan --cohort "final windows"
& $py -m evaluation budget $plan --init-ledger --max-requests 2000 --max-usd 100   # study ledger with the approved ceilings
& $py -m evaluation tasks $plan                                  # 60 tasks: judge suites + agent bundles, hashes checked
& $py -m evaluation judge                                        # judge image, judge-public, selftest
& $py -m evaluation guidance $plan                               # DRY RUN: 120 missing artifacts = 120 paid requests

# --- PAID: one request per C/D artifact (120 requests, about $1-2 at list prices) ---------------------------------
& $py -m evaluation guidance $plan --yes                         # author, then write final-main.freeze.json

# --- go / no-go ------------------------------------------------------------------------------------------------------
& $py -m evaluation ready $plan                                  # must print "ready": true
& $py -m evaluation budget $plan                                 # remaining paid requests against the ledger

# --- PAID AND LONG-RUNNING: 900 attempts (B and E call the API during the run) ---------------------------------------
& $py -m evaluation run $plan                                    # resumable: rerun the same command after any stop
& $py -m evaluation status $plan                                 # any time: state of every scheduled attempt

# --- after every attempt finished (no paid requests) -----------------------------------------------------------------
& $py -m evaluation score $plan                                  # judge-hidden, then guided_agent measure
& $py -m evaluation metrics "$env:CSC2108_STUDY_ROOT\runs\final-main" --out "$env:CSC2108_STUDY_ROOT\report"
```

Expected resources (from `evaluation budget` on the official plan; estimates, not guarantees): about **794 paid
requests** (120 guidance, ~584 B coder turns, ~90 E diagnoses), **$39 of the ledger's conservative reservation** and
**about $5 token-derived** at list prices. In a high-usage scenario (every B run needing 7 requests, every E run
triggering) the study needs ~1,560 requests, which is why the request ceiling is 2,000 (the $100 ceiling is unchanged);
see [§7](#7-api-budget). Wall time on
the reference host: the local conditions take up to 600 s of coding per attempt (A, C, D, E: 720 local attempts), so
plan for roughly one to three days of machine time; B runs need no GPU.

Outputs: `<study>\runs\final-main\` (one directory per attempt, `plan.json`, `provenance.json`, `eval\`),
`<study>\plans\final-main.freeze.json`, `<study>\api-ledger.json`, `<study>\report\{report.md, report.json, runs.csv,
tasks.csv}`.

**Smoke first.** The same commands with a separate study root and `--manifest judge\manifests\pilot.json
--per-difficulty 1 --seeds 2108 --batch smoke-final` (3 pilot tasks, 15 attempts, ~18 paid requests) and a small ledger
(`budget ... --init-ledger --max-requests 60 --max-usd 6`) check the whole path, including the API.

## 2. Environment and host setup

| Requirement | Reference host (Windows 11) | Notes |
| --- | --- | --- |
| Python | 3.11.9 in `E:\CSC2108Local\.venv` with the pins in `local_agent/requirements.txt` (mini-swe-agent 2.4.6, litellm 1.81.16, pydantic 2.12.5) | `local_agent verify` refuses other versions |
| Docker | Docker Desktop (engine 29.x), images `python:3.11-slim-bookworm@sha256:a83b…`, `csc2108-judge:0.2.1` | `evaluation judge` builds the judge image |
| Local model | Ollama serving `qwen3.5:9b` digest `56671c2a…3c90` (Q4_K_M) on the dedicated `127.0.0.1:11435` | `ready` compares the served digest with the frozen one |
| Ollama app | the user's Ollama on `127.0.0.1:11434` must respond with **no model loaded** | the frozen runtime waits for foreign models (GPU exclusivity) |
| GPU | NVIDIA RTX 4080 SUPER, 16 GB | timings are hardware-specific (see cohorts) |
| Frontier | `OPENAI_API_KEY` and `FRONTIER_MODEL=openai/gpt-6.2-sol` in the `.env` that `guided_agent.providers.env_file()` reads (default: the folder above the checkout; override with `CSC2108_ENV_FILE`) | never commit it; the key is never written to artifacts |

**Supported systems.** Windows (frozen backend) is the reference. macOS/Linux run the portable backend
(`--backend portable`); results from another OS or machine are a separate hardware cohort and are never pooled with
Windows timings (`metrics` refuses mixed hosts in an official report).

**Services.** Start Docker Desktop. Start the project Ollama server with `& .\local_baseline\start_ollama.ps1` (it also
stores `OLLAMA_MODELS` in the user environment), or for one session only:

```powershell
$env:OLLAMA_MODELS = 'E:\OllamaModels'; $env:OLLAMA_HOST = '127.0.0.1:11435'; $env:OLLAMA_NO_CLOUD = '1'; $env:OLLAMA_NOPRUNE = '1'
Start-Process (Get-Command ollama).Source -ArgumentList serve -WindowStyle Hidden `
  -RedirectStandardOutput E:\CSC2108Local\logs\ollama-project.stdout.log -RedirectStandardError E:\CSC2108Local\logs\ollama-project.stderr.log
```

`--study` and `--backend` go before the command (`python -m evaluation --study D:\s run $plan`); `--backend` is passed
to `guided_agent`.

## 3. Steps in detail

| Step | Paid? | What it does |
| --- | --- | --- |
| `select` | no | deterministic, outcome-blind selection into a judge manifest ([§4](#4-benchmark-selection)) |
| `plan` | no | tasks of a manifest (default `judge/manifests/final.json`), conditions, seeds → one plan JSON (schema v2: records the manifest sha256 and the selected task hashes; condition order counterbalanced) |
| `tasks` | no | judge suites (public and hidden) and the agent's bundles, built by `judge/build_data.py` and hash-checked against the manifest; records each hidden suite's judge digest |
| `judge` | no | builds `csc2108-judge:0.2.1` if missing, starts judge-public for the study, runs the selftest (isolation, no network, tests unreadable) |
| `guidance` | **yes** with `--yes` | authors missing C/D artifacts with `guided_agent author`, then writes the freeze (v2: bound to the plan hash and the expected artifact set) |
| `budget` | no | paid-request and reservation estimate against the ledger; `--init-ledger` creates the study ledger |
| `ready` | no | every readiness check without running anything (plan, manifest, tasks, bundles, freeze, git state, frozen hashes, Ollama digest, judge image, frontier config, budget, resume binding) |
| `run` | **yes** (B, E) | `ready`, then writes/compares `provenance.json`, then `guided_agent batch` |
| `status` | no | state of every scheduled attempt ([§6](#6-scoring-completeness-and-integrity)) |
| `score` | no | judge-hidden on every finished run → `eval/<run_id>.json` (refused while attempts are unfinished), then `guided_agent measure` |
| `metrics` | no | `report.md`, `report.json`, `runs.csv`, `tasks.csv` (refused for incomplete data unless `--preliminary`) |
| `exclude`, `freeze`, `check`, `exposure`, `crosscheck` | no | documented exclusions; the freeze on its own; the exposure registry; judge cross-validation |

Plan options: `--seeds S...` or `--repetitions N [--first-seed 2108]`; `--conditions A B C D E` (any subset);
`--tasks ID...` or `--per-difficulty N` (subset of the manifest); `--manifest M`; `--order balanced|fixed`
(default balanced: block *i* uses row *i* mod 10 of a Williams design, so every condition appears equally often in
every position and after every other condition; `fixed` is the alphabetical order of earlier plans); `--b-max-requests`
(28); `--outer-timeout` (1000 s); `--cohort LABEL`.

**Why task preparation and hidden scoring live here.** The agent should not build, hold or score the tests it is
evaluated on: the only things it touches are `<study>/bundles/<id>` and judge-public. Hidden tests are built by the
evaluation and loaded into judge-hidden only by `evaluation score`. `guided_agent prepare-tasks` and `evaluate` still
exist but the final pipeline does not use them. The task and bundle bytes match `guided_agent.tasks.prepare`, the judge
container names match `guided_agent.backend.judge_client`, and `evaluation score` writes the same `eval/<run_id>.json`
as `guided_agent evaluate` plus `submission_sha256` (tests check all three).

## 4. Benchmark selection

The pinned dataset is `livecodebench/code_generation_lite`, shard `test6.jsonl`, revision
`0fe84c3912ea0c4d4a78037083943e8f0c4dd505` (sha256 `bb4c364f…d1f5`, checked by `build_data.py`). Its stdin-judgeable pool
is the 112 AtCoder tasks (26 easy, 26 medium, 60 hard; the 63 LeetCode tasks are functional and cannot be judged by
judge 0.2.1). Eligibility (`evaluation/selection.py`):

* output semantics `exact` in `evaluation/data/output-semantics-audit.json` (all 112 reviewed from public statements:
  102 exact; excluded: tolerance `abc392_d`; case-insensitive `abc395_a`, `arc192_a`, `arc192_b`; multiple valid
  outputs `abc396_e`, `abc397_d`, `abc398_f`, `arc190_a`, `arc191_c`, `arc195_c`). The comparison rule is never relaxed;
* at least `--min-hidden-tests` hidden tests (default 40);
* not reserved (`--reserve`, default `judge/manifests/pilot.json`, kept for smoke tests; `--no-reserve` to allow);
* optionally `--exclude-previously-used`: no recorded historical exposure (**off by default**).

Order: explicit `--tasks`; then `--base` members that are eligible (ineligible ones are reported as removed, with
reasons, and replaced from the same difficulty and contest series); then the remaining quota by
`sha256(seed:final-v1:difficulty:task_id)`. `--prefer-unexposed` puts tasks without recorded exposure first within each
stratum (exposed tasks stay eligible). Counts: `--counts easy=20 medium=20 hard=20` (unequal counts allowed),
`--per-difficulty N` or `--total N`. A quota the pool cannot fill is an error listing the eligible counts; nothing is
silently reduced. `--dry-run` prints the selection without writing.

The official manifest was produced (and is reproduced byte for byte) by:

```powershell
& $py -m evaluation select --out judge\manifests\final.json --name final --base judge\manifests\main.json `
  --counts easy=20 medium=20 hard=20 --seed 2108 --min-hidden-tests 40 --prefer-unexposed
```

| Removed from main.json | Reason | Replacement (same difficulty and series) |
| --- | --- | --- |
| abc395_a (easy) | case-insensitive judge: exact comparison rejects `yes` for `Yes` | abc391_a |
| abc399_d (medium) | 1 hidden test | abc396_d (the only eligible medium left) |
| abc400_e (hard) | 4 hidden tests | abc390_g |
| abc400_g (hard) | 4 hidden tests | abc398_g |
| arc195_c (hard) | constructive, several valid outputs; 4 hidden tests | arc194_d |
| arc196_b (hard) | 1 hidden test | arc192_e |

Eligible pool at 40 hidden tests (pilot reserved): 22 easy, 20 medium, 45 hard. With `--exclude-previously-used` it is
10 easy, 5 medium and 19 hard, so a 60-task benchmark of unexposed tasks is not possible on this shard.

**Historical exposure.** `evaluation/data/exposure-registry.json` (rebuild: `evaluation exposure --build --study-roots
...`) reads task lists structurally from the development commit `900d33f` (local baseline pilot, local evaluation v2,
the Qwen optimization development / selection / held-out splits, the agent-delivery pilot, the one-shot ablation, the
reasoning-effectiveness passes 1–4) plus run-directory names on the reference host. Classes: `development`,
`selection_holdout`, `other_scored`, `uncertain`, `none_known`. `none_known` means *potentially unseen*, not verified
unseen. Of the 60 main tasks, 27 were exposed. The final 60: 10 development, 10 selection/held-out, 8 other scored, 32
none known. `evaluation exposure TASK...` shows the evidence for any task.

## 5. Interruption, resume, infrastructure failures, exclusions

* **Resume.** Rerun `evaluation run $plan`. Finished attempts are kept; a half-written run directory is renamed
  `*.incomplete-xxxxxx` and retried. `run` compares the current configuration with `runs/<batch>/provenance.json` and
  refuses to continue when a binding field changed (plan, benchmark, built tasks, freeze, code fingerprint, judge,
  model digest, frontier model, profile and budgets, prompts, seeds, hardware cohort, software versions). A docs-only
  commit does not bind. Each session is appended to `provenance-sessions.jsonl`. Never edit the plan of a started
  batch; start a new `--batch` instead.
* **GPU in use.** If another model is loaded on the Ollama app endpoint for more than 30 minutes, the batch stops with
  `resource-status.jsonl`; unload it and rerun.
* **Infrastructure failures** (a hidden `infrastructure_error`, a runner infrastructure error that is not the model's own
  such as Docker, the judge, a crashed model server or the outer timeout, or a frontier provider fault: B coder or E
  diagnosis transport/HTTP error, provider error, ledger ceiling reached) exclude their whole (task, seed) block from
  every condition; the report lists each block with the reason. The decision is made before the outcome is looked at,
  so a fault excludes a run whether it passed or not. Model failures (local request timeout, context overflow, output
  truncation, no submission, exhausted action/repair/time budget, an incomplete frontier answer) are failures, never
  excluded. To rerun a block: move its run directories out of `runs\<batch>` (for example to
  `<study>\set-aside\<batch>\`), rerun `evaluation run $plan`, then `evaluation score $plan`. A budget-exhausted run
  needs a fresh, larger ledger first ([§7](#7-api-budget)), which is a deliberate decision.
* **Documented exclusions.** `evaluation exclude $plan --task T --seed S --reason "..." --by NAME` writes
  `runs\<batch>\exclusions.json`; the block is excluded everywhere and listed with its reason. Use it only for
  attempts that cannot be completed, never after looking at outcomes.

## 6. Scoring completeness and integrity

`evaluation status $plan` gives every scheduled attempt one state: `not_executed`, `incomplete` (interrupted),
`awaiting_scoring`, `scored`, `excluded` (documented) or `invalid` (malformed record, or a verdict that does not match its
run). A hidden verdict is valid only when its run_id, task and condition equal the run record's; the judged code hash
equals the record's `submission_sha256` and the bytes of `submission.py` on disk; its tests digest equals the judge
digest of the study's hidden suite (itself checked against the plan's manifest); the judge version is 0.2.1; and
`measurement.json` carries the same hidden status.

* `score` refuses a batch with unfinished attempts (`--allow-incomplete` scores what exists, for a preliminary look) and
  stops when a stored verdict no longer matches its run (`--rescore-stale` moves it to `eval\stale\` and rescores).
  Verdicts are written atomically, so an interrupted `score` resumes.
* `metrics` refuses an official report unless every attempt is `scored` or `excluded`, the batches' provenance agrees,
  and the included runs come from one host, local model digest, agent configuration and frontier model. `--preliminary`
  writes a report titled **PRELIMINARY** that lists the problems; unfinished, unscored and invalid attempts exclude their
  block (they are never counted as failures).
* Two valid runs of the same (task, condition, seed) across batches are an error; a later batch replaces only an
  infrastructure failure or a missing run of an earlier one (`metrics BATCH1 BATCH2`).

## 7. API budget

* **Ledger.** Every paid request is reserved in the study ledger (`<study>\api-ledger.json`, or `CSC2108_API_LEDGER`)
  before it is sent; no retries; no fallback model. A request that would pass a ceiling is refused before sending (B and
  E runs then end as budget-exhausted infrastructure failures).
* **Ceilings.** The code maximum is `MAX_REQUESTS, MAX_USD = 2000, 100.00` in `guided_agent/providers.py` (a ledger can
  lower it, never raise it). `evaluation budget $plan --init-ledger --max-requests N --max-usd X` creates a fresh ledger
  with the study's approved ceilings (refused if a ledger exists or a value exceeds the code maximum). Raising the code
  maximum is a reviewed code change, and a new ledger.
* **What the dollar ceiling measures.** `max_usd` is checked against the ledger's *conservative reservation*: every
  completed request is charged at `PRICE_CONSERVATIVE` ($12 / $60 per 1M input / output tokens, 6× the Standard list
  price, cached input not discounted) and every pending one at its full pre-request bound (~$0.5 for an 8,000-token
  output cap). It is a safety bound, not the expected bill.
* **Preflight.** `evaluation budget $plan` reports four scenarios against the ledger's remaining room: `expected`
  (historical means: B ≈ 3.2 requests per run, E triggers in half of its runs), `high` (B 7 per run, every E run
  triggers, mean request sizes), `stress` (high counts at the largest observed request sizes) and `worst` (B at
  `max_requests`, every request at the output cap). For the official plan at 2000 / $100:

  | Scenario | Requests | Reservation | Token-derived cost | Fits |
  | --- | --- | --- | --- | --- |
  | expected | 794 | $38.84 | $5.10 | yes |
  | high | 1,560 | $75.42 | $9.60 | yes (did not fit at the earlier 1,500-request maximum) |
  | stress | 1,560 | $350.92 | $58.49 | no (reservation) |
  | worst | 5,340 | $4,389 | $732 | no |

  The request maximum was raised from 1,500 to 2,000 before the official freeze because the high-count scenario
  needed ~1,560; the $100 ceiling was not changed. 2,000 / $100 is expected to suffice but is **not guaranteed**
  (stress and worst exceed the reservation ceiling). Rerunning budget-exhausted blocks with a new ledger is a
  deliberate decision. The provider-side spending limit is set in the OpenAI account, not here.

## 8. Measurement definitions

Correctness (the task is the statistical unit throughout):

| Metric | Definition |
| --- | --- |
| Final pass rate = pass@1 (primary) | hidden status `pass` / included runs (a missing submission or a context overflow is a failure) |
| pass@k (secondary for k ≥ 2) | per task and condition with *n* valid attempts and *c* hidden passes, 1 − C(n − c, k) / C(n, k), averaged over tasks with n ≥ k (fewer: reported as unavailable). Overall, by difficulty, by exposure subgroup; matched difference vs A and gap closed toward B per k on the seeds every compared condition has; task-bootstrap 95% CIs; eligible-task counts; share of tasks with all attempts successful |
| Paired vs A (primary C, D, E) | mean over tasks of the per-task pass-rate difference; 95% bootstrap CI (10,000 task resamples, seed 2108); paired sign-flip permutation p (exact up to 16 non-zero tasks); Holm over C, D, E. B and the by-difficulty tables are exploratory; McNemar on (task, seed) pairs is exploratory (pairs of one task are not independent) |
| Gap closed toward B | (X − A) / (B − A) with task-level means on (task, seed) pairs that have A, B and X; undefined when B does not exceed A; 95% CI resamples tasks |
| Seed consistency | tasks whose seeds all pass, are mixed or all fail; mean p(1 − p) |
| Public–hidden gap; failure recovery; E triggered subset | as before; the E triggered subset is descriptive (it conditions on the trigger) |
| Sensitivity | without blocks with a local timeout; without tasks below `--low-coverage-threshold` hidden tests (not applicable when all tasks have 40) |
| Exposure subgroups | pass rate, pass@k and paired difference vs A for `exposed` / `potentially_unseen` / `uncertain` tasks (descriptive) |

**pass@k interpretation.** pass@1 is the primary outcome. C and D reuse one upfront guidance artifact per task across
seeds, so their pass@k describes repeated local execution conditional on shared guidance, not independently regenerated
frontier guidance. pass@k counts a task as solved when any of k attempts passes the *hidden* tests; it does not mean an
agent could identify the correct submission without them.

Runtime (seconds; medians and IQRs):

| Metric | Definition |
| --- | --- |
| Warm-start latency | the attempt's wall time (`time.wall_seconds`, setup included) with reusable guidance already generated; B's API calls and E's diagnosis wait are inside it, counted once |
| Cold-start E2E latency (main table) | A, B, E: the warm-start latency. C, D: plus the authoring latency of the guidance artifact the attempt used |
| Amortized latency | C, D: warm-start + authoring latency / number of included attempts sharing the artifact |
| Relative runtime | on matched (task, seed) pairs, median and IQR of X − ref and X / ref (ref = A, B) for the *same* quantity on both sides; reduction = 1 − median ratio |
| Kept | local coding, local inference, prompt/generation time, frontier wait, public-test and sandbox time, time to first executable candidate, authoring latency |

Frontier API (token-derived cost = provider usage × list price from `evaluation/pricing.py`: gpt-6.2-sol Standard
$2.00 input, $0.10 cached input, $10.00 output per 1M tokens, read from the OpenAI pricing page on 2026-11-24; **not**
invoiced expenditure):

| Metric | Definition |
| --- | --- |
| Total / upfront / run-time cost | run-time requests (B coder turns, E diagnosis) of included runs + upfront guidance (C, D) once per artifact (deduplicated by artifact sha256, never per seed) |
| Per included attempt, per pass | total / included runs; total / passes (undefined, not 0, with no pass) |
| Cold-start / amortized cost per attempt | C, D: run-time + artifact cost / run-time + artifact cost / sharing attempts |
| Cost reduction vs B; extra passes per $ vs A | 1 − cost_X / cost_B; (passes_X − passes_A) / (cost_X − cost_A), undefined without extra spend, negative values flagged |
| Requests | unique requests: upfront (artifacts) + run-time; failed; per attempt; per pass; requests without usage (missing usage makes a total unavailable, never zero) |
| Tokens | input, cached input, output (reasoning included: the provider counts reasoning inside output tokens; reasoning is shown as a breakdown, not added), total = input + output, per pass, reduction vs B |
| Study expenditure | every ledger request of the batch's purposes (failed calls, excluded runs and reruns included), split into requests attributable to included runs and the rest; token-derived cost and reservation |

Local compute: model calls, prompt and completion tokens, inference seconds and per-host decode speed. A has zero
frontier API spend, not zero computational cost. Energy is only reported as *modelled* when `guided_agent measure` is
given `--watts` and `--usd-per-kwh`.

**Failure categories** (`infrastructure` first, then the outcome): `hidden_pass`; `context_overflow`;
`local_timeout_no_program` / `local_timeout_with_program`; `truncated_no_program`; `budget_limit`; `format_errors`;
`public_pass_hidden_fail`; `never_passed_public`; `no_submission`. The report also gives a transition table against A,
process metrics and per-host decode speed.

Outputs: `report.md` (human-readable; starts with the main results table: hidden pass rate, cold-start E2E latency,
frontier cost, cost per pass, frontier tokens, gap closed), `report.json` (everything, for plots), `runs.csv` (one row per
scheduled attempt, with state, category, exposure, hidden-test count, latencies, costs and tokens) and `tasks.csv` (one
row per included (task, condition): attempts, passes, pass@k).

## 9. Results preservation and provenance

Keep the whole study root (it is outside the checkout and never committed): `plans\` (plan and freeze), `runs\<batch>\`
(attempts, `plan.json`, `provenance.json`, `provenance-sessions.jsonl`, `eval\`, `exclusions.json`), `guidance\`,
`bundles\`, `judge\`, `tasks-manifest.json`, `api-ledger.json` and `report\`. `provenance.json` records the git commit and
state, code fingerprint, benchmark manifest and task hashes, dataset revision and shard hash, plan hash, freeze hash,
judge version and image ID, local model digest (expected and observed), requested frontier model, agent profile and
budgets, prompt and template hashes, seeds and sampling, hardware cohort, pricing assumptions and package versions;
every run records the observed frontier model. Archive the study root (and the git commit it names) before analysis.
Never commit `.env`, keys or runtime artifacts.

## 10. Judge cross-validation

`evaluation crosscheck BATCH_DIR... --out DIR [--limit 40]` re-judges saved hidden-scored submissions (alternating
passes and failures) with the official LiveCodeBench evaluator at the pinned revision `28fef95e`, through the frozen
wrapper `local_baseline/judge_lcb.py` in the isolated `csc2108-lcb-judge:v2` container (no network, read-only, 1 GB,
unprivileged, capabilities dropped), on the hidden tests only, and writes `DIR\crosscheck.json`. No model is run.
Agreement does not remove the shared limitation of exact comparison on tasks with several acceptable outputs.

## 11. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ready`: tasks not built / bundle file changed | `evaluation tasks $plan` (a changed bundle means the study root is not trustworthy: use a new one) |
| `ready`: no guidance freeze / artifacts missing | `evaluation guidance $plan --yes`; failed authoring requests are in the ledger and are retried only by rerunning that command |
| `ready`: freeze written for a different plan / not bound to a plan | the plan changed after freezing: rebuild the plan as it was, or start a new batch and freeze again |
| `ready`: uncommitted changes in execution paths | commit (or revert) them; an official batch must be reproducible from a commit |
| `ready`: Ollama digest differs | the served `qwen3.5:9b` is not the frozen GGUF; on macOS see [§12](#12-macos-notes) |
| `ready`: expected requests do not fit | create a new ledger with larger ceilings (within the code maximum) |
| `run`: provenance recorded with another configuration | something binding changed; start a new `--batch` |
| `score`: attempts have not finished | finish the batch (`evaluation run $plan`), or `--allow-incomplete` for a preliminary look |
| `score`: stored verdicts no longer match | a submission or the hidden suite changed after scoring: investigate, then `--rescore-stale` |
| `metrics`: problems block an official report | read the listed states with `evaluation status $plan`; finish, score, document exclusions, or use `--preliminary` |
| judge tests fail with `No module named 'fcntl'` on Windows | `judge/container/judge.py` runs inside its Linux container; run its unit tests in `python:3.11-slim-bookworm` |

## 12. macOS notes

Mac results are a separate hardware cohort. On Apple Silicon, `ollama pull qwen3.5:9b` now returns an MLX nvfp4
build with a different digest. Pull the frozen GGUF instead and give it the name the runtime uses:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen3.5:9b-q4_K_M        # digest 56671c2a…, Q4_K_M
OLLAMA_HOST=127.0.0.1:11435 ollama cp qwen3.5:9b-q4_K_M qwen3.5:9b
```

The POSIX commands are the same with `python -m evaluation ...` and `export` instead of `$env:`.

## 13. Tests

```bash
python -m unittest evaluation.test_evaluation evaluation.test_final       # offline: no model, Docker or network
```
