# Provider validation: Codex (development substitute) and the direct OpenAI API

**The two provider cohorts are kept separate and never pooled.**

* **Codex:** Sol 6.2 through the isolated, model-only `codex exec` path is the development frontier
  substitute. It produced all 24 C/D artifacts of the extended benchmark and every live E diagnosis in it.
* **Direct API** (`gpt-6.2-sol`): used only for a few end-to-end checks on consumed development tasks.

## 1. Codex model-only inference checks

| Check | Result |
| --- | --- |
| Isolation per call | Fresh ephemeral session in an empty temporary directory; user config and rules ignored; read-only sandbox; web search and 12 features disabled; credential-like variables stripped |
| Event audit (24 benchmark guidance artifacts) | Exactly one `agent_message` per call, **0** tool, command, file or search events, 0 leftover files, `codex-cli 0.171.0` |
| Input | C/D: versioned system prompt plus the public statement only. E: the evidence packet (statement, judged candidate, public report, budget state) |
| Requested and observed model | Requested `gpt-6.2-sol`, effort medium. Codex does not report the serving model (`observed_model = null`). |
| Token accounting | Codex-reported counts include its harness context: about 11–12k input tokens per call against 0.6–1.1k for the same API request. **Not comparable to metered API usage** and never converted to dollars. |
| Format compliance | 24/24 artifacts passed the guidance validator (headings, no fenced code); 0 soft code flags |

**Live E diagnoses in the extended benchmark (Codex).** Every triggered E run requested and received a
diagnosis, and every one was delivered: no timeout, transport, isolation, format or budget failure. The event
streams held 0 tool events, and the harness wall time was 11–15 s. All 6 of 6 triggered E runs (both seeds)
were delivered; details are in `EXTENDED_BENCHMARK.md` §4.

## 2. Paid API requests (pass-3 ledger)

**Ledger:** `evidence/api-ledger.json`, sanitized; the private original is in the study root.

* **Use:** 10 of the 12 allowed requests, all `POST /v1/chat/completions` to `gpt-6.2-sol`, effort medium,
  `max_completion_tokens` 8,000.
* **Before each request:** the model was checked with one non-billable `GET /v1/models/gpt-6.2-sol` (200),
  and a conservative bound was reserved first (write-ahead).
* **Outcome:** every request returned HTTP 200 with `finish_reason = stop`. **0 retries, 0 failures**, and
  the observed model matched in 10/10.

| # | Kind | Task / state | Input / output tokens | Latency | Cost (standard) | Reserved bound (conservative) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | plan-v1 | abc388_g | 1,069 / 996 (99 reasoning) | 13.0 s | $0.01210 | $0.493 |
| 1 | contract-v1 | arc195_a | 575 / 473 | 6.4 s | $0.00588 | $0.490 |
| 2 | diagnosis-v1 | abc390_c, seed 2108 (frozen trigger) | 1,617 / 226 | 4.4 s | $0.00549 | $0.505 |
| 3 | diagnosis-v1 | arc195_a, seed 2109 (frozen trigger) | 1,545 / 287 | 4.6 s | $0.00596 | $0.505 |
| 4–6 | B coder turns 1–3 | abc393_d | 678/156, 840/20, 886/21 | 3.5, 1.7, 1.4 s | $0.00678 | $1.48 |
| 7–9 | B coder turns 1–3 | abc388_g | 1,197/549, 1,616/20, 1,662/21 | 8.6, 1.8, 1.4 s | $0.01485 | $1.50 |
| | **Total** | | **11,685 / 2,769** | | **$0.05105** | $4.98 (all ≤ $10) |

**Cumulative history:**

| Pass | Requests | Cost (standard) |
| --- | --- | --- |
| 1 | 10 | $0.0832 |
| 2 | 8 | $0.0386 |
| 3 | 10 | $0.0511 |
| **All passes** | **28** | **$0.1729** |

**Accounting.**

* **Cost:** cost is computed at the standard price ($2 / $10 per 1M input / output tokens) on the reported
  usage, with cached input tokens charged at the full input price, so it is an upper estimate.
* **Reservation:** each request reserved a conservative bound ($12 / $60 per 1M tokens, on the estimated
  input plus the full `max_completion_tokens`) before sending. The ledger refuses any request that would
  exceed 12 requests or $10.
* **Purpose:** no paid request was used for debugging, summarizing, coding, task selection or trajectory
  analysis.

## 3. Matched guidance on identical public inputs

Same statement bytes (statement sha256 equal), same versioned system prompt, different provider.

