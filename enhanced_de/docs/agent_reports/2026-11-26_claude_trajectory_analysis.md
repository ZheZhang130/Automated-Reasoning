> Independent read-only trajectory analysis by a Claude Opus 5.5 subagent, continuation session, 2026-11-26 (phases 1A-1C; phase 1C was incomplete and unscored at the time).

# Trajectory analysis: enhanced D/E v2 (phases 1a, 1b, 1c)

Sources: trajectories, raw `ollama-responses.json` (includes cap-truncated replies) and `eval/`. A = baseline hidden score. Every phase-1a gated or reviewed program is byte-identical to A's submission.

Phase 1c snapshot: 12 clate, 12 diag and 3 neutral runs complete; no `eval/`, so public results only.

Key: TF targeted fix; RW rewrite; LOOP identical response/program ≥3×; TR cut at the 4,096 cap inside the heredoc; RFE RepeatedFormatError; ctx = 16,384-token context full.

## Q1. Responses after a D2 or E2-review counterexample

The 25 delivered D2 runs collapse to 18 distinct trajectories. abc390_d, abc394_f and abc400_c@2108 are byte-identical across all three arms, and abc400_c@2109 is identical for oracle and property. D2's "3 rescues" are therefore **1**.

| Run (arms) | After delivery | Class | len | Hidden (A) |
|---|---|---|---|---|
| abc387_c O | One RW without prose, keeps `range(1, m)`; same write ×17 | RW→LOOP | 0 | 27 (27) |
| abc387_c P | Same pattern | RW→LOOP | 0 | 27 |
| abc390_d SOP | Gate shows `RE: ''`; 1-line edits, loop | LOOP | 0 | 38 (38) |
| abc390_e O | Fixes the WA, adds an RE on a large input; "display issue in the test harness", submits | RW→ignored | 0 | 25 (24) |
| abc390_e P | Same, until the action limit | RW | 0 | 25 |
| abc394_e S | Unchanged rewrite, TR, 4-line edit, loop, ctx RFE | LOOP | 1+3ctx | 25 (17) |
| abc394_e O | Same pattern | LOOP | 1+3ctx | 17 |
| abc394_e P | TR, then the gated program rewritten unchanged ×8 | LOOP | 1 | 17 |
| abc394_f SOP | Fixes the TLE, gate passes; hidden WA untouched | TF | 0 | 38 (38) |
| abc398_g O/P | RW, then identical writes (O runs `echo "2 0"` 6× and sees `Takahashi`) | LOOP | 1/0 | 38 (38) |
| **abc400_c@2108 SOP** | "too slow…b can go up to 10^9"; two reasoned rewrites to O(log N) | **TF** | 0 | **40 (36)** |
| abc400_c@2109 S/OP | TR, unchanged slow rewrite, 3 RWs that are still slow | RW | 1 | 36–37 (36) |
| arc194_d O | RW, TR, identical writes, ctx RFE | LOOP | 1+3ctx | 17 (22)↓ |
| arc194_d P | 2 TR, then the gated program unchanged ×8 | LOOP | 2 | 22 |
| arc195_b O | 1-line edit, then 3 TR → RFE | TR | 3 | 36 (36) |
| arc195_b P | Loop; "POST-5 seems to be a false alarm from the test harness display", submits | LOOP→ignored | 0 | 36 |
| **Review abc387_c@2108** | Applies the given two-line fix and checks C-1 and C-2 itself | **TF** | 0 | **40 (27)** |
| Review abc390_e | Knapsack RW; 1/2 three times, then 2/2 | RW | 0 | 25 (24) |
| Review abc394_e, abc394_f, abc398_g, arc194_d | 3 TR → RFE (all four directions were new algorithms) | TR | 3 each | = A |
| Review abc400_c@2108 | Ignores the formula, writes an O(√N) loop; self-test hangs → CommandExecutionError | RW | 0 | 36 (36) |
| **Review abc400_c@2109** | Implements the given formula, checks it with a python one-liner | **TF** | 0 | **40 (36)** |
| Review arc195_b | Two RWs | RW | 0 | 31 (36)↓ |

**Tallies.** D2 (18 distinct trajectories): 2 targeted fixes (only one also fixed the hidden failure), 11 loops, 4 rewrites without a fix, 1 truncation death. E2-review (9 runs): 2 targeted fixes, 4 RFE deaths, 3 rewrites (1 regression).

**Why only abc400_c@2108 for D2.**
- A TLE on N≈10^18 explains itself (a sublinear count is needed). A WA must be localized first; here the agent wrote prose-free rewrites and almost never ran the counterexample.
- At 2108 the gate fired at action 6 and the first program already summed `isqrt(N // 2^k)`. At 2109 it fired at action 12, after long debug output; the reply hit the cap, then the slow program was rewritten unchanged.

