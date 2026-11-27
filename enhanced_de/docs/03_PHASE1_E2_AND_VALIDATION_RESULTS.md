# Phase 1 (E2), protocol v2, outcome-blind validation and paid-API checks

Written by the continuation session (Claude Opus 5.5, 2026-11-26), which took over from the first session's lead
(Gemini 4 Neon). Every number below comes from `<study>/runs/*/summary.json`, `<study>/reports/*.json` or the per-run
`result.json` and `eval/*.json` files; `<study>` is `E:\CSC2108Local\enhanced-de-v2-study` on the reference host, and
the sanitized copies are under `results/enhanced-de-v2/`.

**Provider labels are never pooled.** `codex-replay` is isolated Codex (`codex exec`, empty working directory,
read-only, tools disabled) standing in for the frontier. It is free and is **not** API-equivalent. `openai-api` is
the paid `gpt-6.2-sol` API under the v2 ledger. No mocked results appear in these tables.

**Development versus validation.**

* **Development.** Phases 0–1 and the protocol-v2 check reuse consumed `final-main` tasks. The states were selected
  on historical outcomes.
* **Validation.** Phase 2 uses 16 `test5` tasks: 8 medium and 8 hard. No agent had run on them before this phase,
  and no design decision was revised after their outcomes were seen.
* **Small samples.** Single seeds and small n throughout. There are no significance claims.

---

## 1. Offline E2 checks (Phase 0, codex-replay; Neon session, numbers re-verified)

| Check | Result |
| --- | --- |
| E2-review on 10 A submissions that passed public and failed hidden tests (PPHF) | DEFECT verdict 9/10. Sandbox-verified delivery 8/10. All 11 verified counterexamples were correct against passing reference programs |
| E2-review on 6 genuinely correct A submissions | NO-DEFECT 6/6. False deliveries 0/6 |
| E2-strict at 12 historical E-v1 trigger states | Schema-valid 12/12: 4 LOCAL-FIX, 8 METHOD-CHANGE, no hedging. An aligned V-check in 10/12 states; 11/11 aligned checks correct on references. The V-checks would have flagged 3 of the 7 historical post-diagnosis PPHF submissions |

**Caveat (Codex audit).** The offline review sends official A submission bytes as the candidate. That is the object
under review, not leaked evidence, and the reference adjudication happens after inference.

## 2. Phase 1A: D2 gates and E2-review at PPHF states (development, codex-replay)

**Cohort.** 10 (task, seed) states where the official A run passed the public tests and failed the hidden ones, plus
6 safety states. Because the local agent is deterministic on this host, every arm reaches the same first public pass
that A reached (checked: candidate hashes match the official A run at 42/42 D2 and 10/10 review trigger states).

| Arm | Runs | Delivered | Hidden passes (PPHF states) | Rescues vs A | Losses vs A |
| --- | --- | --- | --- | --- | --- |
| D2-inputs-stress | 16 | 5 | 1/10 | 1 (abc400_c@2108) | 0/4 safety |
| D2-property | 16 | 10 | 1/10 | 1 (same state) | 0/4 safety |
| D2-oracle | 16 | 10 | 1/10 | 1 (same state) | 0/4 safety |
| E2-review | 10 | 9 | 2/10 | 2 (abc387_c@2108, abc400_c@2109) | no live safety states |

**What the trajectories show** (`agent_reports/2026-11-26_claude_trajectory_analysis.md`, Q1):

* **D2 rescue counts are not independent.** The 25 delivered D2 runs collapse to 18 distinct trajectories, because
  the same counterexample produces the same response. The three D2 "rescues" are one trajectory: a TLE on huge `N`,
  which explains itself.
* **D2 detection was high and repair was rare.** Property and oracle gates fired on 10/10 wrong programs with 0 false
  alarms. After delivery, 11 of 18 distinct trajectories entered identical-response loops. The agent almost never
  ran the counterexample. Twice it dismissed a valid failure as a "display issue in the test harness", right after
  the header "NOT verified; judge-public above is authoritative" and a clipped large input.
* **Localization matters more than the counterexample.** On abc387_c@2108, D2-oracle and E2-review show the same
  failing input. D2 shows bare input and output, and the agent loops. E2-review adds the faulty line and a two-line
  repair, and the agent fixes it.
