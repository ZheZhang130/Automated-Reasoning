# Agent failure analysis: truncation and identical rewrites (pass 3)

**Scope.**

* **Sources:** the frozen original agent (Qwen3.5 9B, mini-SWE-agent 2.4.6, `heredoc-v6-16k-common`, 4,096
  output tokens, thinking off), from preserved pass-1/2 runs plus the pass-3 runs.
* **Observable text only:** every number comes from emitted model text, captured request/response bodies,
  public-test records or hidden scores. Nothing about hidden model reasoning is inferred.
* **Separation:** runs with ACI options (pass-1 `aci-v1`/`aci-v2`) and probe runs are kept apart from the
  original agent.

Tools (all in `diagnostics/`, rerunnable from the repository root):

* `failure_mechanisms.py`: per-response truncation position, heredoc composition, parsable prefix,
  identical rewrites;
* `repeat_context.py`: what precedes an exact repeat;
* `salvage_probe.py`: an offline truncation-salvage counterfactual on public tests in a sandbox;
* `repeat_probe.py`: model-only resampling at loop starts;
* `guidance_uptake.py`, `e_uptake.py`: visible use of C/D guidance and E messages.

**Pass-3 replication on the extended cohort** (96 fresh attempts; `evidence/analysis/failure-mechanisms-ext.json`,
`repeat-context-*.json`). Sections 1–2 below were first measured on passes 1–2. The fresh, all-hard cohort
reproduces every mechanism:

| Measure | Passes 1–2 (original agent) | Pass 3 extended cohort |
| --- | --- | --- |
| Truncated responses inside the open heredoc | 98 of 99 | 151 of 158 in A/C/D (96%); 7 stop in prose before the fence |
| Prose before the fence (median) | 0 characters | 0 characters |
| Comment lines per truncated body (median) | 221, 35% deliberation wording | 202, median 74 deliberation lines |
| Start of a ≥10-line comment run (median code lines before it) | 11 | 17 |
| P(truncated \| previous truncated), A / C / D | 48% / 0/3 / 86% | **77% / 74% / 76%** |
| P(truncated \| previous complete), A / C / D | 6% / 1% / 0% | 5% / 0% / 7% |
| First response at the 4,096-token cap: A / C / D | 6/19 and 5/10 / 1/19 and 1/5 / 10/23 and 9/26 | **23/24 / 14/24 / 23/24** |
| Runs ending without any program: A / C / D / E | 5/29, —, 14/49, 3/16 | **17/24 / 8/24 / 17/24 / 17/24** |
| Exact consecutive repeats: A / C / D / E | 10 / 12 / 25 / 0 | 23 / 7 / 0 / 0 |

**Notes on the table.**

* **E's truncation counts are not independent of A's.** Every E truncation in pass 3 occurred before any
  trigger, so the bodies are byte-identical to A's. E is excluded from the composition and persistence rows.
* **Persistence is much higher on the hard cohort.** Once a response truncates, the next one does too three
  times in four, in every condition including C.
* **C differs at the start, not after a truncation.** C still truncates the first response in 14 of 24 runs
  on these tasks, but in 10 of 24 its first response is a complete program; A and D manage that in 1 of 24.

## 1. The truncation mechanism

**Where the response becomes long.** In the original agent's pass-1/2 runs, 98 of 99 truncated responses
(`done_reason = length` at 4,096 tokens) had **opened** the command block and the heredoc to
`/workspace/solution.py` and never closed it. The median prose before the fence is **0 characters**: Qwen
starts the shell command at once, so any deliberation happens *inside the file being written*.

**What the output is spent on.**

* **Mostly comments:** across truncated heredoc bodies, comment lines outnumber code lines by about 6 to 1
  (A: 8,175 comment / 1,270 code lines; D: 16,363 / 961; E: 3,737 / 286).
