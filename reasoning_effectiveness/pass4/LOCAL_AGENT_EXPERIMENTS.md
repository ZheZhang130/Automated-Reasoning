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
