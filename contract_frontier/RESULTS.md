# Contract frontier smoke results

Date: 2026-11-20. Both runs use Codex-authored contracts and local Qwen3.5 9B
MLX, with mini-SWE-agent 2.4.6 and LiteLLM 1.81.16. A fresh Codex authoring
context received the two public statements and contract-format instructions,
used no tools, and returned both contracts in one turn. Earlier solutions,
execution logs and independent test cases were not supplied to the author.
Saved input artifacts preserve the contract text, statement hashes and provenance.

Each local run receives one upfront contract. No local feedback is sent back
to Codex and no frontier API is called inside the runner. Authoring cost and
latency are unknown and excluded from wall time. The selected local settings
are 16384 context tokens, 4000 output tokens, 20 actions, 3 repair groups,
and 600 task seconds.

| Task | Local termination | Actions / repairs | Public checker | Independent cases | Seconds |
| --- | --- | --- | --- | --- | ---: |
| Signed sum | Submitted | 3 / 0 | 1 invocation, all 3 cases passed | 6/6 passed | 25.06 |
| Dynamic connectivity | Model request timeout | 7 / 3 | 3 invocations, each failed first case | 0/31 passed | 523.08 |

The difficult task's final captured model request hit its 180-second request
timeout, before the 600-second total deadline. The record retains this as
error/APIConnectionError. There was one earlier output-truncated coding response.
The local model later produced code and observed actual public failures.
It answered NO instead of YES for an available two-edge path on the first
case. The unchanged result persisted after attempted repair.

The 31 independent difficult cases are the same 30 randomized oracle cases and
one large stress case used in the planning smoke tests. The final candidate
executed but gave incorrect results on all of them. It was evaluated after the
run; these results were never returned to either model. The six independent
sum cases include cancellation, zero, two negatives and very large integers.

## Scope

The simple test validates contract loading, injection, coding, public testing,
submission and candidate extraction. The difficult run validates the same
guidance delivery and the local test/repair/error paths. It does not demonstrate
a correctness benefit from contracts. There are only two synthetic smoke tasks,
with no new resource-matched baseline or statistical comparison.

The paper studies extracting contracts from source and using them for test
generation. This implementation derives task contracts and guides implementation.
Conditions remain labeled Unverified; neither the prose nor the section validator
is a proof of correctness. Codex-generated contracts were replayed, and the live
frontier API provider remains untested without credentials.

12 offline tests pass: 3 contract tests plus 9 existing planning/runner tests.
Raw evidence is retained locally under smoke-evidence/ and ignored by Git;
smoke-summary.json is a lightweight numerical handoff suitable for GitHub.
