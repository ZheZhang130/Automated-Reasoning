# Condition finalization (pass 4)

One recommended primary configuration per condition. All hashes are sha256 of the exact text the code uses; the
final branch's `FINALIZATION_MANIFEST.json` records them, and `guided_agent.test_pass4.Manifest` rechecks them on
every test run.

## Shared agent

| Item | Final |
| --- | --- |
| Version | **`frozen-v6`** (definition `{}`, sha256 `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`): profile `heredoc-v6-16k-common`, frozen prompts and observation format, 38 hash-verified files |
| Mechanics | mini-SWE-agent 2.4.6 text protocol, one fenced command per response, judge-public for `python -I /public/check.py`, frozen sandbox |
| Budgets | 20 actions, 3 repair groups, 600 s, 180 s per request, 3 consecutive format errors, 16K context, 4,096 output tokens |
| Validation | reproduces historical runs byte for byte (pass 4: 8/8 screening tasks, 2/2 C spot checks); 217-run bottleneck audit |
| Known limitations | no place to reason outside the file being written (deliberation truncates on hard tasks); 16K context can overflow in long sessions (1 pass-4 run under this agent) |
| Alternative | `l1-selfplan-v1` (sha256 `06b12c078be874b47a9ded3a26f438cd46a0eaf351dbe56e45d18f0203efa30c`): A 4/16 → 7/16 but C 14/16 → 12/16; context overflow in 3/16 C runs. Not promoted under the pre-registered rule (`LOCAL_AGENT_EXPERIMENTS.md` §6) |
| Reason | the pre-registered rule did not select the candidate; the original agent is reproducible and its limits are now documented |
| Historical comparability | preserved (unchanged agent) |

## A: local only

| Item | Final |
| --- | --- |
| Version | `frozen-v6` with the frozen first message `{{task}}` |
| Frontier calls | 0 |
| Budgets | 20 actions, 3 repair groups, 600 s coding time, 180 s per request (frozen) |
| Validation | 40 screening attempts (pass 4), passes 1–3; determinism verified byte for byte |
| Known limitations | no program on 4 of 8 development tasks under the original agent (deliberation inside the heredoc truncates); see `BOTTLENECK_AUDIT.md` |

## B: frontier only

| Item | Final |
| --- | --- |
| Version | `frontier_coder.ApiCoder`: `gpt-6.2-sol`, effort medium, `max_completion_tokens` 8,000, full history; the shared agent's interface (system prompt, action regex, observation template, sandbox, judge-public, budgets) |
| Requests | one per turn; recommended per-run cap `max_requests` 28 (the step limit); no retries; ledgered write-ahead |
| Development substitute | `CodexCoder` (isolated `codex exec -s read-only`, empty directory, per-turn transcript); label as replay, never pool with API |
| Validation | 12 hard development tasks with the Codex coder (11/12, 3 actions each); 2 hard tasks via the API ($0.043 and $0.096, the second a natural self-repair trajectory, 7 requests); pass-3 API runs on 2 easier tasks; scripted-coder repair and request-cap tests |
| Known limitations | API cost on hard tasks measured on only 2 runs; frontier sampling is not seeded (no seed variation); B does not use the local model, so its "local" fields are null |

## C: frontier plan

| Item | Final |
| --- | --- |
| Version | `plan-v1` (teammates' planner prompt, sha256 `f4f830d2f2fba0f664778577e06dd6a60d61215b54445ced792b2c67d8f74da6`) + `inject-v1` plan template (`e5d9ff35f486775d820fd14ed8681b5e4478b92fbd74b7a8d3934eddd28425cf`) |
| Frontier calls | 1 per task, before any run; artifact frozen by hash and reused by seeds |
| Validation | passes 1–3 (13/24 on the hard cohort against A 2/24); pass 4: 14/16 on the 8 development tasks (two seeds) against A 4/16; one end-to-end API run (see `EXPERIMENT_LOG.md`) |
| Known limitations | plan quality decides the outcome (pass 1); one sample per task; the Codex-authored development plans are not API cost measurements |
| Reason | strongest guided condition; unchanged since pass 1 |

## D: frontier contract

| Item | Final |
| --- | --- |
| Version | **D-v1**: `contract-v1` (teammates' contract prompt, `97fd739455bc0a55ce04e25fd291dac666d0ce7a93477c5e0cad983508d4b682`) + `inject-v1` contract template (`30e3fb753cd7c7afb042c89372c84ba36ec6510185f276892f0919e04da44c2e`) |
| Frontier calls | 1 per task, before any run |
| Validation | passes 1–3; pass 4 D-active comparison: D-v1 3/8, contract-v3 passive 2/8, D-active 3/8, inputs-only control 3/8 |
| Known limitations | does not shorten the local agent's deliberation (pass 3 §6.1); contracts rarely help an agent that cannot find the algorithm |
| Alternative (not promoted) | **D-active**: contract-v3 (`3dae83acc76cabb361a7b79678626b95176af713fe0cacb4f22ddfd704e00644`) + `inject-active-v1` (`93e220bed686356caf66802614ebcd91cad54627fd6ab9fa382310f3baa059ec`) + harness-executed K-checks (`contract_checks.py`, development branch). Benchmark-safe and tested. Detects public-passing wrong programs (abc388_e) and solved abc397_f; net +1 over passive and 0 over the inputs-only control. If adopted, it must be a labelled variant run with its control. |
| Reason | the proposal's original D, unchanged teammates' prompt; D-active's gain is not separable from extra testing opportunity on this evidence |

## E: frontier diagnosis

| Item | Final |
| --- | --- |
| Version | `diagnosis-v1` (`3d2c77611009163d4d1a8fa20922db5e719f184207f2efa84ff0f65fdc0fefb8`) + `deliver-v1` (`dbe4c788c6329843f146737b6d4baf4dcdf95170b4ba846974c92b991d09b954`) |
| Trigger | first qualifying public failure (WA/RE/TLE/CE of a non-empty candidate whose judged hash equals the snapshot); never an infrastructure error; at most once per attempt |
| Frontier calls | 0 or 1 per attempt; timeout 300 s; no retry; the wait is excluded from the local clock |
| Session | the same mini-SWE-agent conversation, workspace, candidate, action and repair counters and budgets; one extra user message |
| Validation | integration tests (passes 2–4); 16 audited real diagnoses (16/16 identified the fault); 11-state probe: v1 6/11, neutral 2/11, v2 5/11, A 3/11 |
| Known limitations | triggers only when a program reaches a public test (6/24 on the pass-3 hard cohort under the original agent); one diagnosis sample per state; rescues are limited by local implementation capability |
| Alternative (not promoted) | `diagnosis-v2` (`b89363cecda80a48fbaa559d9758f3ddea438f779b8e0ec20b89cacfe501a6d7`): 5/11 |
| Reason | best supported; its benefit over a neutral interruption is now demonstrated on the hard states |
