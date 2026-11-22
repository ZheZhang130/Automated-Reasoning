# Final report: frontier reasoning for a local coding agent (overnight pass, 2026-11-21/22)

**Preliminary, exploratory evidence.** 4 development tasks and 10 fresh tasks, one seed for the fresh tasks, one machine (Windows, RTX 4080 SUPER).
Codex-authored guidance replay and direct-API guidance are reported separately and never pooled. No statistical significance is claimed.

## Short answers

| # | Question | Answer |
| --- | --- | --- |
| 1 | Is frontier planning functional? | **Yes.** One request per task from the statement only, validated, task-bound, injected into the first user message of the unchanged frozen agent. Exercised with Codex replay (10 plans) and the direct API (5 plans). |
| 2 | Is contract generation functional? | **Yes.** Same path (14 Codex contracts including 4 contract-v2, and 5 API contracts). The contracts are accurate and stay behavioral: no algorithms. |
| 3 | Does planning help? | **Yes, consistently, in every cohort.** Dev mediums: C 4/4 vs A 1/4. Fresh tasks: C 7/10 vs A 5/10 (official judge), 9/10 vs 6/10 with correct checkers. C never lost a task A solved, and it used ⅛ (dev) to ⅓ (fresh) of A's local completion tokens. |
| 4 | Do contracts help? | **Not shown.** Dev mediums: D 0/4 vs A 1/4. Fresh tasks: D 6/10 vs A 5/10 (official), 8/10 vs 6/10 (corrected). The gain comes from the direct-API cohort (abc393_d, abc396_e) and is within noise. Contracts never fixed an algorithm-discovery failure. |
| 5 | When does each help? | Planning: when the bottleneck is the **algorithmic insight**, and the plan is **simple to implement**. Contracts: when the failure is a **misread requirement** (abc393_d: "adjacent swaps"). |
| 6 | When does each fail? | Planning: when the plan is correct but hard to implement (API DP plan on arc192_a), or when implementation repair loops (abc391_e). Contracts: whenever the algorithm is not obvious, because Qwen still brainstorms in-file and truncates. |
| 7 | Where are the problems? | Mostly **local reasoning surfacing through the mini-SWE-agent output/format path**, not frontier guidance. No frontier guide was wrong. Two of tonight's fresh-task "failures" were **judge false negatives**. |
| 8 | Which modifications measurably improved things? | None that survived fresh tasks. aci-v2 improved delivery on dev tasks but tied or regressed on fresh tasks. The Windows LF fix to task building is an infrastructure correction, not a performance change. |
| 9 | Which approaches were ineffective? | aci-v1 (feedback notes), aci-v2 (repeat guard) on fresh tasks, and contract-v2's "run the checks" instruction (never executed). |
| 10 | Retain, modify or reconsider mini-SWE-agent? | **Retain** as the primary backend. Its observed weaknesses (in-file brainstorming → 4,096-token truncation; deterministic identical-rewrite loops) are real, but upfront plans largely bypass them. Targeted text-feedback fixes did not help, so a deeper ACI change (history management, edit tool) is the next agent experiment, separately controlled. |
| 11 | Adherence to proposal and papers? | High for C/D and the controls: same agent, tools, budgets and judge; one upfront intervention; frontier never writes code. Deviations are listed in §8. |
| 12 | Next controlled experiment? | §9: the main A/C/D cohort with ≥3 seeds on judge-supported tasks, plus a plan-form ablation (compact/closed-form vs. full sketch) and E (diagnosis). |
| 13 | Ready to freeze for the real benchmark? | **A, C and D on the original agent: yes**, after the judge/task-pool fixes in `BENCHMARK_READINESS.md` §3. aci variants and contract-v2: no. B and E: not yet integrated. |
| 14 | Windows and macOS? | Windows: fully exercised (real inference, both host backends, identical tokens). macOS: software-compatible and tested on Linux POSIX, but **native Mac inference was not validated tonight**. §10. |

## 1. System as run

