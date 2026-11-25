# CSC2108 official benchmark results: batch `final-main`

This directory is the exported result set of the official final evaluation, taken from the study root
`E:\CSC2108Local\final-study` on the Windows reference host. Nothing here was rerun, recomputed or edited by hand. Every
file was copied from the study root by `export_results.py`, and `MANIFEST.json` records each file's source path and
sha256.

| | |
| --- | --- |
| Question | When and how should a stronger frontier model provide reasoning to a small local coding agent? |
| Benchmark | `judge/manifests/final.json`: 60 AtCoder tasks from LiveCodeBench `code_generation_lite` `test6.jsonl` at revision `0fe84c39…`. 20 easy, 20 medium and 20 hard; 40 hidden tests per task |
| Design | 5 conditions × 60 tasks × 3 seeds (2108, 2109, 2110) = **900 attempts**. Seed-major order, with a Williams-balanced condition order inside each (task, seed) block |
| Local agent | mini-SWE-agent 2.4.6 (`frozen-v6`) running Qwen3.5 9B Q4_K_M (digest `56671c2a…3c90`) on Ollama. 16k context, 4,096 output tokens, 20 actions, 3 repair groups, 600 s coding budget |
| Frontier | `gpt-6.2-sol` through the OpenAI API, medium reasoning effort, at most 8,000 completion tokens per request |
| Judge | `csc2108-judge:0.2.1`, exact comparison. Cross-checked against the official LiveCodeBench evaluator with 40/40 agreement (`evaluation/VALIDATION.md`) |
| Code | Ran at commit `bf160d8`. Plan sha256 `7342a46f…d052`, guidance freeze sha256 `224c492c…3515`, provenance binding sha256 `8822ddd7…805c` (identical in both sessions) |
| Run | 2026-11-25 05:55–20:53 UTC; hidden scoring 20:55–21:30 UTC; Windows 11, RTX 4080 SUPER (cohort `final windows`) |
| Completeness | 900/900 attempts scored; 0 excluded blocks; 0 invalid records; the official (non-preliminary) report was accepted |

Conditions: **A** local only. **B** frontier only (the frontier model is the coder, through the same agent interface).
**C** one upfront natural-language plan (`plan-v1`). **D** one upfront passive behavioural contract (`contract-v1`).
**E** at most one frontier diagnosis (`diagnosis-v1`), given at the first public-test failure in the same session.
Each C/D guidance artifact was generated once per task and reused for all three seeds.

## Key findings

The primary outcome is pass@1 on hidden tests. Confidence intervals are 95% intervals from resampling tasks (10,000
resamples). p-values come from a paired sign-flip permutation test on per-task differences vs A, with a Holm
adjustment over C, D and E. B is exploratory.

| Condition | pass@1 | Δ vs A [95% CI] | Holm p | pass@2 | pass@3 | Gap closed toward B |
| --- | --- | --- | --- | --- | --- | --- |
| A Local | **0.533** | – | – | 0.561 | 0.567 | – |
| B Frontier | **0.967** | +0.433 [0.317, 0.556] | (exploratory) | 0.967 | 0.967 | – |
| C Planning | **0.717** | +0.183 [0.100, 0.272] | **0.0006** | 0.761 | 0.783 | 0.42 [0.26, 0.59] |
| D Contract | **0.544** | +0.011 [−0.017, 0.044] | 1.0 | 0.572 | 0.583 | 0.03 [−0.05, 0.10] |
| E Diagnosis | **0.550** | +0.017 [0.000, 0.044] | 1.0 | 0.578 | 0.583 | 0.04 [0.00, 0.11] |

pass@1 by difficulty (each cell is 20 tasks × 3 seeds):

| Difficulty | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- |
| easy | 0.983 | 1.000 | 1.000 | 1.000 | 1.000 |
| medium | 0.533 | 0.950 | 0.833 | 0.550 | 0.567 |
| hard | 0.083 | 0.950 | 0.317 | 0.083 | 0.083 |

Efficiency figures use median cold-start end-to-end latency per attempt, where C and D include the time to author
their guidance. Costs are **token-derived** (provider usage × list price: $2 input, $0.10 cached input and $10 output
per 1M tokens). They are not invoices.

