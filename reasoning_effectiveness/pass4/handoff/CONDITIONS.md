# Condition specifications (final)

**Shared by every condition:**

* **Sandbox and protocol:** the same task bundle, sandbox, mini-SWE-agent loop, action protocol (one fenced shell
  command per response), judge-public and judge-hidden.
* **Budgets:** 20 actions, 3 repair groups, 600 s of local coding time, 180 s per model request.
* **Shared agent configuration:** `<AGENT>` (see §0). The configuration is the same for A, C, D and E in any
  comparison. B substitutes the coder and keeps the interface.

## 0. Shared agent

`<AGENT SECTION>`

## A: local only

| Item | Value |
| --- | --- |
| Frontier calls | 0 |
| First message | the statement (frozen `{{task}}` template)`<A extra>` |
| Feedback | judge-public report at each `python -I /public/check.py` |
| Records | no frontier fields; `frontier.n_requests = 0` |

## B: frontier only

| Item | Value |
| --- | --- |
| Coder | `gpt-6.2-sol` through the OpenAI API (`frontier_coder.ApiCoder`), effort medium, up to 8,000 completion tokens per request, full message history every turn |
| Interface | identical to A: same system prompt, regex action parser, observations, sandbox, judge-public and budgets. No tools of the frontier's own |
| Requests | one per agent turn; per-run cap `max_requests` (recommended 28, the agent's step limit); no retries; every request reserved in the ledger before sending |
| Development substitute | isolated Codex replay (`provider: codex`); not billed, not API-equivalent, label separately |
| Local model | none (no GPU lock taken) |

## C: frontier plan

| Item | Value |
| --- | --- |
| Frontier calls | 1 per task, before any run (`author --prompt-id plan-v1`) |
| Frontier input | the public statement and the teammates' `plan-v1` prompt only |
| Output | natural-language plan: `## Observations`, `## Solution sketch` (no code; validated) |
| Delivery | `inject-v1`: the statement, then "Implementation plan from a stronger model … not verified", then the plan, in the first user message |
| Reuse | one write-once artifact per task (statement-hash bound), shared by seeds; never regenerated after outcomes |

## D: frontier contract

`<D SECTION>`

## E: frontier diagnosis

`<E SECTION>`

## Open decisions (team approval needed before the final freeze)

`<OPEN>`