* **Comments after a short header:** in 81 of 98 truncated bodies, a run of 10 or more consecutive comment
  lines starts after a median of **11** code lines (max 37), typically imports and input parsing.
* **The body:** a median of 221 comment lines. 35% contain deliberation wording ("wait", "actually", "let's
  try", "example", question marks).
* **A representative case** (pass-2 validation, `abc396_f`, A): `import sys`, about 11 parsing lines, then
  comments such as "This is complex. Let's try a different approach … Alternative approach: for each k … Actually,
  let's use a Fenwick tree over the values … But threshold = M - k, which decreases", cut off at the token cap.

This is **algorithm discovery written as comments**, not code writing.

**Was valid source generated before truncation? No usable program.**

* 38 truncated bodies had a parsable line prefix that reads input and prints (30 distinct programs).
* **None passed a single public test** when run in a network-less sandbox; the harness passes a known-correct
  program 2/2.
* The parsable prefixes are 10–19 lines of input handling and placeholder output, followed by deliberation.

**Persistence.** A truncated response is followed by another truncated response far more often than a normal
one is:

| Original agent | P(truncated \| previous truncated) | P(truncated \| previous complete) |
| --- | --- | --- |
| A | 11/23 (48%) | 6/106 (6%) |
| D | 31/36 (86%) | 0/171 |
| E | 7/15 | 2/62 |
| C | 0/3 | 1/89 |

The frozen format-error rule ends a run after three such responses (`RepeatedFormatError`). That is how
"no program" outcomes arise: 5 of 29 A runs, 14 of 49 D runs, 3 of 16 E runs.

**Which problem classes are vulnerable.**

* In original-agent A runs, truncation occurs only on tasks that A fails or barely solves: `arc195_a`,
  `arc192_a`, `abc393_d`, `abc388_e`, `abc388_g`, `abc391_e`, `abc396_f`, `abc398_d`.
* It never occurs on the routine easy/medium tasks (`abc390_c`, `abc391_a`, `abc394_b/c`, `abc396_a/d`,
  `abc400_b`, `abc399_f`).
* LiveCodeBench's labels are a weak proxy (`arc192_a` and `arc195_a` are labelled *medium*); the observable
  correlate is that the method is not immediately known.

**Does C avoid it by reducing algorithmic uncertainty? Yes, that is what the observable data show.**

| Pass 1/2, original agent | First response: median tokens | First response truncated |
| --- | --- | --- |
| A | 749 (pass 1), 2,629 (pass 2) | 6/19, 5/10 |
| C | 402, 434 | 1/19, 1/5 |
| D | 619, 1,449 | 10/23, 9/26 |
| E (same first message as A) | 4,096 (pass 2) | 9/16 |

* **C writes shorter files:** with a plan, Qwen's first file is mostly code (truncated C bodies: 447 comment
  lines in total), and C runs almost never truncate.
* **Low visible vocabulary uptake:** about 8% of the plan's distinctive words reappear in comments, 0% in
  code. The plan works by fixing the method, not by being quoted.
* **A contract does not shorten the first response.** It specifies *what* to compute, not *how*, so the
  deliberation remains.

## 2. The identical-rewrite mechanism

**What repeats.** This covers all three passes (`repeat_context.py`; `evidence/analysis/repeat-context-all.json`).
An exact consecutive repeat of the previous model response follows a **constant observation**:

* **Usually the empty acknowledgement:** 69 of the original agent's 77 repeats follow the empty
  successful-command `<returncode>0</returncode>`.
* **The other 8 follow a constant non-empty output.** Seven are in pass-3 abc397_f C at seed 2108: a manual
  run whose output is always `0`.
* **It is a streak:** in 69 of the 77, the observation is byte-identical to the one before the previous
  response.