| Task / prompt | Codex | API | Format | Semantic content (my reading of both texts) |
| --- | --- | --- | --- | --- |
| abc388_g / plan-v1 | 542 words (pass 1) | 489 words, 1,069 in / 996 out tokens, 13.0 s, $0.0121 | both valid, no code | **Same method:** pair the K smallest with the K largest; a forward pointer gives the first valid bottom `p_i`; range-maximum test on `p_i − i` with a sparse table; feasibility monotone in K, so binary search per query. The API text states the monotonicity and the index arithmetic a little more compactly. |
| arc195_a / contract-v1 | 296 words (pass 1) | 322 words, 575 in / 473 out tokens, 6.4 s, $0.0059 | both valid | **Same postconditions:** distinct position sets, Yes/No at "at least two", M = N gives No, M = 1 means a repeated value. Similar edge-case suggestions. Neither contains an algorithm, as the prompt requires. |

**E diagnoses at identical frozen packets.** These are the same candidate and public-report hashes as pass 2,
reproduced by the same seed.

| State | Codex (pass 2) | API (pass 3) | Agreement | Local outcome Codex / API |
| --- | --- | --- | --- | --- |
| abc390_c, seed 2108 (candidate `e6eafc96…`) | 187 words, 12.8 s | 152 words, 4.4 s, 1,617 in / 226 out, $0.0055 | **Same fault and fix:** 1-based bounding-box coordinates compared against 0-based loop indices; store `i`, `j` directly | ✓ / ✓ (5 actions each) |
| arc195_a, seed 2109 (candidate `14660809…`) | 183 words, 8.4 s | 196 words, 4.6 s, 1,545 in / 287 out, $0.0060 | **Same fault and fix:** `count` counts matched elements, not complete matches; compare the earliest (forward greedy) and latest (backward greedy) matches | ✓ / ✓ |

Together with pass 2 (arc195_a and abc393_d at seed 2108; abc398_d validation), the comparisons at identical
packets give **5 of 5 diagnoses semantically equivalent**. The API versions were sometimes a little more
specific (arc195_a seed 2108, pass 2), and the local outcomes matched in 4 of 5 (pass-2 arc195_a: same hidden
39/40, different public path).

## 4. End-to-end functionality (direct API)

Each paid artifact went through the same run path as Codex guidance: the artifact replayed through the
teammates' `SavedPlan`/`SavedContract`, the frozen agent, judge-public, then the hidden judge after the batch.

| Check | Run | Hidden result | Codex counterpart (same task, same seed) |
| --- | --- | --- | --- |
| C with an API plan | `api-checks/abc388_g-C-api` | **✓ 40/40** in 3 actions | pass-1 C with a Codex plan: ✓. A: no program. |
| D with an API contract | `api-checks/arc195_a-D-api` | ✗ no program (three truncated responses) | pass-1 D with a Codex contract: no program |
| E with a live API diagnosis | `api-checks/abc390_c-E-api-s2108` | ✓ 40/40 | Codex E: ✓ |
| E with a live API diagnosis | `api-checks/arc195_a-E-api-s2109` | ✓ 40/40 | Codex E: ✓ |
| B with the API coder | `b-real-api/abc393_d-B-api`, `b-real2-api/abc388_g-B-api` | see `FRONTIER_ONLY_COST.md` | Codex B on the same tasks |

All four C/D/E paths behaved identically to their Codex counterparts at the outcome level. That is n = 4: it
shows the pipelines are interchangeable, not that the providers are equivalent in general.

## 5. Provider differences and unresolved equivalence limits

**Observed differences.**

* **Latency:** the API is 2–3× faster (diagnoses 4.4–4.6 s against 8–15 s for Codex; plans 13 s).
  Codex time includes process start and harness overhead.
* **Length:** API texts are about the same length (contracts) or a little shorter (plans, diagnoses).
* **Format:** both providers had 100% format compliance across every pass-3 artifact and diagnosis.
* **Cost:** the API costs $0.005–0.012 per guidance or diagnosis request. Codex has no metered cost in this
  study.

**Equivalence limits that remain open.**

1. **Context.** Codex replay always carries the Codex harness context: about 11–12k input tokens of
   instructions and tool descriptions the model sees but must not use. The API sees only the system prompt
   and the input. The outputs agree semantically on every pair inspected in passes 2–3 (5 diagnoses,
   1 plan, 1 contract-v1 and 2 contract-v3), but a distributional difference cannot be excluded.
2. **Serving model.** Codex does not report it. That both paths use `gpt-6.2-sol` at medium effort is the
   configuration, not an observation.
3. **Comparison size.** Pairs number 2–5 per artifact kind.
4. **Provider-sensitive outcomes.** The local agent is near-deterministic, so any wording difference can flip
   an outcome (pass 2: D-v3 on abc388_e). Provider-matched outcomes on 4/4 pass-3 checks say nothing about how
   often such flips occur over a full cohort.
5. **Recommendation.** For the final benchmark, use **one** provider for all guidance and diagnoses of a
   condition. The direct API is preferred (metered, reproducible, no harness context). Do not mix it with
   Codex replay.
