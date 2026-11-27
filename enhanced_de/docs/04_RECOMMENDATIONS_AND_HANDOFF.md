# Enhanced D (contract) and E (diagnosis): recommendations, interpretation and handoff

## Morning handoff (one page)

**Question.** Can contract-based (D) and diagnosis-based (E) frontier reasoning become competitive standalone
interventions with stronger implementations, or is their value specialized and complementary to planning (C)?

**Answer on this evidence.** Mostly specialized and complementary. Better implementations fixed real defects in
D-v1 and E-v1, but did not make either condition competitive with C for this local agent:

* **Held-out, codex-replay frontier.** 16 test5 tasks, 1 seed. Every enhanced D and E policy scored 7/16, the same
  as A. C scored 9/16 and C-late 8/16.
* **Held-out, paid API.** The E2 diagnoses rescued 2 of the 8 A-failing tasks they reached: the same two tasks C
  rescued.

None of this is a significance claim.

**What was built** (branch `feat/csc2108-enhanced-d-e-v2`, package `enhanced_de/`, 94 offline tests):

* **D2.** Statement-only executable verification banks: postconditions, metamorphic relations, stress inputs, an
  optional tiny oracle. They are run by the harness after each authoritative public pass.
* **E2-strict.** A committed repair mode, static and timing evidence, and advisory checks.
* **E2-stall.** Triggers on the second consecutive no-program truncation, with neutral and C-late controls. Protocol
  **v2** (this session) resets the format-error streak on delivery, separates the test command, and asks for
  numbered steps.
* **E2-review.** Fires at the first public pass and is silent unless its counterexample reproduces.
* **Trigger-partitioned validation and process analysis.**

**Key findings:**

1. **D2 is a strong offline detector and a weak live intervention.**
   * Offline: 38–40/46 natural mutants killed, with 0 semantic false rejections on 96 references.
   * Development, selected PPHF states: detected 10/10, rescued 1 (a timeout).
   * Held-out: detected 0/3 PPHF, with 1 harmless false alarm.
   * Counterexamples without localization led to identical-response loops.
2. **E2-strict did not beat the original E-v1** with the provider held fixed: 1/12 against 2/12 on development
   states, and 0 against 0 on held-out tasks. The historical "E-v1 failed 12/12" cohort was partly a selection
   artifact.
3. **v1 stall diagnosis was crippled by delivery defects** (one response to act, a combined-command trap). v2 fixed
   delivery: programs went from 5/12 to 12/12. Passes did not rise (3 to 1).
   * A plan delivered at the stall did better: 5/12 on development, 1/3 held-out. The development comparison is
     confounded by provider and length.
   * The neutral nudge never produced a pass.
4. **Broadening E's triggers fixed reach** (15/16 held-out tasks reach some trigger) but not effectiveness (codex
   7/16). The paid-API draws did better than Codex replay at the same states, so artifact quality and draw variance
   matter as well as local repair capacity.
5. **Process facts.** Every silent or untriggered run reproduced A byte-for-byte (determinism held). No arm lost a
   task that A solved. Paid API use: 14 requests, $0.21 standard and $1.26 conservative.

**Recommendations:**

* **D-v2 = `D2-property`** with the `D2-inputs-stress` and sham-gate controls, after four harness fixes (§5).
* **E-v2.** Keep `diagnosis-v1` at the strict trigger. `E2-adaptive` (stall v2, E-v1, review) is exploratory only,
  and must run with API artifacts and matched C.
* **Next experiment:** frozen-state **C+D and C+E forks at the official C failure states**: 39 states, about 120
  runs, with sham and plan-refresh controls (§8).

**Unresolved:**

* whether trace conditioning adds anything over a plan at the stall;
* whether API-quality E artifacts beat C on a larger, seed-replicated, provider-matched cohort;
* whether a better shared interface (pass-4 `l1-selfplan`, the unrun L5/L4 probe) would let D and E artifacts be
  used.

**Session notes.**

* **Two sessions.** Session 1 (Gemini 4 Neon lead, with Claude and Codex delegations via T3) built and ran phases
  0–1C. Session 2 (Claude Opus 5.5 lead) verified those results, fixed bugs, ran the controls, protocol v2,
  validation and the API checks, with an independent Codex audit, a Codex interpretation review and a Claude
  trajectory analysis.