| Group | Runs | Exact consecutive repeats | After the empty acknowledgement | After another constant output | After an ACI note | Observation identical to the previous one | Longest streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original A | 53 | 33 | 32 | 1 | — | 30 | 9 |
| Original C | 49 | 19 | 12 | 7 | — | 16 | 9 |
| Original D | 74 | 25 | 25 | 0 | — | 23 | 16 |
| Original E | 42 | **0** | — | — | — | — | — |
| ACI A (`aci-v1/v2`) | 18 | 32 | 1 | 1 (format error) | **30** | 28 | 19 |
| ACI D | 18 | 16 | 1 | 1 (format error) | **14** | 13 | 15 |

**Where the loops start.** In every pass-3 A run with a repeat loop (abc390_f and abc395_f at seed 2108;
abc388_f and arc190_c at seed 2109), the loop starts **after the first failed public test**. That is exactly
where E intervenes, and no E run in any pass has an exact repeat (§6).

A representative trajectory (pass-1 MB2, `abc391_e`, C):

1. Qwen writes a program; the observation is the 27-byte `<returncode>0</returncode>`.
2. It runs the public test; the test fails.
3. It writes an identical file, receives the same 27-byte acknowledgement, writes the identical file again,
   and so on (messages 10–17).
4. After one format error it settles on a second program and repeats *that* 12 times until the 20-action limit.

**Why the format reinforces the repeat.**

* After a write, the history ends with the pair (*assistant: write X*, *user: the constant empty
  acknowledgement*).
* The next query sees the same suffix it saw one turn earlier, plus one more copy of the pair.
* At temperature 0.2 with a fixed seed, the most likely continuation of a self-similar context is the previous
  turn, and each further copy makes the pattern stronger. The streak lengths above (5–19) show this
  self-reinforcement.
* Hidden reasoning is not needed to explain it: the input to the model is byte-identical in the decisive suffix.

**Consequences.**

* **Wasted budget:** an identical rewrite consumes an action without changing the candidate.
* **No repair at all:** the agent never retests (re-testing an identical failed candidate is rare: 3 times in
  pass-1 A). It simply rewrites until the action limit.
* **Scale:** writes that reproduced a candidate that had already failed:

  | Condition | Pass 1 | Pass 3 (extended cohort) |
  | --- | --- | --- |
  | A | 21 of 38 heredoc writes | 50 of 64 writes |
  | C | 22 of 40 | 17 of 34 |
  | D | — | 31 of 41 |

## 3. Why the earlier text-feedback interventions failed

* **`aci-v1` (notes only)** and the notes of **`aci-v2`** (unchanged-source note; retest-of-failed note) add
  text to the observation. In the repeat loop that text is *also constant* across repeats, so the decisive
  suffix stays self-similar. The note itself became the context that precedes the repeat (44 of 48 ACI
  repeats), and the loops got longer.
* **`aci-v2`'s repeat guard** skips executing an identical consecutive action but leaves the duplicate
  assistant message in the history, so the fixed point is untouched.
* **`aci-v2`'s truncation message** arrives only *after* a truncation and asks for short reasoning. It lowered
  persistence somewhat (A: 6/16 truncations after a truncation instead of 11/23; D: 12/21 instead of 31/36),
  but the next response often still deliberated inside the file. That is expected if the deliberation is the
  model's way of finding the method rather than a formatting habit.

These were not controlled comparisons: the ACI runs used pass-1 development and mini-benchmark tasks.

## 4. Interventions considered

| Candidate | Mechanism addressed | Evidence | Decision |
| --- | --- | --- | --- |
| Salvage a truncated heredoc (save its parsable prefix) | Truncation | 0 of 38 salvageable prefixes pass any public test | **Rejected**: nothing usable is lost |
| Another observation note | Identical rewrite | Constant notes became the repeat context (44/48) | **Rejected**: same failure as aci-v1/v2 |
| Resample on an exact repeat (different seed, response not executed) | Identical rewrite | Model-only probe at the loop starts (§5): 12/15 resamples identical; the other 3 still rewrite | **Rejected** at the frozen temperature 0.2: the fixed point does not depend on the seed |
| Allow or require plain-text planning before the command (thinking on, or a reasoning budget) | Truncation | C shows that removing method uncertainty prevents truncation; the plan comes from outside | **Not tested**: changes the agent's protocol and token budget for every condition. A team-level decision, not an ACI tweak. |

