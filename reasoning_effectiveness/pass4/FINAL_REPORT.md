# Pass 4 final report: agent optimization, condition validation, economics and handoff

**Branches.**

* `feat/csc2108-contract-diagnosis-pass2`: the development archive of passes 1–4.
* `feat/csc2108-final-agent`: the clean deliverable for Peter.

Every pass-4 result is **development evidence on consumed tasks**, not a holdout estimate. Selection rules were
committed before each stage ran (`PREREGISTRATION.md`).

## Executive summary

1. **The shared agent was artificially constrained in one specific way.**
   * Its protocol leaves no place to reason except inside the file being written. All 82 of 217 historical runs
     without a program ended on three consecutive 4,096-token cap hits, which is runaway deliberation inside an
     unclosed heredoc.
   * Time, context, observation size, request timeouts and the action and repair limits essentially never bound.
2. **Giving the same local model one bounded planning step outside the action protocol (`l1-selfplan-v1`)
   quadrupled A** on 8 development tasks: 1 → 4 at seed 2108, with 0 losses, 1.06× tokens and 1.09× time.
   * Raising the output allowance to 8K (`l3`) mostly bought more deliberation.
   * Native thinking at 8K (`l2`) cost twice as much and did worse.
   * State receipts (`l4`) eliminated every identical rewrite but changed no outcome.
   * A one-shot probe confirms the reading: Qwen alone solves 2 tasks that the original agent fails, and l1
     recovers both.
   * `STAGE-D`
3. **D-active works as a detector, not yet as a condition.** Harness-executed contract checks were correct 32/32,
   caught 20/27 known wrong programs offline, flagged a public-passing wrong program live, and solved one task.
   But D-active (3/8) did not beat the inputs-only control (3/8) or D-v1 (3/8). **D-v1 stays primary.**
4. **E's benefit is the diagnosis's content.** At 11 frozen trigger states:

   | Arm | Hidden passes |
   | --- | --- |
   | diagnosis-v1 | 6 |
   | a length-matched neutral message | 2 (and it harmed 2 states A solves alone) |
   | no message (A) | 3 |
   | the new diagnosis-v2 | 5 |

   This reverses pass 3's tentative reading. **diagnosis-v1 stays primary.**
5. **B is strong and cheap; C is cheaper but much weaker.** On the 12-task hard cohort:

   | | Success | API cost |
   | --- | --- | --- |
   | B (frontier-only) | 11/12 (Codex replay) | $0.043–0.096 per hard task (measured, n = 2) |
   | C (frontier plan) | 13/24 | ≈ $0.017 per one-off plan (modelled) |

   * Per success, C costs about $0.03 of API against B's $0.08–0.14, roughly 2.5–4.5 times less, plus about
     70 s of local GPU time per attempt.
   * C buys most of its value over A (2/24 → 13/24) for about a cent. The cheapest way to *solve* these tasks is
     still B.
6. **The deliverable.**
   * One shared agent and five conditions, with a stable per-attempt measurement record
     (`csc2108-run-measurement-v1`), sanitized fixtures, the handoff documents and 74 offline plus 6 Docker tests.
   * Paid API use this pass: `API`.

## 1. Shared agent

`BOTTLENECK_AUDIT.md` and `LOCAL_AGENT_EXPERIMENTS.md`. `STAGE-D-DETAIL`

## 2. Conditions

| Condition | Final version | Evidence this pass | Changed vs pass 3? |
| --- | --- | --- | --- |
| A | the shared agent, frozen first message | screening, stage D | `A-CHANGE` |
| B | API coder, gpt-6.2-sol, medium, 8,000 tokens, per-run cap 28 | 12 Codex + 2 API runs on hard tasks; audit | no (settings documented) |
| C | plan-v1 + inject-v1 | stage D (C under the candidate agent) | `C-CHANGE` |
| D | contract-v1 + inject-v1 (D-v1) | D-active study with two controls | no; D-active documented as an alternative |
| E | diagnosis-v1 + deliver-v1 | 11-state probe with a neutral control | no; diagnosis-v2 documented as an alternative |

## 3. Economics

See `COST_COMPARISON.md`.

**Measured API spending this pass** (ledger `reasoning-effectiveness-pass4/api-ledger.json`): `API-DETAIL`.

**What is not cost.** Codex-replay token counts (they include Codex's harness context) and Codex B success rates.
These are labelled replay everywhere and never pooled with the API.

## 4. Negative and corrective findings

* **Thinking mode at 8K is a clear negative:** 1/8, 2.1× tokens, 5 runs without any action.
* **A larger output cap is mostly more deliberation:** +1 task at 1.7× tokens.
* **Fixing identical rewrites (receipts) does not fix correctness:** the loops are a symptom, not a cause.
* **D-active did not beat its own inputs-only control.**
* **diagnosis-v2 did not beat diagnosis-v1.**
* **Corrections to earlier passes:**
  * aci-v2's repeat guard *did* remove duplicate assistant messages; the loops persisted because its notes were
    constant.
  * E's rescues are not explained by interruption; that holds on the 6 hard states, while the 5 easier states
    remain mixed.

## 5. Open decisions for the team

`OPEN`

## 6. Limitations

* 8 development tasks (plus 11 trigger states and 12 B tasks), one or two seeds; no confirmatory holdout. The
  only fresh, unreserved tasks left in the pinned shard are 8 of the hardest band (ABC G, ARC D/E), where local
  conditions rarely succeed. They were not spent.
* Codex replay is not the API. Single samples of frontier outputs per task or state.
* One machine (RTX 4080 SUPER). The macOS native path is still not validated with real inference.
