# Final benchmark options: 60, 90 or 120 problems

This document only plans the final study; nothing here was run, and the main 60-task cohort was not
touched. The decision belongs to the team. All counts come from public metadata and statements
(`diagnostics/shard_pool.py`, `evidence/output-semantics-review.json`).

COST_PLACEHOLDER

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

ESTIMATES_PLACEHOLDER

## 4. Statistical precision (what each size can show)

The unit of analysis is the task, with seeds nested (task-clustered bootstrap, as in `diagnostics/ext_analysis.py`).
For a paired difference between two conditions:

* **Standard error:** with discordance rate `d` (the fraction of tasks where the two conditions differ) and
  `n` tasks, the standard error of the paired accuracy difference is about `sqrt(d / n)`.
  * Pass 1–3 data put `d` for C versus A at about 0.2–0.4.
  * At `d = 0.3` the 95% half-widths are about **±0.14 at n = 60**, **±0.11 at n = 90** and **±0.10 at n = 120**.
* **What C needs:** C's observed advantage (+0.2 to +0.4 in passes 1–2) would be detectable at 60.
* **What D and E need:** their effects so far are 0 to ±1 task, and a +0.05 effect needs several hundred tasks.
  Their final result will most likely be "no detectable difference". Size the study for C and for B,
  not for D or E.
* **Seeds** reduce within-task noise but do not add tasks. Three seeds were enough here to show seed-induced
  flips (pass 2, abc393_d; pass 3, see `EXTENDED_BENCHMARK.md`).

## 5. Recommendation

RECOMMENDATION_PLACEHOLDER