## 5. Isolated experiments performed in pass 3

### 5.1 Truncation salvage (offline counterfactual, sandboxed; `salvage_probe.py`)

* **Sample:** all 99 truncated responses of the original agent in passes 1–2.
* **Prefixes:** 98 opened a heredoc. 38 had a parsable line prefix that reads input and prints
  (30 distinct programs).
* **Public-test results:** run on the public tests in a network-less, read-only, unprivileged container,
  **0 of 38** passed any public case. The harness passes a known-correct program 2/2.

**Rejected.** Saving a truncated prefix would only save an input parser.

### 5.2 Resampling at the start of an identical-rewrite loop (model only; `repeat_probe.py`)

**Method.**

* **Loop starts:** every place where the original agent's response k is byte-identical to response k−1.
  There are 6 unique starts in passes 1–2 (one pass-2 rerun of a pass-1 run deduplicated).
* **Replay:** the exact captured request body (messages, options, seed) was resent to the project Ollama
  endpoint with the original seed and with seeds 3001–3003, under the GPU lock. No agent, sandbox or judge
  was involved.

**Results.**

| Loop start | Original seed | Seeds 3001 / 3002 / 3003 |
| --- | --- | --- |
| arc195_a A (pass 1) | identical | identical / identical / identical |
| arc192_a D-cv2 (2 starts) | identical | identical / **different** (still a rewrite) / identical |
| abc391_e C, first loop | identical | identical / **different** (still a rewrite) / identical |
| abc391_e C, second loop | identical | identical / identical / identical |
| abc394_c D-v3 (pass 2) | not reproduced | not reproduced (all four replies run the test) |

* **Determinism:** in 5 of 6 starts the original seed reproduced the repeat byte for byte. This confirms
  that the loop is a deterministic property of the context. The abc394_c start did not reproduce, most likely
  because that run's request and response captures are misaligned; it is excluded.
* **Seed changes:** 12 of the 15 remaining resamples are identical. The 3 that differ are still writes to
  `solution.py`, not tests or new strategies.

**Rejected for the frozen configuration.** The fixed point holds across seeds at temperature 0.2. Breaking it
would need a control-flow change: refusing an exact repeat and changing the context, for example by dropping
the duplicated pair *and* adding state that differs from the previous turn. Raising the temperature is the
other option. Either changes the agent's sampling or protocol for every condition, so it is a new agent
configuration that would need its own validation. It is not an ACI note.

### 5.3 E: genuine diagnosis versus a neutral, length-matched message (frozen pre-trigger states)

**Method.**

* Five development trigger states from pass 2 were reproduced exactly: same seed, statement and agent. The
  packet candidate hashes matched pass 2 in **5/5**.
* At each state, a fixed **non-diagnostic** message was delivered through the same `deliver-v1` wrapper. It
  has the same four headings, 187 words (genuine diagnoses: 183–200), and says nothing about the task or the
  program.
* It is a separately labelled mechanism probe (`runs/probe-neutral`), never a condition.

| Frozen state | A (no message) | Genuine Codex diagnosis (pass 2) | Neutral message (pass 3) |
| --- | --- | --- | --- |
| abc390_c, seed 2108 | ✓ | ✓ | ✓ |
| abc393_d, seed 2108 | ✗ 9/40 | **✓ 40/40** | **✓ 40/40** |
| abc398_d, seed 2108 | ✗ 36/40 | ✗ 36/40 | ✗ 36/40 |
| arc195_a, seed 2108 | ✗ 39/40 | ✗ 39/40 | ✗ 3/40 |
| arc195_a, seed 2109 | ✓ | ✓ | **✗ 37/40** |
| **Hidden passes** | 2/5 | 3/5 | 2/5 |