| Condition | Latency s, median (IQR) | Frontier $ total | $ per pass | Frontier requests | Frontier tokens |
| --- | --- | --- | --- | --- | --- |
| A | 42.0 (13.3–128.2) | 0 | 0 | 0 | 0 |
| B | 12.0 (10.3–18.0) | 1.85 | 0.0106 | 571 | 650,978 |
| C | 25.9 (19.0–72.8) | 0.57 (60 plans, once each) | 0.0044 | 60 | 84,463 |
| D | 36.5 (19.9–136.7) | 0.35 (60 contracts, once each) | 0.0036 | 60 | 65,993 |
| E | 39.3 (13.3–128.2) | 0.26 (33 diagnoses) | 0.0026 | 33 | 81,944 |

A spends nothing on the frontier API, but it is not free: it uses local GPU compute, at a median decode speed of
105.8 tok/s on this host. The whole study used 725 paid requests: 724 completed and 1 failed with HTTP 503. That is
$3.03 token-derived, against a conservative reservation of $20.46 out of the $100 ceiling.

What the agent did:
* **C** raises hidden correctness on medium and hard tasks. Hard tasks go from 8.3% to 31.7%; that difficulty-level
  comparison is exploratory, with Δ +0.233 [0.067, 0.417]. C produced a program in 175/180 runs, against 132/180 for
  A, and was truncated far less often (35 runs vs 84).
* **D** and **E** are statistically indistinguishable from A. E's diagnosis triggered in only 18.3% of its runs
  (33/180), because most hard-task failures of the local model happen before any public test runs. The output hits
  the 4,096-token limit: 48 of A's and 48 of E's runs are `truncated_no_program`. In the triggered subset, E passed
  42.4% against 33.3% for A; this is descriptive only, because it conditions on the trigger.
* **B** solved 174/180. Its failures were all `public_pass_hidden_fail`.
* Seed consistency: every seed passed for 29 tasks under A, 58 under B and 39 under C.
* Historical exposure: 28 tasks were used in earlier development work and 32 have no known use. A passed 61.9% of
  exposed tasks and 45.8% of potentially unseen ones; C's gain over A appears in both subgroups. These subgroups are
  descriptive. See `report/report.md`.

Do not read more into these numbers than they support. Only one model pair and one AtCoder subset were tested.
Historical exposure is mixed and training-data contamination is possible, so this is not a fully held-out benchmark.
Hidden tests are not formal verification. C and D share one guidance artifact across seeds, so the repeated seeds are
not independent draws of guidance. The conditions have different budgets. Timings are specific to this host. Contracts
are passive, and diagnosis depends on reaching a public-test failure. Pass rates alone do not establish mechanisms.

## Incident affecting one attempt

At 14:23 UTC the diagnosis request for `lcb-atcoder-abc395_e-E-s2109` received API HTTP 503
(`server_is_overloaded`). The frozen policy (`evaluation/README.md` §5) classifies that as a frontier provider fault
and would exclude the whole (abc395_e, 2109) block. Before any hidden scoring, without regard to outcome, the run was
moved to the study's `set-aside/` folder and kept there. It was rerun at 20:53 UTC by resuming the same plan, and the
rerun's diagnosis was delivered. The original record is in `set-aside/` here. The failed request stays in the ledger,
where it is counted under `not_attributable` in the report's study-expenditure table.

## Files

