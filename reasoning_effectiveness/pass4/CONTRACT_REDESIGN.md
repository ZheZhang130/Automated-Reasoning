# Condition D redesign: executing the contract (pass 4, Phase III)

## 1. Why passive contracts may under-implement the mechanism

**What passes 1–3 established about D.**

* **The checks were right:** contract-v3's concrete checks were correct, 32 of 32 against reference programs
  (pass 2, and again in pass 4 on the 8 development tasks, §4).
* **They were discriminating:** they would have caught 14 of 15 plausible wrong programs (pass 2) and 20 of 27 here.
* **They were never used:** the local agent never ran a single one (pass 2), and D-v1 reached 0 of 24 on the
  pass-3 hard cohort.

**What the motivating papers actually study.**

| Paper | Mechanism | What passive D implemented | What was missing |
| --- | --- | --- | --- |
| Endres et al., FSE'24 | postconditions judged by **test-set correctness** and **bug-completeness** (do they reject natural buggy implementations?) | correct, discriminating checks (contract-v3 design) | the rejection never happens unless the checks are **evaluated against the program** |
| Tufano et al., SpecOps'26 | a semi-formal spec is the blueprint for **generated tests that are then executed**; bug detection rises when the spec captures the violated contract (54.9% vs 19.4%) | the spec and its test suggestions | **phase II, execution**: the suggestions stay prose for the coder to act on, which this agent never does |

**The hypothesis tested.** D's weakness is an integration gap, not that contracts carry no information. The
passive design asks a 9B agent, already short of output budget, to take the extra steps of turning prose
suggestions into commands. D-active closes that gap with **harness execution**, the step both papers depend on.

## 2. D-active design (`guided_agent/contract_checks.py`)

1. **One upfront frontier call**, unchanged: contract-v3 from the public statement only. No algorithm, code, plan,
   hidden tests or reference implementation.
2. **Parse once.** The K-checks (stdin plus proposed stdout) are taken from `## Test suggestions`.
3. **Validate without any reference** (benchmark-safe). Drop a check if it is malformed, a duplicate, larger than
   2,000 characters, beyond the limit of 6 checks, or **contradicts a public test** (same input, different
   expected output). Everything else stays **`unverified`**.
4. **Execute.** Each time the agent runs `python -I /public/check.py`, the harness first obtains the authoritative
   judge-public report. It then runs **the same judged bytes** (`/workspace/solution.py`) on every accepted check
   input **inside the agent's own sandbox container** (network-less, read-only, unprivileged; 3 s per case),
   compares with the judge's own comparator, and appends the results **below** the public report.
5. **Label trust explicitly.** The appended block begins `[Contract checks: supplementary, NOT verified]` and says
   the proposed outputs were derived by hand by a stronger model and may be wrong, and that the judge-public result
   is authoritative. Each check shows input, proposed output, the program's output and *same / DIFFERENT*.
6. **Injection `inject-active-v1`:** the contract-v3 text plus one sentence saying that the harness runs the
   K-checks at every public test and that the results are marked unverified.

**What the model can tell apart.**

| Source | Label shown | Can it be wrong? |
| --- | --- | --- |
| judge-public report | `PUBLIC TESTS: …` (first) | no (real expected outputs) |
| contract check | `[Contract checks: supplementary, NOT verified]`, "proposed, unverified" | yes |
| control: extra input | `[Extra inputs: supplementary]`, no expected output | n/a |

## 3. Fairness and controls (brief §7.4)

**Budget accounting.**

* **Actions:** D-active adds **no action, model call or frontier request**. The checks run inside the same
  public-test action.
* **Time:** their harness time is part of the public-test time and recorded (`contract_checks_summary.seconds_total`,
  typically under 1 s per test), so it is inside the 600-second clock. **No extra coding time is granted.**

**Three effects, three arms.** D-active changes three things at once, so they are separated by arms that share the
same artifacts and seed:

| Arm | Contract text in first message | Extra executions | Proposed outputs shown |
| --- | --- | --- | --- |
| `v3passive` (pass-2 D-v3) | yes | no | no (only inside the contract text) |
| `active` (D-active) | yes | yes | yes, labelled unverified |
| `inputs` (control) | **no** (A's frozen message) | yes, the same inputs | **no** |

* `active` vs `v3passive` isolates **execution plus feedback presentation**.
* `inputs` vs historical A isolates the **extra testing opportunity** (outputs on more inputs, crashes and
  timeouts).
* `active` vs `inputs` isolates the **contract's behavioural information** (the contract text and the proposed
  outputs).

**Reference labels.** Reference-based correctness labels (§4) are a development-only analysis and are never shown to
the model.

## 4. Check validity on the 8 development tasks (`diagnostics/check_validity.py`)

Each task's single Codex contract-v3 artifact, as used in the runs, gives four checks, all of which pass the
benchmark-safe validation.

* **A reference** is a submission with 40/40 hidden.
* **Wrong programs** are distinct failed submissions of the same task, from passes 1–4.