Mechanism measures (`e_uptake.py`):

| | Changed lines in the next program (median) | Public pass after the message | Hidden pass |
| --- | --- | --- | --- |
| Genuine diagnosis (5 Codex) | 0.48 | 4/5 | 3/5 |
| Neutral message (5) | 0.26 | 3/5 | 2/5 |

**Reading.**

* **The rescue is not the diagnosis's content.** E's only development rescue (abc393_d) is reproduced by a
  message with no diagnostic content. It comes from the perturbation and the extra turn at that state.
* **Content changes the size of the repair.** Genuine diagnoses lead to edits about twice as large, and they
  avoided the one harm the neutral message caused (arc195_a, seed 2109).
* **Tiny sample:** n = 5 states, one seed each. This shows a mechanism, not an effect size.

## 6. D and E mechanisms

### 6.1 D: why a contract does not help this agent

**Result.** D passed 0/24 in pass 3: 0 gains and 2 harms against A. Passes 1–2 showed no consistent gain.

**Mechanism (observable).**

* **The contract does not shorten the method search.**
  * D's first response hits the 4,096-token cap in 23 of 24 runs, the same as A.
  * Its truncated bodies have the same composition as A's: 12,716 comment lines against 1,294 code lines.
  * Once truncated, the next response also truncates in 76% of cases.
  * A contract states *what* to compute (postconditions, edge cases). On hard tasks the bottleneck is *how*,
    which the contract deliberately leaves out.
* **Visible uptake is lower than C's.** Distinctive contract vocabulary reappears in a median 13% of comment
  lines and 0% of code, against C's 21% and 1.6% (`guidance_uptake.py`).
* **Hand-run checks cost actions.** D ran 5 manual checks (`printf … | python solution.py`), all on
  arc193_a seed 2108, which reached 18/40. They use budget without changing the verdict.
* **Both harms are first-response truncations.**
  * At abc395_f@2108 and arc194_e@2109, A truncated once and then wrote a passing program.
  * D truncated three times and ended without a program.
  * The observable difference is only the extra contract text before the same task. It cannot be shown to
    have caused the longer deliberation.
* **Partial programs.** When D did produce a program, it was sometimes close (abc388_f: 38/40 at both
  seeds). The contract's edge cases do not get it over the line.

**Interpretation.** For a 9B agent that has to discover the method inside a 4,096-token response, a
specification adds information it cannot use until the method is known. A contract may help an agent that
already has a method, such as **C+D**. That combination is planned only after the individual conditions are
benchmarked.

### 6.2 E: what the diagnosis changes

**Trigger bound.** E is identical to A until its first failed public test: all untriggered E runs are
byte-identical to A. On the hard cohort, 17 of 24 E runs never reach a public test, so E triggers in only
6 of 24. In passes 1–2 it triggered in 5 of 13 live runs. **E's opportunity is set by the agent's
truncation, not by the diagnosis.**

**At the trigger, E changes what happens next.**

* **A never recovered** after any of the six triggering failures: 0/6 reached a public pass again.
  * In four, A entered an exact repeat loop, all starting after that failure (§2).
  * A spent its remaining actions (20-action or repair limit).
* **E reached a public pass in 5/6** and improved the hidden score in all five runs where A failed:
  8→13, 21→38, 34→40, 0→34 and 4→40 cases.
* **No E run entered a repeat loop.** The diagnosis turn replaces the constant observation with
  task-specific text, which removes the self-similar suffix that sustains a loop.
* **But only two of those five became hidden passes.**

**What the local model does with a diagnosis.**

* **It always rewrites.** In pass 3, all 6 programs changed after the diagnosis (changed-line ratio
  0.08–0.85, median 0.65), and in pass 2, 8 of 8.
