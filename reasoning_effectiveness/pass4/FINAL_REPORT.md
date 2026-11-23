# Pass 4 final report: agent optimization, condition validation, economics and handoff

**Branches.**

* `feat/csc2108-contract-diagnosis-pass2`: the development archive of passes 1–4.
* `feat/csc2108-final-agent`: the clean deliverable for Peter (`HANDOFF_TO_PETER.md`).

Every pass-4 result is **development evidence on consumed tasks**: 8 development tasks, 11 frozen trigger states
and the 12-task pass-3 hard cohort. Nothing here is a holdout estimate. Every selection rule was committed before
its stage ran (`PREREGISTRATION.md`).

## Executive summary

1. **The shared agent is artificially constrained in one specific way.**
   * Its protocol leaves no place to reason except inside the file being written. All 82 of 217 historical runs
     without a program ended on three consecutive 4,096-token cap hits, which is deliberation inside an unclosed
     heredoc.
   * Time, request timeouts, observation size and the action and repair limits essentially never bind.
   * The 16K context bound in 4 of the 132 pass-4 local-model attempts (context overflow, below).
2. **A local planning step helps A, but it was not adopted.**
   * Giving the same model one bounded planning step outside the action protocol (`l1-selfplan-v1`) raised A from
     1/8 to 4/8 in screening, and from 4/16 to 7/16 over two seeds. It also raised D-v1 (3 → 4/8) and E (2 → 4/8).
   * It lowered C from 14/16 to 12/16. At the second seed A was level, and in 3 long C sessions the extra context
     overflowed 16K. Under the pre-registered rule it is **not** adopted: **`frozen-v6` stays the primary shared
     agent**.
   * **C's advantage over A halves under l1** (+10 to +5 of 16 pairs). Part of C's measured benefit compensates
     for the original interface; the rest is real frontier-plan value.
   * The other three changes do not help:
     * an 8K output allowance mostly buys more deliberation (+1 task at 1.7× the tokens);
     * thinking at 8K is a clear negative (1/8, 2.1× the tokens);
     * state receipts remove every identical rewrite (5 → 0) but change no outcome.
   * A one-shot probe separates the failure types: Qwen alone solves 2 tasks the original agent fails (interface
     failures), and 4 tasks are beyond it with or without the agent.
3. **D: contract checks work as a detector, but D-active does not beat its controls.**
   * Harness-executed contract checks (D-active) had correct proposed outputs 32/32. Offline they caught 20/27
     known wrong programs; live they flagged a public-passing wrong program and solved one task no other arm did.
   * D-active (3/8) did not beat its inputs-only control (3/8) or D-v1 (3/8). **D-v1 stays primary**, and D-active
     is a documented, tested alternative.
4. **E's benefit is the diagnosis's content, not the interruption.** At 11 frozen trigger states (hidden passes):

   | Arm | Passes |
   | --- | --- |
   | diagnosis-v1 | 6 |
   | a length-matched neutral message | 2 (it harmed 2 states that A solves alone) |
   | no message (A) | 3 |
   | the new diagnosis-v2 | 5 |

   This reverses pass 3's tentative reading. **diagnosis-v1 stays primary.** E's reach depends on the agent: under
   l1 it triggered 1/8 times instead of 3/8.
5. **B against C: C is cheaper in API dollars per success, but B is far stronger.** On the 12-task hard cohort:

   | | Success | API cost |
   | --- | --- | --- |
   | B (frontier-only) | 11/12 (Codex replay) | $0.043 and $0.096 per hard task (measured, n = 2) |
   | C | 13/24 | about $0.017 per one-off plan (the measured API plan was $0.0168) |

   * Per success, C costs about $0.03 of API against B's $0.08–0.14, plus about 70 s of local GPU time per
     attempt.
   * C turns a 2/24 local agent into 13/24 for about two cents. The cheapest way to *solve* these tasks is still B.
6. **Deliverable.** One shared agent and five conditions on a clean branch, with:
   * a stable per-attempt measurement record (`csc2108-run-measurement-v1`);
   * 12 sanitized fixtures and the handoff documents;
   * 71 offline tests, 8 Docker integration tests and the `local_agent` portable suite, all passing.

   Paid API use: **14 requests, $0.175** (standard prices; $1.05 at the conservative bound), against the $10 and
   20-request ceilings. There were no retries.

## 1. Shared agent (P0)

* **Audit** (`BOTTLENECK_AUDIT.md`):

  | Bottleneck | Status |
  | --- | --- |
  | The protocol forces all reasoning into the action | binding; the root cause of the no-program runs |
  | 4,096-token output cap | binding (322 cap stops in 217 runs) |
  | 16K context | rarely binding (4 overflow runs in pass 4) |
  | Empty acknowledgement after writes | precursor of identical rewrites |
  | Time, action and repair limits; request timeout; observation clip; container lifetimes | not binding |

  The thinking and LiteLLM paths were verified on the wire.
