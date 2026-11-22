# Condition D research: contract-v1, v2 and the paper-grounded contract-v3

**Bottom line.** Contract-v3 is a better *specification* than v1: its checks are precise, correct and
discriminating. It is **not** a better *intervention* for this local agent. On 8 development tasks it solved
3 (pass-1 D-v1: 4; A: 3), and the frozen validation cohort shows the same pattern (§6).

The reason is not contract content:

* **Truncation:** 4 of the 5 development failures happen before any program exists. Qwen brainstorms inside
  the file and hits the 4,096-token cap; that is an algorithm-discovery problem.
* **Rewrite loop:** the fifth is the frozen agent's identical-rewrite loop, after both the contract and the
  public test had exposed the bug.
* **No self-checks:** Qwen ran **0** contract checks in every D run of both passes.

**Recommendation.** Keep **contract-v1 + inject-v1** as Condition D for the benchmark (the control).
Contract-v3 stays experimental. Its K-checks are a useful *measurement instrument*, and the natural next
intervention is running contract checks automatically, which must be a shared-agent change (§8).

## 1. What was wrong with contract-v1 and contract-v2 (pass-1 artifacts and trajectories)

| Hypothesis from the brief | Evidence | Verdict |
| --- | --- | --- |
| Restated requirements rather than making them more precise | arc192_a v1: POST-1..3 paraphrase the operation rules and the Yes/No output | **Yes** for v1 |
| Postconditions too general to discriminate | v1 suggestions are prose ("Check that `0 0 0` yields `No`"), mostly samples and trivial boundaries; 0 of 6 v1 artifacts have machine-checkable checks | **Yes** for v1 |
| Useful tests, but the local model did not use them | v2's arc192_a checks were 6/6 correct and killed 7/7 natural mutants, but Qwen never ran them: **0** custom-input runs in all 117 pass-1 attempts | **Yes** for v2 |
| Too many conditions / too verbose | v1 has 275–330 words. Long plans did not hurt C (up to 629 words), and there were no prompt overflows | **No** evidence |
| No clear link between behavior and checks | v1 suggestions cite PRE/POST IDs but carry no expected output for most | Partly |
| Local agent misunderstood which properties were essential | abc393_d: A modelled arbitrary swaps; D-v1 (API) stressed adjacency and fixed it | Occurs, but rarely |
| Accurate but not actionable | Contracts state what is correct but not how; on algorithmic tasks Qwen still brainstorms in the file | **Yes** |
| Primary difficulty is algorithm discovery | D truncated (0 actions, 3 format errors) on arc192_a 3/4, arc195_a 2/3, abc388_g and abc391_e | **Yes, dominant** |

## 2. Design of contract-v3 (`guidance.CONTRACT_V3`, `inject-v3-contract`)

| Element | Source | Text in the prompt |
| --- | --- | --- |
| Postconditions as precise input–output relations (equality, bound, ∀-property, if-then), not story retelling | Endres Table 3 (p. 12): relational properties kill 82–89% of natural bugs, type/format checks 14% | "each a precise relation between the input and the output …" |
| Several *simple*, individually checkable properties (≤ 6) | Endres §3.2.1 (p. 9): simple postconditions are significantly more often correct | "Keep each property simple and individually checkable" |
| Most-violated requirements first: misread rule, off-by-one, ties, duplicates, order, minimum and all-equal inputs, exactness | Endres bug-completeness against *natural* mutants (§2.1.2, p. 5); Tufano ContractCoverage: catching the *violated* contract matters (p. 2, 6) | "List first the properties a plausible but wrong program is most likely to violate …" |
| Acceptance property for multi-answer outputs | Endres p. 17: Boolean postconditions accept all valid outputs | "If several outputs are acceptable, state what makes an output acceptable" |
| K-1..K-4 linked to POST IDs, each naming the *misreading* it exposes, with exact stdin and hand-derived stdout | Tufano §2 (p. 2–3): condition-linked test suggestions; Endres discrimination | "the misreading … it exposes … exact stdin … exact expected stdout" |
| PRE/POST/unspecified structure; everything Unverified | Tufano §2; proposal | five teammate headings kept (replay compatibility) |
| No algorithm, data structure, complexity or approach hints; ≤ 350 words | Proposal ("what … rather than how") | explicit |

The injection (`inject-v3-contract`) is `inject-v1` plus one sentence. It says the postconditions list the
most commonly violated requirements first, and that a K-check can be run as its own command
(`printf 'INPUT LINES' | python /workspace/solution.py`). D gets no extra tool, action, file or time.

Example: an abc393_d excerpt from the Codex-authored artifact. It contains public-statement material only.

> **POST-1 (Unverified)** — Every sequence of swaps of adjacent characters that leaves the `1`s in a single
> contiguous block uses at least the reported number of swaps.
> **POST-2 (Unverified)** — Some sequence of exactly the reported number of adjacent swaps leaves the `1`s in
> a single contiguous block anywhere in the string. …
> **K-1** (POST-1, POST-2, POST-4) — *Treating a swap between arbitrary positions as one operation.*
> stdin `5 / 10001` → expected `3`.

## 3. Semantic correctness and discriminative power (Endres-style)

`diagnostics/contract_checks.py` runs inside a network-less, read-only container:

* **Reference:** a pass-1 submission that passed all 40 hidden cases.
* **Natural mutants:** distinct pass-1 submissions that failed hidden cases.
* **A check is correct** if the reference's output equals its expected output.
* **A correct check kills a mutant** if the mutant's output differs.