* **Gemini did not participate in session 2.** T3 failed to connect, and no Gemini CLI is installed.
* **Infrastructure incidents, both resolved.** The local model server was stopped by a tool time limit (one run set
  aside and rerun before scoring). Three deterministic context overflows are counted as failures.

---

## 1. What was built (code map)

| Component | File | Role |
| --- | --- | --- |
| D2 authoring and banks | `enhanced_de/d2_contract.py` | `D2_BUNDLE_V1` makes one statement-only frontier call that returns a semi-formal contract plus a pure verification module (validator, small/stress generators, postconditions, metamorphic relations, tiny exhaustive oracle). It is compiled and calibrated on the public examples in throwaway Docker, then materialized as a bank |
| D2 gate | `d2_contract.D2GateChecker`, `runner_v2._public_judge` | After each authoritative public **pass**, runs the bank against the judged bytes in a separate container and appends the smallest failing case below the public report. Modes: `inputs-stress` (crashes and timeouts only), `property` (no expected outputs), `oracle` |
| E2 controllers | `enhanced_de/e2_diagnosis.py` | `E2StrictController`: first public failure, static and timing evidence packet, one committed repair mode, advisory V-checks. `E2StallController`: second consecutive no-program length stop; modes `stall-diag`, `c-late`, `neutral`; protocols `v1` and `v2`. `E2ReviewController`: first public pass, silent unless its counterexample reproduces a discrepancy |
| Runner | `enhanced_de/runner_v2.py` | Wraps the frozen `frozen-v6` runtime (38 hashes verified per attempt) with the D2/E2 hooks. Arms are dormant until their trigger fires |
| Experiments | `run_experiments.py`, `run_phase2_validation.py`, `run_phase3_api.py` | Development phases 1A–1C, trigger-partitioned validation, paid-API checks |
| Measurement | `analyze_v2.py` | Per-run process record (trigger, delivery, program, length stops, tokens, wall time, hidden outcome, official-A comparison) |
| Ledger | `ledger_guard.py` | Fail-closed v2 ledger: 20 requests and $10 (conservative) hard caps; isolated Codex wrapper and event audit |
| Tests | `test_foundation.py`, `test_d2_contract.py`, `test_e2_diagnosis.py`, `test_phase2.py` | 94 offline tests (1 skipped); no GPU, API or Codex |

Original conditions, configurations and the official benchmark are untouched. `results/final-main/` is byte-identical,
and `local_agent verify` checks the 38 frozen files.

## 2. Literature to design: what the v2 arms adopt and what they still omit

| Paper | Mechanism | Original (D-v1, E-v1) | v2 adds | Still omitted, and why |
| --- | --- | --- | --- | --- |
| Endres et al. (nl2postcond) | Executable postconditions judged by test-set correctness and bug-completeness | Prose contract, never executed; 0 reasoning tokens on 59/60 contracts | Executable postconditions and metamorphic relations, a tiny exhaustive oracle, and the offline Endres-style benchmark (96 references, 46 natural public-pass mutants) | A single sample per task (no accept@k). Our "functions" are stdin/stdout programs |
| Tufano et al. (spec-driven tests) | Spec, then generated tests that are **executed** | Phase I only (structure and test suggestions as prose) | Phase II: harness execution of contract-derived tests at every public pass | Spec derived from the statement, not from code. Author and consumer are different models |
| Chong et al. (CUDAnalyst) | Multi-tool feedback (debugger, static analysis, profiler) into an explicit plan step; frozen-state interventions; misaligned feedback hurts | One channel (public report), one diagnosis | Static and timing analysis packet, a committed repair mode, sandbox-verified advisory checks, stall-conditioned replanning, frozen-state comparisons with neutral and C-late controls | No iterative multi-round planning (one intervention per attempt). No attribution of effects to feedback components |
| Yang et al. (SWE-agent) | ACI design: thought channel, edit receipts, guardrails | `frozen-v6` has no deliberation channel; reasoning happens inside the heredoc | Nothing in the shared agent. Stall v2 changes only the stall arms' delivery (format-error streak reset, separate test command) | Shared-interface changes need a separately versioned agent and matched A/C arms (§7) |
| Wang et al. (PlanSearch) | Search over natural-language plans | C = one plan | C-late as a control (the same plan delivered at the stall) | No search |

