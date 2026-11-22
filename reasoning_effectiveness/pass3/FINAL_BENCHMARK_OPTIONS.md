# Final benchmark options: 60, 90 or 120 problems

This document only plans the final study; nothing here was run, and the main 60-task cohort was not
touched. The decision belongs to the team. All counts come from public metadata and statements
(`diagnostics/shard_pool.py`, `evidence/output-semantics-review.json`).

**Summary.** Estimates are derived in §3, with B and API costs in `FRONTIER_ONLY_COST.md`.

| Option | Tasks | Local attempts (A/C/D/E × 3 seeds) | B attempts (× 3) | Local GPU time | Paid API, standard (expected) | Ledger ceiling to plan for (conservative 6×) |
| --- | --- | --- | --- | --- | --- | --- |
| 60 | 59–60 | 720 | 180 | 12–25 h | $10–30 | about $180 |
| **90 (recommended)** | 89–90 | 1,080 | 270 | 18–38 h | $16–44 | about $265 |
| 120 | 119–120 | 1,440 | 360 | 24–50 h | $21–60 | about $360 |

## 1. Task sources

**Dataset.** There is **no newer official LiveCodeBench shard**. The Hugging Face dataset
`livecodebench/code_generation_lite` was last modified on 2025-06-05. At the pinned revision `0fe84c39…` it
contains `test.jsonl` and `test2.jsonl`–`test6.jsonl`, and `test6` is the newest; the project already pins
this revision. Older shards at the **same pinned revision** are the only additional official source. Each is
fixed by its LFS sha256; `test5.jsonl` was downloaded and verified (`7f77571c…`).

| Shard (release) | AtCoder contest dates | AtCoder easy / medium / hard | Cues needing review | Already used by the project |
| --- | --- | --- | --- | --- |
| `test6` (v6) | 2025-01-04 – 2025-04-06 | 26 / 26 / 60 | 10 | 100 (main 60, pilot 8, union, passes 1–3) |
| `test5` (v5) | 2024-09-22 – 2024-12-28 | 24 / 24 / 57 | 6 | **0** |
| `test` (v1) | 2023-05-13 – 2024-03-02 | 76 / 76 / 58 | 23 | 3 |
| `test2`–`test4` (v2–v4) | 2024 (not downloaded: 2.5 GB) | not counted | — | 0 |

**What remains of `test6` outside the main 60 after pass 3:** 9 fresh tasks, all labelled hard (ABC G and
ARC C or later), and nothing easy or medium.

**Contamination.** Every LiveCodeBench shard predates Qwen3.5's release, so LiveCodeBench's release-date
guarantee does not hold for this model on any shard. Older shards are more exposed (more editorials and
solutions online). The shards must therefore be **stratified in the analysis, never pooled silently**.

## 2. The main 60: what reuse means

