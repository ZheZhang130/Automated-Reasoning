# Pass 3 final report: hardening, extended evaluation and benchmark preparation

Branch `feat/csc2108-contract-diagnosis-pass2`. All pass-3 work is on top of `e254ccd` (pass 2), with no history
rewritten. Supporting documents in this directory:

| Document | Contents |
| --- | --- |
| `READINESS_AUDIT.md` | Readiness checks, judge validation, CI, isolation, privacy, frozen baseline |
| `AGENT_FAILURE_ANALYSIS.md` | Truncation and identical-rewrite mechanisms, probes, D and E mechanisms |
| `EXTENDED_BENCHMARK.md` | The 96-attempt paired benchmark |
| `PROVIDER_VALIDATION.md` | Codex compared with the direct API |
| `FRONTIER_ONLY_COST.md` | Condition B on real tasks and cost estimates |
| `FINAL_BENCHMARK_OPTIONS.md` | 60, 90 or 120 problems |

Sanitized evidence is in `evidence/`.

## What was run

| Item | Count | Outcome |
| --- | --- | --- |
| Extended benchmark: 12 fresh tasks × A/C/D/E × seeds 2108, 2109 | **96 attempts** | 96 completed; 0 infrastructure errors; 38-file frozen verification on every attempt |
| Neutral-vs-genuine E probe (frozen pass-2 states) | 5 | Mechanism probe, not a condition |
| API end-to-end checks (C, D, two E) on consumed development tasks | 4 | |
| Condition B on consumed development tasks: Codex 3, API 2 | 5 | 5/5 hidden 40/40 |
| Model-only repeat probe at loop starts | 24 model requests | No agent, sandbox or judge |
| Offline truncation-salvage counterfactual | 38 programs | Sandboxed public tests only |

**API use:** **10 of the 12 allowed requests and $0.0511** (standard prices). Across passes 1–3 the total is
28 requests and $0.173. There were 0 retries and 0 failures.

## Answers

### 1. Is the integrated system now reliable enough for longer experiments?

**Yes, for the frozen configuration on Windows with Docker and the project Ollama.**

**Evidence.**

* **Pass-3 attempts:** 110 (96 benchmark and 14 development) with 0 infrastructure or setup errors.
* **Frozen verification** passed on every attempt: 38 files, the model digest and the sampler wire.
* **Tests:** 74 offline tests pass in both backend modes (`evidence/tests/`), and 6/6 Docker integration tests
  pass.
* **CI:** green on Windows, Ubuntu and macOS.
* **Run safety:**
  * Batch plans are validated and hash-checked against the freeze.
  * Any change is refused, and malformed records are quarantined.
  * The API ledger is locked against concurrent writers.
  * A resource conflict defers the batch instead of consuming an attempt.
* **Isolation checks:**
  * E's pre-trigger trajectories are byte-identical to A's in 24/24 pairs.
  * The Codex isolation audit shows 0 tool events in 24 artifacts, 6 diagnoses and 9 Codex coder turns.

**Limits.**

* Native macOS inference is not validated; CI covers macOS offline only.
* One operational interruption (a tool time cap at the first launch) was handled by the resume rule and is
  documented.

### 2. Were the known judge issues resolved or safely contained?

**Contained, not resolved by rescoring.**

* **Reproduction:** regression tests reproduce both historical false negatives. On abc392_d, `repr(1/3)` is
  rejected under a 1e-8 tolerance; on abc396_e, a valid alternative minimum is rejected.
* **Reference checkers** accept the correct outputs. They are not used for scoring, and **no cohort was
  rescored**.
* **Selection now refuses non-exact tasks:** an automatic classifier plus a manual review of every cue.
  Pass 3 excluded five pool tasks. It also found a case-insensitive task that the pass-2 regex missed.
* **Windows line endings:** the line-ending bug in `build_data.py` is fixed at the source, and the earlier
  workaround produced byte-identical data.
* **Two main-60 tasks need a decision before the final freeze:**
  * `arc195_c` (constructive): exclude it, or add a validator in a new judge version.
  * `abc395_a` (case-insensitive): keep it and report the risk, or add case folding.

### 3. Did the larger benchmark reinforce planning's apparent advantage?

**Yes, more strongly than passes 1–2.**

| Measure | Result |
| --- | --- |
| Hidden accuracy | C **13/24** against A 2/24 |
| Paired against A | 12 gains and 1 harm; mean difference +0.46, task-clustered 95% interval (0.17, 0.75) |
| Tasks favouring C | 7 of 8 discordant tasks |
| Tokens and time | C used about half of A's tokens and local time |