## 3. Agent participation (both sessions)

| Agent | Session | Contribution | How |
| --- | --- | --- | --- |
| Gemini 4 Neon | 1 (overnight lead) | Research lead: literature gap analysis, unified D2/E2 design, phases 0–1C, test5 cohort, API parity check | T3 (lead thread) |
| Claude Opus 5.5 | 1 | Independent design analysis, critique of the unified plan, implementation of `e2_diagnosis.py` | T3 delegations (links in doc 01; not reachable from session 2) |
| Codex GPT-6.2 Sol | 1 | Independent forensic analysis of the 900 runs, critique, implementation of `d2_contract.py` | T3 delegations |
| Claude Opus 5.5 | 2 (continuation lead) | Verification of session-1 results, determinism check, trigger-partitioned validation design, E2-stall protocol v2, controls, analysis, docs | Claude Code |
| Codex GPT-6.2 Sol | 2 | Independent read-only integrity audit: isolation, trigger fidelity, ledger, claims (`agent_reports/2026-11-26_codex_independent_audit.md`) | `codex exec -s read-only` (T3 unavailable) |
| Claude Opus 5.5 subagent | 2 | Independent trajectory analysis of phases 1A–1C. It found the stall-delivery defects behind protocol v2 (`agent_reports/2026-11-26_claude_trajectory_analysis.md`) | Claude Code subagent |
| Codex GPT-6.2 Sol | 2 | Independent critique of the results interpretation before the final recommendations. It found the C-late provider confound and argued the strongest case for artifact-quality limits; it proposed the C+D and C+E fork designs (`agent_reports/2026-11-26_codex_interpretation_review.md`) | `codex exec -s read-only` |
| Gemini | 2 | **Did not participate.** The T3 MCP server failed to connect for the whole session (`InvalidHTTPResponse` on 127.0.0.1:3773), and no Gemini CLI is installed. Nothing in session 2 is attributed to Gemini | – |

**Role separation.** Codex acting as an **auditor** ran in the repository read-only. Codex acting as the
**experimental frontier** always ran through the isolated replay wrapper: an empty directory, read-only, user
config and rules ignored, tools disabled, and every event stream audited. 116/116 audited streams contained no tool
events. Claude and Gemini never produced text that reached a benchmarked local agent.

## 4. Hypotheses and outcomes (including negative results)

| ID | Hypothesis | Evidence | Status |
| --- | --- | --- | --- |
| H-D0 | Put mathematical reformulations in the contract | – | Rejected before implementation: it collapses into C |
| H-D1 | Show the D2 prose contract upfront | Official D-v1: +6/−4 symmetric prompt noise | Rejected: the D2 arms change nothing before their trigger |
| H-D2a | Executable statement-only checks find natural bugs | Offline: property 38/46 mutants (25/33 WA), oracle 40/46 (27/33 WA), stress-only 16/46; 0/96 semantic false rejections | **Supported offline** |
| H-D2b | Detection carries over to live PPHF states | Dev 10/10 on selected states; held-out **0/3**: stress dropped at calibration; 2 subtle WAs missed | **Not supported on held-out tasks** |
| H-D2c | A detected bug gets repaired | Dev: 1 independent rescue, a self-explaining TLE. 11/18 distinct trajectories looped | **Not supported** |
| H-D3 | The local agent writes its own oracle from a prose contract | – | Deferred: it costs actions and tokens the 9B agent does not have |
| H-E1 | A structured strict diagnosis beats E-v1 at the same trigger | Dev 1/12 vs a provider-matched E-v1 2/12; held-out (codex) 0 vs 0 rescues; API E2-strict rescued 1 of 2 A-failing held-out states (abc385_c; no API E-v1 comparator) | **Not supported** against E-v1 |
| H-E1b | The historical E-v1 failure states are hard | A fresh E-v1 sample rescues 2/12 | Selection artifact confirmed |
| H-E2 | Stall diagnosis rescues no-program runs | Codex: v1 3/12, v2 1/12 (dev); held-out 0/3 (38/40 partial). **API v2: held-out 1/3** (arc185_e), with 33/40 and 34/40 on the other two | **Weak to mixed**; depends on the artifact draw |
| H-E2b | v1's stall failures were delivery defects | v2 raised programs from 5/12 to 12/12, passes from 3 to 1 | **Partly**: delivery was a real defect, but correctness is the binding limit |
| H-E2c | Interruption explains stall gains | Neutral nudge: 0/12 (v1), 0/12 (v2), 0/3 held-out | **Rejected**: content matters |
| H-E2d | Trace-conditioned diagnosis beats a statement-only plan at the stall | Dev stall-diag 4/24 vs C-late 9/24, confounded (API plans vs Codex diagnoses, plans 2× longer, cohort partly chosen on C success); held-out, provider-matched, 0/3 vs 1/3 | **Not supported**; not cleanly tested either |
| H-E3 | A code-aware review at public pass rescues PPHF | Dev 2/10; held-out 0/3 delivered, 0/7 false alarms | **Specialized**: few-line bugs only, and safe |
| H-E4 | Broader triggers make E competitive | Held-out: 15/16 tasks reach some trigger. Composed adaptive E2: codex 7/16 (= A); API rescue side +2, giving 9/16 (= C codex), but the harm side was not re-run and providers are mixed | **Unresolved**. Codex says no; small API evidence says possibly, on the same tasks planning rescues |

