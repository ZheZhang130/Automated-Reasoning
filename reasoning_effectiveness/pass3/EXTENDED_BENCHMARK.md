# Extended benchmark (pass 3): 12 fresh tasks × A/C/D/E × two seeds

## Executive summary

**What ran.**

* **96 of 96 planned attempts** completed: 12 tasks × 4 conditions × 2 seeds.
* **Integrity:** 0 infrastructure or setup errors, and 0 excluded blocks. All 96 attempts passed the 38-file
  frozen verification with the pinned model digest and a verified sampler wire.
* **Cohort:** 12 fresh `test6` tasks, selected outcome-blind and frozen before any guidance or run. All are
  labelled *hard*.

**Hidden accuracy** (24 attempts per condition):

| Condition | Seed 2108 | Seed 2109 | Pooled | Mean share of hidden tests passed |
| --- | --- | --- | --- | --- |
| A (local only) | 1/12 | 1/12 | **2/24** | 0.15 |
| C (plan) | 6/12 | 7/12 | **13/24** | 0.54 |
| D (contract) | 0/12 | 0/12 | **0/24** | 0.10 |
| E (live diagnosis) | 1/12 | 3/12 | **4/24** | 0.26 |

**Against passes 1–2.**

* **C (planning) is reinforced and stronger.**
  * Against A: 12 gains and 1 harm over 24 (task, seed) pairs. Mean difference +0.46, with a task-clustered
    95% interval of (0.17, 0.75).
  * 7 of the 8 tasks where the conditions differ favour C (exact sign test p = 0.070, descriptive only).
  * Passes 1–2 showed +0.2 to +0.4 on development tasks. Here the cohort was outcome-blind, fresh and all hard.
* **D (contract) is reinforced as no benefit, now slightly negative.**
  * 0/24 hidden passes: 0 gains and 2 harms against A.
  * The first response hits the 4,096-token cap in 23 of 24 D runs, so the contract does not prevent the
    method search that truncates the response.
* **E (diagnosis) is reinforced as "helps when it fires, but rarely fires".**
  * E triggered in **6 of 24** runs. 17 untriggered runs never reached a public test because of truncation,
    and in one the first public test passed.
  * All 6 diagnoses were delivered. Overall E is +2 / −0 against A.
  * **After a triggered failure, E recovered far more often than A from the identical state:** a public pass
    afterwards in 5/6 runs against A's 0/6, and 205/240 hidden cases against A's 107/240.
  * **Attribution is weakened.** The pass-3 neutral-message probe shows that some rescues come from the
    perturbation, not the diagnosis's content. Both E rescues where A failed fixed an input-parsing slip.

**What these results do not show.**

* The difference is not statistically significant, and none is claimed: 12 tasks from one shard and
  difficulty band, two seeds.
* They do not show generalization to easy or medium tasks.

## 1. Methodology

**Cohort selection.** Selection was deterministic and outcome-blind. It is implemented in
`guided_agent/selection_pass3.py` and frozen in `evidence/selection-pass3.json`.

* **Pool:** AtCoder stdin tasks in the pinned `test6` shard (revision `0fe84c39…`, sha256 `bb4c364f…`), which
  is the newest official shard; none is newer. Excluded: the main 60-task manifest, the 75-ID scored union,
  teammate-used tasks and every pass-1/2 task.
* **Judge compatibility:** each statement and its sample outputs were classified by
  `output_semantics.classify`, and the 10 cue-flagged tasks were reviewed by hand
  (`evidence/output-semantics-review.json`). Only tasks whose decided category is `exact` are eligible.
  * **Excluded:** five tasks. abc397_d, abc398_f, arc190_a and arc191_c are multiple-answer or constructive;
    arc192_b is case-insensitive (Yes/No in any case).
  * **No unreviewed cue was allowed through.**
* **Order:** LiveCodeBench labels every remaining fresh task *hard*, so the order uses the public contest
  letter.
  * Bands: 1 = ABC D/E, 2 = ABC F, 3 = ARC A/B, 4 = ABC G and ARC C or later.
  * Pool per band: 1 / 6 / 2 / 11. Within a band the order is sha256(seed:pass3:band:id).
  * The first 12 tasks form the cohort: 1 band-1, 6 band-2, 2 band-3 and 3 band-4 tasks.
* **Caveat:** the cohort is **hard-heavy by necessity**. The fresh part of `test6` has no easy or medium
  AtCoder tasks left.