* **Backend.** `guided_agent` runs the unchanged frozen `local_eval_v2/runtime.run` bytecode (mini-SWE-agent 2.4.6, LiteLLM 1.81.16, Qwen3.5 9B Q4_K_M digest `56671c2a…`, `heredoc-v6-16k-common`: 16K context, 4,096 output tokens, temperature 0.2, top-p 0.9, top-k 40, min-p 0, repeat 1.0/64, non-thinking, seed 2108; 20 actions, 3 repair groups, 600 s, ≤180 s per request). Every attempt re-verified the 38 frozen hashes and the sampler wire options. Only the first-message template (guidance) and the public-test command (routed to judge-public) are rebound, identically for A/C/D.
* **Evaluation.** Peter's `csc2108-judge:0.2.1`. Public results are fed to the agent; the hidden suite is scored after all attempts. "Correct" means all 40 hidden cases AC.
* **Budget policy.** Equal local coding opportunity: guidance is generated before the run and replayed, so frontier latency is not deducted from the 600 s. Frontier time and cost are reported separately (§5).
* **Guidance.** `plan-v1` and `contract-v1` are the teammates' prompts, unchanged. Codex: `gpt-6.2-sol`, effort medium, isolated `codex exec`. API: `gpt-6.2-sol`, effort medium, 8,000 max completion tokens.

## 2. Results

Notation: ✓ = all hidden cases pass; ✗ k/40 = hidden cases passed; "none" = no candidate (exit reason shown).

### 2.1 Fresh mini-benchmark 1: Codex-authored guidance replay, original agent

| Task (difficulty) | A | C | D |
| --- | --- | --- | --- |
| abc396_a (E) | ✓ | ✓ | ✓ |
| abc392_d (M) | ✗ 15/40 † | ✗ 15/40 † | ✗ 15/40 † |
| abc390_c (M) | ✓ | ✓ | ✓ |
| abc396_d (M) | ✓ | ✓ | ✓ |
| abc394_c (M) | ✓ | ✓ | ✓ |
| abc388_g (H) | none (`RepeatedFormatError`) | **✓** | none (`RepeatedFormatError`) |
| **Correct (official judge)** | **4/6** | **5/6** | **4/6** |
| Correct, statement-tolerance check † | 5/6 | **6/6** | 5/6 |
| Length-truncated responses | 3 | 0 | 4 |
| Local completion tokens | 14,961 | 2,753 | 18,226 |
| Local coding seconds | 215 | 89 | 246 |

† abc392_d accepts error ≤ 1e-8, but the judge requires exact decimal equality. All three candidates pass 40/40 under the stated tolerance (`diagnostics/`).

### 2.2 Fresh mini-benchmark 2: direct OpenAI API guidance, original agent (LCB "hard", ABC D/E)

| Task | A | C | D |
| --- | --- | --- | --- |
| abc393_d | ✗ 9/40 (`RepairLimit`) | **✓** | **✓** |
| abc396_e | ✗ 18/40 | ✗ 26/40 ‡ | ✗ 28/40 ‡ |
| abc393_e | ✓ | ✓ | ✓ |
| abc391_e | none (`RepeatedFormatError`) | ✗ 5/40 (`ActionLimit`) | none (`RepeatedFormatError`) |
| **Correct (official judge)** | **1/4** | **2/4** | **2/4** |
| Correct, special judge ‡ | 1/4 | **3/4** | **3/4** |
| Length-truncated responses | 5 | 1 | 3 |
| Local completion tokens | 31,106 | 14,506 | 18,108 |
| Local coding seconds | 379 | 239 | 247 |

‡ abc396_e accepts any minimum-sum valid sequence, but the judge compares against one reference output. Under a validity checker (all XOR constraints plus the reference sum): C 40/40, D 40/40, A 24/40.

### 2.3 Paired outcomes on the 10 fresh tasks (original agent)

| | Rescued vs A (official) | Rescued vs A (corrected) | Harmed vs A |
| --- | --- | --- | --- |
| C (plan) | abc388_g, abc393_d | + abc396_e | none |
| D (contract) | abc393_d | + abc396_e | none |

Tasks solved by every condition: abc396_a, abc390_c, abc396_d, abc394_c, abc393_e (and abc392_d under tolerance). Solved by none: abc391_e.

### 2.4 Development tasks (repeatedly examined; diagnosis only, not generalization)

Medium dev tasks arc192_a and arc195_a; both easy tasks were solved by everything:

