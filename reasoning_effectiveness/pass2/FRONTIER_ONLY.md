# Condition B — frontier only (functional integration)

**Status: the pathway is operational and validated on a synthetic fixture only; it has not been benchmarked.**
The frontier model has driven the shared mini-SWE-agent interface end to end, via the direct API and via
Codex replay:

1. it wrote `/workspace/solution.py` with the frozen heredoc protocol;
2. it ran the recognized public test through judge-public;
3. it read the report;
4. it submitted;
5. the submission passed the independent hidden judge.

No LiveCodeBench task has been run under B. Accuracy, cost per task and behavior on long trajectories are
unknown.

## 1. Implementation: a model substitution, not a new framework

`guided_agent/frontier_coder.py` rebinds **one** global of the frozen `local_eval_v2.runtime.run`: `TextModel`.
The replacement subclasses the same upstream `LitellmTextbasedModel`, and only `_query` changes: it asks a
frontier provider instead of Ollama and wraps the text in a `litellm.ModelResponse`.

Everything else is the frozen, shared code path:

* the system prompt and first message (`PROMPT`, `{{task}}`);
* the ```` ```mswea_bash_command ```` regex action parser and the format-error template, including
  `finish_reason == 'length'`;
* the observation template (`<returncode>…</returncode>` and the first 6,000 characters);
* the Docker sandbox (no network, read-only root, 512 MB) and the judge-public routing of
  `python -I /public/check.py`;
* the action, repair and time budgets (20 / 3 / 600 s, 180 s per request);
* candidate extraction, run records and hidden evaluation.

Three more globals are replaced only for coders that are not the local model:

* `exclusive_gpu` → no-op: B uses no GPU and must not wait on or unload anything;
* the Ollama `/api/show` and `/api/tags` metadata calls → a record naming the coder;
* the frozen model allow-list → extended by exactly the coder label (`frontier:<model>`).

Codex's own agent tools are never the coding interface. Every action is text that the shared environment
parses and executes.

## 2. Providers

| Provider | Interface | Accounting |
| --- | --- | --- |
| `api` | `POST /v1/chat/completions` with the full message history (system/user/assistant), model from `.env` `FRONTIER_MODEL` (`gpt-6.2-sol`), effort medium, `max_completion_tokens` 8,000 | Every request is reserved in the write-ahead ledger (12 requests / $10 per study), plus a **per-run request cap** (`max_requests`). The cap ends the run cleanly as `FrontierRequestLimit` instead of spending. No retries: `FrontierCoderError` and mini-swe-agent's limit interrupts are in `abort_exceptions`, so tenacity cannot retry a paid call (tested). |
| `codex` | A fresh isolated `codex exec` per turn; the transcript is rendered into the request; one response | Free; Codex harness context remains (label: Codex replay); tool events are audited each turn |
| `scripted` | Predetermined responses | Deterministic integration tests (also used for E) |

The per-request timeout comes from the frozen agent (`min(180, remaining local time)`). B's frontier
inference time *is* coding time, so it counts against the 600 s budget like Qwen's.

## 3. Validation actually executed

| Check | Result |
| --- | --- |
| Offline adapter tests (`test_pass2.FrontierCoder`) | Frozen text protocol: action parsed; a missing block raises `FormatError`. Request cap → `LimitsExceeded`. Provider error raised once, not retried. API coder refuses at the ledger ceiling without any network use. Non-Ollama globals never touch the GPU or Ollama metadata. |
| Deterministic multi-step trajectories | The scripted coder drives the real frozen runtime and sandbox through write → test → edit → retest → submit (`test_pass2.IntegrationE`, 6 runs) |
| Live Codex coder smoke (`runs/b-smoke-codex`) | `frontier:gpt-6.2-sol`, 3 turns (5.0 / 3.7 / 3.2 s Codex wall), write → public test 2/2 → submit, **hidden 5/5 pass**, 0 format errors, 0 tool events |
| Live direct-API smoke (`runs/b-smoke-api`) | Reduced smoke limits: 4 actions, 300 s, `max_requests` 4. 3 requests, all `finish_reason=stop`: prompt tokens 253 / 317 / 363; cost $0.00098 + $0.00083 + $0.00094 = **$0.0028**; latency 2.5 / 1.0 / 1.4 s. Write → public test 2/2 → submit, **hidden 5/5 pass**. |
| Provider failure / budget | Covered by the offline tests (above) |

Both smokes are labelled **functional smokes, not research results**.

## 4. Not validated or not done

* **No LiveCodeBench task under B.** Expected cost per task is low: at about 300–3,000 prompt tokens per
  turn and ≤20 turns, roughly $0.01–0.10 per task by the fixture's token profile. That is an estimate, not a
  measurement. Long histories with reasoning tokens could cost more; set a per-run `max_requests` and a
  separate B ceiling before benchmarking.
* `sampler_wire_verified` is `false` for B by construction (no Ollama sampler). `model_calls` and token
  telemetry come from `coder/coder-calls.json` instead of `ollama-responses.json`.
* B on the portable (macOS) backend: the composition uses the host-adapted globals, but no live portable B
  run was made.
* Decide before the benchmark whether B should keep `reasoning_effort=medium` and 8,000
  `max_completion_tokens` per turn. Hidden reasoning tokens count toward the cap, so this is not the same
  output limit as Qwen's 4,096.