| Order | Task | Band | Public / hidden tests |
| --- | --- | --- | --- |
| 1 | abc397_e | 1 | 2 / 40 |
| 2 | abc388_f | 2 | 3 / 40 |
| 3 | abc395_f | 2 | 4 / 40 |
| 4 | abc389_f | 2 | 3 / 40 |
| 5 | abc397_f | 2 | 2 / 40 |
| 6 | abc391_f | 2 | 3 / 40 |
| 7 | abc390_f | 2 | 3 / 40 |
| 8 | arc193_a | 3 | 2 / 40 |
| 9 | arc193_b | 3 | 2 / 40 |
| 10 | arc195_d | 4 | 1 / **1** |
| 11 | arc194_e | 4 | 2 / 40 |
| 12 | arc190_c | 4 | 2 / 40 |

`arc195_d` has a single hidden test in LiveCodeBench, so its hidden score is all-or-nothing.

**Two-stage freeze.**

1. `evidence/FREEZE-ext.json` was written at 19:18 UTC from commit `7ea7773` (clean tree), before any guidance
   or run. It records:
   * the configuration and the source hashes of `guided_agent/`;
   * dataset, statement, public and hidden hashes;
   * agent digest and budgets, prompt, injection and delivery hashes;
   * seeds, plan hashes, the analysis plan and the policies below.
2. `evidence/FREEZE-ext-guidance.json` was written at 19:23 UTC, before any local run. It records the sha256
   of all 24 guidance artifacts.

**Conditions.** These are identical to passes 1–2.

| Condition | What the local agent receives |
| --- | --- |
| **A** | The statement only |
| **C** | `plan-v1` guidance via `inject-v1` |
| **D** | `contract-v1` guidance via `inject-v1` |
| **E** | The statement only. Then, at the first public WA/RE/TLE/CE, one live `diagnosis-v1` call delivered into the same session via `deliver-v1`, with the deadline suspended during the call |

* **Provider:** all guidance and diagnoses are Codex-authored (isolated `codex exec`, `gpt-6.2-sol`,
  effort medium). The label is **"Codex-authored frontier guidance replay"**.
* **Guidance reuse:** guidance was generated once per task and reused for both seeds.
* **No paid API request** was used in this cohort.

**Agent and judge.** These are frozen and identical to passes 1–2.

* **Agent:** `local_eval_v2.runtime.run`, with 38 files hash-verified on every attempt. Qwen3.5 9B Q4_K_M
  (digest `56671c2a…`), `heredoc-v6-16k-common`, temperature 0.2, 4,096 output tokens, thinking off.
* **Budgets:** 20 actions, 3 repair groups, 600 s.
* **Judges:** judge-public gives the agent public tests only. The hidden judge `csc2108-judge:0.2.1` runs in
  a separate container after each batch.

**Predeclared policies** (from `FREEZE-ext.json`).

* **Order:** the seed-2108 matrix first, then seed 2109. Tasks follow the frozen order, with A, C, D and E
  interleaved per task. Every attempt is checkpointed.
* **Reduction rule:** if seed 2109 cannot finish, keep the longest prefix of complete task blocks.
* **Infrastructure:** an `infra_error` or `setup_error` attempt is never rerun; its (task, seed) block is
  excluded from every paired comparison.
* **E provider failures** are part of the E outcome and are not retried.
* **Scoring:** a missing submission counts as a failure.
* **No tuning** after the freeze.

**Analysis** (`diagnostics/ext_analysis.py`, commit `4615853`). It was committed at 14:36 EST, while the
seed-2108 attempts were running and before any hidden result existed, and it was not changed afterwards.

* **Accuracy:** hidden accuracy per condition, per seed and pooled.
* **Paired comparisons** per (task, seed): gains and harms.
* **Uncertainty:** a task-clustered bootstrap, resampling tasks with seeds kept together (20,000 resamples,
  RNG seed 2108), and an exact sign test over tasks. Both are descriptive; **no claim of statistical
  significance is made.**

**Codex guidance provenance.**

* **Generation:** the 24 C/D artifacts (12 `plan-v1`, 12 `contract-v1`) were produced once per task,
  between the two freezes, by isolated `codex exec` calls (`codex-cli 0.171.0`). Each call saw only the
  versioned system prompt and the public statement.
* **Validation and isolation:** every event stream held exactly one `agent_message` and 0 tool, command,
  file or search events. All 24 artifacts passed the guidance validator. None was regenerated, and both seeds
  reused the same bytes, hash-checked against `FREEZE-ext-guidance.json`.
* **Length:** plans ran 384–993 words, contracts 272–389.
* **Sanitized copies:** `evidence/guidance/ext-codex/`.

## 2. Per-task, per-seed outcomes