**Why:** a plan removes the method search that otherwise fills the 4,096-token response. C's first response
was a complete program in 10/24 runs, against 1/24 for A.

**Caveats:**

* 12 tasks, all hard, from one shard. Two seeds of a near-deterministic agent.
* The sign-test p = 0.07 is descriptive, and **no significance is claimed**.

### 4. Did D show any consistent benefit?

**No.**

* **Pass 3:** D scored 0/24, with 0 gains and 2 harms against A.
* **Passes 1–2:** no consistent gain.
* **Why:** the contract does not shorten the method search. D's first response hit the cap in 23/24 runs,
  the same as A's.
* **Scope of the null:** this is a negative result for *this* agent. A contract may still help an agent that
  already has a method (C+D), which is not tested yet.

### 5. Did E improve correctness, and how often did it trigger?

**Slightly, and rarely.**

* **Accuracy:** E scored 4/24 against A's 2/24 (+2 / −0, interval 0.00 to 0.21).
* **Trigger rate:** E triggered in **6 of 24 runs (25%)**: 1 at seed 2108 and 5 at seed 2109.
* **Why the others did not trigger:** 17 runs never reached a public test because of truncation, and 1
  passed its first test.
* **Delivery:** all 6 diagnoses were delivered (Codex, 11–15 s, 0 tool events).
* **E's ceiling** on hard tasks is set by the agent's truncation, not by the diagnosis.

### 6. Did E improve post-failure recovery even when the overall pass rate barely changed?

**Yes, clearly on the triggered subset, with an attribution caveat.**

| From the identical failure state | A | E |
| --- | --- | --- |
| Reached a public pass again | 0/6 | 5/6 |
| Hidden cases passed | 107/240 | 205/240 |
| Hidden passes | 1/6 | 3/6 |

* **A's path:** in four of these runs A entered an identical-rewrite loop that started after this failure.
* **E's path:** E never entered one.
* **Which faults:** the two rescues where A failed were input-parsing slips. Algorithmic faults improved
  (21→38, 0→34 cases) without passing.
* **Attribution:** the neutral-message probe reproduced one development rescue without diagnostic content.
  Part of E's recovery effect is therefore the perturbation that breaks the loop, and part is the content
  (larger, targeted edits).

### 7. Are the remaining failures mostly model-reasoning failures or agent-interface failures?

**Mostly reasoning-capacity failures that the interface turns into "no program".**

* **The dominant failure is no program at all:** 17 of A's 22 failures and 17 of D's 24. Three truncated
  responses end the run with `RepeatedFormatError`.
* **The cause is reasoning:** 96% of truncations stop inside the open file. That file's body is mostly
  comments deliberating about the algorithm (a median of 202 comment lines per body).
  * Thinking is off and the cap is 4,096 tokens, so the method search has no other place to go.
  * Salvaging the truncated prefix gives nothing (0/38 pass any public test).
  * Supplying the method (C) removes about half of these failures.
* **Repair failures are an interface property:** an identical-rewrite loop is a deterministic fixed point
  of a self-similar context (69 of 77 repeats follow a constant observation).
* **True wrong-program failures are a minority:** A 5, C 3, D 7, E 3.

### 8. Did any new ACI investigation produce a justified improvement?

**No. Every candidate was rejected on evidence, and no ACI change is proposed for the final benchmark.**

| Candidate | Evidence | Why rejected |
| --- | --- | --- |
| Salvage truncated heredocs | 0/38 usable prefixes | Nothing usable is lost |
| Resample on an exact repeat | 12/15 resamples identical; the other 3 still rewrite | The fixed point does not depend on the seed |
| Another observation note | aci-v1/v2 notes became the repeat context in 44/48 repeats | Same failure as before |

The neutral E probe was a mechanism measurement, not an intervention.

### 9. Is the original frozen agent still our best primary configuration?

**Yes, as the primary configuration of the final comparison.**

* **No usable fix:** none of the candidate changes improves it at the observation level.
* **What would help changes the protocol** for every condition: a planning turn, thinking on, a larger output
  budget, a repeat-refusal with changed context, or temperature.
* **Such a change also changes what C measures,** and it would break comparability with passes 1–3.
* **If the team wants a stronger agent,** freeze it as a separately validated second configuration. Do not
  substitute it silently.

### 10. Is B ready for cost-controlled full benchmarking?

**The pipeline is ready; the budget needs two decisions first.**

* **Pipeline evidence:**
  * 5/5 real-task B runs (Codex 3, API 2) passed hidden 40/40, each in 3 turns with clean protocol.
  * Requests are per-turn ledger entries with a per-run cap and no retries (tested).
  * Measured API cost per passing attempt was $0.007–0.015.