* **Algorithmic repairs fail even with good content.** E2-review failed in 7 of 9 runs. Every review that prescribed
  a new algorithm (tree DP, pair-BFS, game parity) ended in output-cap truncation or regression. Both rescues were
  few-line or one-formula changes.

## 3. Phase 1B: E2-strict at the first public failure (development, codex-replay)

**Cohort.** 12 states where the **official API E-v1 diagnosis failed**. Selecting states on E-v1's failure biases
any comparison against E-v1 (regression to the mean), so a provider-matched control was added. That control re-runs
E-v1 (`diagnosis-v1` + `deliver-v1`, official runner) with a fresh isolated-Codex diagnosis at the same 12 states.

| Arm | Hidden passes | Hidden cases passed (sum over 12 × ≤40) |
| --- | --- | --- |
| Official A (deterministic) | 0/12 | 235 |
| Official E-v1 (API, historical; selected to fail) | 0/12 | 302 |
| **E2-strict (codex-replay)** | **1/12** (abc400_c@2109) | 303 |
| **E-v1 control (codex-replay, same states, official runner)** | **2/12** (abc389_d@2110, arc191_a@2108) | 296 |

**Reading.**

* **E2-strict does not beat the original diagnosis.** With the provider held fixed it is 1/12 against 2/12, and
  the passing states do not overlap.
* **The historical 0/12 was partly a selection artifact.** A fresh E-v1 sample rescues 2 of the states selected
  for E-v1's failure, as regression to the mean would predict. Without this control, E2-strict's 1/12 would have
  looked like an improvement.
* **One control run overflowed its context.** E-v1 on arc194_d reached a 16.2k-token prompt, the connection
  dropped, and the runner logged `infra_error`. It is counted as a failure, as the official policy requires.

**Mode adherence** (trajectory analysis, Q2):

* **METHOD-CHANGE (8 runs).** Followed in 5, partly in 1, not in 2. Output-cap truncation in 3 of 8, none fatal; a
  repeat loop in 3 of 8.
* **LOCAL-FIX (4 runs) did worse: all 4 looped.** With full-file heredoc rewrites, a "local" fix means re-emitting
  the whole program. Twice the agent re-emitted the diagnosed program unchanged.

## 4. Phase 1C: stall interventions, protocol v1 (development, codex-replay)

**Cohort.** 12 states where official A truncated twice and never wrote a program, stratified by whether official C
solved them:

* 4 medium states, C passed;
* 4 hard states, C passed;
* 4 hard states, C failed.

**Trigger and arms.** The trigger is the second consecutive length stop with no candidate. The two truncated
responses are byte-identical across arms, so these are matched comparisons. The arms differ only in the message:

* **stall-diag:** a frontier diagnosis of the truncated deliberation (`E2_STALL_V1`);
* **C-late:** the frozen official `plan-v1` delivered at the same moment;
* **neutral:** a content-free "stop deliberating, write the code" nudge.

| Arm (protocol v1) | Program after delivery | Hidden passes | Passing states |
| --- | --- | --- | --- |
| A (official, deterministic) | 0/12 | 0/12 | – |
| neutral | 1/12 | 0/12 | – |
| stall-diag | 5/12 | **3/12** | abc390_d, abc390_e, arc194_a |
| C-late | 11/12 | **4/12** | abc390_d, abc400_d, arc194_a, arc195_b |
| Upfront C (official, same seeds; reference) | – | 8/12 | – |

**Protocol deviation (disclosed).** The first five stall-diag runs had their diagnosis rejected by the original
220-word validator (221–233 words), so nothing was delivered. Neon raised the cap to 300 and reran those five. The
rejected runs are archived in `runs/phase1c-e2-stall-codex/_v1_220cap_archive/`. The table uses the reruns.

**Why v1 under-performed.** The trajectory analysis (Q3–Q4) found three delivery defects, not a lack of content:

1. **One response to act.** The frozen agent's consecutive format-error streak was already 2 when the message
   arrived, and v1 did not reset it. One more cut-off response ended the run with RepeatedFormatError. That
   happened in 11 of 27 delivered stall runs.
2. **The combined-command trap.** The v1 wrapper and prompt said "write … in a single command, then run
   python -I /public/check.py". The agent appended the test to the heredoc. The public-check stub rejects that, and
   the agent repeated it until the action limit. 4 of the 5 diag runs that wrote a program lost all 20 actions this
   way. Two of them (abc390_d, abc390_e) had in fact written a correct program and still passed hidden tests.
