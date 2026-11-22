# Condition B on real tasks: cost, reliability and estimates

**Setup.** B is the frontier model as the *coder*. It is the same frozen mini-SWE-agent loop and text action
protocol (one ```mswea_bash_command``` block per turn), with the same sandbox, judge-public routing,
20 actions, 3 repair groups and 600 s, and the same hidden judge. Only the model behind `TextModel` changes
(`guided_agent/frontier_coder.py`). B was run on consumed development tasks only, never on the extended cohort.

## 1. Runs

B_RUNS_PLACEHOLDER

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

ESTIMATE_PLACEHOLDER
