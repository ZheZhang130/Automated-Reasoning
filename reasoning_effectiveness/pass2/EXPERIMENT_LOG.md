# Pass-2 experiment log (2026-11-22)

All times are local (EST). The branch `feat/csc2108-contract-diagnosis-pass2` starts from
`origin/feat/csc2108-reasoning-effectiveness` at `d5ec2e2`, which was still the latest commit after the fetch.
The new worktree is `ar-pass2`. Runtime artifacts live outside Git in `E:\CSC2108Local\reasoning-effectiveness-pass2`.

Fixed configuration for every local run unless stated otherwise: the original frozen agent (mini-SWE-agent
2.4.6, Qwen3.5 9B Q4_K_M digest `56671c2a…`, `heredoc-v6-16k-common`, seed 2108, 20 actions, 3 repair groups,
600 s, 180 s per request), judge `csc2108-judge:0.2.1`, Windows backend, no ACI option. Frozen file
verification (38 hashes) passed on every attempt.

## 1. Reading and audit (≈09:10–09:55)

**Read:** the proposal and all five papers in full. Endres et al. and CUDAnalyst are untracked PDFs in the
user's `Automated-Reasoning/papers`; I read them in place and did not copy them. The design mapping is in
`PAPER_ALIGNMENT.md`.

**Audit of pass-1 D runs** (`E:\CSC2108Local\reasoning-effectiveness\runs`, 40 D attempts):

* **Truncation was the dominant D failure.** Runs with 0 actions and 3 format errors (in-file brainstorming
  reaches the 4,096-token cap) occurred on arc192_a (3 of 4 D-v1), arc195_a (2 of 3), abc388_g and abc391_e.
  A contract cannot prevent this, because it gives no method.
* **Plausible but wrong programs passed the public tests:** arc192_a D-v1 scored 20/40 hidden and
  contract-v2 30/40 (with A at seed 2109 at 39/40).
* **contract-v2's checks were never executed.** A strict regex count over all 117 pass-1 attempts finds
  **0** commands running the program on custom input (`printf … | python /workspace/solution.py` or `… < file`).
  (A first, looser regex counted heredoc writes `solution.py <<'PY'` as self-checks; that was a false
  positive.) In arc192_a's contract-v2 run, Qwen spent its 20 actions rewriting the same file without testing.
* **contract-v1's content mostly restates the statement.** In arc192_a, POST-1 to POST-3 paraphrase the rules,
  and the three "test suggestions" are a sample, an all-ones case and `0 0 0` / `0 1 0`, all written as prose.
  None of the six v1 artifacts' suggestions is machine-checkable.

**Frozen loop facts used for E:**

* `DefaultAgent.step` runs `query()` then `execute_actions()`, and observations are appended in
  `execute_actions`.
* The deadlines are `env.deadline` (monotonic) and `agent._start_time` (wall clock, for
  `wall_time_limit_seconds`).
* The Docker container runs `sleep 660s`.
* The judge distinguishes `candidate_failure` (WA/RE/TLE/CE/MISSING) from `infrastructure_error`.

## 2. Implementation (≈09:55–10:20)

* **contract-v3** (`guidance.CONTRACT_V3`, `inject-v3-contract`). Hypothesis: precise, discriminating,
  prioritized behavioral requirements and hand-derived K-checks reduce *interpretation* errors and catch
  plausible-wrong programs, without supplying an algorithm. Success criterion: on development tasks, D-v3 ≥
  D-v1 in hidden passes with no new delivery failures, and its checks are correct and discriminating.
* **E** (`diagnosis.py`, hooks in `backend.py`, runner/CLI support) and **B** (`frontier_coder.py`).
* **Providers refactor:** `providers.codex_infer` and `providers.api_chat` are shared by authoring, diagnosis
  and B. Pass-1 artifact formats are unchanged.

**Tests** (offline; no model, Docker or network):