3. **Re-derivation instead of transcription.** Faced with a one-paragraph key observation, the agent re-derived it
   inside code comments until the output cap; on abc391_d, 186 comment lines against 23 code lines. With C-late's
   numbered recipe, it transcribed.

## 5. E2-stall protocol v2 (development check, codex-replay)

**What changed** (`e2_diagnosis.E2_STALL_V2`, `DELIVERY_STALL_V2`, `NEUTRAL_NUDGE_V2`, and `runner_v2` resetting the
streak on delivery). The changes are identical for all three stall arms, so the controls stay matched:

* the consecutive format-error streak is reset when the message is delivered (the limit of 3 is unchanged);
* one procedural tail closes every message: write the file with a command that only writes it, then run the tests
  in the next response as a separate command;
* the diagnosis gives the approach as 3–7 numbered steps, to be implemented without re-derivation. The word target
  rises to 280 and the validator cap to 380.

**What is unchanged:** the trigger, the evidence packet, the frozen plans and the nudge's content.

Results on the same 12 states (`runs/phase1c-v2-e2-stall-codex`). A is 0/12 throughout.

| Arm | v1: program / hidden pass | **v2: program / hidden pass** | v2 passing states |
| --- | --- | --- | --- |
| neutral | 1/12 / 0/12 | 3/12 / **0/12** | – |
| stall-diag | 5/12 / 3/12 | **12/12 / 1/12** | arc194_a |
| C-late | 11/12 / 4/12 | 12/12 / **5/12** | abc390_d, abc391_d, abc400_d, arc194_a, arc195_e |
| Upfront C (official reference) | – / 8/12 | – | – |

Run accounting:

* **The abc390_g stall-diag run was rerun.** The original run was hit by an outage of the local model server (the
  server process reached a tool time limit). It was set aside before any hidden scoring as
  `…abc390_g-E2-stall-diag-s2108.incomplete-ollama-outage-2108` and rerun. The rerun was delivered, wrote a program
  and failed hidden tests (4/40).
* **Two v2 runs ended in a deterministic context overflow** (C-late on abc390_g, neutral on arc192_e). The prompt
  passed about 15k tokens and the 4,096-token reply no longer fit in 16k. Ollama dropped the connection, which the
  runner logged as `infra_error`. As in the official policy, a context overflow counts as a failed attempt, and
  neither run passed hidden tests.

**Reading.**

* **v2 fixed delivery.** stall-diag now produced a program in 12/12 states (v1: 5/12). The two cut-off responses
  are byte-identical across arms, so these are matched comparisons.
* **More programs did not mean more passes.** The diagnoses name sensible algorithms: on abc400_d a 0-1 BFS in
  which a kick costs one; on abc391_d per-rank maxima of initial heights. But the local implementations were
  wrong (15/40 hidden tests on both), while the frozen plan, delivered at the same moment and on the same v2
  protocol, led to full passes.
* **Pooled over both protocols** (single samples, so suggestive only):

  | Arm | Hidden passes |
  | --- | --- |
  | stall-diag | 4/24 |
  | C-late | 9/24 |
  | neutral | 0/24 |
  | Upfront C at the same states | 8/12 |

* **What this suggests, and what it cannot show.** At a stall, algorithmic content is what produces passes; a
  content-free nudge produced none. The diag-versus-C-late gap is **not a clean test** of trace conditioning,
  because the two arms differ in several ways at once (the Codex review in `agent_reports/` raised these points):
  * **Provider.** On these development states, C-late delivered the *official API* plans, while the diagnoses
    were fresh *Codex* samples.
  * **Length.** The delivered plan bodies were 484–673 words; the v2 diagnoses were 219–292.
  * **Protocol bundle.** v1 to v2 changed the delivery fixes, the diagnosis format and budget, and the sample all
    at once.
  * **Cohort.** 8 of the 12 states were chosen because upfront C solved them, which favors any C-derived arm.
    That includes the "late versus upfront" comparison (5/12 against 8/12).

  The provider-matched held-out comparison (§6) has C-late 1/3 and stall-diag 0/3: too small to settle it.
* **The neutral nudge produced no passes** (0/12 in v1, 0/12 in v2). It did reach partial credit once
  (arc195_b, 37/40 in v1).

