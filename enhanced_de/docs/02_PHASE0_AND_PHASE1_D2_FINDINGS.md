# Phase 0 Offline Benchmarks, Provider Parity & Phase 1A Live D2 Findings

> **Review note (2026-11-26, Claude Opus 5.5, after an independent Codex audit):** numbers below were rechecked
> against `reports/*.json` and `runs/*/summary.json`. Corrected: WA kill counts (3/33, 25/33, 27/33; earlier text
> said 2, 24, 26), the provider-agreement denominator, and wording that claimed detection was "completely solved" or
> that one run "proved" a mechanism. All Phase 0 and Phase 1 cohorts are **consumed final-main tasks selected on
> historical outcomes**; treat them as development evidence. The outcome-blind validation is in document 03.

> **Provider Separation Policy**: Isolated Codex replay (`codex-replay`, free) and direct OpenAI API (`openai-api`, billed under `E:/CSC2108Local/enhanced-de-v2-study/api-ledger.json`, hard ceiling 20 requests / $10.00 conservative) are strictly separated in all tables below and never pooled.

---

## 1. Phase 0: Offline D2 Endres Mutant Benchmark (`codex-replay`)

Evaluated across **all 18 exposed `final-main` tasks** having at least one hidden-passing reference and at least one `public_pass_hidden_fail` mutant (**96 distinct passing reference solutions**, **46 distinct public-pass hidden-fail mutants**: 33 WA, 8 TLE, 5 RE; `abc388_d` and `abc392_f` have 0 passing refs even under B and are automatically excluded).

- **Authoring & Compilation Validity**:
  - Initial AST whitelist (`ast.literal_eval`, no `Lambda`, no helper decorators) rejected 4/18 valid modules (`abc387_c` `LIMIT = 10**18`, `abc391_d` & `abc394_f` `key=lambda`, `abc398_g` `@lru_cache(maxsize=None)`), plus `abc395_e` (`nonlocal`) in the safety set.
  - After permitting bounded pure constant arithmetic, `ast.Lambda`, `ast.Nonlocal`, and `functools.{cache,lru_cache}` on helper functions, and raising `_STRESS_LIMIT` from 2 MB to 8 MB (to accommodate `N=2e5` graph/query inputs), **20/20 (100.0%)** first-shot bundles parsed without re-generation and compiled with **`val_ok=18/18`, `prop_ok=18/18`, `oracle_ok=18/18`, `stress_ok=18/18`**.
  - On the **16 completely unseen `test5_val16.json` tasks** under the strictly frozen `d2_contract.py` (commit `7eb927e`, zero post-hoc rule edits): **15/16 (93.8%)** compiled on first shot (`15/15 val_ok`, `14/15 prop_ok`, `14/15 oracle_ok`, `14/15 stress_ok`; only `arc184_e` rejected for `from operator`).

### Aggregate Offline Results (18 Tasks, 96 References, 46 Public-Pass Mutants)

| D2 Ablation Mode | Ref FRR (Programs) | Ref FRR (Tasks) | Public-Pass Mutant Kill Rate | Tasks Detected | WA Kill (n=33) | TLE Kill (n=8) | RE Kill (n=5) | Kill Reasons |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`D2-inputs-stress`** (control: small + stress, RE/TLE only) | **0/96 (0.0%)** | **0/18 (0.0%)** | **16/46 (34.8%)** | 9/18 (50.0%) | 3/33 (9.1%) | **8/8 (100%)** | **5/5 (100%)** | 3 RE, 13 TLE |
| **`D2-property`** (postconditions + metamorphic + stress; compile-time size/soundness filtered) | **0/96 (0.0%)** | **0/18 (0.0%)** | **38/46 (82.6%)** | 17/18 (94.4%) | **25/33 (75.8%)** | **8/8 (100%)** | **5/5 (100%)** | 4 RE, 11 TLE, **14 postcond, 9 metamorphic** |
| **`D2-property` (Pure Zero-Oracle Ablation: `reference_small` disabled)** | 2/96 (2.1%)* | 1/18 (5.6%)* | **38/46 (82.6%)** | 17/18 (94.4%) | **25/33 (75.8%)** | **8/8 (100%)** | **5/5 (100%)** | 1 RE, 14 TLE, **14 postcond, 9 metamorphic** |
| **`D2-oracle`** (bounded exact specification evaluator + stress) | **0/96 (0.0%)** | **0/18 (0.0%)** | **40/46 (87.0%)** | **18/18 (100%)** | **27/33 (81.8%)** | **8/8 (100%)** | **5/5 (100%)** | 3 RE, 12 TLE, **25 oracle_mismatch** |