* **Screening:** 8 tasks × 5 configurations; only l1 qualified (`LOCAL_AGENT_EXPERIMENTS.md` §1–3).
* **Confirmation** (stage D, both seeds, A and C): l1 rejected under the rule (§6). Determinism was verified (frozen
  reruns byte-identical).
* **Final:** `frozen-v6` (`44136fa3…`); historical comparability preserved.

## 2. Conditions

| Condition | Final version | Evidence this pass | Changed vs pass 3? |
| --- | --- | --- | --- |
| A | `frozen-v6`, frozen first message | screening, stage D, one-shot probe | no |
| B | API coder: gpt-6.2-sol, effort medium, 8,000 tokens, per-run cap 28 | 12 Codex and 2 API hard-task runs (one natural self-repair); audit | no (settings documented) |
| C | plan-v1 + inject-v1 | 14/16 on development tasks; end-to-end API run (arc192_a, pass) | no |
| D | contract-v1 + inject-v1 (D-v1) | D-active study with passive and inputs-only controls | no; D-active documented |
| E | diagnosis-v1 + deliver-v1 | 11-state probe with a neutral control; live API run (abc393_d, triggered, repaired, pass) | no; diagnosis-v2 documented |

Hashes and full specifications: `CONDITION_FINALIZATION.md`; on the final branch, `CONDITIONS.md` and
`FINALIZATION_MANIFEST.json`.

## 3. Economics (`COST_COMPARISON.md`)

* **Measured API spending this pass** (14 requests): 11 B coder turns ($0.140), 1 plan ($0.0168), 1 contract
  ($0.0113), 1 diagnosis ($0.0070).
* **Local compute:**
  * measured GPU-busy time is about 130 s per A attempt and about 70 s per C attempt (hard cohort);
  * modelled electricity, at 350 W and $0.15/kWh (assumptions), is under $0.002 per attempt.
* **What is not cost:** Codex-replay token counts include its harness context. Codex B success rates are labelled
  replay and never pooled with the API.
* **Final-benchmark budget implication** (updating `pass3/FINAL_BENCHMARK_OPTIONS.md`): hard tasks cost B about
  $0.04–0.10 per attempt, against about $0.01 on easier ones. That is consistent with pass 3's estimate of $14–42 of
  B spending for the 90-task design with 3 B seeds. Set the ledger ceiling with margin.

## 4. Negative and corrective findings

* Thinking at 8K, an 8K output cap and state receipts do not improve correctness.
* D-active does not beat its inputs-only control; diagnosis-v2 does not beat diagnosis-v1.
* Under l1, C gets worse and E triggers less.
* **Corrections to earlier passes:**
  * aci-v2's repeat guard *did* remove duplicate assistant messages; the loops persisted because its notes were
    constant.
  * E's rescues are not explained by interruption on the hard states.
  * "Context never binds" holds for passes 1–3 only.
* **A runner limitation:** a context overflow surfaces as `infra_error`. It is deterministic and must be counted as
  a failure. The measurement record now flags it (`correctness.context_overflow`).

## 5. Open decisions for the team (before the final freeze)

1. **Shared agent:**
   * keep `frozen-v6` (recommended on this evidence); or
   * adopt `l1-selfplan-v1` with a validated larger context, keeping a `frozen-v6` A arm to measure the interface
     effect on the holdout.

   This is a research-scope decision. l1 makes A a much stronger baseline and halves C's measured advantage.
2. **D:** D-v1 (recommended), or D-active as a labelled variant run with its inputs-only control.
3. **Controls in the final study (optional):**
   * E with the neutral message (`provider: fixed`; no API cost);
   * D's inputs-only arm, if D-active is run.
4. **Context-overflow policy:** count it as a failed attempt (recommended).
5. **Ledger ceilings and B's per-run cap** for the final run.
6. **Task pool and the judge items** listed in pass 3: arc195_c, abc395_a, the `test5` review.

## 6. Limitations

* **Small samples:** 8 development tasks, one or two seeds, single frontier samples per task or state; no
  confirmatory holdout. The only fresh, unreserved tasks left in the pinned shard are 8 of the hardest band
  (ABC G, ARC D/E), where local conditions rarely succeed, so they were not spent. `test5` stays reserved for the
  final benchmark.
* **B's API cost on hard tasks:** measured on 2 runs only.
* **One machine** (RTX 4080 SUPER). The native macOS inference path is still not validated.