## 6. Phase 2: outcome-blind validation on test5_val16 (codex-replay)

**Cohort** (`manifests/test5_val16.json`). 16 AtCoder tasks from LiveCodeBench `test5.jsonl`, pinned by sha256 and
selected deterministically:

* 8 medium and 8 hard;
* exact-output tasks only;
* at least 10 hidden tests each;
* no overlap with `final.json` or the project's exposure registry.

No agent run had ever touched these tasks. The configurations were frozen before any validation outcome was seen.
One deviation: the stall arms use protocol v2, whose development check (§5) finished before any validation stall
run. Seed 2108 only.

**Design: trigger partitioning** (`enhanced_de/run_phase2_validation.py`).

* A runs on all 16 tasks.
* Each arm runs live only where A's own trajectory reaches that arm's trigger:
  * a stall, 4 tasks: stall-diag, neutral, C-late;
  * a public failure, 4 tasks: E2-strict, E-v1;
  * a public pass, 10 tasks: the three D2 modes and E2-review.
* On every other task the arm's outcome is A's, because the arm cannot fire there.
* C and E-v1 run through the unchanged official `guided_agent` runner, with Codex `plan-v1` artifacts and Codex
  `diagnosis-v1`.

**The determinism premise held.** All 37 silent live runs reproduced A's submission byte-for-byte: 27 D2 runs
that delivered nothing and 10 silent E2-review runs.

| Arm | Hidden passes (of 16) | vs A | Live runs | Delivered | Notes |
| --- | --- | --- | --- | --- | --- |
| A | **7** | – | 16 | – | medium 6/8, hard 1/8 |
| C (`plan-v1`, upfront) | **9** | +2 / −0 | 16 | 16 | gains abc385_c and arc185_e |
| C-late (stall, protocol v2) | **8** | +1 / −0 | 4 | 4 | gains arc185_e |
| E2-stall-diag (v2) | 7 | 0 | 4 | 4 | arc189_c went from no program to 38/40 hidden tests, not a pass |
| E2-stall-neutral (v2) | 7 | 0 | 4 | 4 | – |
| E2-strict | 7 | 0 | 4 | 4 | – |
| E-v1 (`diagnosis-v1`) | 7 | 0 | 4 | 4 | – |
| D2-oracle / D2-property / D2-inputs-stress | 7 / 7 / 7 | 0 | 10 each | 1 each | the one delivery was a false alarm (below) |
| E2-review | 7 | 0 | 10 | 0 | – |
| E2-stall-full (composed: stall-diag, else strict) | 7 | 0 | – | – | – |
| E2-adaptive (composed: stall > fail > review) | 7 | 0 | – | – | – |

**Where each mechanism could act, and what it did.**

* **Public pass that later fails hidden tests (PPHF), 3 tasks.**
  * abc375_c failed hidden tests by TLE/RE (19 TLE, 3 RE). The D2 bank's stress inputs had been dropped at
    calibration, because a maximum-size grid exceeds the 8 MB input cap, so no D2 mode could see the problem.
  * abc376_e (3 hidden WA) and abc382_d (2 hidden WA) were not caught by property, metamorphic or oracle checks.
  * E2-review abstained on all three. On abc375_c it said DEFECT, but its counterexample did not reproduce, so it
    stayed silent. On the other two it said NO-DEFECT.
  * Development detection was 10/10 on selected PPHF states; held-out detection was **0/3**.
* **False alarms, 7 genuinely correct programs.**
  * D2 fired once, in all three modes: a stress TLE at the gate's 4 s limit on abc378_e, a program that passes all
    40 hidden tests within the judge's limit. The agent optimized the program and still passed, so there was no
    harm.
  * E2-review never fired on these 7.
* **Public failure, 4 tasks.** E-v1 and E2-strict were both delivered on all 4. Two states were ones A eventually
  solved; both arms kept them. On the other two (abc376_g, abc385_c), neither diagnosis rescued anything. Upfront C
  solved abc385_c.
* **Stall, 4 tasks** (3 with no program in A, plus abc380_c, where A recovered and passed).
  * All three stall arms kept abc380_c: no harm.
  * On the three no-program tasks: C-late rescued arc185_e. stall-diag produced programs on two (38/40 and 2/40
    hidden tests) and passed none. The neutral nudge produced one program (1/40).
  * arc184_e failed in every arm, including C.