| Category | Tasks | Meaning for interpretation |
| --- | --- | --- |
| **Prior model execution** (earlier evaluator's 75-ID scored union) | **27 of the 60** (earlier documents said 28) | The same local model was run on these, with a different harness and before any guidance design. Fresh sessions mean no memory carries over, but the team has seen those outcomes. |
| **Development-tuned** (used to design or tune prompts, ACI or E in passes 1–3) | **0 of the 60** | Passes 1–3 excluded the main manifest, and no prompt was tuned on it |
| **Fully independent holdout** | 33 of the 60 never scored by anyone; all of `test5` | Cleanest estimate |

**Reading the 27.**

* **Selection-bias risk:** knowing which tasks the local model failed could tempt task-specific choices. No
  such choice has been made, and none should be.
* **Fresh sessions do not remove that bias.** They only remove information leakage *into the model*.
* **Reporting:** report the 27 and the 33 as separate strata, plus the pooled number.

**Judge problems in the main 60** (`READINESS_AUDIT.md` §3), both to be decided **before** freezing:

* **`arc195_c`** (constructive "show one example") is not exact-judgeable. Exclude it, or score it with a
  validator in a new judge version.
* **`abc395_a`** is case-insensitive. Keep it with exact scoring and report the risk, or add case folding in
  that version.

## 3. Options

| | 60 | 90 | 120 |
| --- | --- | --- | --- |
| Tasks | main 60, with arc195_c dropped (59) or validated | main 60 + 30 from `test5` (10/10/10, outcome-blind, stratified) | main 60 + 60 from `test5` (20/20/20) |
| Difficulty mix | 20/20/20 | 30/30/30 | 40/40/40 |
| Freshness | 27 prior-execution + 33 never scored | + 30 never-used tasks (older shard) | + 60 never-used tasks |
| Dataset strata | 1 | 2 (`test6`, `test5`) | 2 |
| Judge work | Decide arc195_c / abc395_a | + review about 6 cue-flagged `test5` tasks before selection | same |
| Local attempts (A, C, D, E × 3 seeds) | 720 | 1,080 | 1,440 |
| B attempts (× 3 seeds) | 180 | 270 | 360 |

**Time.** This is wall time of the frozen agent per attempt, measured with container setup and public judging
included:

| Measured on | Mean wall time per attempt |
| --- | --- |
| Mixed development tasks, passes 1–2 | 55–74 s |
| Pass-3 all-hard cohort | 123 s (97–104 minutes per 48-attempt matrix) |

* **Per-attempt planning range:** a 20/20/20 cohort should average between these, so the plan uses
  **60–125 s per attempt**. A seed matrix of 60 tasks × 4 conditions then takes 4–8.5 h.
* **Totals:**
  * 720 attempts: **12–25 h**
  * 1,080 attempts: **18–38 h**
  * 1,440 attempts: **24–50 h**
* **Excluded from those totals:**
  * Hidden evaluation adds a few minutes per batch.
  * B adds 270 × 15–60 s = 1–4.5 h at 90 tasks. It does not use the local model, but this pass did not test
    running it alongside a local batch.
* **Runs are sequential** under the project GPU lock and must not share the GPU with other models: the
  runner defers when foreign models are loaded.

**Money.** Only B and frontier guidance cost money:

| Cost item | Expected at 60 / 90 / 120 tasks |
| --- | --- |
| B, with 10–40% failing attempts at the full-budget cost | $9–28 / $14–42 / $18–57 |
| C/D/E guidance and diagnoses via the direct API | about $1.4–1.5 / $2.0–2.3 / $2.7–3.0 |

**Request counts for the ledger.** At 90 tasks:

| Item | Requests |
| --- | --- |
| Guidance | 180 |
| E diagnoses | 70–110 |
| B | 1,270–2,650 |

**Seeds.** If the run must be cut short, the predeclared pass-3 rule applies: keep the longest prefix of the
frozen task order in which every condition completed. A third seed adds 50% to the GPU time for little
independent information, because outcomes were identical across seeds on 10–12 of 12 tasks per condition.
Two seeds for local conditions plus three for B are a defensible fallback, decided **before** the freeze.

## 4. Statistical precision (what each size can show)

The unit of analysis is the task, with seeds nested (task-clustered bootstrap, as in `diagnostics/ext_analysis.py`).
For a paired difference between two conditions:

* **Standard error:** with discordance rate `d` (the fraction of tasks where the two conditions differ) and
  `n` tasks, the standard error of the paired accuracy difference is about `sqrt(d / n)`.
  * Passes 1–2 put `d` for C versus A at about 0.2–0.4. The all-hard pass-3 cohort gave 0.54 (13 of 24
    pairs).
  * At `d = 0.3` the 95% half-widths are about **±0.14 at n = 60**, **±0.11 at n = 90** and **±0.10 at n = 120**.
    At `d = 0.54` they are ±0.19, ±0.15 and ±0.13.
* **What C needs:** C's observed advantage would be detectable at 60. It was +0.2 to +0.4 in passes 1–2
  and +0.46 in pass 3 on hard tasks.
* **What D and E need:** their effects so far are 0 to ±2 tasks (pass 3: D −0.08, E +0.08), and a +0.05
  effect needs several hundred tasks.
  Their final result will most likely be "no detectable difference". Size the study for C and for B,
  not for D or E.
* **Seeds** reduce within-task noise but do not add tasks. Three seeds were enough here to show seed-induced
  flips (pass 2, abc393_d; pass 3, see `EXTENDED_BENCHMARK.md`).

## 5. Recommendation

**Recommendation: the 90-problem study.** It is the main 60 plus 30 never-used `test5` tasks, 10/10/10,
stratified by shard.

**Why 90 rather than 60.**

* **Precision is not the reason;** 60 already detects C. The 30 `test5` tasks add:
  1. **Clean tasks:** 30 tasks that nobody on the team has run or scored, raising the never-scored stratum
     from 32 to 62 (with arc195_c excluded).
  2. **A second dataset stratum**, so C's effect can be checked for replication across shards rather than
     assumed.
  3. **More hard tasks,** where pass 3 found C's effect largest (+0.46 on the all-hard cohort).
* **The cost is one more night** of GPU time and $6–14 more API spending.

**Why not 120.** It doubles the GPU time of the 60 option. Precision improves only from about ±0.11 to ±0.10,
and the extra `test5` easy and medium tasks are almost exhausted (24 each before the output-semantics
review).

**Task source and selection.**

* **Main 60:** as frozen, minus `arc195_c`, so **59 tasks**.
  * `arc195_c` is constructive. Exact judging would score correct answers as wrong, so exclude it.
  * The alternative is a validator in a new judge version, decided before the freeze.
* **`test5` (30 tasks):**
  * Pinned revision `0fe84c39…`, shard sha256 `7f77571c…`; AtCoder stdin tasks only.
  * Excluded: the 75-ID union and every task used in passes 1–3 (none are in `test5`).
  * Selection is **outcome-blind**, by the same rule as `selection_pass3.py`: hash order within each difficulty
    label, 10/10/10.
  * Run the output-semantics classifier and **review every cue-flagged task by hand before selecting**. Only
    `exact` tasks are eligible.
* **Freeze:** the manifest, both shard hashes and the review file go in the two-stage freeze, before any
  guidance or run.
* **Reporting strata:**
  * `test6`, prior model execution (27 tasks)
  * `test6`, never scored (32 tasks)
  * `test5` (30 tasks)
  * pooled

**Judge strategy.**

* **Score only `exact` tasks with the unchanged judge `csc2108-judge:0.2.1`.** It is the frozen LiveCodeBench
  rule, regression-tested on abc392_d and abc396_e (non-exact tasks are excluded, not scored wrongly).
* **Keep `abc395_a`** (case-insensitive Yes/No) under exact scoring and report it as a known risk; the
  samples print `Yes`/`No`. The alternative is case folding for that task in a new judge version.
* **Freeze the judge version** with the experiment. Any judge change before the run is a new version with
  its own regression tests. Do not change the judge after the run.

**Conditions and providers.**

* **Conditions:** A, C, D and E as frozen in passes 1–3, with the original frozen agent and no ACI. B uses the
  same agent loop with the frontier model as coder.
* **One provider per condition, never mixed:** the **direct API** for all C/D guidance (generated once per
  task, frozen by hash before runs), E diagnoses and B. That costs about $16–44 at 90 tasks.
* **Codex replay** stays the development substitute only.
* **Seeds:** 3 for the local conditions and 3 for B. The fallback (2 local seeds) must be decided before the
  freeze.

**Analysis.**

* **Predeclare** the `ext_analysis.py` statistics: paired per (task, seed), task-clustered bootstrap, sign
  test over tasks.
* **Report E's trigger rate** next to every E result, and split failures into *no program* and *wrong
  program*.
* **Primary comparisons:** C vs A and B vs A. D and E vs A are secondary, and likely to show no detectable
  difference (§4).

**Before freezing:**

1. a **B pilot** on about 10 consumed development tasks that fail locally (≤ $6), to measure the cost of a
   failing B attempt;
2. a team decision on the **ledger ceilings** (`FRONTIER_ONLY_COST.md` §3);
3. the `test5` **output-semantics review**;
4. a decision on arc195_c and abc395_a.
