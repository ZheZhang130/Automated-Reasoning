# Paper-to-design mapping (pass 2)

How each of the proposal's five method papers shaped a concrete design decision in this pass.
I read the full papers from the local `papers/` folder. Two of them, `2310.01831v2.pdf` (Endres et al.) and
`chong26b.pdf` (CUDAnalyst), exist only as untracked files in the user's `Automated-Reasoning` checkout; they
were read there and not copied or committed. Page numbers are PDF pages.

| Paper | Used for | Mechanism the paper studies |
| --- | --- | --- |
| [4] Endres et al., FSE'24 (nl2postcond) | D: the content of contract-v3 | Can LLMs turn NL intent into checkable postconditions, and how correct and how discriminating are they? |
| [5] Tufano et al., SpecOps'26 | D: the structure of every contract version | Does a semi-formal spec written before the work improve the agent's tests? |
| [3] Chong et al., ICML'26 (CUDAnalyst) | E: the whole diagnosis design | When does an explicit plan help an agent, and how does it depend on feedback? |
| [1] Yang et al., NeurIPS'24 (SWE-agent) | E and B: keep the local agent loop and ACI unchanged | How the agent–computer interface affects agent performance |
| [2] Wang et al., ICLR'25 (PlanSearch) | C: unchanged planning reference | Searching over natural-language plans for code generation |

## [4] Endres et al. — *Can LLMs Transform Natural Language Intent into Formal Method Postconditions?*

**What it studies.**
- **The task (nl2postcond):** generate method postconditions, i.e. assertions relating input and output state, from the natural-language docstring.
- **Two quality metrics** (§2.1, p. 4–5):
  - *test-set correctness*: the reference implementation satisfies the postcondition on all tests;
  - *bug-completeness*: the fraction of distinct buggy implementations the postcondition rejects. The buggy set is LLM-sampled *natural* mutants that fail the tests.
- **Findings:**
  - Explicitly asking for *simple* postconditions makes them more often correct (p = 0.008, p. 9).
  - *Base* (complete) postconditions are more discriminating but more often wrong, and tend to turn into re-implementations (p. 7, 10).
  - Natural language alone is as good as giving the reference code when the description is detailed (p. 9).
  - Natural bugs are harder to kill than seeded ones (p. 10).
  - Type checks are the most common category but kill only 14% of natural bugs. Arithmetic-equality relations between input and output kill 82–89% (Table 3, p. 12).
  - A postcondition is a Boolean property, so it can accept *every* valid output, whereas a test oracle is an equality on one value (p. 17).

**What contract-v3 adopts directly.**
- **POST items as relations:** each is a precise relation between input and output ("an equality, a bound, a 'for every …' property or an 'if … then …' rule"), not a retelling of the story. This targets the strong Table 3 categories over format or type checks.
- **Several simple properties** instead of one complete one, keeping the correctness advantage of the simple prompt.
- **Ordered by discrimination:** properties are listed by how likely a *plausible but wrong* program is to violate them. This is the paper's discrimination criterion, aimed at natural mistakes.
- **Multi-answer tasks:** state the acceptance property instead of one expected output.
- **Statement only:** generation sees no code, which the paper supports for detailed natural-language intent.

**What the evaluation adopts.** `pass2/diagnostics/contract_checks.py` applies both metrics to each contract's concrete checks:
- **Correctness:** a pass-1 program that passed all 40 hidden cases serves as the reference.
- **Bug-completeness:** the distinct pass-1 programs that failed hidden cases serve as the natural mutants. This is the same natural-mutant idea, with real outputs of our own local agent.

**Simplified or adapted.**
- **No executable assertions:** postconditions are natural language, and only the K-checks are machine-checkable. The proposal says contracts are natural language and not formally checked, and our coding agent writes stdin/stdout programs, not functions.
- **One sample per task:** Endres samples 10 per prompt and reports accept@k; we generate one contract per task and never resample.
- **Few mutants:** our pool has 0–8 per task, not 4–233.

**Why it stays faithful.** The mechanism we transfer is that precise, discriminating behavioral requirements derived from natural-language intent can separate correct from plausible-wrong programs. The coder still gets only WHAT is correct.

**Claims we cannot make.** We do not measure postcondition correctness as the paper does (no executable postconditions, single sample, tiny mutant pools), so no accept@k or bug-completeness numbers are comparable to the paper's.

## [5] Tufano et al. — *Grounding AI Agents in Contracts: Spec-Driven Test Generation*

**What it studies.**
- **Setup:** a two-phase agent (Gemini 3 Flash, p. 4).
- **Phase I** reads the code under test and existing tests, then writes a semi-formal `.spec.md` (§2, p. 2): description, preconditions, postconditions, and condition-linked test suggestions. Each condition is marked Tested or Untested.
- **Phase II** turns the spec into tests; the spec is "the blueprint reasoning plan for the subsequent test generation phase" (p. 3).
- **Results:** +9.8 pp bug detection and +2.5 pp branch coverage over a same-harness baseline. When the spec captures the violated contract, the tests catch the bug 54.9% of the time, against 19.4% when it does not (ContractCoverage, p. 2, p. 6).

**What every contract version adopts.**
- **The structure:** the teammates' five headings (Description, Preconditions, Postconditions, Test suggestions, Unspecified behavior).
- **Linked checks:** test suggestions tied to PRE/POST IDs.
- **Unverified marking:** every condition is marked *Unverified*, because the contract author sees no code or test outcome.