## 5. Recommended configurations

### D-v2

**Primary contract variant: `D2-property`.**

* **What it does.** One `D2_BUNDLE_V1` call per task, from the statement only. The harness executes postconditions,
  metamorphic relations and stress inputs at every public pass, and shows the smallest failing case, labelled
  unverified.
* **Why this variant.** It is the closest to Endres and Tufano (executable postconditions plus test execution).
  It never shows an expected answer, so it stays on the "what, not how" side of the line. Offline it is almost as
  discriminating as the oracle (38/46 against 40/46 mutants killed).

**Variant and controls:**

* **`D2-oracle`** is optional and kept out of the main comparison (the Codex review recommends the same). Its
  offline edge (40/46 against 38/46) produced no extra live rescue, and it is the variant closest to a
  reference-solution leak. If it is run, label it a statement-authored bounded differential oracle.
* **`D2-inputs-stress`** is the mandatory control: same executions, no contract semantics.
* **A sham gate** with an equal repair opportunity is recommended as a second control.

**Before any next-stage run, fix four things the trajectories exposed:**

1. Calibrate the stress timeout against the judge's time limit (the abc378_e false alarm).
2. Generate large stress inputs inside the sandbox instead of materializing them, so the 8 MB cap stops dropping
   max-scale cases (abc375_c).
3. Include stderr in RE reports (D2 showed `RE: ''`).
4. Replace the "NOT verified … authoritative" header with neutral provenance plus a ready-to-run reproduction
   command. Twice the agent dismissed a valid failure as a harness display issue.

**Expected value.** Small as a standalone condition, because it can act only on PPHF runs: 18/180 of A's official
runs and 0/3 detected on held-out tasks. Its natural place is **C+D**.

### E-v2

* **Strict trigger (the same first-public-failure trigger as E-v1).** Keep **`diagnosis-v1`**. E2-strict did not
  beat it with the provider held fixed, so E2-strict is documented and not promoted.
* **Broader adaptive variant (exploratory), labelled `E2-adaptive`.**
  * At the stall: stall protocol **v2** delivery (streak reset, separate test command).
  * At the first public failure: `diagnosis-v1`.
  * At the first public pass: the silent-unless-verified `E2-review`.
  * At most one intervention per attempt.
  * Run it with the neutral-nudge control (same v2 delivery) and **C-late** as a labelled planning control.
* **Choose the stall content deliberately.** `E2_STALL_V2` is the diagnosis version and keeps E distinct from
  planning. Delivering the frozen plan at the stall (C-late) worked better on both cohorts, but that is planning,
  not diagnosis, and must not be reported as E.

**What E-v2 should not be expected to do:** beat C as a standalone condition.

* **Codex replay.** On held-out tasks no E variant changed an outcome, while C changed two.
* **Paid API.** The E2 diagnoses rescued the same two tasks C did. That is too little, too mixed in provider and
  too partial (no harm-side runs) to rank E2-adaptive against C.
