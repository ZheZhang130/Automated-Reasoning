# Condition E: diagnosis quality, neutral-interruption controls and refinement (pass 4, Phase IV)

E's mechanics are unchanged and preserved:

* Qwen codes, a public test fails, one frontier diagnosis is made, and the **same** session repairs.
* No restart and no reset of history, workspace, candidate, action counter, repair counter or remaining budget.
* The trigger is the first qualifying public WA/RE/TLE/CE of a non-empty candidate, at most once per attempt.

Pass-2 and pass-3 integration tests cover all of this, and they pass again in pass 4.

## 1. Audit of the saved diagnoses (brief §8.1)

**What was reviewed.**

* **Diagnoses:** all 16 real diagnoses delivered in passes 2–3 at 11 distinct trigger states: 11 Codex, 5 direct
  API, including both providers at abc393_d, arc195_a and abc398_d.
* **For each one:** the delivered text, the failed program, the program written next, and the public and hidden
  outcomes.
* **Edit size:** "changed" is the changed-line ratio between the failed program and the next program, from
  pass-3 `e_uptake.py`.
* **What "correct" means here:** the cause named is consistent with the failed public case, and the next program
  that applied it fixed that case. It is not a formal proof.

| State (seed) | Provider | Cause identified | Prescription | Changed | Public pass after | Hidden |
| --- | --- | --- | --- | --- | --- | --- |
| abc390_c (2108) | Codex / API | yes: 1-based bounds compared with 0-based loop indices | **local**: use `i`, `j` in four updates | 0.11 / 0.19 | yes / yes | pass / pass |
| abc395_f (2108) | Codex | yes: upper and lower lengths read as two blocks instead of pairs | **local**: read pairs | 0.69 | yes | pass |
| arc193_a (2109) | Codex | yes: interval endpoints read as two blocks | **local**: read pairs | 0.61 | yes | pass |
| abc388_f (2109) | Codex | yes: `bisect_left` skips the containing interval | **local**: `bisect_right(...) - 1` | 0.08 | yes | fail 38/40 |
| arc190_c (2109) | Codex | yes: product instead of sum over predecessors in the DP | **local**: `A[r][c]*(top+left)`, with a complexity caveat | 0.28 | yes | fail 34/40 |
| abc398_d (2108) | Codex / API | yes: answer recorded before the wind step; also too slow | local fix **plus** a new data structure | 0.48 / 0.43 | yes / yes | fail 36/40 (TLE) / fail |
| abc393_d (2108) | Codex / API | yes: the sliding window assumes one swap per missing 1 | **algorithm in words**: median of adjusted positions | 0.65 / 0.58 | yes / yes | pass / pass |
| arc195_a (2108) | Codex / API | yes: `count >= 2` counts matched elements, not matches | **algorithm in words**: earliest and latest greedy scans | 0.40 / 0.60 | no / yes | fail / fail 39/40 |
| arc195_a (2109) | Codex / API | yes (same) | **algorithm in words** (same) | 0.61 / 0.53 | yes / yes | pass / pass |
| abc390_f (2108) | Codex | yes: first/last occurrence instead of presence | **algorithm in words**: gap counting with inclusion–exclusion | 0.78 | no | fail 13/40 |
| abc395_f (2109) | Codex | yes: pair misread, plus `min(U+D)` not always attainable | local fix **plus** binary search with interval propagation | 0.85 | yes | pass |

**Findings.**

* **The frontier finds the actual fault: 16 of 16.** Every diagnosis names the defective line or construct and
  ties it to the failed case with concrete numbers. None claims more than the evidence shows, and the arc190_c and
  abc398_d diagnoses even flag the remaining complexity problem.
* **The diagnosis never contains a replacement program.** There are no code blocks and no multi-line code. Soft
  code flags (inline expressions such as `A[r][c] * (top + left)`) are allowed by the prompt.
* **Two kinds of prescription, with different results:**
  * **Local defect fixes** (indices, input pairing, `bisect`, a recurrence; 8 diagnoses including abc398_d) were
    applied in every case and fixed the failed public case in 8 of 8. Hidden passes followed in 4: abc390_c (two
    providers), abc395_f at 2108 and arc193_a. The rest (abc388_f, arc190_c, abc398_d ×2) still failed hidden on
    other cases or on time.
  * **Algorithm replacements in words** (abc393_d, arc195_a, abc390_f) work when Qwen can implement the described
    method (abc393_d at both providers, arc195_a at seed 2109). They fail when it cannot: abc390_f, and arc195_a at
    seed 2108, where the edit is large and the next program still fails the public case.
* **Qwen implements rather than copies.** The median share of the diagnosis's distinctive words that reappear in
  the code is 0–8%. The changes are structural: changed-line ratio 0.08–0.85, median about 0.5.
* **Diagnosis quality versus local capability.** Every failure after a diagnosis is a failure to *implement* a
  correct diagnosis (abc390_f, arc195_a at 2108) or a residual defect the diagnosis flagged but did not fully solve
  (complexity: abc398_d, arc190_c). None is caused by a wrong diagnosis.

**Implication for a refined prompt.**

* There is room to make the **local repair target** more explicit and shorter, so that edits stay small where the
  defect is local.
* There is risk in discouraging method changes, because 5 of the 9 hidden successes needed a new method
  (abc393_d ×2, arc195_a at 2109 ×2, abc395_f at 2109).
