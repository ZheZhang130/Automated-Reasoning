# B versus C economics (pass 4, Phase VI)

**Question.** Does frontier-guided local coding (C) save money relative to frontier-only coding (B), and at what
loss of success?

**Cohort.** The 12 hard tasks of the pass-3 extended benchmark. In pass 4 they are **consumed development tasks**,
not a holdout. A and C have two seeds each (pass 3, original agent, Codex plan-v1). B was run in pass 4.

**Sources.** `diagnostics/cost_comparison.py` → `evidence/cost-comparison.json`; per-attempt records follow the
pass-4 measurement schema.

## 1. B's implementation (audit, brief §10.1)

| Check | Result |
| --- | --- |
| Same coding interface and sandbox | yes: `frontier_coder` rebinds only `TextModel`; system prompt, action regex, observation template, sandbox, judge-public and budgets are the frozen agent's |
| Context and output budget | full message history every turn; 8,000 completion tokens per request (API), Codex default (replay). B's first responses on hard tasks used 2,000–3,600 tokens including reasoning; none hit the limit |
| Can write, run, inspect, repair and resubmit | yes. On arc190_c (API) B wrote the program, patched it with `sed`, ran the public tests, then wrote and ran its **own random brute-force comparison**, patched again, retested and submitted (7 requests). Synthetic repair after a public failure is covered by the scripted-coder integration tests |
| No extra tools | yes: every action is text executed by the shared environment; Codex runs as a fresh ephemeral `codex exec -s read-only` session in an empty directory; 0 tool events in all 36 Codex coder turns |
| Request limits and accounting | per-run `max_requests` (Codex 28 = the agent's step limit; API 8 in this pass); one pass-wide ledger (`CSC2108_API_LEDGER`), 20 requests / $10, write-ahead reservation, no retries |
| Premature termination | none observed. The 20-action / 600-second budgets were never approached (at most 7 actions, 148 s) |

## 2. Results on the 12 hard tasks

| | Attempts | Hidden passes | No program | Frontier requests / attempt | API $ / attempt | API $ / success | Local inference s / attempt | Wall s / attempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A (local only) | 24 | **2** (8%) | 17 | 0 | 0 | — | 130.0 | 143 |
| C, plan generated for this one attempt | 24 | **13** (54%) | 8 | 1 (upfront) | 0.0165 (modelled) | 0.0305 | 70.5 | 81 |
| C, plan shared by 2 seeds | 24 | 13 | 8 | 0.5 | 0.0083 (modelled) | 0.0152 | 70.5 | 81 |
| C, plan shared by 3 seeds | 24 | 13 | 8 | 0.33 | 0.0055 (modelled) | 0.0102 | 70.5 | 81 |
| B, Codex replay coder | 12 | **11** (92%) | 0 | 3.0 | not billed | — | 0 | 54 |
| B, direct API coder (arc194_e, arc190_c) | 2 | 1 | 0 | 5.5 | **0.0698 (measured)** | 0.140 (n = 2) | 0 | 83 |
| B, direct API, pass 3 (abc393_d, abc388_g; easier) | 2 | 2 | 0 | 3.0 | 0.0108 (measured) | 0.0108 | 0 | 14 |

**How the C plan cost is modelled.**

* The hard-cohort plans were authored by Codex, so their dollar cost is not measured.
* Per task, the model is Codex's output tokens (which include its reasoning) at $10/1M, plus the mean input of the
  measured API plans (about 780 tokens) at $2/1M. The mean is **$0.0165** (range 0.0087–0.0388).
* The 6 measured API plan-v1 requests of passes 1–3 (easier tasks) cost $0.0070–0.0160, mean **$0.0104**, so the
  model is in line with what was measured. Hard tasks need more reasoning.

**Local compute.** `local inference s` is the measured sum of Ollama `total_duration`, i.e. GPU-busy time on the
RTX 4080 SUPER. The modelled electricity at 350 W and $0.15/kWh is about **$0.0019 per A attempt and $0.0010
per C attempt**. These are assumptions, not measurements; the GPU seconds are the measured quantity.

**Per-task pattern (hard cohort).**

* **B fails only arc190_c**, at both providers. Its program passes the public tests and fails hidden; C fails
  arc190_c at both seeds too.
* **C fails 5 tasks completely:** abc388_f, abc397_f, arc190_c, arc194_e, arc195_d. B passes 4 of those.
* **C succeeds on no task where B fails.**

## 3. Conclusions

1. **On hard tasks, C costs less API money per success than B.** Per success, C (one-off plan) costs about $0.03
   and B (API) about $0.07–0.14, roughly 2.5–4.5 times more. Taking B's success rate from the 12 Codex-replay
   runs (92%) instead of the two API runs (50%), B's cost per success is about $0.076.
2. **C does not reach B's success rate:** 54% against 92% (Codex replay) on the same tasks. C's cheaper API dollar
   buys a much lower probability of solving the task, and C additionally needs about 70 s of local GPU time per
   attempt.
3. **Amortizing a plan over seeds halves or thirds C's API cost.** This only applies to benchmark reuse. A real
   one-off task pays the full plan cost, and the one-off row is the relevant one for the "saves money" claim.
4. **On easier tasks the comparison reverses.** B's measured cost falls to about $0.011 per task, comparable to one
   plan ($0.010), and A alone often succeeds at zero API cost. C then saves almost nothing over B.
5. **Repair trajectories raise B's cost, but modestly.** The one natural repair trajectory (arc190_c: 7 requests)
   cost $0.096, 2.2 times the 4-request run. No B run approached its request or action limit.
6. **Local inference is not free.** C needs a GPU and time: 81 s of wall time per attempt against B's 54 s
   (Codex) to 83 s (API).

**The defensible economic claim** is narrow:

* C buys a large improvement over local-only coding (2 → 13 of 24) for about one cent of API per attempt.
* It costs less per success than B in API dollars on hard tasks.
* But frontier-only coding solves substantially more of the same tasks, at a cost that remains well under $0.15
  per task.

Whether C "saves money" depends on whether a 54% local success rate is acceptable. Taking the Codex-replay success
rate as representative, the cheapest *successful* path for these hard tasks is B. **Do not claim a cost advantage
for C without stating its success rate.**

## 4. Uncertainty and limitations

* **Tiny API sample.** Only two direct-API B runs exist on hard tasks (two more on easier ones). B's API cost per
  success on hard tasks is uncertain within roughly $0.05–0.15.
* **Codex replay is not the API.** Different harness context; its token counts are not costs. Its success rate is
  used as an estimate of B's, and the two API runs agree on the shared tasks (arc194_e pass, arc190_c fail).
* **Consumed tasks, one B sample per task, no seeds for B** (frontier sampling is not seeded).
* **Hardware.** C's local time is for one RTX 4080 SUPER under exclusive use. Modelled electricity ignores idle
  power, amortized hardware cost and the user's time.
* **The improved shared agent** (if any is selected) is evaluated with C in `LOCAL_AGENT_EXPERIMENTS.md`. This
  table uses the original agent.

## 5. API spending of pass 4 (ledger, measured)

| # | Kind | Condition | Input / output tokens | USD (standard) |
| --- | --- | --- | --- | --- |
| 0–3 | coder turns | B, arc194_e (pass) | 913–1,710 / 119–2,532 | 0.0433 |
| 4–10 | coder turns | B, arc190_c (public pass, hidden fail; self-repair) | 1,621–4,265 / 20–3,553 | 0.0964 |
| 11 | plan-v1 | C, arc192_a (end-to-end run: pass 40/40) | 917 / 1,497 | 0.0168 |
| 12 | contract-v3 | D-active, arc192_a (run produced no program; checks never ran) | 1,267 / 877 | 0.0113 |
| 13 | diagnosis-v1 | E, abc393_d (triggered, delivered in 6.4 s, repaired, pass) | 1,994 / 300 | 0.0070 |
| | **Total** | 14 requests (ceiling 20) | | **$0.1748** (conservative bound $1.05; ceiling $10) |

* **No retries.** All 14 requests completed. One free metadata call (`GET /v1/models/gpt-6.2-sol`) confirmed the
  model identity first; the pricing was rechecked against public listings ($2 / $10 per 1M; cache writes $2.50).
* **The hard-task plan model checks out.** The measured API hard-task plan ($0.0168) matches the $0.0165 modelled
  mean used in §2.