* **Pass 1:** `test_guided`, 18 tests, still pass.
* **Pass 2:** `test_pass2`, 22 tests covering trigger policy, delivery position, deadline suspension, every
  provider-failure category, replay binding, evidence packet, contract-v3 replay through `SavedContract`, and
  the B adapter (frozen parser, request cap, no retries, ledger refusal, no GPU/Ollama metadata).

**Integration tests:** `test_pass2.IntegrationE` (`CSC2108_INTEGRATION=1`) uses the real frozen runtime,
Docker sandbox and judge-public with a scripted coder on the synthetic fixture.

* First run: 5/6 passed. The failure was my test script: after `abs(a + b)` the third `sed` pattern no longer
  matched. I fixed the script, not the code.
* Second run: **6/6 passed**. E's container lifetime was 990 s and A's the frozen 660 s.

Commit `6f1b10d`.

## 3. Contract-v3 authoring and Endres-style check evaluation (10:13–10:40)

**Authoring.** Codex (`gpt-6.2-sol`, effort medium, isolated) authored contract-v3 for 8 development tasks in
one parallel batch, without regeneration: 211–330 words, 0 validation problems, 0 soft code flags. Two
spot-checked artifacts (arc192_a, abc393_d) contain precise relational postconditions and K-checks labelled
with the misreading they expose. I verified abc393_d's K-1 to K-3 by hand.

**Check evaluation.** `pass2/diagnostics/contract_checks.py` runs each contract's machine-checkable checks
inside a network-less, read-only Docker container:

* **Reference:** a pass-1 submission with 40/40 hidden passes.
* **Natural mutants:** distinct pass-1 submissions that failed hidden cases.
* **Metrics:** Endres §2.1 *test-set correctness* and *bug-completeness*.

| Contract | Artifacts with checks | Checks correct vs. reference | Mutants killed (union of correct checks) |
| --- | --- | --- | --- |
| contract-v1 (pass 1) | 0 of 6 (prose suggestions only) | — | — |
| contract-v2 (pass 1) | 3 of 4 parsed (abc400_b layout not parsed) | arc192_a 6/6 | arc192_a 7/7 |
| contract-v3 (pass 2) | 8 of 8 (4 K-checks each) | **32/32** on the 7 tasks with a reference (abc391_e has none) | arc192_a 6/7, arc195_a 5/5, abc393_d 2/2, abc394_c 1/1 (**14/15**) |

The v3 checks are correct and discriminate natural failures well. Whether Qwen *uses* them is a separate
question (section 6).

## 4. Validation selection and freeze (10:20–10:27)

`guided_agent/selection_pass2.py` uses public metadata and statement text only. Eligible tasks are AtCoder
stdin tasks that are:

* not in the main 60-task manifest;
* not in the 75-ID union;
* not teammate-used and not used in pass 1;
* not tolerance or multiple-answer tasks (4 excluded by statement regex: abc397_d, abc398_f, arc190_a,
  arc191_c).

The pool held **1 easy, 0 medium and 25 hard** tasks. A labelled *confirmation* stratum (previously scored,
non-main, medium) was **empty**, and LeetCode tasks are functional, which the judge does not support.

Selected by seeded order: abc394_b (easy, pilot manifest), and abc399_f, abc398_d, abc388_e, abc396_f (lower
hard, ABC D–F).

Codex authored plan-v1, contract-v1 and contract-v3 for all 5 tasks: 15 artifacts, 0 problems.
`FREEZE-val.json` was written at 10:26, before any validation run, recording commit `20ed474`, prompt and
template hashes, artifact hashes and the 25-attempt plan. Nothing is regenerated and nothing is rerun
selectively.

## 5. Condition B functional smokes (10:20–10:24)

* **Codex coder** (`runs/b-smoke-codex`): 3 isolated turns with 0 tool events. Write → public 2/2 → submit;
  hidden 5/5 **pass**.