| Configuration | arc192_a (s2108 / s2109) | arc195_a (s2108 / s2109) | Correct |
| --- | --- | --- | --- |
| A original | none / 39/40 | 39/40 / ✓ | 1/4 |
| C original | ✓ / ✓ | ✓ / ✓ | **4/4** |
| D original | 20/40 / none | none / none | 0/4 |
| A aci-v1 · C aci-v1 · D aci-v1 (s2108) | 29 · ✓ · none | 37 · ✓ · 17 | A 0/2 · C 2/2 · D 0/2 |
| A aci-v2 · C aci-v2 · D aci-v2 (both seeds) | 29, 39 · ✓✓ · none, 39 | ✓, 39 · ✓✓ · 38, ✓ | A 1/4 · C 4/4 · D 1/4 |
| D contract-v2 (s2108) | 30/40 (`ActionLimit`) | ✓ | 1/2 |

### 2.5 aci-v2 arm on the fresh tasks (secondary, separately labeled)

| Cohort | A | C | D | vs original agent |
| --- | --- | --- | --- | --- |
| MB1 (Codex) | 4/6 | 5/6 | 3/6 | D lost abc394_c: 39/40 after 22 repeat guards → step limit |
| MB2 (API) | 1/4 | 2/4 | 2/4 | identical outcomes |

## 3. How and why planning helps (trajectory evidence)

* **It removes the in-file algorithm search.** Without a plan, Qwen writes its reasoning as `#` comments inside the heredoc. Rejected responses run 11–16K characters ("Actually, let's use a simpler approach…") and end at the 4,096-token limit before the command fence closes. Three in a row end the run (`RepeatedFormatError`, no candidate). Across all original-agent runs (dev, both seeds, fresh cohorts and the provider comparison), length-truncated responses were **C: 2 in 19 attempts**, A: 16 in 18 and D: 21 in 19.
* **The code follows the plan.** arc195_a C's first program is the plan's forward/backward greedy scan. abc388_g C, a hard ABC-G, implements the plan's pᵢ, pᵢ−i transform, sparse table and binary search over K in **3 actions**; A and D never produced a program. Several C programs quote the plan in comments ("the stronger model's observation 4").
* **It makes runs cheaper.** Fresh tasks: C used 17,259 local completion tokens vs 46,067 (A) and 36,334 (D), and 328 s vs 594 s (A) of local coding time.
* **Repair still happens locally.** C found an index-order bug in arc195_a by tracing the failing public case and fixed it in one edit.

## 4. When the reasoning fails

* **Correct but hard-to-implement plans** (provider comparison, arc192_a). Codex gave a closed-form parity / N mod 4 rule: C ✓ in 6/6 runs. The API gave an equally correct cyclic DP over "center" bits: C ✗ 21/40, with a cyclic pair-indexing error. *Plan form, not just correctness, governs transfer* (n=1; not a provider claim).
* **Local implementation plus repair loops.** abc391_e C: correct tree-DP plan; first program wrong on sample 1; Qwen then rewrote the same file **17 times byte-identically** until the action limit.
* **Contracts cannot supply algorithms.** On every medium/hard task where A failed for lack of an algorithm (arc192_a, arc195_a, abc388_g, abc391_e), D failed the same way: in-file brainstorming → truncation. Where D helped, the issue was **interpretation**. abc393_d A modelled arbitrary swaps (`k − max ones in a window`); D's contract stressed adjacent swaps, and its code says "Since we can only swap adjacent elements" before using the correct median formula.
* **Unused verification.** contract-v2's hand-derived checks were correct and would have exposed D's wrong arc192_a heuristic (fails `4 / 0 0 0 0 → Yes` and `5 / 0 0 1 0 0 → Yes`). The coder never ran them, despite an explicit instruction.

### Failure attribution (fresh tasks, original agent; categories from the brief)

| Failure | Primary cause |
| --- | --- |
| abc388_g A, D; abc391_e A, D (no submission) | (6) output budget exhausted by in-file brainstorming → (4) delivery; underlying (3) no algorithm |
| abc393_d A | (3) misread requirement; then repair-limit |
| abc396_e A | (3) local algorithmic error (24/40 under the special judge) |
| abc391_e C | (3) implementation bug → (5) ineffective repair (identical-rewrite loop) |
| abc392_d A/C/D; abc396_e C/D | (7) **evaluation**: judge lacks tolerance / special checking |

