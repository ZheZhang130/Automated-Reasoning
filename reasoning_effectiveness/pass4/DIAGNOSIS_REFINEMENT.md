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