Each cell gives the hidden verdict (✓/✗), hidden cases passed, and length truncations (T). For E it also says
whether E triggered. "none" means no program was submitted (`RepeatedFormatError` after three truncated
responses, or no file written).

### Seed 2108

| # | Task | A | C | D | E |
| --- | --- | --- | --- | --- | --- |
| 1 | abc397_e | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 2 | abc388_f | ✗ none (3T) | ✗ none (3T) | ✗ 38/40 (1T) | ✗ none (3T, untrig) |
| 3 | abc395_f | ✓ 40/40 (1T) | ✓ 40/40 | ✗ none (3T) | ✓ 40/40 (1T, trig) |
| 4 | abc389_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 5 | abc397_f | ✗ none (3T) | ✗ 0/40 (1T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 6 | abc391_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 7 | abc390_f | ✗ 8/40 (5T) | ✓ 40/40 (1T) | ✗ 2/40 (1T) | ✗ 13/40 (1T, trig) |
| 8 | arc193_a | ✗ none (3T) | ✗ none (3T) | ✗ 18/40 (2T) | ✗ none (3T, untrig) |
| 9 | arc193_b | ✗ none (3T) | ✓ 40/40 | ✗ 1/40 (2T) | ✗ none (3T, untrig) |
| 10 | arc195_d | ✗ none (3T) | ✗ 0/1 (2T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 11 | arc194_e | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 12 | arc190_c | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |

### Seed 2109

| # | Task | A | C | D | E |
| --- | --- | --- | --- | --- | --- |
| 1 | abc397_e | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 2 | abc388_f | ✗ 21/40 (1T) | ✗ none (3T) | ✗ 38/40 (1T) | ✗ 38/40 (1T, trig) |
| 3 | abc395_f | ✗ 34/40 (2T) | ✓ 40/40 | ✗ 0/40 (2T) | ✓ 40/40 (2T, trig) |
| 4 | abc389_f | ✗ none (3T) | ✓ 40/40 (1T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 5 | abc397_f | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 6 | abc391_f | ✗ none (3T) | ✓ 40/40 (1T) | ✗ 0/40 (3T) | ✗ none (3T, untrig) |
| 7 | abc390_f | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 8 | arc193_a | ✗ 4/40 (1T) | ✓ 40/40 | ✗ none (3T) | ✓ 40/40 (1T, trig) |
| 9 | arc193_b | ✗ none (3T) | ✓ 40/40 | ✗ none (3T) | ✗ none (3T, untrig) |
| 10 | arc195_d | ✗ none (3T) | ✗ none (3T) | ✗ none (3T) | ✗ none (3T, untrig) |
| 11 | arc194_e | ✓ 40/40 (1T) | ✗ none (3T) | ✗ none (3T) | ✓ 40/40 (1T, untrig) |
| 12 | arc190_c | ✗ 0/40 (2T) | ✗ 0/40 (1T) | ✗ none (3T) | ✗ 34/40 (2T, trig) |

**Seed sensitivity.** The outcome (pass or fail) was identical across the two seeds for 10/12 tasks in A,
11/12 in C, 12/12 in D and 10/12 in E. Most changes came with a different truncation pattern. The local agent
is near-deterministic at temperature 0.2, so the second seed adds little independent information per task.

**Generated sources:** `evidence/analysis/ext-tables.md` and `ext-analysis.json` (per-run rows), and
`evidence/runs.json` (public attempts and hidden outcomes as hashes and verdict counts).

## 3. Paired gains and harms

The unit is the (task, seed) pair (24 pairs). The interval is a task-clustered bootstrap. The sign test is
over tasks: a task counts as positive or negative when its two seeds net in one direction.

| Comparison | Gains | Harms | Both pass | Both fail | Mean difference | Task-clustered 95% interval | Sign test over tasks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C vs A** | 12 | 1 (arc194_e@2109) | 1 | 10 | **+0.458** | (+0.167, +0.750) | 7+ / 1−, p = 0.070 |
| D vs A | 0 | 2 (abc395_f@2108, arc194_e@2109) | 0 | 22 | −0.083 | (−0.208, 0.000) | 0+ / 2−, p = 0.50 |
| E vs A | 2 (abc395_f@2109, arc193_a@2109) | 0 | 2 | 20 | +0.083 | (0.000, +0.208) | 2+ / 0−, p = 0.50 |
| C vs D | 13 | 0 | 0 | 11 | +0.542 | (+0.250, +0.833) | 7+ / 0−, p = 0.016 |
| C vs E | 10 | 1 | 3 | 10 | +0.375 | (+0.083, +0.667) | 5+ / 1−, p = 0.22 |
| D vs E | 0 | 4 | 0 | 20 | −0.167 | (−0.375, 0.000) | 0+ / 3−, p = 0.25 |

**C's gains are spread across tasks**: 7 of 12 tasks, with both seeds gaining on 5 of them. The one harm (arc194_e,
seed 2109) is a task A solved with one truncation, where C's three responses all truncated.

**How to read these.**

* The p-values are descriptive. Six comparisons were made, and no correction or significance claim is made.
* Only the three comparisons involving C (against A, D and E) have intervals that exclude 0.
* Neither D nor E differs detectably from A.

## 4. Condition E: trigger, delivery and recovery

| Measure | Value |
| --- | --- |
| Assigned E runs | 24 |
| Triggered (first public WA/RE/TLE/CE) | **6 (25%)** |
| Untriggered: never ran a public test (truncation, no program) | 17 |
| Untriggered: first public test passed | 1 (arc194_e@2109, which then passed hidden, as A did) |
| Diagnoses requested / delivered | 6 / 6; 0 timeouts, transport, isolation or format errors |
| Codex wait at the trigger | 11.2–15.4 s (mean 13.1 s), excluded from the local deadline; 0 tool events |
| Program changed after the diagnosis | 6/6 (changed-line ratio 0.08–0.85) |
| Public pass after the diagnosis | **5/6** |
| Hidden pass among triggered runs | 3/6 (A at the same states: 1/6) |
| Triggered where A failed / recovered there | 5 / **2** |

**Pre-trigger identity (checked byte for byte).**

* All 18 untriggered E runs are identical to the A run with the same task and seed, message for message.
* The 6 triggered runs match A up to the triggering observation.
* E's effect is therefore exactly what happened after the trigger.

**After the same failure: A against E.**

| Run | Fault named by the diagnosis | A after this point | E after the diagnosis |
| --- | --- | --- | --- |
| abc395_f@2108 | **Input parsing:** reads all upper lengths, then all lower ones; the input gives pairs | 20 actions, no public recovery, 6 unchanged rewrites; hidden ✓ (last untested write) | Public pass on the next test; ✓ 40/40 in 5 actions |
| abc390_f@2108 | Counting uses global first/last occurrences; presence needs one | 20 actions, 10 unchanged rewrites; 8/40 | Rewrote; no public pass; 13/40 (repair limit) |
| abc388_f@2109 | `bisect_left` skips the containing interval; use `bisect_right − 1` | 20 actions, a 9-response identical loop; 21/40 | Public pass; **38/40** (1 TLE, 1 RE) |
| abc395_f@2109 | **Input parsing** (pairs) plus an infeasible-`H` assumption | 20 actions, 8 unchanged rewrites; 34/40 | Public pass; **✓ 40/40** |
| arc190_c@2109 | DP multiplies predecessor terms that must be added | 20 actions, a 9-response identical loop; 0/40 | Public pass; **34/40** (6 TLE: the diagnosis noted the per-update cost) |
| arc193_a@2109 | **Input parsing:** interval endpoints read as two lists | 11 actions, repair limit; 4/40 | Public pass; **✓ 40/40** |

**Reading.**

* **Recovery improved.**
  * A never reached a public pass again after any of these six failures.
  * In five of them A rewrote an unchanged program. In four it entered an exact repeat loop
    (`AGENT_FAILURE_ANALYSIS.md` §2).
  * E reached a public pass in five, and improved the hidden score in all five where A failed: 8→13, 21→38,
    34→40, 0→34 and 4→40.
* **Correctness improved less.**
  * Only two of the five became hidden passes.
  * Both were input-parsing slips, which are shallow, local faults. The algorithmic faults (abc390_f,
    arc190_c, abc388_f) improved but did not pass.
* **Attribution is limited.**
  * The pass-3 neutral probe (`AGENT_FAILURE_ANALYSIS.md` §5.3) shows that a content-free message at the
    same kind of state can also break the loop and sometimes rescue a run.
  * The post-failure difference measures *E's intervention*, not proof that the diagnostic content caused
    each repair.
  * All six diagnoses named a concrete fault consistent with the public failure, and five next programs
    passed the public tests. The larger edits after genuine diagnoses (§5.3: median changed-line ratio 0.48
    against 0.26 for the neutral message) suggest the content matters.
* **The bottleneck is the trigger.** With 71% of E runs never reaching a public test, E's overall effect is
  capped by the frozen agent's truncation, not by the diagnosis.

## 5. Tokens and time

Means per attempt over 24 attempts:

| Condition | Model calls | Completion tokens | Truncations | Local coding s | Wall s | Frontier wait s |
| --- | --- | --- | --- | --- | --- | --- |
| A | 7.4 | 13,048 | 2.7 | 142.6 | 143.2 | 0 |
| C | 5.0 | **6,875** | 1.3 | **80.4** | 81.1 | 0 (guidance prepared upfront) |
| D | 5.8 | 12,664 | 2.6 | 138.2 | 138.8 | 0 (guidance prepared upfront) |
| E | 4.4 | 11,565 | 2.5 | 128.2 | 128.9 | 3.3 (13.1 per triggered run) |

* **C does more with less.** It uses about half of A's local tokens and time per attempt, and the first
  response stays under the 4,096-token cap in 10/24 runs (A: 1/24, D: 1/24).
* **Upfront cost:** one Codex plan or contract per task, reused for both seeds. Codex gives no metered cost;
  the API equivalent is about $0.006–0.012 per artifact (`PROVIDER_VALIDATION.md`).
* **Batch wall time:** 97–104 minutes per 48-attempt seed matrix, about 2 minutes per attempt including
  container setup and public judging. Hidden evaluation adds a few minutes per batch.

## 6. Failure categories

| Category | A | C | D | E |
| --- | --- | --- | --- | --- |
| Pass | 2 | **13** | 0 | 4 |
| No program (truncation, `RepeatedFormatError`) | 17 | 8 | 17 | 17 |
| Partial: wrong answers on some tests | 3 | 0 | 3 | 1 |
| Partial: RE/TLE on some tests | 1 | 0 | 2 | 2 |
| Wrong everywhere (0 hidden cases) | 1 | 3 | 2 | 0 |

* **No program is the dominant failure:** 17 of 22 A failures and 17 of 24 D failures.
  * This is the agent-interface mechanism of `AGENT_FAILURE_ANALYSIS.md` §1: method search inside the
    heredoc until the token cap.
  * It is not a judged wrong answer.
* **C removes about half of those**, 8 against 17. Its remaining failures split into no program (8) and wrong
  programs (3: abc397_f, arc190_c, arc195_d).

## 7. Uncertainty and limitations

1. **Small and narrow.**
   * 12 tasks, all LiveCodeBench-hard, from one shard (`test6`, contests January–April 2025).
   * C's effect on easy or medium tasks, where A already passes, is not measured here; passes 1–2 suggest it
     is smaller there.
   * The interval for C vs A is wide: 0.17 to 0.75.
2. **Two seeds of a near-deterministic agent.** Seeds changed the outcome on 1–2 tasks per condition. The
   effective sample is closer to 12 than to 24.
3. **Codex replay.** All guidance and diagnoses are Codex-authored, through a harness context the API does
   not have. Matched API checks agreed (`PROVIDER_VALIDATION.md`), but the cohort was not repeated with the API.
4. **arc195_d** has a single hidden test, so its score is all-or-nothing.
5. **E's measured effect** mixes diagnosis quality with trigger opportunity, and the neutral probe shows part
   of a rescue can be perturbation.
6. **No tuning.** No prompt, runtime or selection change was made after the freeze, so these findings are
   not optimized for this cohort. The same holds in the other direction: nothing was tuned to make D or E
   look better.

## 8. Reproduction

From the repository root on the branch (Docker, the project Ollama with the pinned digest, `codex` logged in;
no API key is needed for this cohort):

```bash
export CSC2108_STUDY_ROOT=<study>          # the pass-3 study directory
python -m guided_agent.selection_pass3 <test6.jsonl> reasoning_effectiveness/pass3/evidence/output-semantics-review.json <out>.json 12
# rerun on 2026-11-22: identical to evidence/selection-pass3.json except created_utc
python -m guided_agent batch <study>/plans/ext-s2108.json && python -m guided_agent evaluate <study>/runs/ext-s2108
python -m guided_agent batch <study>/plans/ext-s2109.json && python -m guided_agent evaluate <study>/runs/ext-s2109
python -m reasoning_effectiveness.pass3.diagnostics.ext_analysis <study> <study>/analysis ext-s2108 ext-s2109
python -m reasoning_effectiveness.pass3.diagnostics.failure_mechanisms <out>.json "<study>@ext-s2108,ext-s2109"
```

* **Replay:** C/D guidance comes from `<study>/guidance/ext-codex/` (sha256 in `FREEZE-ext-guidance.json`).
* **Refusal:** a plan that differs from its frozen hash is refused (`integrity.check_unchanged`).
* **Determinism:** a rerun reproduces A, C and D. E reproduces up to the trigger; the live Codex diagnosis is
  not byte-reproducible.