| Contract | Machine-checkable checks | Correct | Mutants killed |
| --- | --- | --- | --- |
| v1 (6 Codex + 5 API artifacts in pass 1) | none (prose) | — | — |
| v2 (4 artifacts) | 3 parsed (18 checks) | arc192_a 6/6 | arc192_a 7/7 |
| **v3 (8 dev artifacts)** | **32** | **32/32** (7 tasks with a reference) | **14/15** (arc192_a 6/7, arc195_a 5/5, abc393_d 2/2, abc394_c 1/1) |

Every validation-cohort v3 artifact was also format-valid (5/5), at 235–318 words. Those tasks have no
reference programs, so their checks cannot be scored the same way.

**Limits of this assessment:**

* a single reference program per task;
* 0–7 mutants per task, a far smaller pool than Endres's;
* correctness is checked against one passing program, not proved;
* a correctly generated contract does not establish program correctness.

## 4. Does Qwen use the contract?

* **Self-checks: never.** There are 0 custom-input runs in every pass-2 D run (dev and validation; see
  `pass2-tables.md`), and 0 in pass 1. With contract-v3 too, Qwen's loop is write → `python -I
  /public/check.py` → submit or rewrite. The frozen system prompt says to submit "once your source is saved
  and you have tested it", and the public test satisfies that.
* **Prevention, measured by running each final program on its task's verified K-checks**
  (`analysis-kcheck-programs.json`):

  | Program | K-checks satisfied |
  | --- | --- |
  | D-v3, when a program existed | abc390_c 4/4, abc391_a 4/4, abc393_d 4/4, abc394_c **3/4** (its failure) |
  | Wrong programs from other conditions | A abc393_d 2/4, D-v1 arc192_a 2/4, C-API arc192_a 2/4, A and E arc195_a 3/4 |
  | Correct programs | 4/4 |

  So the K-checks **would** expose most wrong programs if they were executed. D-v3's own abc394_c failure
  is one of them: K-1 `WWWA → ACCC` captures the cascade bug.
* **Interpretation:** on abc393_d, every contract (v1-API, v1-Codex, v3) fixes A's misread of "adjacent
  swaps" (A 9/40 → D 40/40). The behavioral content does reach Qwen when the bottleneck is a requirement.

## 5. Controlled development comparison (seed 2108, same frozen agent; pass-1 references verified token-identical)

Cells show the hidden result, then format errors and actions.

| Task | A | C plan-v1 | D-v1 (pass 1) | D-v1 Codex (pass 2) | **D-v3 Codex** | D-v3 failure mode |
| --- | --- | --- | --- | --- | --- | --- |
| arc192_a | ✗ no program | ✓ 40/40 | ✗ 20/40 (Codex) | — | ✗ no program | truncation (3 × 4,096 tokens) |
| arc195_a | ✗ 39/40 | ✓ 40/40 | ✗ no program (Codex) | — | ✗ no program | truncation |
| abc393_d | ✗ 9/40 | ✓ 40/40 | ✓ 40/40 (API) | ✓ 40/40 | **✓ 40/40** | — |
| abc394_c | ✓ 40/40 | ✓ 40/40 | ✓ 40/40 (Codex) | — | ✗ 39/40 (20 act) | identical-rewrite loop after public WA on `WWA` |
| abc390_c | ✓ | ✓ | ✓ (Codex) | — | ✓ | — |
| abc388_g | ✗ no program | ✓ | ✗ no program (Codex) | — | ✗ no program | truncation |
| abc391_e | ✗ no program | ✗ 5/40 | ✗ no program (API) | ✗ no program | ✗ no program | truncation |
| abc391_a | ✓ | ✓ | ✓ (Codex) | — | ✓ | — |
| **Total** | 3/8 | 7/8 | 4/8 | 1/2 | **3/8** | |

**Hypothesis test for v3** (D-v3 ≥ D-v1 with no new delivery failures): **not met**. There is one new
failure (abc394_c, caused by the agent loop), and arc192_a moved from a plausible-wrong 20/40 to no program.
Both changes are within the variance of a small prompt perturbation on a near-deterministic sampler. I made
**no further contract versions**: no contract content addresses truncation or the rewrite loop, so more
prompt search would have been unguided.

## 6. Frozen validation cohort

*(Filled in after the 25-run validation cohort; see `FINAL_REPORT.md` and `analysis/pass2-tables.md`.)*

## 7. Failed approaches and limitations

* contract-v2 (pass 1): correct checks plus "run them before submitting" were never run.
* contract-v3: better checks and a prioritized layout, still never run, and no hidden-pass gain.
* Small n: 8 development tasks and 5 validation tasks, one seed. The A/D comparison is paired and
  deterministic, but D-v3 differs from D-v1 in *text*, which can flip a near-deterministic first attempt
  either way (abc394_c, arc192_a).
* Provider: all v3 artifacts are Codex-authored replay; no direct-API v3 was run (budget reserved for E and B).

## 8. Recommendation and what would plausibly help D

1. **Benchmark D with contract-v1 + inject-v1** (unchanged control); report v3 as a negative pass-2 result.
2. If contracts are to matter on this agent, the checks must be *executed*, not offered. The clean design is a
   **shared verification intervention**: the harness also runs a fixed set of extra public checks for every
   condition. For D, those checks would come from the contract; the analogous source for A, C and E would
   have to be defined. That is a new condition or ACI change, not D-v3, and it must be applied and labelled
   consistently.
3. D's ceiling on this agent is set by truncation (in-file brainstorming). Anything that fixes truncation is
   an agent change for **all** conditions (pass-1 aci-v2 was not promoted), or it is C's job: supplying the
   method.