*\*Adjudication of the 2/96 false rejections in Pure Zero-Oracle `D2-Property`*: Both occurred on a single task (`abc390_d`) with **`reason = "TLE"`** (NOT a postcondition or metamorphic violation!) because `metamorphic_pairs` generated a max-scale `N=12` Bell-number instance evaluated under `small_timeout=2.0s`. **Semantic/postcondition/metamorphic false rejection rate was 0/96 (0.00%) across ALL 18 tasks**, and `metamorphic.reference_mismatched` was **0 across all 18 tasks**.

**Unexpected result (offline, 18 consumed tasks)**: before Phase 0 the skeptical prior was that non-oracle `D2-Property` would reach only ~20–40% bug-completeness on count/optimum tasks. Offline, the pure non-oracle variant killed **38/46** public-pass mutants (**25/33 WA**) with no postcondition or metamorphic false rejection on 96 references (2/96 timeout false rejections on one task). That is close to `D2-Oracle` (40/46; 27/33 WA). The mutants are natural failures of our own agent on these tasks and each bank is a single frontier sample, so this is a development estimate, not a population rate.

---

## 2. Phase 3 (Part 1): Direct OpenAI API vs Isolated Codex Provider Parity (`openai-api`)

Authored **4 `D2_BUNDLE_V1` banks directly via OpenAI API (`gpt-6.2-sol`, `effort=medium`)** on the first 2 medium + first 2 hard unseen `test5` tasks under `api-ledger.json` (4/20 requests used):

| Task | Prompt Tok | Comp Tok | **Reasoning Tok** | Latency (s) | Std USD | Cons USD | Calibration (`val/prop/orac/str`) | Cross-Provider Oracle Parity (`API` vs `Codex`) |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `abc384_c` (med) | 1,387 | 2,072 | **512** | 30.88 | $0.0235 | $0.1410 | `T/T/T/T` (`45` small) | **90 / 90 agreed (0 disagreed)** |
| `abc383_c` (med) | 1,013 | 3,340 | **969** | 51.94 | $0.0354 | $0.2126 | `T/T/T/T` (`45` small) | **68 / 68 agreed (0 disagreed; 22 `None`)** |
| `abc379_g` (hard) | 962 | 2,610 | **827** | 38.38 | $0.0280 | $0.1681 | `T/T/T/T` (`45` small) | **90 / 90 agreed (0 disagreed)** |
| `abc376_e` (hard) | 1,022 | 3,425 | **1,024** | 51.53 | $0.0363 | $0.2178 | `T/T/T/T` (`45` small) | **90 / 90 agreed (0 disagreed)** |
| **Total (4 calls)** | **4,384** | **11,447** | **3,332 (mean 833/task)** | **mean 43.2s** | **$0.1232** | **$0.7394** | **4/4 (100%)** | **338 / 338 (100.0%, 0 disagreed)** |

- **D-v1's shallow reasoning**: official `D-v1` used **36 reasoning tokens in total across 60 tasks** (0 on 59/60). `D2_BUNDLE_V1` elicited **833 reasoning tokens per task** at about `$0.031/task` standard cost. Where both providers' `reference_small` returned an answer they agreed on **338/338** inputs (360 checked; 22 had no answer from one side). Agreement between two samples of the same model family is not evidence of correctness.

---

## 3. Phase 0: Offline `E2-Review` & `E2-Strict` Benchmark (`codex-replay`)