**Content vs capacity.** On abc387_c, D2-oracle and E2-review show the same counterexample (`10 10` → 1, got 9):
- D2 shows bare I/O and the agent loops.
- E2-review adds "The shorter-length loop starts at `1`…" plus the repair, and the agent fixes it.

So for local bugs, the content (fault localization) is the bottleneck. But E2-review's rich content still failed in 7 of 9 runs. Every algorithmic direction (tree DP, pair-BFS, game parity) led to truncation or regression, and both rescues were changes of a few lines or one formula. For algorithmic defects, repair capacity is the bottleneck.

## Q2. E2-strict (12 runs, all delivered)

| Run | Mode | Followed? | After delivery | len | Pub | Hidden E2/A/E-v1 |
|---|---|---|---|---|---|---|
| abc387_c | LOCAL | Partly (wrong formulas) | RW, then 11 identical writes, no test | 0 | 0/3 | 2/0/5 |
| abc389_d | LOCAL | **Ignored**: code-identical; keeps the flagged `count += max_odd` | TR, 13 identical writes, ctx RFE | 1+3ctx | 0/3 | 0/0/32 |
| abc399_e | LOCAL | Over-applied (485-line RW) | RWs, then loop ×6 | 1 | 3/4 | 38/35/36 |
| arc191_a | LOCAL | **Ignored**: code-identical | 16 identical writes, never tested | 0 | 2/3 | 23/23/26 |
| abc390_e | METHOD | Yes | Write, pass | 0 | 2/2 | 35/18/38 |
| abc394_e | METHOD | **No**: applied the rejected local fix | TR, write, pass | 1 | 2/2 | 25/17/17 |
| abc397_b | METHOD | Yes, wrong greedy | 1/3, then 10 identical writes | 0 | 1/3 | 16/9/8 |
| abc398_g | METHOD | Yes | Write, pass | 0 | 3/3 | 38/34/34 |
| abc400_c | METHOD | Yes (literal formula) | Write, pass | 0 | 3/3 | **40**/36/36 |
| arc191_d | METHOD | **No**: patched the public case (`print(2)` → `print(3)`) | 13 identical writes, never tested | 0 | 1/3 | 32/17/34 |
| arc194_c | METHOD | Yes | 2 TR, write, pass | 2 | 3/3 | 39/24/14 |
| arc194_d | METHOD | Yes, buggy | TR, 2 RWs, loop ×7 | 1 | 1/2 | 15/22/22 |

- **METHOD-CHANGE (8 runs):** followed in 5, partly in 1, not in 2. Cap truncation in 3 of 8 (none fatal); a repeat loop in 3 of 8; only 3 of 8 were clean.
- **LOCAL-FIX (4 runs) did worse:** all 4 looped and 2 re-emitted the diagnosed program unchanged. With full-file heredocs, a "local" edit means re-emitting the program, and the agent re-emits its old one.
- **Partial credit:** compared with A, hidden counts rose in 8 of the 11 failed runs (total 303 vs 235). Compared with E-v1 it is 6 better and 6 worse (303 vs 302), plus one extra full pass.
- Two of the largest gains came from not following the mode (arc191_d +15, abc394_e +8). States were selected on E-v1 failure (regression to the mean); one seed.

## Q3. Stall arms (cell: post-delivery behavior; length hits after delivery)

| State | C-late | Diag | Neutral |
|---|---|---|---|
| abc387_f | 0/3 ×4, repair limit; 0 | TR → RFE; 1 | – |
| abc390_d | 3/3 ✓; 0 | 20 combined write+test rejected; 0 | TR → RFE; 1 |
| abc390_e | 1/2 ×5, action limit; 0 | 20 combined rejected; 0 | – |
| abc390_g | 0/3 ×5, 9 identical writes; 0 | TR → RFE; 1 | – |
| abc391_d | TR → RFE; 1 | TR → RFE; 1 | TR → RFE; 1 |
| abc394_e | 17 combined rejected, ctx RFE; 3ctx | TR → RFE; 1 | – |
| abc394_f | 3/3 ✓; 0 | TR → RFE; 1 | – |
| abc400_d | 4/4 ✓; 0 | 20 combined rejected; 0 | TR → RFE; 1 |
| arc192_e | 0/3, 15 identical writes; 0 | TR → RFE; 1 | – |
| arc194_a | 3/3 ✓; 0 | 3/3 ✓; 0 | running |
| arc195_b | 3/3 ✓ (third try); 0 | 20 combined rejected; 0 | – |
| arc195_e | 0/3 ×10, 1 TR; 1 | TR → RFE; 1 | – |