* **It does not copy the diagnosis.** Distinctive diagnosis vocabulary reappears mostly in comments (median
  10%) and rarely in code (median 2.5%; at most 24%, at abc388_f).
* **Shallow faults are fixed.** Both rescues where A failed (abc395_f@2109, arc193_a@2109), and the pass at
  abc395_f@2108, came from diagnoses of an **input-parsing slip**: pairs read as two consecutive lists.
* **Algorithmic faults are only partly fixed.**
  * abc388_f: the diagnosis named the exact `bisect` fix; E reached 38/40.
  * arc190_c: the recurrence was fixed but the method stayed too slow (34/40, 6 TLE).
  * abc390_f: a complete repair recipe was given; the program changed 78% and still failed the public tests.
* **This confirms the brief's premise:** a correct diagnosis is not always implemented correctly by the local
  model.

**Content versus perturbation (§5.3).**

* On frozen pass-2 states, a content-free message of the same length reproduced the one development rescue.
  Genuine diagnoses produced larger edits (median 0.48 against 0.26) and avoided one harm the neutral message
  caused.
* The extended cohort is consistent with both parts: E's specific diagnoses produced large, targeted edits,
  and the recoveries were concentrated on easily localized faults.
* With n = 6 triggers, the share of E's benefit due to content cannot be separated from the share due to
  breaking the loop.

## 7. Should the shared agent remain frozen?

**Recommendation: keep the shared agent frozen for the final benchmark, and do not ship an ACI change.**

**Why.**

1. **Neither mechanism has a fix at the observation level.**
   * Truncation is the model doing algorithm discovery inside the file; 0 of 38 salvageable prefixes were
     usable.
   * The identical rewrite is a deterministic fixed point of a self-similar context. It survives seed changes
     (12/15), and constant notes reinforced it (44/48).
   * Every candidate that could work changes the agent's protocol, sampling or token budget **for every
     condition**: a plain-text planning turn, thinking on, a larger output budget, refusing and rewriting
     repeated turns, or a higher temperature.
2. **Any such change also changes what is measured.**
   * C's advantage runs largely *through* truncation: a plan removes the method search that otherwise fills
     the 4,096-token response.
   * An agent that plans for itself, or has more output room, would shrink A's no-program floor and probably
     C's gain with it.
   * That is a legitimate research question, but a different one, and it would break comparability with
     passes 1–3 and with any main-60 results.
3. **The study does not need it.** A low A baseline is a property of the frozen 9B agent at this
   configuration, and the guidance conditions are defined relative to it. What matters is that all
   conditions share the identical agent, and they do (38-file verification on every attempt).

**What the team should know before the final run.**

* **E's opportunity is bounded by A's behaviour.**
  * E shares A's first message, so on hard tasks where the agent never produces a program, E never triggers
    (seed 2108: 10 of 12 E runs untriggered for lack of any public test).
  * E's measured effect therefore mixes "how good is the diagnosis" with "how often does the agent reach a
    public failure". Report the trigger rate next to every E number.
  * On the mixed-difficulty development tasks of pass 2, E triggered in 5 of 13 live Codex runs. Its
    pre-trigger history was byte-identical to A's.
* **No-program outcomes dominate hard tasks.** On the fresh hard cohort, `RepeatedFormatError` after three
  truncated responses is the most common A, D and E outcome. The final report should split failures into
  *no program* and *wrong program* (as `ext_analysis.py` does).

**If the team wants a stronger agent**, freeze it as a **new, separately validated configuration** and run
it as an additional arm. Candidates: a plain-text planning turn with its own token budget, thinking on, or a
repeat guard that removes the duplicated turn and adds changed state. It should be validated on the
development tasks first, with the same integrity checks. Never replace the frozen agent silently or mix the
two in one table. Replacing mini-SWE-agent as the backend is out of scope without an explicit team decision.
