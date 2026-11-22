# Condition B on real tasks: cost, reliability and estimates

**Setup.** B is the frontier model as the *coder*. It is the same frozen mini-SWE-agent loop and text action
protocol (one ```mswea_bash_command``` block per turn), with the same sandbox, judge-public routing,
20 actions, 3 repair groups and 600 s, and the same hidden judge. Only the model behind `TextModel` changes
(`guided_agent/frontier_coder.py`). B was run on consumed development tasks only, never on the extended cohort.

## 1. Runs

B was run on three consumed development tasks of increasing difficulty: Codex first, then the paid API on
two of them, each with its own request cap.

| Run | Task (LiveCodeBench label; local outcomes) | Provider | Requests | Actions / repairs | Input tokens per turn | Output tokens per turn | Wall s | Cost | Hidden |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `b-real-codex` | abc391_a (easy; local A ✓) | Codex | 3 | 3 / 0 | 11,503–11,614 (harness) | 48, 21, 22 | 15.5 | not metered | ✓ 40/40 |
| `b-real-codex` | abc393_d (medium; A ✗ 9/40, E ✓) | Codex | 3 | 3 / 0 | 11,719–11,920 (harness) | 134, 21, 22 | 16.8 | not metered | ✓ 40/40 |
| `b-real-api` | abc393_d | API (cap 6) | 3 | 3 / 0 | 678, 840, 886 | 156, 20, 21 | 11.6 | **$0.0068** | ✓ 40/40 |
| `b-real2-codex` | abc388_g (hard; A no program, C ✓) | Codex | 3 | 3 / 0 | 12,240–12,711 (harness) | 767 (359 reasoning), 21, 22 | 34.3 | not metered | ✓ 40/40 |
| `b-real2-api` | abc388_g | API (cap 4) | 3 | 3 / 0 | 1,197, 1,616, 1,662 | 549 (140 reasoning), 20, 21 | 16.6 | **$0.0149** | ✓ 40/40 |

**Behaviour.**

* **The same three-turn pattern in all five runs:** (1) write `solution.py` in one heredoc, (2) run the
  public tests through judge-public (pass), (3) submit.
* **Clean protocol:** no format errors, no truncation and no repair. Every turn emitted exactly one
  ```mswea_bash_command``` block, and every hidden result was 40/40.
* **Context length:** API input grows from 0.7–1.2k to 0.9–1.7k tokens over the three turns. That is the
  system prompt, statement, one program and two short observations.
* **Prompt caching:** the API's prompt cache served 1,194 and 1,613 cached tokens on abc388_g turns 2–3. The
  cost above ignores the discount, so it is an upper estimate.
* **Codex context:** Codex's reported input is 11.5–12.7k tokens per turn, nearly all of it harness context.
  It is not comparable with API usage.
* **Runtime:** 11.6–16.6 s with the API and 15.5–34.3 s with Codex per attempt, including the local sandbox
  and judge-public. The local agent's attempts on the hard cohort take about 140 s.

**What this does not cover.**

* B never failed, so these runs did not exercise the repair path, long contexts, format errors or the
  request cap under load.
* Five runs on three development tasks (two with the API) show the pipeline works on real tasks. They do not
  measure B's accuracy.

**Codex coder isolation.**

* Every Codex turn is a fresh, tool-less, single-response `codex exec` session over the transcript.
* The event streams showed 0 tool events in every turn, so Codex's own agent tools were never the coding
  interface.
* Every action was emitted as text and executed by the shared environment.

## 2. Request-cap and retry safety (tested)

* **Ledger:** each API turn is one reserved, write-ahead `POST /v1/chat/completions` with no retries.
* **Per-run cap:** `max_requests` raises `LimitsExceeded("FrontierRequestLimit")` *before* a request that
  would exceed it.
* **No tenacity retries:** provider errors are wrapped in `FrontierCoderError`, which is in mini-swe-agent's
  `abort_exceptions`, so tenacity never retries a frontier call. `test_request_cap_stops_cleanly_and_errors_are_never_retried`
  asserts exactly one provider call.
* **Ledger ceilings:** 12 requests and $10 conservative, capped in code, refused before sending, and locked
  against concurrent writers.

## 3. Estimates for the final benchmark

**Model** (standard price $2 / $10 per 1M input / output tokens; cached input charged at full price).

* **A B attempt that passes** costs what was measured: **$0.007–0.015**. That is three requests, dominated
  by the first turn's program and the repeated context.
* **A B attempt that fails and uses the whole budget** is extrapolated from the measured per-turn sizes:
  * **Context:** system prompt plus statement is about 1.2k tokens, and each turn adds about 0.7k (a
    response plus a public report).
  * **Over 20 actions:** about 157k input tokens ($0.31) and about 6k output tokens ($0.06), so
    **≈ $0.37**.
  * **With format errors** up to the 28-request harness cap: **≈ $0.6**.
* **Hard ceiling per attempt (theoretical):** 28 requests at 16k input and 8k output each is $3.14 standard
  ($18.8 conservative). It is never approached at the observed sizes, but it is the reason a per-attempt
  request cap must stay on.

**Full-benchmark B arm** (tasks × 3 seeds). B's failure rate is unknown, so the range uses 10–40% failing
attempts, each at the full-budget cost:

| Final size | B attempts | Expected B requests | Expected cost (standard) | Pessimistic: every attempt fails at $0.6 | Conservative-price ledger bound (6×) |
| --- | --- | --- | --- | --- | --- |
| 60 | 180 | 850–1,760 | **$9–28** | $108 | $54–170 |
| 90 | 270 | 1,270–2,650 | **$14–42** | $162 | $81–255 |
| 120 | 360 | 1,700–3,530 | **$18–57** | $216 | $108–340 |

**Frontier guidance for C/D/E** (if the final study uses the direct API rather than Codex replay), from the
measured requests:

| Item | Measured cost | Count at 60 tasks | Cost at 60 / 90 / 120 tasks |
| --- | --- | --- | --- |
| C plan | about $0.012 per task, reused across seeds | 60 | $0.73 / $1.09 / $1.45 |
| D contract | about $0.006 per task | 60 | $0.35 / $0.53 / $0.71 |
| E diagnosis | about $0.006 per triggered run, at a 25–40% trigger rate over 3 seeds | 45–72 | $0.27–0.43 / $0.40–0.65 / $0.54–0.86 |
| **Guidance total** | | | **about $1.4–1.5 / $2.0–2.3 / $2.7–3.0** |

**Total paid cost of a full A/B/C/D/E comparison:** about **$10–30 at 60 tasks, $16–44 at 90 and $21–60 at
120** (standard prices; the 6× conservative bound for planning is shown above). B dominates the cost. Local
conditions cost nothing in API terms; their cost is GPU time (`FINAL_BENCHMARK_OPTIONS.md`).

**Ledger settings the team must decide before the final run.**

* **Ceilings:** the code constants (12 requests, $10) are deliberately pass-3 limits. The final run needs
  ceilings from this table, for example 2,000–4,000 requests and $200 conservative at 60 tasks, fixed in a
  reviewed commit before the freeze.
* **Per-attempt request cap:** keep it (`max_requests`), for example 28 = 20 actions + 3 repair groups +
  format errors. A request that would exceed it ends the attempt as a B failure, never as a retry.
* **No automatic retries:** keep them disabled. A provider error ends the attempt and is reported, as in
  E's policy.
* **Pilot first:** a B run on ~10 consumed development tasks that fail locally would measure the failing-
  attempt cost directly instead of extrapolating it. At most $6 at the pessimistic rate.