* `diagnosis-v2` therefore keeps the four v1 headings and the "no code" rule. It asks for:
  * the exact faulty expression, quoted;
  * the exact repair target;
  * the rule or invariant the fix must satisfy;
  * one hand-checked failing input.

  It allows method changes when "the cause requires more". Whether that is better is measured in §2, never assumed.

## 2. Diagnosis against interruption at 11 frozen trigger states (brief §8.2; `p4-eprobe`)

**Design.**

* **States:** every trigger state of passes 2 and 3: 5 development and 6 hard-cohort states.
* **Reproduction:** each state was re-entered by rerunning the original agent at the original seed. The trigger
  packet's candidate sha256 equalled the historical one in **11/11** neutral and **11/11** diagnosis-v2 runs, so
  every arm saw the identical failed program and public report.
* **Arms:**
  * **A:** the original continuation, without a message (historical);
  * **diagnosis-v1:** historical Codex;
  * **neutral:** a fixed, length-matched, content-free message (187 words, same `deliver-v1` wrapper). Pass-2
    states come from pass 3; pass-3 states are new;
  * **diagnosis-v2:** new, live isolated Codex.
* **What stays fixed:** budgets and session continuity are identical; only the delivered text differs.

| State (seed) | A (no message) | diagnosis-v1 | neutral | diagnosis-v2 |
| --- | --- | --- | --- | --- |
| abc390_c (2108) | ✓ | ✓ | ✓ | ✓ |
| abc393_d (2108) | ✗ 9 | **✓** | **✓** | **✓** |
| abc398_d (2108) | ✗ 36 | ✗ 36 | ✗ 36 | ✗ 36 |
| arc195_a (2108) | ✗ 39 | ✗ 39 | ✗ 3 | **✓** |
| arc195_a (2109) | ✓ | ✓ | ✗ 37 | ✗ 10 |
| abc390_f (2108) | ✗ 8 | ✗ 13 | ✗ 8 | ✗ 8 |
| abc395_f (2108) | ✓ | ✓ | **✗ 0** | ✓ |
| abc388_f (2109) | ✗ 21 | ✗ 38 | ✗ 0 | ✗ 38 |
| abc395_f (2109) | ✗ 34 | **✓** | ✗ 0 | ✗ 0 |
| arc190_c (2109) | ✗ 0 | ✗ 34 | ✗ 26 | ✗ 26 |
| arc193_a (2109) | ✗ 4 | **✓** | ✗ 0 | **✓** |
| **Hidden passes** | 3 | **6** | 2 | 5 |
| Public pass after the message | — | 9 | 4 | 8 |
| Harms (pass → fail against A) | — | 0 | **2** | 1 |

(Numbers are hidden cases passed out of 40.)

**Findings.**

* **On the hard states the diagnosis's content matters, not the interruption.** At the 6 new states the neutral
  message reaches **0** hidden passes. It is worse than no message: 0/40 on abc395_f at 2108, where A passes
  alone, and on abc388_f and arc193_a. Both diagnoses reach 2–3.
  * Pooled: diagnosis-v1 rescues 3 states A fails (abc393_d, abc395_f at 2109, arc193_a) and harms none. The
    neutral message rescues 1 (abc393_d) and harms 2.
  * This **reverses pass 3's tentative reading** ("the rescue is not the diagnosis's content", from 5 easier
    states). There, a neutral message reproduced the one development rescue (abc393_d). It still does, but on the
    harder states it does not.
* **The neutral message harms by derailing.** After it, the agent rewrote the program (changed-after in 11/11) but
  usually never got back to a public pass (4/11, against 9/11 for v1). An unexplained interruption at a failure
  invites a rewrite, not a repair.
* **diagnosis-v2 does not beat v1.**
  * It wins arc195_a at 2108, where its shorter "exact repair target" produced a correct fix and v1 did not.
  * It loses arc195_a at 2109 and abc395_f at 2109. Both of those needed a method change, which v1 described in
    words and v2's local-fix framing discouraged, as anticipated in §1.
  * Its diagnoses are shorter (125–164 words against 171–244) and just as fast (7–24 s).
  * On abc390_f the agent truncated three times right after the v2 message and ended without acting on it.
* **Single samples.** Codex diagnoses are not seeded. Each state has one v1 sample (historical) and one v2 sample,
  so a one-state difference between v1 and v2 is within sampling noise. The neutral-versus-diagnosis difference
  (2 against 5–6, with 2 harms) is the robust finding.

## 3. E under the improved shared agent (brief §8.3)

See `LOCAL_AGENT_EXPERIMENTS.md` §6 (batch `p4-stageD-de`: diagnosis-v1 under `l1-selfplan-v1`). The trigger rate
is reported separately from diagnosis quality there.

## 4. Decision

* **The pre-registered rule is not met:** v2 must beat both v1 and neutral by at least 2 states and harm no v1
  rescue. It reaches 5 against 6, and it loses one v1 rescue (abc395_f at 2109).
* **Primary E remains `diagnosis-v1` + `deliver-v1`:** one call at the first qualifying public failure, at most
  once per attempt, with the frontier wait excluded from the local clock.
* **The neutral-interruption control belongs in the final study.** It is the evidence that separates diagnosis
  content from interruption, and it costs no API money (`provider: fixed`). This is recommended as an optional
  control arm on a subset; it is a team decision.
* **diagnosis-v2** stays in the development archive as a documented alternative.