No failure traced to incorrect frontier reasoning; every guide checked by hand (§6) was correct. There were no infrastructure or setup failures in 117 agent attempts, and no context truncation (largest prompt 9,620 of 16,384 tokens).

## 5. Cost and compute

| Item | Value |
| --- | --- |
| Paid API requests | **10 of 12**: 2 connectivity / provider-comparison, 8 MB2; all `finish_reason=stop`; no retries |
| API spend | **$0.0832** at the verified standard rate ($2 / $10 per 1M); ≤ $0.50 under the most conservative listed tier |
| API latency per guidance | plan 7.3–22.1 s (median ~10 s); contract 5.8–7.2 s |
| API tokens per guidance | 550–987 input; 429–1,415 output (0–512 reasoning) |
| Codex replay | 24 artifacts; harness wall 8.5–45 s (median 14 s). Cost, latency and observed model identity are **unknown**; Codex token counts include ~10.9K tokens of harness context |
| Guidance length | plans median 345–449 words; contracts 275–330 words |
| Local compute | see tables; C is cheapest in every cohort |

Saved-guidance replay does not include generation time in the runner's wall time. End-to-end time per guided task ≈ local coding time plus ~10 s (API).

## 6. Guidance quality

Every plan I checked by hand against its public statement was correct and named a workable algorithm with complexity: 8 of the 10 Codex plans (arc195_a, arc192_a, abc391_a, abc392_d, abc390_c, abc396_d, abc394_c, abc388_g) and 4 of the 5 API plans (arc192_a, abc393_d, abc391_e, abc396_e). The rest were not read in full, but their C runs gave no sign of wrong guidance. Lengths: plans 192–629 words, contracts 187–377. Contracts were precise and behavioral (PRE/POST, M=1 and M=N boundaries, hand-derived small checks); none leaked an algorithm. The contract-v2 checks I hand-verified (6 for arc195_a, 3 for abc400_b, 6 for arc192_a) were all correct. Verbosity was not a problem: no prompt overflow, and Qwen used long plans successfully. The main quality dimension that mattered was **implementation simplicity of the chosen method**.

## 7. Interventions

| Family | Hypothesis | Change | Success criterion | Outcome | Decision |
| --- | --- | --- | --- | --- | --- |
| Seed replication | dev differences are stable | seed 2109 | — | C stable 4/4; A varies; D 0/4 | (measurement) |
| aci-v1 (shared) | notes reduce identical rewrites / truncation loops | specific length message; "[harness] unchanged" notes | fewer loop exits, no correctness loss | notes ignored 14–19× per run; more action-limit exits | **Reject** |
| aci-v2 (shared) | removing duplicate turns breaks loops | repeat guard (not executed, de-duplicated history) + aci-v1 | fewer loop/format exits, +1 A/D correct, C unchanged | dev: met by one task; fresh: tie, plus one D regression (22 consecutive guards) | **Reject for promotion** (keep code, off) |
| contract-v2 (D only) | discriminating checks + "run them" catch wrong programs | prompt + injection | D correctness up | 1/2; checks never executed | **Not promoted** |
| Plan prompt | — | none; plan-v1 was already effective | — | — | keep plan-v1 |

Qwen's identical-rewrite loops are a decoding attractor: at temperature 0.2 with a fixed seed it regenerates the same command after notes or guards. Text feedback at the observation level did not break it.

## 8. Adherence to proposal and papers