* **Direct API coder** (`runs/b-smoke-api`): reduced smoke limits (4 actions, 300 s, `max_requests` 4).

  * Pricing re-verified at 10:24 (developers.openai.com): `gpt-6.2-sol` costs $2 / $10 per 1M input/output
    tokens at standard rates. The ledger bound stays $12 / $60.
  * Configured model `openai/gpt-6.2-sol`.
  * **API requests 1–3**, all `stop`: 253/47, 317/20 and 363/21 tokens; **$0.0028**. Hidden 5/5 **pass**.

## 6. Development: E with live Codex diagnosis (10:27–10:36)

The user's own Ollama (port 11434) had `gemma4:12b` loaded until 10:27. The frozen runtime refuses to run
next to a foreign model and must never unload it, so the batch runner now waits politely
(`__main__.wait_for_gpu`). Runs started at 10:27:33.

| Task | Trigger | Diagnosis (Codex) | After delivery | Hidden (A at the same seed, pass 1) |
| --- | --- | --- | --- | --- |
| arc195_a | WA at action 2, 548 s left | 193 words, 8.3 s wait. Correct cause (`count >= 2` counts matched *elements*, not complete subsequences). The repair direction gives the earliest/latest scan method. | Qwen restructured its code as "Greedy forward match: find earliest possible indices" but implemented it incorrectly (no increasing-index constraint), then made byte-identical rewrites; 17 actions, 7 tests, repair limit | ✗ 39/40 (A ✗ 39/40) |
| abc393_d | WA at action 2 | Correct cause: `k - max_ones` assumes one swap per missing 1, but swaps are adjacent. Repair: median of adjusted positions. | One rewrite, public 3/3, submit (5 actions) | **✓ 40/40** (A ✗ 9/40) |
| abc390_c | WA at action 2 | Correct cause: bounding box stored 1-based, compared 0-based | Applied ("using zero-based coordinates"), public pass, submit | ✓ 40/40 (A ✓ 40/40; A also self-recovered) |
| arc192_a | **not triggered**: 3 truncated responses, no public test | — | — | ✗ none (A ✗ none) |

* **Frozen state:** the pre-trigger history is byte-identical to pass-1 A's in all three triggered runs
  (same seed and prompts). Each intervention lands on a fixed program state, our analogue of CUDAnalyst's
  trajectory freezing.
* **Diagnosis quality:** all three delivered diagnoses were accurate and specific, and Qwen visibly followed
  each (test 7: live Codex diagnosis delivered to real Qwen).

## 7. Determinism of the A reference (10:32–10:37)

The pass-2 A reruns of arc195_a and abc393_d are **token-for-token identical** to the pass-1 A runs (18 and
13 calls), with byte-identical submissions. The pass-2 backend changes leave A unchanged, so pass-1 A, C and
D-v1 runs at seed 2108 are valid paired references for development.

## 8. Development: D-v3 versus D-v1 (10:37–10:52)

D-v3 (Codex) solved 3 of 8 development tasks; pass-1 D-v1 solved 4/8 and A 3/8. The provider-matched D-v1
(Codex) solved abc393_d and failed abc391_e, the same as D-v3.

| Task | D-v3 result | Mechanism |
| --- | --- | --- |
| arc192_a, arc195_a, abc388_g, abc391_e | ✗ no program | Truncation (3 × 4,096 tokens) |
| abc394_c | ✗ 39/40 | Identical-rewrite loop after a public WA on `WWA`, which the contract's K-1 also exposes |
| abc393_d, abc390_c, abc391_a | ✓ | — |

**Hypothesis test (D-v3 ≥ D-v1, no new delivery failures): not met.** I made no further contract variants:
no contract content addresses truncation or the rewrite loop, and further prompt search would not have been
hypothesis-driven.

**K-check test on final programs** (`analysis-kcheck-programs.json`):

* D-v3 programs satisfied 4/4, 4/4, 4/4 and 3/4 of their task's verified K-checks; the 3/4 is the
  abc394_c failure.
* Wrong programs from other conditions violated them (e.g. A abc393_d 2/4, D-v1 arc192_a 2/4).
* **0 self-check commands** in all D-v3 runs.

## 9. Development: E through the direct API (10:52–10:56)