- **`E2-Review` (10 PPHF buggy A submissions + 6 true A hidden-passing submissions)**:
  - Schema compliance: **16/16 (100%)**.
  - **PPHF buggy submissions (n=10)**: `9/10 (90%)` `DEFECT` verdict; **`8/10 (80%)` sandbox-verified delivery** (`abc390_d@2110` `NO-DEFECT`, `abc394_f@2110` `unverified_abstain`). **11/11 (100.0%) verified counterexamples were confirmed ground-truth sound on passing references (`ref_false = 0`)**.
  - **True hidden-passing submissions (n=6: `abc389_d@2108`, `abc398_b@2108`, `abc393_f@2108/2109`, `abc395_e@2108/2109`)**: **`6/6 (100.0%)` `NO-DEFECT`, `0/6 (0.0%)` false deliveries**.
- **`E2-Strict` (12 historical `E-v1` triggered-failure states)**:
  - Schema compliance: **12/12 (100%)**, zero hedging: **4 `LOCAL-FIX`, 8 `METHOD-CHANGE`** (all 6 historical dual-advice algorithmic failures committed unambiguously to `METHOD-CHANGE`).
  - Sandbox-aligned V-checks: **10/12 (83.3%)** states (`11` aligned V-checks total), **11/11 (100.0%) sound on passing references (`ref_false = 0`)**, retroactively catching **3/3** historical `E-v1` WA post-diagnosis `public_pass_hidden_fail` submissions (`abc397_b@2108`, `arc191_d@2108`, `arc194_d@2109`; the remaining 4 were scale TLE/REs).

---

## 4. Phase 1A: Live GPU D2 Ablations (`codex-replay`, 48 Runs on RTX 4080 SUPER)

Tested all three D2 ablations (`D2-inputs-stress`, `D2-property`, `D2-oracle`) live on `frozen-v6` (`qwen3.5:9b`, 38 frozen files verified per attempt) across the 10 historical A `public_pass_hidden_fail` pairs + 4 genuine A hidden-passing safety pairs (+ 2 pre-trigger A-failure checks confirming 100% deterministic host reproduction):

| Arm | Public-Pass Triggered | PPHF Bugs Caught (n=10) | WA-Only Caught (n=5) | True Passes Preserved (n=4) | Live Rescues vs A (n=10) | Losses vs A (n=4) | Mean Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`D2-inputs-stress`** (control) | 14/16 | 5/10 (50%) | 0/5 (0%) | **4/4 (100%)** (`0` FA) | **+1** (`abc400_c@2108`) | **0** | 100.9 |
| **`D2-property`** (non-oracle) | 14/16 | **10/10 (100%)** | **5/5 (100%)** | **4/4 (100%)** (`0` FA) | **+1** (`abc400_c@2108`) | **0** | 153.3 |
| **`D2-oracle`** (bounded differential) | 14/16 | **10/10 (100%)** | **5/5 (100%)** | **4/4 (100%)** (`0` FA) | **+1** (`abc400_c@2108`) | **0** | 143.2 |

### Core Finding: The Live Detection-vs-Uptake Gap
1. **Detection was high on this selected cohort**: on 10 states selected because A passed public tests and failed hidden ones, `D2-property` and `D2-oracle` delivered a counterexample in **10/10** runs (including the 5 WA-only states that `D2-inputs-stress` missed), with **0/4** false alarms on the 4 genuine-pass safety states. The cohort is small and selected on A's hidden outcome; this is not a population detection rate.
2. **Counterexample-only feedback rarely led to a repair here**: Despite receiving exact minimal counterexamples (e.g., `abc387_c@2108`: `'10 10\n'` -> `'9\n'` vs `'1\n'`), **`qwen3.5:9b` rescued 0/5 WA-only bugs** — instead entering deterministic local rewrite loops (`action_limit=20` or `agent_error`) and converting silent bad submissions into failed repair loops. Only the stress-caught TLE (`abc400_c@2108`) was rescued across all three arms.
3. **Contrast with `E2-review` (suggestive only)**: `E2-review` rescued 2/10 (`abc387_c@2108`, `abc400_c@2109`) against 1/10 for each D2 arm. The arms differ in more than code awareness (different counterexamples, a prose repair direction, different timing), and `E2-review` had no live safety states in Phase 1A, so the contrast is not attributable to code inspection alone. Full Phase 1 E2 results, controls and the validation cohort follow in `03_PHASE1_E2_AND_VALIDATION_RESULTS.md`.