**What contract-v3 adds.**
- **The violated contract first:** the paper's key predictor is whether the spec captures the condition the faulty code violates, so v3 asks for the most commonly violated requirements first.
- **Checks naming their misreading:** each K-check names the *misreading* it exposes. That makes each check traceable to a requirement and to a failure mode.

**Simplified or adapted.** The direction is reversed:
- the paper extracts contracts from **existing code** to guide **test generation**;
- we derive them from the **statement** to guide **implementation** by a different, smaller model.

The proposal states this adaptation explicitly (§2). Our contract author and coder are different models. There is no Tested state, because nothing has been run.

**Claims we cannot make.** We do not reproduce spec-driven test generation, ContractCoverage or the paper's bug-detection gains.

## [3] Chong et al. — *Towards Feedback-to-Plan Decisions for Self-Evolving LLM Agents in CUDA Kernel Generation* (CUDAnalyst)

**What it studies.** An analysis layer that feeds structured feedback reports about the *current* program state into an explicit PlanAgent (§3.1, p. 2), with controlled interventions at frozen generations (§3.2, p. 3). Findings:
- **RQ0 (p. 4):** explicit planning without feedback degrades results; feedback-grounded planning gives stable gains, "particularly for weak-reasoning models". Randomized (misaligned) feedback harms all models.
- **RQ2 (p. 6):** summarizing feedback helps mainly weaker models, by reducing their representational burden.
- **RQ3 (p. 7):** plans from stronger models transfer partially to weaker ones.

**What E adopts directly.**
1. **Grounded in current evidence:** the diagnosis is conditioned on the actual failed program and *its* public-test report, bound by sha256 of the judged bytes and of the report. This addresses the paper's main warning, misaligned feedback; we never diagnose a later source version.
2. **Explicit evidence/decision boundary:** a fixed evidence packet (statement, submission contract, tested program, public report, local budget state), everything between nonce-delimited DATA markers treated as untrusted data, and one fixed `diagnosis-v1` prompt. This mirrors the role of the PlanAgent prompt (App. D.4, p. 31).
3. **Summary, then decision:** `## Observed failure` is a short evidence summary for the weak model (RQ2). Then come `## Likely cause`, `## Repair direction` and `## Verification target`, the plan-like decision (RQ0).
4. **Stronger to weaker:** the diagnosis comes from a stronger model to the weak local coder (RQ3).
5. **Intervention at a frozen state:** with the frozen sampler (temperature 0.2, fixed seed), E's trajectory up to the trigger reproduces A's. The diagnosis is therefore an intervention at a fixed program state, our analogue of trajectory freezing, which makes the paired E-versus-A comparison unusually clean. This can be checked per task, and the experiment log records it.

**Simplified or adapted.**
- **Feedback sources:** only one (the public judge report). There are no static analyzers, sanitizer or profiler, and no Banzhaf attribution.
- **One intervention per task,** as the proposal specifies (§3.2), not a persistent plan across generations.
- **Python correctness, not CUDA performance.**
- **No length-matched dummy-diagnosis control** (the paper's DummyPlan). It is listed as recommended future work.

**Claims we cannot make.** No attribution of effects to feedback components, no generalization across backbones, and no claim that we reproduce CUDAnalyst.

## [1] Yang et al. — *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*

**What it studies.** How ACI design changes agent performance: simple and compact actions, informative but concise feedback, guardrails (§2, p. 3), and editor, linter and history design (p. 4).

**What we adopt.** Every pass-2 condition runs the same mini-SWE-agent ACI, unchanged:
- **E** inserts one user message into the *existing* conversation. It never restarts the agent, resets history, files, container or counters, or adds an action.
- **B** substitutes only the model, keeping the frozen text action parser, the observation template, the sandbox and judge-public.
- **No ACI intervention for D:** no ACI change is given to D, so condition differences stay in the reasoning channel, consistent with the proposal ("focus on guidance … rather than improvements to the agent-computer interface", §2).

**Claims we cannot make.** Nothing about ACI design effects. The pass-1 aci-v1/v2 variants are not used.

## [2] Wang et al. — *Planning in Natural Language Improves LLM Search for Code Generation* (PlanSearch)

**What it is used for.** Condition C keeps `plan-v1` (observations plus a solution sketch, the single-plan reduction from pass 1) and `inject-v1`, unchanged. The paper's finding that outcomes polarize on whether the sketch is correct (p. 4–5) explains why C is the planning reference.

**Simplified.** No search over plans, observation combinations or a pseudocode stage. Single-plan transfer is what the proposal specifies.

## Why the pass-2 designs stay within the proposal

| Condition | Proposal text (§3.2) | Pass-2 implementation |
| --- | --- | --- |
| B | "the frontier model will directly perform these tasks" | The frontier model is the coding model inside the same mini-SWE-agent loop and judge |
| D | "a behavioral contract … preconditions, postconditions, invariants, and important edge cases … what the solution must satisfy rather than how" | contract-v3: precise, discriminating POST items and K-checks; no algorithm; one upfront artifact |
| E | "called after the local agent encounters its first qualifying failure … receive the original task, the attempted implementation, and relevant test feedback … repair suggestions without directly supplying replacement code … limit this intervention to one per task" | Exactly this: first qualifying public failure, one call, no code blocks allowed, delivered into the same session |

No new frontier stage was added: there is no verification call for D, no second diagnosis for E, and no combined condition F.