| Path | What it is |
| --- | --- |
| `report/report.md` | Human-readable report: main table, pass@k overall and by difficulty, paired tests vs A with Holm, gap closed, runtime (cold/warm/amortized, matched ratios vs A and B), cost/requests/tokens, ledger reconciliation, exposure subgroups, E triggered subset, sensitivity, process metrics, host speed, failure categories, transitions vs A, seed consistency |
| `report/report.json` | Everything in the report, machine-readable (use this for plots and re-analysis) |
| `report/runs.csv` | One row per scheduled attempt (900): state, hidden status, failure category, exposure, latencies, costs, tokens |
| `report/tasks.csv` | One row per (task, condition): attempts, passes, pass@k |
| `batch/measurements.jsonl` | One `csc2108-run-measurement-v1` record per attempt: correctness, local inference, agent process, frontier usage, time and cost (fields documented in `MEASUREMENT_SCHEMA.md`) |
| `batch/runs/<run>/result.json` | The agent's run record: exit status, budgets, guidance delivery, diagnosis trigger, inference telemetry, usage, model digest |
| `batch/runs/<run>/measurement.json` | The same measurement record as above, for one attempt |
| `batch/runs/<run>/submission.py` | The submitted program (755 of 900 runs produced one) |
| `batch/runs/<run>/attempts.jsonl` | Each public-test call made during the run (public suite only) |
| `batch/eval/<run_id>.json` | Hidden verdicts: status, passed/total, verdict counts, and hashes binding each verdict to the run, submission and hidden suite. No test contents |
| `batch/plan.json`, `batch/provenance.json`, `batch/provenance-sessions.jsonl` | The executed plan, and the frozen provenance: git commit and code fingerprint, manifest and dataset hashes, freeze, judge image, model digests, profile, budgets, prompt hashes, seeds, hardware cohort, package versions, pricing |
| `guidance/final-plans/*.json`, `guidance/final-contracts/*.json` | The 120 frozen C/D guidance artifacts (text, prompts and their hashes, usage, latency, cost). Each comes with its raw API response (`*.response.json`) |
| `study/plans/final-main.json`, `study/plans/final-main.freeze.json` | The plan as created, and the guidance freeze bound to it |
| `study/api-ledger.json` | The write-ahead API ledger: one entry per paid request (kind, condition, model, usage, latency, cost, state). No request bodies, no credentials |
| `study/tasks-manifest.json` | Built-task record: public and hidden suite sha256s and judge digests per task (hashes only) |
| `study/budget-preflight-initial.json`, `study/guidance-dryrun.json`, `study/ready-pre-guidance.json`, `study/ready-final.json` | Pre-launch budget assessment, guidance dry run and readiness gates |
| `study/ops/OVERNIGHT_HANDOFF.md`, `study/ops/PROGRESS.log`, `study/ops/logs/*` | Run supervision: handoff, progress log, watchdog log, launch records, and the stdout of the run, score, metrics and guidance steps |
| `set-aside/` | The set-aside record of the provider-fault attempt, and its reason (`SET_ASIDE_LOG.jsonl`) |
| `MANIFEST.json` | Every exported file: source path, source sha256, exported sha256, size, sanitized flag |
| `export_results.py` | The script that produced this directory |

## What is excluded, and why

* **Hidden-test contents.** The study's `judge/` (public and hidden suites) is not exported. Hidden verdicts carry
  only counts and hashes, and the exporter refuses any verdict with test-level fields. The hidden tests are the
  pinned dataset's private cases; their sha256s are in `study/tasks-manifest.json`.
* **Credentials.** The `.env` file is not part of the study root. Every exported file was scanned for API keys,
  tokens and home paths, and none were found.
* **Host identity.** The machine's network name appeared in host fields and was replaced by `<HOST>` in 1,808 files,
  using the repository's `guided_agent.privacy` placeholders. These files are marked `"sanitized": true` in
  `MANIFEST.json`, and their original sha256 is kept as `source_sha256`. No other value was changed. All other files
  are byte-identical to the originals.
* **Large runtime artifacts** (~190 MB): per-attempt agent directories (trajectories; Ollama request, response and
  server logs; agent configuration), agent task bundles and per-attempt stdout logs. They stay in the archived study
  root. `evaluation metrics` reads some of them, such as agent-level errors and decode speeds, so regenerating
  `report/` from scratch needs the full study root. Every reported number is already in `report.json`, `runs.csv` and
  `measurements.jsonl`.

## Verifying and using the data

```python
import csv, hashlib, json, pathlib
root = pathlib.Path('results/final-main')
manifest = json.loads((root / 'MANIFEST.json').read_text())
bad = [e['path'] for e in manifest['entries'] if hashlib.sha256((root / e['path']).read_bytes()).hexdigest() != e['sha256']]
print(len(manifest['entries']), 'files,', len(bad), 'mismatches')

runs = list(csv.DictReader(open(root / 'report/runs.csv', encoding='utf-8')))          # 900 rows
report = json.loads((root / 'report/report.json').read_text(encoding='utf-8'))         # all tables
```

A hidden verdict is valid only when `submission_sha256` in `batch/eval/<run_id>.json` equals the sha256 of
`batch/runs/<run>/submission.py` and that run's `result.json`. The pipeline checked this for all 900 attempts
before it wrote the report. `.gitattributes` marks this directory `-text`, so checkouts on every OS keep the exact
bytes behind these hashes.

The pipeline, its definitions and the runbook are in `evaluation/README.md`. Pre-launch validation (tests, smoke
run, judge cross-check, manifest reproduction, budget change) is in `evaluation/VALIDATION.md`.
