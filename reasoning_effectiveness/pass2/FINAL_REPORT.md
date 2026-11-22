# Pass 2 final report — contract refinement, frontier diagnosis (E) and frontier only (B)

Branch `feat/csc2108-contract-diagnosis-pass2`. Every local run uses the original frozen agent: Qwen3.5 9B
Q4_K_M, mini-SWE-agent 2.4.6, `heredoc-v6-16k-common`, 20 actions, 3 repair groups and 600 s, with judge
0.2.1 and frozen hashes verified.

The cohorts are reported separately and never pooled:

* **Development:** tasks already consumed in pass 1, with known outcomes.
* **Validation:** 5 fresh, outcome-blind tasks frozen before any run (`FREEZE-val.json`).
* **Codex-authored replay versus direct API.**

Nothing here is statistically significant.

## Headline

* **C (planning) remains the best-supported condition.** On the frozen validation cohort C solved 4/5
  against A's 2/5. It rescued abc388_e and abc398_d and harmed nothing. It also used the fewest local
  tokens: 8.8k, against 26–37k for the other conditions.
* **contract-v3 is a better specification but not a better intervention.**
  * Its checks are 32/32 correct against reference programs and kill 14/15 natural plausible-but-wrong
    programs (Endres-style).
  * Development: D-v3 3/8 against D-v1 4/8 and A 3/8. Validation: D-v3 1/5, D-v1 2/5, A 2/5.
  * Qwen **never ran a contract check** (0 self-check commands in every D run of both passes).
  * Most D failures happen before any program exists: the 4,096-token in-file brainstorming truncation.
  * On abc399_f both contract texts derailed a first attempt that A gets right.
  * **Keep contract-v1 as D.**
* **E is fully implemented and works mechanically.**
  * One frontier diagnosis of the first qualifying public failure is inserted into the *same running*
    mini-SWE-agent session (no restart, continuous counters, frontier wait excluded from local time).
  * Integration tests pass 6/6 on the Windows and portable backends. Live diagnoses from Codex and the
    direct API were delivered to real Qwen.
  * Diagnoses were **accurate in every triggered run** and visibly used.
  * E **rescued one task** (abc393_d, under both providers: A 9/40 → E 40/40). On validation it tied A at 2/5.
  * It triggered only 1 of 5 times on fresh tasks: two passed at the first test, and two never reached a
    public test because of truncation.
  * When the diagnosis carries an algorithmic fix, Qwen often implements it superficially.
* **B works end to end through the shared interface** on a synthetic fixture, via the direct API
  (3 requests, $0.0028) and via Codex replay. It has not been benchmarked.
* **API use this pass: 7 of 12 requests, $0.0327** at standard prices ($0.20 conservative bound). Pass-1
  history was 10 requests and $0.0832, so the cumulative total is 17 requests and $0.116.

## 1. Results

### 1.1 Frozen validation cohort (fresh, outcome-blind, Codex guidance, seed 2108)

Cells show the hidden result, then format errors and actions.

| Task (difficulty) | A | C plan-v1 | D-v1 | D-v3 | E-v1 (trigger) |
| --- | --- | --- | --- | --- | --- |
| abc394_b (easy) | ✓ 40/40 | ✓ | ✓ | ✓ | ✓ (no failure → not triggered) |
| abc399_f (hard) | ✓ 40/40 | ✓ | ✗ 0/40 (15 act, repair limit) | ✗ 20/40 (10 act, repair limit) | ✓ (not triggered) |
| abc398_d (hard) | ✗ 36/40 (TLE×4) | **✓ 40/40** | ✗ 36/40 (TLE×4) | ✗ 36/40 (TLE×4) | ✗ 36/40 (TLE×4; **triggered**, delivered) |
| abc388_e (hard) | ✗ no program (3 fmt) | **✓ 40/40** | **✓ 40/40** | ✗ 31/40 | ✗ no program (not triggered: no public test) |
| abc396_f (hard) | ✗ no program (3 fmt) | ✗ 5/40 (command time-out) | ✗ no program | ✗ no program | ✗ no program (not triggered) |
| **Total** | **2/5** | **4/5** | **2/5** | **1/5** | **2/5** |

Paired with A:

| Condition | Gains | Harms |
| --- | --- | --- |
| C | 2 (abc388_e, abc398_d) | 0 |
| D-v1 | 1 (abc388_e) | 1 (abc399_f) |
| D-v3 | 0 | 1 (abc399_f) |
| E | 0 | 0 |

### 1.2 Development (pass-1 references at the same seed, token-identical by verification)

