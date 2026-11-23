# Shared-agent experiments (pass 4, Phase II)

**Question.** Is the original frozen agent artificially weak? Four single-mechanism alternatives, each motivated by
`BOTTLENECK_AUDIT.md`, were screened against it on the same tasks and seed.

**Cohort.** 8 consumed development tasks (`PREREGISTRATION.md`): 1 easy, 3 medium, 4 hard. This is development
evidence, not a holdout.

**Design.**

* Condition A, seed 2108, all five configurations on every task, with arm order rotated per task.
* Selection rule fixed before any outcome.
* Tables come from `diagnostics/batch_table.py` and `diagnostics/screen_analysis.py`
  (`evidence/screen-s2108-table.json`, `evidence/screen-s2108-analysis.json`).

| ID | Change against `frozen-v6` (everything else identical) | Mechanism addressed |
| --- | --- | --- |
| `frozen-v6` | none (rerun of the historical baseline) | reference |
| `l1-selfplan-v1` | one bounded local planning call (teammates' plan-v1 prompt, Qwen, frozen sampler and seed, 4,096 tokens, no thinking) before the session; the plan is added to the first message; the coding deadline is moved back by the call's duration | deliberation forced into the heredoc (no place to reason outside an action) |
| `l2-think-8k-v1` | thinking on; 8,192 output tokens; 32K context | the same, via the model's native reasoning channel |
| `l3-out-8k-v1` | 8,192 output tokens; 32K context | the 4,096-token cap truncating the first response |
| `l4-receipt-v1` | a one-line harness receipt in every observation: action count and actions left; whether solution.py changed (version, diff size, syntax check in the sandbox); whether this exact version was already tested and with what result | constant empty acknowledgement before identical rewrites; no budget visibility |

**Determinism check.** The `frozen-v6` reruns reproduce the historical original-agent runs byte for byte: the same
submission sha256, action count and generated-token count on every task with a historical seed-2108 run. Historical
frozen results with identical artifacts can therefore stand in for reruns in the later stages, and are labelled
as such.

## 1. Screening results (seed 2108, condition A, 8 tasks × 5 configurations; 40 attempts, 0 infrastructure failures)

| Task | frozen-v6 | l1 self-plan | l2 thinking 8K | l3 output 8K | l4 receipts |
| --- | --- | --- | --- | --- | --- |
| abc400_b (easy) | ✓ | ✓ | ✓ | ✓ | ✓ |
| abc393_d | ✗ repair limit 9/40 | **✓** (3 actions) | no program | **✓** | ✗ repair limit |
| arc195_a | ✗ 39/40 | **✓** (3 actions) | no program | ✗ (identical to frozen) | ✗ repair limit |
| arc192_a | no program | ✗ action limit | no program | no program | no program |
| abc398_d | ✗ 36/40 (TLE) | **✓** (3 actions) | ✗ | ✗ | ✗ |
| abc388_e | no program | ✗ (3 actions) | ✗ (6 actions) | no program | no program |
| abc389_f | no program | no program | no program | no program | no program |
| abc397_f | no program | no program | no program | no program | no program |
| **Hidden passes** | **1** | **4** | 1 | 2 | 1 |
| Net vs frozen (gains/losses) | — | **+3 (3/0)** | 0 | +1 (1/0) | 0 |
| Runs without a program | 4 | **2** | 5 | 4 | 4 |
| First responses truncated | 6 | 4 | 5 | 6 | 6 |
| Truncated responses (all) | 17 | 10 | 17 | 15 | 17 |
| Exact consecutive repeats | 5 | 1 | 1 | 5 | **0** |
| Writes reproducing a failed candidate | 7 | 8 | 0 | 6 | **0** |
| Public tests run / reached a public pass | 12 / 3 | 14 / 5 | 4 / 3 | 11 / 4 | 12 / 2 |
| Local output tokens (incl. self-plan) | 77,008 | 81,681 (1.06×) | 163,566 (2.12×) | 133,555 (1.73×) | 76,488 |
| Local generation seconds | 730 | 784 | 1,567 | 1,276 | 727 |
| Wall seconds (sum) | 850 | 924 (1.09×) | 1,688 (1.98×) | 1,393 (1.64×) | 843 |
| Max prompt tokens | 4,804 | 14,352 | 2,225 | 7,088 | 3,711 |
| Selection rule | reference | **qualifies** | fails 1, 2, 4 | fails 1 | fails 1 |

All 40 attempts verified the 38 frozen files and the model digest, and every sampler option was verified on the wire.
There were no context-cap stops.

## 2. What each mechanism did

**L1, self-plan (qualifies).** The plan is the teammates' plan-v1 prompt answered by Qwen itself.

* **Effect.** It cut first-response truncation (6 → 4) and all truncation (17 → 10), and produced 3 hidden gains.
  In each gain the session was write, test, submit (3 actions), just as C sessions are when the plan is right.
* **The plan step deliberates too.** On 6 of 8 tasks the plan itself hit its 4,096-token cap (about 42 s), and
  was delivered with a "cut off" marker. Two of the three gains (abc398_d, arc195_a) came from truncated plans:
  the plan step gives the deliberation a place where truncation is harmless and its result survives into the
  session.
* **Where it does not help:** the two tasks where no configuration produces a program (abc389_f, abc397_f) still
  truncate in the session after a truncated plan. On arc192_a it produced a program but then looped (8 rewrites of
  a failed candidate, 20 actions).
* **Cost:** +4.7K output tokens and +74 s in total over 8 tasks. The plan's tokens stay in the context, so the
  largest prompt grew from 4.8K to 14.4K tokens (arc192_a, 22 calls). That is still below the 16K context, but a
  long session on a long statement could reach it.

**L2, thinking at 8K.** It is the expensive negative result the teammates' study predicted.

* In 5 of 8 tasks L2 never executed an action: its responses spent the 8,192-token allowance almost entirely
  on thinking (620K thinking characters in total). On abc393_d, for example, one response returned no valid
  command and two stopped at the cap with up to 26.7K characters of thinking.
* It solved only the easy task and cost 2.1× the tokens and 2.0× the time.
* The adapter works (§3 of the audit). The model's thinking simply does not converge within 8K on these tasks.

**L3, output 8K.** Mostly more deliberation, not more programs.

* 15 truncated responses, now at 8,192 tokens. The no-program count is unchanged (4), and 1.7× the tokens.
* It gained abc393_d. The two trajectories are token-identical until a repair response that frozen-v6 cut at
  4,096 tokens (twice); under 8K those responses completed.
* On arc195_a only the first response differs: it is truncated at 8,192 instead of 4,096 tokens. The rest of the
  trajectory, the repeat loop and the final submission (the same sha256) equal frozen's.
* This is the "a longer response that produces more comments" case the brief warns about. Per the brief, 12K was
  not tried, because 8K showed no broad benefit.

**L4, state receipts.** The mechanism works; the outcome does not change.

* Every exact repeat (5 → 0) and every rewrite of an already-failed candidate (7 → 0) disappeared. The receipt
  changes every turn and states whether the file changed and whether this version already failed, so the
  self-similar context of pass 3 §2 never forms.
* The freed actions did not produce correct programs: abc393_d and arc195_a ended at the repair limit with
  *different* wrong programs.
* This confirms pass 3's reading: the loops are a symptom of a missing algorithm, not the cause of failure. Fixing
  the interface defect is worth keeping as a reliability improvement, but on its own it is not a correctness
  intervention.

## 3. Interpretation for the research question (screening only)

* The original agent **is artificially constrained** in one specific way: it has nowhere to reason except inside
  the file it is writing. Giving the *same local model* one bounded reasoning step outside the action protocol
  roughly quadruples A on these 8 development tasks (1 → 4).
* Neither more output (L3) nor native thinking (L2) does the same, so the gain is not about token allowance. It is
  about **separating planning from acting**, which is exactly what C does with a frontier plan.
* This makes C's advantage partly an interface effect. Stage D tests whether C still adds value on top of l1.

## 5. Agent versus model: one-shot probe (Phase I §5.5; `diagnostics/oneshot_probe.py`)

**Design.** One direct Qwen call per task: no agent, tools or feedback, the frozen sampler and seed, 8,192 output
tokens and a 16K context. The program is the last closed `python` block, judged by the team judge. It is a
diagnostic, not a condition.

| Task | One-shot (tokens) | A frozen-v6 | A l1 | Reading |
| --- | --- | --- | --- | --- |
| abc400_b | ✓ (1,495) | ✓ | ✓ | easy |
| abc393_d | ✓ (2,310) | ✗ repair limit | ✓ | **the model knows a method; the original agent fails to express or repair it** |
| arc195_a | ✓ (8,158; 8 code blocks while deliberating) | ✗ 39/40 | ✓ | **the same** |
| abc398_d | no program (8,192 cap) | ✗ TLE | ✓ | the plan step finds the efficient method; free-form generation does not finish |
| abc388_e | no program (8,192 cap) | no program | ✗ | reasoning does not converge |
| abc389_f | no program (8,192 cap) | no program | no program | reasoning does not converge |
| abc397_f | no program (8,192 cap) | no program | no program | reasoning does not converge |
| arc192_a | no program (8,192 cap) | no program | ✗ | reasoning does not converge |
| **Hidden passes** | **3** | **1** | **4** | |

**Failure types on the 8 tasks.**

* **Interface failures** (the model can, the original agent does not): **2** (abc393_d, arc195_a). Both are fixed by
  l1.
* **Expression or efficiency within the interface:** 1 (abc398_d). The original agent's program is too slow; the
  self-planned session is not.
* **Capability or deliberation limits** (no method within 8K tokens, with or without the agent): **4**. Raising the
  output allowance (l3) or thinking (l2) does not help, and neither does any local configuration. These are the
  tasks where frontier reasoning (C, B) is needed.
* **Context or budget exhaustion:** **0** (no context stops; no deadlines).

This agrees with the teammates' earlier one-shot pilot (one-shot 4/6 against a shortened agent's 3/6). The original
agent interface costs Qwen tasks it can solve, and l1 recovers them.
