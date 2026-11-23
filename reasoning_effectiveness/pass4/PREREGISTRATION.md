# Pass 4 pre-registration: shared-agent screening (written before any pass-4 outcome)

Committed before batch `p4-screen-s2108` started. Later stages get their own pre-registration section,
appended (never edited) before they run.

## Cohort (development only, never a holdout)

8 consumed development tasks chosen to cover the failure types named in the brief. Labels come from LiveCodeBench;
the history comes from passes 1–3 (original agent, seed 2108 unless noted).

| Task | Label | Why it is included (history) |
| --- | --- | --- |
| abc400_b | easy | regression check: every condition passes |
| abc393_d | medium | wrong first program, failed local repair (A repair_limit 9/40; seed 2109 passes); C, D and E pass |
| arc195_a | medium | plausible wrong program 39/40; identical-rewrite loop; seed-dependent |
| arc192_a | medium | truncation at seed 2108, wrong program 39/40 at 2109; C passes, D wrong |
| abc398_d | hard | wrong program passing the public tests (36/40) in A, D and E; C passes |
| abc388_e | hard | no program (truncation); C and D-v1 pass |
| abc389_f | hard | no program in A, D and E at both seeds; C passes at both |
| abc397_f | hard | no program in A at both seeds; C fails at both |

The main 60 tasks, `test5` and the remaining `test6` tasks are not used.

## Arms (one mechanism each; all run Condition A, seed 2108)

| ID | Change against `frozen-v6` | Mechanism addressed |
| --- | --- | --- |
| `frozen-v6` | none (rerun of the historical baseline) | reference and determinism check |
| `l1-selfplan-v1` | one bounded local planning call (plan-v1 prompt, Qwen, frozen sampler, 4,096 tokens) before coding; its text is added to the first message; deadline moved back by its duration | algorithm deliberation forced into the heredoc |
| `l2-think-8k-v1` | thinking on, 8,192 output tokens, 32K context | same, via the model's native reasoning channel |
| `l3-out-8k-v1` | 8,192 output tokens, 32K context | 4,096-token cap truncating the first response |
| `l4-receipt-v1` | one-line state receipt in every observation (action count; changed/unchanged; version; diff size; syntax check inside the sandbox; already-tested status) | constant empty acknowledgement before identical rewrites |

## Measures

Hidden pass (primary); a program was produced; first valid action; first public test; truncated responses;
exact consecutive repeats; repairs; local tokens (input, output) and inference seconds; wall seconds; format errors.

## Selection rule (fixed now)

An arm becomes the **candidate** shared agent only if all of these hold against `frozen-v6` on the 8 tasks:

1. hidden passes: at least +2 net tasks, with no more than one task lost;
2. no-program runs: not more than `frozen-v6`;
3. it does not lose `abc400_b`;
4. local output tokens and wall time at most 2.0× `frozen-v6` in total; otherwise the trade-off is reported and the
   arm is not selected on this evidence alone.

If no arm qualifies, `frozen-v6` stays the primary agent. If two qualify, the one with more net passes is chosen
(ties: fewer local tokens). A candidate is then rerun at seed 2109 on the same 8 tasks against `frozen-v6`, and
tested with C, before any recommendation. Arms are never combined without a separate test of the combination. One
task flip never decides anything.

Infrastructure failures (judge or Docker errors, outer timeouts) are rerun under a new run ID and reported. Candidate
failures are never rerun.