| Task | A | C | D-v1 (pass 1) | D-v3 | E Codex | E API |
| --- | --- | --- | --- | --- | --- | --- |
| arc192_a | ✗ none | ✓ | ✗ 20/40 | ✗ none | ✗ none (not triggered) | — |
| arc195_a | ✗ 39/40 | ✓ | ✗ none | ✗ none | ✗ 39/40 | ✗ 39/40 |
| abc393_d | ✗ 9/40 | ✓ | ✓ (API) | ✓ | **✓ 40/40** | **✓ 40/40** |
| abc394_c | ✓ | ✓ | ✓ | ✗ 39/40 (rewrite loop) | — | — |
| abc390_c | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| abc388_g | ✗ none | ✓ | ✗ none | ✗ none | — | — |
| abc391_e | ✗ none | ✗ 5/40 | ✗ none | ✗ none | — | — |
| abc391_a | ✓ | ✓ | ✓ | ✓ | — | — |

Second seed (2109) and the direct-API comparison at the same frozen states: see §1.3, §1.4 and
`evidence/pass2-tables.md`.

### 1.3 Second seed (2109)

*(filled in below from `evidence/pass2-tables.md`)*

### 1.4 Direct-API comparison

*(filled in below)*

## 2. Answers

**1. Did contract-v3 improve over contract-v1?**
No. Development: 3/8 against 4/8. Validation: 1/5 against 2/5, with the same tasks failed except abc388_e,
where v1 was ✓ and v3 scored 31/40.

v3's *checks* are far better: v1's are prose and not machine-checkable, while v3's are 32/32 correct and
kill 14/15 mutants. But the outcome differences come from (a) truncation before any program exists and
(b) prompt-text perturbation of a near-deterministic first attempt (abc399_f, abc394_c, arc192_a), not from
the specification content.

**2. Which ideas from Endres and Tufano were most useful?**
As *specification quality* levers, Endres's were:

* relational input–output postconditions instead of format checks;
* simple atomic properties;
* discrimination against natural plausible-wrong implementations; this was also the most useful
  *evaluation* idea, turning pass-1 programs into a mutant pool.

From Tufano, the most useful was condition-linked checks that name the violated requirement. None of these
translated into outcome gains for this agent.

**3. Did Qwen use the contract's behavioral information?**
Partly. It **never executed** a contract check. It did absorb *interpretive* content: every contract fixed
abc393_d's adjacency misreading, and D-v1/D-v3 produced a program on abc388_e where A truncated. But D-v3's
own failing program on abc394_c violated its K-1, which was never run.

**4. Is Condition E fully implemented?**
Yes. It has the trigger, evidence packet, live Codex/API/fixed/replay providers, validation, delivery, time
accounting, records, CLI support, and offline plus integration tests (`DIAGNOSIS_INTEGRATION.md`).

**5. Does E preserve the original local agent session?**
Yes, by construction and by test:

* the same agent object, history, sandbox container, workspace and budget object;
* one appended user message, placed after the public report;
* the integration test asserts that the coder's message history only grows (2 → 4 → 7 → 9 → 11) and that
  the action counter is continuous.

In live runs, the pre-trigger history is byte-identical to A's.

**6. Are local budgets comparable across A/C/D/E?**
Yes, in local opportunity: the same 20 actions, 3 repairs, 600 s of local time and 180 s per request.
The frontier wait (4.9–12.8 s in live runs) is excluded from E's local deadline and agent wall clock.

The sandbox container's lifetime is extended for E (990 s instead of 660 s); that is a container setting,
not an agent budget. End-to-end wall time differs and is reported. Upfront C/D generation latency is not in
any local budget either.

**7. How often did E trigger?**