* **No trigger, abc379_g.** A wrote programs but never ran the public tests in 20 actions, so no D or E arm can act
  there. C failed it too.

**Reading (codex-replay frontier).** On held-out tasks with the original agent, none of the enhanced D or E arms
changed a single hidden-test outcome. That includes the broadest single-intervention E2 policy. Planning content did
change outcomes, delivered upfront (+2) or at the stall (+1). With 16 tasks and one seed this is not a significance
claim.

Two cautions:

* **Composed rows are reconstructions.** They pick one branch per task from A's record, by priority, and cannot
  estimate fallback after an abstention.
* **The held-out detection failure counts against the "repair capacity" reading.** D2 and E2-review reached all
  three PPHF states and delivered nothing useful. That is an artifact coverage and quality limit, not a local-agent
  limit.

The paid-API rows in §7 qualify this reading.

## 7. Phase 3: paid-API checks (openai-api; never pooled with codex-replay)

**Purpose.** Provider compatibility, and the actual prompt behavior on the real frontier, at held-out test5 trigger
states. Targets were chosen deterministically from A's trigger record (`run_phase3_api.select_phase3_targets`,
dry-run reviewed before any spend), plus two completion runs (`run_phase3_api_completion.py`) that cover the last
A-failing held-out states an E2 arm could reach. Every request went through the fail-closed v2 ledger.

| Arm (API) | State (A's outcome) | Delivered | Hidden | Codex-replay arm, same state |
| --- | --- | --- | --- | --- |
| E2-strict | abc385_c (fail 35/40) | yes, METHOD-CHANGE | **pass 40/40** | E2-strict 35, E-v1 35 (both fail) |
| E2-strict | abc376_g (fail 2/38) | yes, METHOD-CHANGE | fail 4/38 | 0, 0 |
| E2-strict | abc377_d, abc383_c (A passes) | yes, LOCAL-FIX | pass, pass (no harm) | pass, pass |
| E2-stall-diag (v2) | arc185_e (no program) | yes | **pass 40/40** | stall-diag 2/40, C-late pass |
| E2-stall-diag (v2) | arc184_e (no program) | yes | fail **33/40** | no program in every codex arm, and in C |
| E2-stall-diag (v2) | arc189_c (no program) | yes | fail 34/40 | stall-diag 38/40, C-late 37/40 |
| E2-review | abc375_c, abc376_e, abc382_d (PPHF) | no (1 unverified DEFECT, 2 NO-DEFECT) | fail (= A) | the same three abstentions |
| D2-oracle (API-authored banks) | abc384_c, abc383_c (A passes), abc376_e (PPHF) | no (silent) | = A | = A |

**API rescue side on the held-out cohort.** Eight A-failing tasks reach an E2 trigger: 3 stall, 2 public failure,
3 PPHF. The API E2 arms rescued 2 of them (abc385_c and arc185_e). That is the same two tasks C (codex plans)
rescued, so A plus the API E2 rescues comes to 9/16, C's codex-replay score.

**Caveats:**

* **Not a measured live policy.** The harm side was not re-run with the API. Codex-replay arms showed no losses on
  the 8 A-passing trigger states.
* **Providers differ.** C on test5 used Codex plans; these diagnoses came from the API.
* **Single samples, single seed.**

The fair statement: with the paid frontier, broad-trigger E2 diagnoses rescued 2 of the 8 A-failing held-out
states they reached. Codex-replay diagnoses at the same states rescued none. The artifact draw matters, not only
the local agent's capacity.

**Ledger** (`<study>/api-ledger.json`, sanitized copy `results/enhanced-de-v2/api-ledger.sanitized.json`):

* 14 requests: 4 D2 bundles (Neon), 8 E2 diagnoses and 2 completion diagnoses. 0 failed, no retries.
* Tokens: 29,062 prompt, 15,210 completion, 4,596 of them reasoning.
* Token-derived cost: **$0.210** at standard prices, **$1.261** under the conservative reservation, against the
  $10 and 20-request hard caps.
* E2 diagnosis latency: 2.1–16.0 s.
* The prompt asked for 10–12 requests. The last two went over that target, staying under the hard cap, to complete
  the API rescue side after the first eight results diverged from Codex replay.