* **Before the final run:**
  1. **Pilot:** a B run on about 10 consumed development tasks that fail locally (≤ $6). B never failed here,
     so the cost of a failing attempt (estimated at about $0.37–0.6) is not yet measured.
  2. **Ceilings:** the team must set final ledger ceilings in a reviewed commit. The current code constants
     are pass-3 limits.

### 11. How closely did Codex and API guidance agree?

**Semantically, in every pair inspected:**

* **E diagnoses:** 5/5 at identical frozen packets (2 in pass 3).
* **Guidance:** 1/1 plan and 1/1 contract-v1, plus 2 contract-v3 in pass 2.
* **Run outcomes:** the C, D and two E end-to-end checks with the API matched their Codex counterparts at
  the outcome level (4/4).

**Differences:**

* The API was 2–3× faster.
* Codex replay carries about 11–12k tokens of harness context and does not report the serving model.

**Limits:** these are small samples (n = 2–5 per kind). The local agent is sensitive to wording, so
equivalence over a full cohort is not established. **Use one provider (the direct API) for the final study.**

### 12. What is the estimated cost of the eventual full A/B/C/D/E comparison?

All conditions with 3 seeds; paid API at standard prices (`FRONTIER_ONLY_COST.md`):

| Size | Paid API | Plan the ledger for (conservative) | Local GPU time |
| --- | --- | --- | --- |
| 60 tasks | $10–30 | about $180 | 12–25 h |
| **90 tasks** | **$16–44** | about $265 | 18–38 h |
| 120 tasks | $21–60 | about $360 | 24–50 h |

* **B is 85–95% of the money.** C/D/E guidance via the API is about $1.4–3.
* **B adds 1–4.5 h** of non-GPU wall time.

### 13. What should the team do next?

1. **Decide the two judge exceptions** in the main 60 (arc195_c, abc395_a) and freeze the judge version.
2. **Choose the size.** **90 tasks** is recommended: the main 59–60 plus 30 outcome-blind `test5` tasks
   (10/10/10), reported as separate strata. If chosen, run the output-semantics review on `test5` before
   selecting.
3. **Run the B pilot** (≤ $6), then set the final ledger ceilings and per-attempt caps.
4. **Generate all C/D guidance with the direct API** once per task, and freeze by hash before any run. Use the
   API for E diagnoses and B.
5. **Run the final study** with the pass-3 machinery and predeclared analysis:
   * two-stage freeze, plan validation and the seed-prefix reduction rule;
   * C vs A and B vs A as primary comparisons;
   * E reported with its trigger rate, and failures split into no program and wrong program.
6. **Later, not before the individual benchmark:**
   * combined conditions (C+D, C+E), which is where a contract or a diagnosis may add to a plan;
   * optionally, a separately validated stronger-agent arm.
7. **Privacy:** decide on the 49 historical committed Codex artifacts that contain the Windows user name; no
   credentials are involved (`READINESS_AUDIT.md` §6). Redacting them in place would break hashes recorded in
   the pass-1/2 freezes, and removing them from Git history needs a rewrite. This pass did neither.

### 14. Are we ready to freeze the final experiment?

**Almost: the system is ready, but four decisions are not yet made.**

**Ready:**

* the frozen agent and judge;
* the runner, integrity checks and ledger;
* the analysis code and the selection machinery.

**Not yet ready, and each is a short team decision or a small run:**

1. the judge decision for arc195_c and abc395_a;
2. the final size, and with it the `test5` review and selection;
3. the B pilot and the final ledger ceilings;
4. the provider: the direct API for all frontier roles.

After these, the experiment can be frozen with the existing two-stage procedure.

## Negative results and limitations

**Negative results.**

* D gave no benefit: 0/24 here, and no consistent gain in any pass.
* E's correctness gain is small (+2 tasks). It is capped by a 25% trigger rate on hard tasks, and part of its
  recovery effect is not attributable to the diagnosis's content.
* No ACI improvement was found. Salvage, resampling and notes were all rejected.

**Limitations.**

* **The cohort:** 12 hard tasks from one shard, so it says nothing about easy or medium tasks. The fresh
  part of `test6` is exhausted.
* **Seeds:** two seeds of a near-deterministic agent, so the effective sample is close to the number of
  tasks.
* **Provider:** all benchmark guidance is Codex replay, not the direct API.
* **B:** measured only on passing attempts.

**Statistics:** no claim of statistical significance or of generalization beyond this agent and cohort is
made.