| Task | Accepted checks | Proposed outputs correct | References | Wrong programs | Caught by a correct check |
| --- | --- | --- | --- | --- | --- |
| abc400_b | 4 | 4 | 7 | 0 | — |
| abc393_d | 4 | 4 | 11 | 2 | 2 |
| arc195_a | 4 | 4 | 8 | 10 | 10 |
| arc192_a | 4 | 4 | 2 | 7 | 6 |
| abc398_d | 4 | 4 | 1 | 6 | **0** |
| abc388_e | 4 | 4 | 2 | 1 | 1 |
| abc389_f | 4 | 4 | 3 | 0 | — |
| abc397_f | 4 | 4 | 1 | 1 | 1 |
| **Total** | **32** | **32 (100%)** | | **27** | **20 (74%)** |

**Reading the table.**

* **No proposed output is wrong** on these tasks, so in this cohort D-active never shows misleading feedback.
  Wrong proposals remain possible in general, which is why the label says *unverified*.
* **abc398_d's wrong programs are not caught** by small hand-checkable inputs. They produce correct outputs and
  fail only by **time limit**: 36 AC and 4 TLE of 40 hidden cases in all 6 historical failures. A behavioural
  contract with small checks cannot express that, so execution cannot add information the checks do not contain.

## 5. Results (`p4-dactive-s2108`: 24 attempts, original agent, seed 2108; 0 infrastructure failures)

| Task | A (hist) | D-v1 (hist) | v3passive | **active** | inputs (control) |
| --- | --- | --- | --- | --- | --- |
| abc400_b | ✓ | ✓ | ✓ | ✓ | ✓ |
| abc393_d | ✗ | ✓ | ✓ | ✓ | ✓ |
| arc195_a | ✗ | no program | no program | no program | **✓** |
| abc398_d | ✗ (TLE) | ✗ | ✗ | ✗ | ✗ |
| abc388_e | no program | **✓** | ✗ | ✗ | no program |
| abc389_f | no program | no program | no program | no program | no program |
| abc397_f | no program | no program | no program | **✓** | no program |
| arc192_a | no program | ✗ | no program | no program | no program |
| **Hidden passes** | 1 | 3 | 2 | **3** | 3 |
| Runs without a program | 5 | 4 | 4 | 4 | 5 |

**Check execution** (active arm; `evidence/dactive-analysis.json`).

* **How often the checks ran:** at every public test of every run that wrote a program (11 public tests in 5 runs),
  taking 0.19–0.63 s per run in total. No harness error, no added action.
* **abc397_f, the one task D-active alone solved.**
  * At actions 2 and 4 the public tests failed (0/2), and **all four** contract checks were also DIFFERENT. After
    each, the agent changed the program.
  * At action 18 the program passed the public tests and all four checks, then passed 40/40 hidden.
  * **This cannot be attributed to the checks alone.** The public failure was also shown, and the trajectory
    differs from `v3passive` from the very first response, because the injection wording differs. Under
    `v3passive` the first responses truncated three times.
* **abc388_e, a correct detection that was not repaired.**
  * The program passed the public tests (3/3) three times, and each time check **K-3 was DIFFERENT**. K-3 is
    correct against the reference (§4), so the checks detected a real bug that the public tests miss: exactly
    the Endres/Tufano bug-detection mechanism.
  * The agent changed the program twice after the flag but never fixed K-3, then submitted; hidden fail.
* **Everywhere else** the checks agreed with the program, or the run never produced a program to check.
  **No proposed output was wrong**, so D-active never misled the agent in this cohort.

**The control.** `inputs` (the same extra executions, no contract) is no worse than the contract arms. It solves
arc195_a, where its trajectory was A's initial message plus extra outputs, and loses abc388_e. The extra testing
opportunity alone is therefore worth about as much as the contract information on this cohort.

## 6. Decision

Pre-registered rule: at least +2 net over **both** `v3passive` and `inputs`, losing nothing `v3passive` passes.

| Comparison | Gains | Losses | Net |
| --- | --- | --- | --- |
| active vs v3passive | abc397_f | — | **+1** |
| active vs inputs | abc397_f | arc195_a | **0** |
| active vs D-v1 (hist) | abc397_f | abc388_e | 0 |

**D-active is not promoted.** **D-v1** (teammates' `contract-v1` + `inject-v1`) stays the primary D: it is the
proposal's original intervention and the valid control, and it matches D-active's 3/8 here.

**D-active stays documented as an alternative.** It is implemented, tested (Docker integration) and safe:
benchmark-safe validation, unverified labels, no extra actions or frontier calls. What it shows is mechanistically
interesting:

* the executed checks **detect** public-passing wrong programs (abc388_e);
* **repairs** after a detection depend on local capability;
* detection is impossible when the bug is only performance (abc398_d).

If the team wants a D that "affects actual verification", D-active is the defensible implementation. It should
then be a **labelled variant** (`D-active`, contract-v3 + `inject-active-v1` + executed checks), not silently
replace D-v1, and the final study should include the `inputs` control. Otherwise extra testing opportunity is
confounded with contract content.

**Under the improved shared agent (l1).** Measured in stage D, see `LOCAL_AGENT_EXPERIMENTS.md` §6.