* **Followed:** one local model, tools, budgets (20 actions ≈ proposal's ~20, 3 repairs, 600 s) and judge across A/C/D. One upfront frontier intervention, from public information only. The frontier never writes code. Private tests used only for scoring. Easy/medium/hard tasks from LiveCodeBench.
* **PlanSearch:** reduced to a single observation + sketch request (no subset combination, diversity search or pseudocode stage). The paper's finding that outcomes polarize on sketch correctness matches what we saw: when the sketch was right *and implementable*, Qwen succeeded.
* **Spec-driven contracts:** derived from requirements to guide implementation (the paper extracts them from code to guide test generation). Conditions stay Unverified. The paper's own result, that a spec helps when it captures the violated behavior, matches abc393_d.
* **SWE-agent:** frozen bash ACI. Tonight's ACI experiments (feedback notes, repeat guard) were labeled interventions and are not adopted.
* **Deviations, documented:** Codex replay instead of the API for most guidance (isolation verified from events; harness context unavoidable). MB2 uses hard (ABC D/E) instead of medium tasks, because no fresh medium tasks remained. Mini-benchmarks are one seed. Ollama 0.40.17 instead of 0.40.16. Hidden scoring of the primary cohorts ran while the aci-v2 arm executed (20-core host, 4-CPU judge). Two selected tasks need checkers the team judge lacks; official scores are primary, corrected scores secondary.

## 9. Recommended next configuration and experiment

1. Freeze: original frozen agent + `plan-v1` / `contract-v1` + `inject-v1`; direct API `gpt-6.2-sol`, effort medium, 8K cap; judge 0.2.1 restricted to exact-match-gradable tasks (or add tolerance/special checkers).
2. Main controlled run: A/C/D (+E once integrated) on the frozen main cohort, ≥3 seeds, paired bootstrap over tasks.
3. Focused ablation motivated tonight: **plan form**. The same planner asked for (a) the current sketch vs (b) a "simplest correct method" constraint, on medium/hard tasks, original agent.
4. Separately: an ACI experiment on history management or an edit/replace tool against the identical-rewrite attractor, with its own A/C/D control, before any change to the agent.

## 10. Platform validation

| Level | Windows | macOS |
| --- | --- | --- |
| Software compatibility | ✓ | POSIX code path tested on Linux (Python 3.11.18 container: 27 tests incl. real `fcntl` lock) |
| Mocked host contracts | ✓ 18 `guided_agent` + `local_agent` suites | covered by the same platform-neutral tests and the `system='Darwin'` composition test |
| Portable adapter with real Docker + Qwen | ✓ `--backend portable` on Windows: fixture ✓, arc195_a C ✓, **token-for-token identical** to the Windows backend | **not run** |
| Native inference | ✓ CUDA | **not validated (no Mac)** |
| Cross-hardware equivalence | not established | — |

## 11. API request and spending ledger

| # | Task | Kind | Purpose | In / out (reasoning) tokens | Latency | Cost (standard) |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | `GET /v1/models/gpt-6.2-sol` | access check, no inference | — | — | $0 |
| 1 | arc192_a | plan | connectivity + provider comparison | 917 / 1,415 (512) | 22.1 s | $0.0160 |
| 2 | arc192_a | contract | connectivity + provider comparison | 987 / 497 (0) | 7.2 s | $0.0069 |
| 3 | abc393_d | plan | MB2 | 550 / 804 (90) | 11.0 s | $0.0091 |
| 4 | abc396_e | plan | MB2 | 863 / 820 (0) | 10.1 s | $0.0099 |
| 5 | abc393_e | plan | MB2 | 631 / 724 (0) | 9.2 s | $0.0085 |
| 6 | abc391_e | plan | MB2 | 660 / 570 (37) | 7.3 s | $0.0070 |
| 7 | abc393_d | contract | MB2 | 620 / 437 (0) | 6.3 s | $0.0056 |
| 8 | abc396_e | contract | MB2 | 933 / 560 (0) | 7.0 s | $0.0075 |
| 9 | abc393_e | contract | MB2 | 701 / 550 (0) | 7.0 s | $0.0069 |
| 10 | abc391_e | contract | MB2 | 730 / 429 (0) | 5.8 s | $0.0058 |
| | | | **Total** | 7,592 / 6,806 | | **$0.0832** |

Machine-readable: `evidence/api-ledger.json`. All requests used `openai/gpt-6.2-sol` as configured (observed model `gpt-6.2-sol`), reasoning effort medium, 8,000 max completion tokens.

## 12. Limitations

Small samples (10 fresh tasks, one seed). Development tasks were examined repeatedly. Hard-label MB2 tasks. Two judge-incompatible tasks in the fresh cohorts. Codex harness context differs from the API. Near-deterministic decoding means one seed under-represents variance. Single Windows machine; Mac native inference untested.