* **API requests 4–5:** arc195_a and abc393_d, at the identical frozen trigger states (same candidate and
  report hashes as the Codex runs). Latency 5.7 s and 4.9 s; $0.0055 and $0.0069.
* Both diagnoses were accurate, and both delivered (test 8).
* **arc195_a:** the API diagnosis also named the `popleft()` ordering bug. Qwen repaired in 3 actions and
  passed the public tests, but scored 39/40 hidden, the same as A.
* **abc393_d:** ✓ 40/40 again.

## 10. Frozen validation cohort (10:53–11:31)

| Task | A | C | D-v1 | D-v3 | E (trigger) |
| --- | --- | --- | --- | --- | --- |
| abc394_b | ✓ | ✓ | ✓ | ✓ | ✓ (none) |
| abc399_f | ✓ | ✓ | ✗ 0/40 | ✗ 20/40 | ✓ (none) |
| abc398_d | ✗ 36/40 TLE | ✓ | ✗ 36/40 TLE | ✗ 36/40 TLE | ✗ 36/40 TLE (triggered) |
| abc388_e | ✗ none | ✓ | ✓ | ✗ 31/40 | ✗ none (none) |
| abc396_f | ✗ none | ✗ 5/40 | ✗ none | ✗ none | ✗ none (none) |
| **Total** | 2/5 | **4/5** | 2/5 | 1/5 | 2/5 |

* **E on abc398_d:** the Codex diagnosis correctly located the off-by-one and also, beyond the public
  evidence, warned of the quadratic set rebuild that turned out to be the hidden TLE cause. Qwen renamed its
  variables after the diagnosis (`smoke_offsets`) but kept rebuilding the set: 11 actions, public pass,
  hidden 36/40 (TLE×4), the same as A.
* **C on abc396_f:** the run ended as `CommandExecutionError` when Qwen's own `echo … | python` check hung
  past the frozen 27 s command time-out. This is frozen-agent behavior and the only custom-input run seen in
  either pass.

## 11. Second seed (2109) and the API comparison on validation (11:31–11:47)

**Seed 2109:**

| Task | A | E | D-v3 |
| --- | --- | --- | --- |
| abc393_d | ✓ | ✓ (not triggered) | ✓ |
| abc390_c | ✓ | ✓ (not triggered) | ✓ |
| abc394_c | ✓ | ✓ (not triggered) | ✓ |
| arc195_a | ✓ (9 actions, pass 1) | ✓ (triggered; repaired in 3 actions) | ✗ 37/40 |

A's seed-2108 failure on abc393_d does not recur at 2109, so E's development rescue is within seed variance.

**API comparison:**

* **API requests 6–7:** contract-v3 via the API for abc399_f and abc388_e; 230 and 282 words, valid;
  $0.0176.
* **API request 8:** E diagnosis at the abc398_d frozen trigger; $0.0059.

| Run | Result | Same task under Codex |
| --- | --- | --- |
| D-v3-API abc399_f | ✗ 1/40 | D-v3 ✗ 20/40 |
| D-v3-API abc388_e | ✗ no program (truncated) | D-v3 ✗ 31/40 |
| E-API abc398_d | Diagnosis accurate, same substance as Codex; 5 actions, 36/40 TLE again | E ✗ 36/40 |

**API total this pass: 8 requests, $0.0386 at standard prices** ($0.232 conservative bound). Every request
finished with `stop`; there were no errors and no retries.

## 12. Run integrity

There were 48 non-test pass-2 runs:

* **48/48** verified all 38 frozen hashes;
* **0** setup errors and **0** infrastructure errors;
* **46/46** Qwen runs are sampler-wire verified; the other 2 are the B smokes, which have no Ollama sampler.

**Platforms:**

* Linux container (Python 3.11.18, pinned requirements): 49 tests OK.
* E integration tests: 6/6 on the Windows backend and 6/6 on the portable backend (`portable.adapted_run`).

The user's Ollama model on port 11434 was never unloaded; the batch runner waited for it to expire (10:23–10:27).