✓ = public pass and submit; no hidden scores exist for phase 1c.

| Arm | Program after delivery | Length hits after | Public pass |
|---|---|---|---|
| C-late | 11/12 | 5 (2 cap, 3 ctx) | 5/12 |
| Diag | 5/12 | 7 (all at the cap) | 1/12 |
| Neutral | 0/3 | 3 | 0/3 |

- The two stalled responses are byte-identical across arms, so the pairs are clean. All 6 discordant pairs favor C-late (sign test p≈0.03; one seed).
- The 5 archived v1 diag runs were never delivered: the word check rejected them ("too long: 221–233 words (max 220)").

**Why diag failed to produce a program.** The agent did not ignore the message. Each failed reply opens the heredoc and starts the suggested structure, then re-derives the key observation inside comments until it hits the cap.
- abc391_d: 186 comment lines vs 23 code lines, 169 of them duplicated ("# Let's re-derive… # Actually, the removal time for rank k is…").

C-late's numbered recipe gets transcribed; diag's one-paragraph observation gets re-verified.

**When diag did produce a program,** 4 of 5 runs lost all 20 actions to a format trap. The message says "write … **in a single command, then run** python -I /public/check.py", and its "Implementation discipline" section repeats it. The agent appended the check to the heredoc, and the harness rejected that every time ("Run the public tests as a separate action…").

## Q4. Implementation and harness problems

1. **One shot for stall arms.** `max_consecutive_format_errors=3` is not reset on delivery (`consecutive_errors` goes 1 → 2 → 3). 11 of 27 delivered stall runs died after a single response.
2. **The combined-command trap** cost 17–20 actions in each of 5 runs. The harness answered 20 identical rejections without intervening.
3. **Repeat loops go undetected,** although the harness computes `exact_repeats_after` (up to 18). 74 of 139 gate runs (53%) re-checked an already-gated source. In 5 runs the repeats filled the 16k context, giving length stops with 361–1,186 tokens (each format-error note adds 74 tokens), so RFE was guaranteed. These ctx stops are counted as "length" but are not deliberation.
4. **Runtime-error reports carry no detail.** D2 shows `RE: ''` with no stderr or exit code (abc390_d, abc390_e, abc400_c@2109). Hidden results confirm the RE, but the message gives the agent nothing to act on.
5. **Large inputs are clipped** ("… (52239 characters total)"). The agent echoed the clipped prefix and concluded "display issue".
6. **The gate header invites dismissal.** "NOT verified; judge-public above is authoritative" preceded both dismissals of valid failures (arc195_b-P, abc390_e-O).
7. **A command timeout kills the run.** In abc400_c-review@2108 it ended as CommandExecutionError instead of returning a timeout observation.
8. **The v1 220-word cap** rejected 5 of 5 stall diagnoses.
9. **Gate timeouts are stricter than the judge** (2/4 s vs 6 s): abc394_f was flagged TLE, but its hidden failures are WA only.
10. **No false positives:** 12 gate runs on the 4 hidden-correct states all passed, and every counterexample I checked was valid. E2-review missed abc390_d's hidden RE (NO-DEFECT, a false negative).

## Q5. What limits each mechanism

| Mechanism | Main limit | Evidence |
|---|---|---|
| D2-stress | (a) reach | Catches only TLE/RE (delivered 5/14) |
| D2-oracle/property | (d), amplified by (c) | Fired on 10/10 wrong programs, 0 false alarms, but 11/18 trajectories looped; no localization, dismissive header; 1 independent rescue |
| E2-review | (d) | Good, verified content; succeeds only on few-line or one-formula fixes (2/9) |
| E2-strict | (d), weak mode adherence | Gain over A, none over E-v1; loops in 7/12 |
| Stall | (c), then (d) | One-response budget, combined-command trap, v1 word cap; diag content re-derived, not implemented |

Underneath is degenerate decoding at temperature 0.2: unchanged observations produce byte-identical replies, and deliberation moves into the comments of full-file rewrites. Harness fixes would likely change more outcomes than better frontier content:
- loop detection;
- resetting the format-error counter on delivery;
- a separate test command;
- stderr in RE reports.

n is too small for firm claims:
- D2's rescue is n=1 independent.
- E2-review abc400_c succeeded at one seed and failed at the other with the same formula.
- Stall has one seed, no hidden scores and 3 neutral runs.
- E2-strict states were selected on E-v1 failure.
