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

## Stage C pre-registration: D-active and the E probe (written before either batch ran)

Both use the original agent `frozen-v6` and seed 2108 (E states: their original seeds), so they do not depend
on the screening outcome.

**D-active** (`p4-dactive-s2108`, 8 development tasks, one Codex contract-v3 artifact per task, no regeneration):

| Arm | First message | Harness-run checks |
| --- | --- | --- |
| `v3passive` | contract-v3 via `inject-v3-contract` (pass-2 framing) | none |
| `active` | contract-v3 via `inject-active-v1` | K-checks run on the judged candidate at every public test; proposed outputs shown as unverified |
| `inputs` (control) | A's frozen `{{task}}` (no contract text) | the same K-check inputs, own outputs only, no expected outputs |

Historical A and D-v1 results at seed 2108 serve as further references. Check correctness is labelled offline
against reference programs that passed all 40 hidden cases (development analysis only, never shown to the model).

D-active is recommended over D-v1 only if it gains at least +2 net hidden passes over **both** `v3passive` and
`inputs` on the 8 tasks, loses no task that `v3passive` passes, and its wrongly proposed outputs (if any) mislead no
correct program into a wrong one. Otherwise D-v1 stays the primary D and D-active is reported as an alternative.

**E probe** (`p4-eprobe`): the 11 frozen trigger states of passes 2 and 3. At each state the agent is reproduced
exactly up to the trigger (same seed and agent) and then receives one of:
the original continuation (historical A), the historical diagnosis-v1, a length-matched neutral message (pass-2
states: pass 3; pass-3 states: this batch), or diagnosis-v2 (this batch, live Codex). A state counts only if
the packet's candidate hash equals the historical one.

diagnosis-v2 replaces diagnosis-v1 only if, on the reproduced states, it reaches more hidden passes than **both**
diagnosis-v1 and the neutral message, by at least 2 states, and harms no state that v1 rescues. A diagnosis benefit
is claimed only where the neutral message does not achieve the same.

## Screening outcome and stage D pre-registration (written after screening, before stage D ran)

**Screening result.** `l1-selfplan-v1` is the only configuration meeting all four criteria: 4/8 against 1/8, +3
net (abc393_d, abc398_d, arc195_a), 0 losses, 2 no-program runs against 4, and 1.06× output tokens and 1.09× wall
time. `l2`, `l3` and `l4` do not qualify. It becomes the **candidate**.

**Stage D** (`p4-stageD-agent`, 8 development tasks):

* A-l1 at seed 2109.
* C-l1 at seeds 2108 and 2109.
* The missing frozen cells: A-frozen at 2109 for abc398_d and abc388_e; C-frozen at 2109 for abc393_d, abc398_d
  and abc388_e.
* Two fresh C-frozen determinism spot checks at 2108 (abc389_f, arc192_a).

Every other frozen cell is a historical run with the identical artifact; the frozen agent was verified to
reproduce historical runs byte for byte.

**`l1-selfplan-v1` is recommended as the primary shared agent only if all of these hold:**

1. **Seed 2109, A:** l1 net ≥ +1 over frozen, with at most 1 loss (the direction replicates).
2. **Both seeds pooled (16 A pairs):** net ≥ +3, and no more no-program runs than frozen.
3. **C (16 pairs):** C-l1 net ≥ −1 against C-frozen (the improved agent does not materially harm the strongest
   guided condition).
4. **Cost (pooled A):** local output tokens and wall time at most 1.5× frozen.

**Otherwise** `frozen-v6` remains primary and l1 is documented as the alternative. Either way, adopting l1 changes
the shared agent for every condition. It breaks historical comparability with passes 1–3 and is flagged for team
approval.