* **Development:** 3/4 at seed 2108 (tasks chosen because A's first test failed), plus the seed-2109 runs
  in §1.3.
* **Validation:** **1/5 (20%)**. The untriggered runs: 2 passed the first public test, and 2 never ran a
  public test (all three responses truncated).

**8. Were frontier diagnoses accurate and useful?**
Accurate in all delivered cases checked: arc195_a (Codex and API), abc393_d (Codex and API), abc390_c and
abc398_d. Each named the observed mismatch and a correct likely cause in the program (wrong counter
semantics, a misread adjacency rule, a 1-/0-based mismatch, an off-by-one timing).

Useful in 2 of 4 tasks:

* abc393_d: rescue;
* abc390_c: quick repair, though A self-repaired too;
* arc195_a: no rescue with either provider (39/40);
* abc398_d: no rescue. The diagnosis correctly anticipated the time limit, but Qwen copied its vocabulary,
  not its method.

**9. Did E rescue failed local implementations?**
Once: abc393_d (A 9/40 → E 40/40), reproduced with both providers at the same frozen state. Validation: 0/1
triggered.

The paired API-versus-Codex run on arc195_a shows that diagnosis specificity matters for *public* recovery.
The API diagnosis also named the `popleft()` ordering bug, so Qwen passed the public tests. But the hidden
result (39/40) was unchanged.

**10. What causes E to fail or remain untriggered?**

* **Untriggered:**
  * truncated responses before any public test (arc192_a, abc388_e, abc396_f);
  * a first-test public pass (abc394_b, abc399_f, abc393_d at seed 2109);
  * hidden-only failures are invisible by design.
* **Triggered but failed:** Qwen implements algorithmic advice superficially (abc398_d, arc195_a Codex),
  then falls into the frozen agent's identical-rewrite loop.
* **Public pass, hidden fail:** arc195_a API.

**11. Is Condition B operational?**
Functionally, yes: the frontier model drives the shared mini-SWE-agent interface end to end. This was
validated on the synthetic fixture via the API and Codex only. It has not been benchmarked, and its per-task
cost is not measured (`FRONTIER_ONLY.md`).

**12. Did any implementation change violate or substantially depart from the proposal?**
No new frontier stage was added: one upfront artifact for C/D, one diagnosis for E, and B as model
substitution. Departures:

* **Container lifetime:** E's sandbox container lifetime is extended so the suspended deadline is usable.
* **Polite GPU wait:** the batch runner waits while the user's own Ollama holds a model, without
  unloading it.
* **E skips a useless request:** if no local action remains at the trigger, no request is made. This did
  not occur.
* **Algorithm in diagnoses:** E's diagnoses sometimes give the algorithm (allowed: "repair suggestions
  without directly supplying replacement code"), so E transfers more method than D.

**13. Which configuration should be used for the full benchmark?**

* A: frozen.
* C: `plan-v1` + `inject-v1`.
* D: `contract-v1` + `inject-v1`.
* E: `diagnosis-v1` + `deliver-v1`, with the trigger policy above, a 300 s frontier timeout and the
  **direct API** provider for the main run (Codex replay only for development).
* B: the API coder with a per-run request cap and a separate ceiling, once its cost is measured.
* No ACI options. ≥3 seeds.

**14. What remains before the full A/B/C/D/E study?**
See `../BENCHMARK_READINESS.md` §0/§0a:

* the task pool (no fresh medium tasks remain; use the main cohort only for the final run);
* B cost measurement;
* the E provider decision;
* judge coverage for tolerance and multi-answer tasks;
* CI for `guided_agent/**`;
* native macOS validation;
* an equal-*end-to-end*-time sensitivity analysis if wanted.

## 3. Resource use (pass-2 runs)

| Cohort / condition | Runs | Hidden pass | Local completion tokens | Format errors | Frontier wait |
| --- | --- | --- | --- | --- | --- |
| val A | 5 | 2 | 30,876 | 7 | — |
| val C | 5 | 4 | 8,832 | 1 | — |
| val D-v1 | 5 | 2 | 26,583 | 3 | — |
| val D-v3 | 5 | 1 | 26,022 | 3 | — |
| val E | 5 | 2 | 37,095 | 7 | 9.1 s (1 call) |
| dev D-v3 | 8 | 3 | 52,739 | 13 | — |
| dev E (Codex) | 4 | 2 | 28,087 | 4 | 29.2 s (3 calls) |
| dev E (API) | 2 | 1 | 10,392 | 2 | 10.6 s (2 calls) |

Codex diagnosis latency was 8.1–12.8 s and API latency 4.9–5.7 s. The API diagnoses used about 1.2–2.0k
input and 0.3k output tokens, at $0.0055–0.0069 each.

## 4. API ledger (this pass; `evidence/api-ledger.json`)

| # | Purpose | Tokens in/out | Cost (standard) |
| --- | --- | --- | --- |
| 0–2 | B functional smoke (synthetic fixture) | 253/47, 317/20, 363/21 | $0.0028 |
| 3 | E diagnosis, arc195_a frozen trigger | 1,224/305 | $0.0055 |
| 4 | E diagnosis, abc393_d frozen trigger | 1,982/290 | $0.0069 |
| 5 | contract-v3, abc399_f (validation provider check) | 827/641 | $0.0081 |
| 6 | contract-v3, abc388_e (validation provider check) | 947/766 | $0.0096 |

All requests completed with `finish_reason=stop`: no errors and no retries. Pricing was re-verified on
2026-11-22: $2 / $10 per 1M input/output tokens (standard), with the ledger bound at $12 / $60.

## 5. Limitations

* Tiny cohorts: 5 fresh validation tasks (1 easy, 4 hard), 8 development tasks, mostly one seed.
* With temperature 0.2 and a fixed seed, outcomes are near-deterministic per prompt. Any change of prompt
  text, D-v1 against D-v3 included, re-samples the first attempt, so single-task flips are weak evidence.
* Codex replay carries harness context and is not the API. The provider comparisons are n=1 per state.
* The fresh pool is almost exhausted. The validation cohort is mostly hard, which limits E's trigger rate
  and D's chances.
* Diagnosis and contract quality judgments are mine, checked against hidden outcomes and reference programs
  where available.
