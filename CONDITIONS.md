# Condition specifications (final)

**Shared by every condition:**

* the task bundle, sandbox, mini-SWE-agent loop and action protocol (one fenced shell command per response);
* judge-public during the run, judge-hidden after it;
* the frozen budgets: 20 actions, 3 repair groups, 600 s local coding time, 180 s per model request;
* the measurement record.

Hashes are sha256 of the exact text the code uses; `FINALIZATION_MANIFEST.json` lists them, and
`guided_agent.test_pass4.Manifest` rechecks them.

## 0. Shared agent: `frozen-v6` (primary)

| Item | Value |
| --- | --- |
| Agent | mini-SWE-agent 2.4.6, frozen `local_eval_v2/runtime.run` bytecode (38 file hashes verified per attempt) |
| Model | `qwen3.5:9b` Q4_K_M, digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`, project Ollama |
| Profile | `heredoc-v6-16k-common`: 16,384 context; 4,096 output tokens; thinking off; T 0.2; top_p 0.9; top_k 40; min_p 0; repeat penalty 1.0 over 64; presence and frequency 0; fixed seed per attempt |
| Plan field | `"agent": "frozen-v6"`, required in frozen plans (`agent_config.PRIMARY_AGENT`) |
| Alternative | `l1-selfplan-v1`: one bounded local planning step before the session. It is **not primary**: development evidence shows A 4/16 → 7/16 but C 14/16 → 12/16, and context overflows in long C sessions. Adopting it is a team decision (see Open decisions below) |

## A: local only

| Item | Value |
| --- | --- |
| Frontier calls | 0 |
| First message | the statement (frozen `{{task}}` template) |
| Feedback | the judge-public report at each `python -I /public/check.py` |
| Known limits | on hard tasks the model deliberates inside the file being written and hits the 4,096-token cap (no program); see the development branch's `BOTTLENECK_AUDIT.md` |

## B: frontier only

| Item | Value |
| --- | --- |
| Coder | `gpt-6.2-sol` via the OpenAI API (`frontier_coder.ApiCoder`): effort medium, up to 8,000 completion tokens per request, full message history each turn |
| Interface | identical to A: system prompt, regex action parser, observation template, sandbox, judge-public, budgets. No tools of the frontier's own |
| Requests | one per agent turn; per-run cap `max_requests` (recommended 28 = the agent's step limit); no retries; each reserved in the ledger before sending |
| Measured cost | $0.007–0.015 per easier task (3 requests); $0.043 and $0.096 on two hard tasks (4 and 7 requests) |
| Development substitute | `provider: codex` (isolated `codex exec -s read-only`, empty directory). Not billed and not API-equivalent: label it and never pool it with the API |

## C: frontier plan

| Item | Value |
| --- | --- |
| Frontier calls | 1 per task, before any run (`author --provider api --prompt-id plan-v1`) |
| Frontier input | the public statement and the `plan-v1` prompt only (`f4f830d2f2fba0f664778577e06dd6a60d61215b54445ced792b2c67d8f74da6`) |
| Output | `## Observations`, `## Solution sketch`; no code (validated) |
| Delivery | `inject-v1` plan template (`e5d9ff35f486775d820fd14ed8681b5e4478b92fbd74b7a8d3934eddd28425cf`) in the first user message, labelled as unverified |
| Reuse | one write-once, statement-bound artifact per task, shared by seeds; never regenerated after outcomes |

## D: frontier contract

| Item | Value |
| --- | --- |
| Frontier calls | 1 per task, before any run (`author --provider api --prompt-id contract-v1`) |
| Frontier input | the public statement and the teammates' `contract-v1` prompt only (`97fd739455bc0a55ce04e25fd291dac666d0ce7a93477c5e0cad983508d4b682`) |
| Output | `## Description`, `## Preconditions`, `## Postconditions`, `## Test suggestions`, `## Unspecified behavior`: what a correct output must satisfy, never how to compute it |
| Delivery | `inject-v1` contract template (`30e3fb753cd7c7afb042c89372c84ba36ec6510185f276892f0919e04da44c2e`) |
| Alternative | **D-active** (development branch): contract-v3 + harness-executed K-checks, labelled unverified. Not primary: on 8 development tasks it scored 3/8, the same as its inputs-only control and D-v1. If adopted, run it as a labelled variant **with** the inputs-only control |

## E: frontier diagnosis

| Item | Value |
| --- | --- |
| Trigger | the first qualifying judge-public failure: WA/RE/TLE/CE of a non-empty candidate whose judged hash equals the harness snapshot. Never an infrastructure error, never a hidden test; at most once per attempt |
| Frontier input | statement, submission contract, the exact failed program and its public report, local budget state; between nonce-delimited DATA markers; bound by sha256 |
| Prompt | `diagnosis-v1` (`3d2c77611009163d4d1a8fa20922db5e719f184207f2efa84ff0f65fdc0fefb8`): `## Observed failure`, `## Likely cause`, `## Repair direction`, `## Verification target`; no code |
| Delivery | `deliver-v1` (`dbe4c788c6329843f146737b6d4baf4dcdf95170b4ba846974c92b991d09b954`): one user message right after the triggering observation, in the same session |
| Continuity | nothing is reset: history, workspace, candidate, action and repair counters, and remaining budget all carry on. The frontier wait is excluded from the local clock |
| Provider | `provider: api` (final); one request, 300 s timeout, no retry; a failure is recorded and the agent continues with the public feedback |
| Evidence | at 11 frozen trigger states: diagnosis-v1 6, a neutral length-matched message 2, no message 3 |
| Optional control | `provider: fixed` with the neutral text: separates diagnosis content from interruption; no API cost |

## Open decisions (team approval needed before the final freeze)

1. **Shared agent:** keep `frozen-v6`, or adopt `l1-selfplan-v1` with a validated larger context. If adopted, keep a
   `frozen-v6` A arm so the interface effect is measured on the holdout.
2. **D:** D-v1 (primary) or D-active as a labelled variant, with its inputs-only control.
3. **Context overflow policy:** a deterministic `correctness.context_overflow` counts as a failed attempt
   (recommended), not as an infrastructure exclusion.
4. **Optional controls:** the E neutral-message arm; the D inputs-only arm.
5. **API ceilings** for the final run (`providers.MAX_REQUESTS` / `MAX_USD`) and B's `max_requests` per run.
6. **Task pool:** main 60 (arc195_c excluded or validated) plus `test5`, as in the pass-3 options.