* **If a next-stage benchmark runs E2-adaptive,** it must use the API for every arm with a matched C, more seeds,
  and live policies, not composed ones.

The Codex interpretation review recommends dropping E2-strict and stall diagnosis as standalone contenders, keeping
E-v1 as the historical control, and moving the E effort into a plan-aware E with C (§8). I agree for E2-strict.
For the stall arm, the API result (1/3 rescued, plus two partial runs from nothing) justifies one more exploratory
look, not a primary condition.

## 6. Interpretation: implementation, local agent, or scenario?

**1. Implementation limits were real, and fixing them did not change outcomes.**

* **Contracts.** D-v1's contracts were shallow (0 reasoning tokens on 59/60) and never executed. D2 fixes both:
  833 reasoning tokens per task, harness execution, strong offline bug-completeness.
* **Diagnosis.** E-v1's reach was 18%; E2 triggers on 15/16 held-out tasks. The v1 stall delivery had three
  defects, all fixed in v2.
* **Result.** After these fixes, hidden-test outcomes on held-out tasks did not move.
* **Conclusion.** The original D and E were under-implemented, but their weak results were **not mainly caused**
  by that.

**2. The binding limits are on the local-agent side.** There are three:

* **No program at all.** On the official benchmark 48/180 of A's runs ended without one. Only algorithmic
  content, upfront or late, rescues those runs. A diagnosis of the stalled deliberation gives a correct but terse
  algorithm, which the 9B agent then implements incorrectly.
* **Repair capacity after a correct detection.**
  * A counterexample without localization leads to identical-response loops.
  * Algorithmic repairs push the agent back into deliberating inside the heredoc until the output cap.
  * "Local" fixes mean re-emitting the whole file, often unchanged.
* **The interface.** There is no deliberation channel, no loop detection, a 16k context that overflows in long
  repair sessions, and a format-error budget that caps recovery. These belong to the shared `frozen-v6` agent and
  were kept fixed on purpose.

**3. What is scenario-specific.** Competitive programming failures are dominated by algorithm discovery, which is
what C supplies. D2 and E2 are tools for the remaining cases:

* PPHF programs with performance bugs (D2 stress);
* one-line or few-line local defects (E2-review, E-v1 LOCAL-FIX);
* states where the agent's method is already right.

These are real but rare, so they cannot make D or E competitive standalone conditions here. That matches the
source papers' settings: Endres's postconditions judge given functions, and Tufano's specs come from existing code.
Both assume an implementation to check.

**4. Artifact quality is also a limit, not only the local agent.** This is the strongest case against reading
everything as local-agent limits (the Codex review argued it; the paid-API rows support it):

* On the held-out PPHF states, D2 and E2-review found nothing: a missing stress case, two subtle WAs that escaped,
  and NO-DEFECT verdicts.
* At the same held-out states, API diagnoses rescued 2 tasks where Codex-replay diagnoses rescued none.

So coverage and actionability of the frontier artifact matter, and single artifact draws carry a lot of variance.
Localization is one example: on abc387_c the same counterexample failed bare (D2) and succeeded with a localized
fault and repair (E2-review).

**Answer to the research question.** With well-designed implementations, contract- and diagnosis-based reasoning
did **not** become competitive standalone interventions for this local agent on this benchmark.

* **Diagnosis.** Codex-replay diagnoses were usually correct, yet seldom turned into passing code. The few paid-API
  rescues occurred on exactly the tasks upfront planning also rescues.
* **Contracts.** They were strong offline detectors whose detections were seldom repaired, and they missed the
  held-out failures.

Their defensible roles are specialized and complementary to planning:

* a **verifier** (D2) and **reviewer** (E2-review) behind a plan that has already produced a viable program;
* a **repair aid** for local defects (E-v1).

This is development and small-validation evidence, not a confirmatory result.

## 7. Proposed next-stage benchmark

**Goal.** Compare the enhanced conditions with the frozen originals on fresh held-out tasks, cheaply and with
proper controls.

**Cohort.** About 40 tasks from the unused pinned `test5.jsonl` pool:

* the eligible pool is easy 23, medium 22, hard 51 (the 16 `test5_val16` tasks must be excluded);
* draw 13 medium, 14 hard and 13 easy;
* 3 seeds (2108–2110);
* select deterministically, as `tasks_v2.py` does, and freeze before any run.

**Arms:**

* frozen originals: A, C (`plan-v1`), D-v1, E-v1;
* enhanced: `D2-property`, `D2-inputs-stress` (control), `E2-adaptive` (diagnosis stall content), stall-neutral
  (control), C-late (planning control);
* optional: `D2-oracle`.

**Compute.**

* **Trigger partitioning** cuts the cost to A plus C plus D-v1 on every (task, seed), and the D2/E2 arms only on
  their trigger states. That is roughly 360 full runs plus 150–250 triggered runs.
* **Determinism re-check first.** Rerun 10 A runs and compare submission hashes before relying on partitioning on
  a new host or Ollama build.

**Frontier.**

* Use Codex replay to develop the D2 fixes (§5).
* Use the API only for the final run's artifacts. Estimated paid requests: 40 C plans, 40 D-v1 contracts, 40 D2
  bundles, plus E calls at roughly 1–2 per triggered run. Below $5 at the measured prices.

**Analysis.**

* Paired by (task, seed) against A, with Holm correction over the pre-registered enhanced arms.
* Report trigger reach, delivery, programs produced, and hidden-case partial credit next to pass@1.
* Report C-late separately as planning.

## 8. Recommendations for C+D and C+E

**Why the combinations are promising.**

* **C gives D2 something to verify.** C yields more programs (official 175/180 against A's 132/180) and therefore
  more public-pass states; C had 19 official PPHF runs.
* **C gives E repairable states.** C runs that fail public tests already contain the right method, so E's local
  repairs have something to work with; C had 20 never-passed-public runs.

**Most informative next experiment: frozen-state C+D2 and C+E at the official C failure states.**

* **States.** The 60 official C plans are frozen and C's trajectories are deterministic on this host, so every
  official C run that reached a public pass and failed hidden tests (19), or failed public tests (20), is a
  reproducible trigger state. No new C runs are needed except at those states.
* **Arms.** These follow the Codex review's fork design:
  * **C+D (fork at C's first public pass).** Three arms: a sham gate; D2-property feedback; and the same feedback
    plus an independently verified fault localization. This separates residual defect detection from the ability
    to repair after a useful finding. Keep silent gates in the overall comparison.
  * **C+E (fork at C's own first public failure).** Three arms: a diagnosis that sees C's plan, the candidate and
    the failure evidence; an equally long, identically formatted plan refresh that sees only the statement and the
    prior plan; and a sham with the same remaining repair budget. This tests whether failure evidence adds value
    beyond another dose of planning at the same moment.
* **Cost.** About 39 states × 3 arms ≈ 120 runs (about 3–4 GPU hours). Development can use Codex replay with
  zero API spend. Given the provider gap seen here, the confirming run should use the API for every frontier
  artifact (about 40 calls). Spot-check C determinism first.
* **What it tells you.** Whether a viable plan changes the local agent's ability to use a counterexample or a
  diagnosis. That is the hypothesis this study could not test standalone.

**Prior evidence.** Pass 4 found that C's advantage halves under the `l1-selfplan` agent. Any C+D or C+E result
should be checked against that agent configuration too.

## 9. Reproducibility, costs and limitations

**Prompts (sha256).** `reports/reproducibility_v2.json` lists the hashes, and the exact texts are in
`enhanced_de/e2_diagnosis.py` and `enhanced_de/d2_contract.py`:

* `D2_BUNDLE_V1` `ed475797…`
* `E2_STRICT_V1` `c3499626…`
* `E2_STALL_V1` `29f555be…`
* `E2_STALL_V2` (see the regenerated file)
* `E2_REVIEW_V1` `6203f39c…`
* `NEUTRAL_NUDGE_V1` `43b0ae34…`
* official `plan-v1` `f4f830d2…` and `diagnosis-v1` `3d2c7761…` (unchanged)

**Models.**

* **Local:** `qwen3.5:9b` Q4_K_M, digest `56671c2a…3c90`, on project Ollama 0.40.17 (127.0.0.1:11435). `frozen-v6`
  agent with 16k context, 4,096 output tokens, 20 actions, 3 repair groups and a 600 s budget, unchanged.
* **Frontier:** `gpt-6.2-sol`, effort medium, through isolated Codex replay (`codex-cli 0.172.0`) or the direct API.

**Commands** (Windows host). Use `E:\CSC2108Local\.venv\Scripts\python.exe`, after
`. .\local_baseline\env.ps1; $env:CSC2108_STUDY_ROOT='E:\CSC2108Local\enhanced-de-v2-study'`:

```text
python -m enhanced_de.run_experiments phase1a|phase1b|phase1c [--protocol v2]
python -m enhanced_de.run_phase2_validation run-a | triggers | official-plan | run-arms --arms ... | compose
python -m guided_agent --study <study> batch <study>\plans\<plan>.json ; ... evaluate <batch dir>
python -m enhanced_de.run_phase3_api [--dry-run]
python -m enhanced_de.analyze_v2
python -m enhanced_de.export_sanitized
python -m unittest enhanced_de.test_foundation enhanced_de.test_d2_contract enhanced_de.test_e2_diagnosis enhanced_de.test_phase2
```

**Costs.**

* **Paid API** (`api-ledger.json`, v2 ledger, hard caps 20 requests and $10 conservative). **14 requests, 0
  failed**, no retries:
  * 4 D2 bundle authorings (Neon's provider-parity check, $0.123 standard);
  * 8 Phase 3 E2 diagnoses;
  * 2 completion diagnoses.
* **Token-derived totals.** $0.210 at standard prices, $1.261 under the conservative reservation. Tokens: 29,062
  prompt and 15,210 completion, 4,596 of them reasoning.
* **Codex replay.** Free and not billed: D2 banks for 35 tasks, all live E2 diagnoses in phases 1–2, and 16 test5
  `plan-v1` artifacts. Its token counts include Codex's harness context and are not API-comparable.
* **Local compute.** All GPU work ran on the RTX 4080 SUPER host, sequentially. Median wall time per run, from
  `reports/process_v2.json`:

  | Run type | Median wall time |
  | --- | --- |
  | A (held-out) | 58 s |
  | C (held-out) | 22 s |
  | Public-pass arms (D2, E2-review) | 45–65 s held-out; 90–155 s on development |
  | Strict and stall arms | 140–315 s |

  About 170 live attempts in this continuation session: 15 Phase 1C completions, 37 v2 development runs, 16 A,
  20 official C/E-v1, 56 validation arms, 12 Phase 1B controls and 13 API runs. About 95 in session 1.

**What was not run.**

* **Phase 4, the shared-interface probe** (`shared_interface_v2.py`: L5 carries the discarded deliberation forward;
  L4 adds write receipts). It is implemented by session 1, imports cleanly, and is **unreviewed and never
  executed**. It was dropped for time. Pass 4 had already shown the shared interface is a large lever (`l1-selfplan`
  raised A from 4/16 to 7/16), and the prompt ranks interface work as supporting. It is recommended as a separately
  versioned study with A and C arms.
* **No E-v1 on API at the held-out states.** So API E2-strict has no provider-matched E-v1 comparator.

**Limitations.**

* **Samples.** One seed per state, 12–16 states per cohort, and one frontier sample per artifact. Differences of
  one or two tasks are within noise.
* **Determinism.** Trigger partitioning relies on host determinism. It was checked: every untriggered or silent run
  reproduced A's submission byte-for-byte. A different host or Ollama build needs the check repeated.
* **Exposure.** Development cohorts reuse consumed `final-main` tasks selected on historical outcomes. The test5
  validation cohort is outcome-blind but small, and training-data exposure cannot be excluded.
* **Provider.** Codex replay is not the API. Its diagnoses are unseeded samples of the same model family under a
  different harness. Only §8 uses the API.
* **Isolation.** The Codex replay wrapper has no OS-level read boundary; see the audit. Tools are disabled, there are
  no global instructions and memories are empty, but this is documented as residual risk.
* **E2-review "verified".** It means the program's output differs from the reviewer's hand answer, or the program
  crashes or times out on the reviewer's input. It does not mean the program is wrong. No false delivery was
  observed on correct programs (6/6 offline; see §5 for live safety).
* **Unequal clocks.** D2 gate time is charged to the local clock; E2 frontier waits are excluded from it. Both
  extend container lifetimes.
