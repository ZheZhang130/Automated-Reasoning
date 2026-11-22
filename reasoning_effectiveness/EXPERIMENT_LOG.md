# Experiment log — reasoning-effectiveness pass (2026-11-21/22, Windows desktop)

All times are EST. Raw artifacts are under `E:\CSC2108Local\reasoning-effectiveness` (outside Git).
Each entry gives the hypothesis, what changed, the evidence and the decision.

## 22:31 — Session start and environment

* Fetched origin; `origin/orchestration` was still `a42aaff`. Created `feat/csc2108-reasoning-effectiveness` in worktree `../ar-reasoning`.
* Docker Desktop and the project Ollama server were stopped. I started both with the existing scripts, after backing up the previous Ollama logs to `E:\CSC2108Local\logs\*.pre-reasoning-*.log`. Ollama is now **0.40.17**; historical runs used 0.40.16.
* `python -m local_agent verify` passed (38 frozen files, model digest `56671c2a…`).
* Existing offline suites: planning 10/10, contract 4/4, orchestration 9/9, local_agent 14 (2 skipped). The judge tests cannot import on Windows (`fcntl`). See `INTEGRATION_AUDIT.md`.

## 22:40 — Frontier provider setup (no paid calls)

* **T3 Code delegation was unavailable**: its MCP server failed to connect this session. I used the supported alternative, `codex exec` (Codex CLI 0.171.0), configured as a model-only single response. Fresh `--ephemeral` session, `--ignore-user-config`, `--ignore-rules`, `-s read-only`, an empty temporary working directory, web search and tool features (`shell_tool`, apps, plugins, multi-agent, browser, computer use, hooks, skills…) disabled, and credential-like environment variables removed.
  * Smoke prompt ("reply OK"): the event stream contained exactly one `agent_message` and no tool events. It reported 10,915 input tokens, which is Codex's own harness context. **Limitation:** Codex's harness instructions and tool descriptions stay in the model's context. Isolation is verified post hoc from events, not by the absence of tools.
  * Model `gpt-6.2-sol` (the catalogue lists default effort `low`). Tonight both providers use explicit reasoning effort `medium`.
* `.env` lists `FRONTIER_MODEL=openai/gpt-6.2-sol` (key not printed). Official pricing, checked 2026-11-21: $2.00 / 1M input and $10.00 / 1M output (standard tier). The pricing page also shows unlabeled $4/$20, $6/$30 and $12/$60 tables. The ledger therefore bounds every request at the highest tier ($12/$60), with `max_completion_tokens=8000`: ≈ $0.50 per request, ≈ $6 for 12, under the $10 ceiling. The client is direct HTTPS (no LiteLLM, no retries) with a write-ahead ledger.

## 22:55 — Integrated backend (`guided_agent/`) and smoke

* **Design.** The unchanged `runtime.run` bytecode runs every condition. Only two globals are rebound: `Agent` (instance template gets a guidance block; A keeps `{{task}}`) and `Environment` (the recognized `python -I /public/check.py` goes to Peter's judge-public, and the agent sees its `report`). Hosts: on Windows the original globals; on portable hosts `local_agent.portable.adapted_run`, then the same two rebindings.
* **Bug found in the team pipeline:** `judge/build_data.py` writes test files with `Path.write_text`, which converts LF→CRLF on Windows. Manifest hashes therefore fail on Windows (arc195_a: public and hidden mismatch). The study builder writes with `newline=''`; afterwards all 4 pilot-manifest tasks matched the manifest hashes. Judge code was not edited. Team action: fix `build_data.py` (`newline=''`).
* Built Peter's image `csc2108-judge:0.2.1` (`sha256:c8e6c9b6…`, amd64). Judge containers use study-specific names (`csc2108re-judge-public/hidden`) and data root, so teammates' containers are untouched.
* Synthetic fixture smoke (A): 3 actions (write, judge-public 2/2, submit), sampler wire-verified, hidden fixture `pass`. 35.7 s wall.

## 22:58 — Task selection (before any task inference)

`guided_agent/selection.py`, seed 2108, public metadata only → `E:\CSC2108Local\reasoning-effectiveness\selection.json`.

| Cohort | Tasks |
| --- | --- |
| Development (previously scored / teammate-used, outside main manifest) | abc391_a (E), abc400_b (E), arc195_a (M, pilot), arc192_a (M) |
| Mini-benchmark 1 (Codex replay; fresh) | abc396_a (E, pilot), abc392_d (M), abc390_c (M, pilot), abc396_d (M), abc394_c (M, pilot), abc388_g (H) |
| Mini-benchmark 2 (direct API; fresh) | abc393_d, abc396_e, abc393_e, abc391_e (all LCB "hard", ABC D/E) |

The fresh pool is the problem. After the main manifest, the 75-ID union and teammate use, test6 has **0 fresh easy and 2 fresh medium** tasks outside the pilot manifest. MB1 therefore uses 4 fresh pilot-manifest tasks; the pilot manifest is designated for pipeline piloting, so the main cohort stays untouched. MB2 cannot follow the "prefer medium" guidance, because no fresh medium task remains, so it uses the lowest hard band (ABC D/E).

## 22:58–23:10 — Phase III, dev1: A/C/D, Codex-authored v1 guidance, original agent

Guidance: `plan-v1` (teammates' PlanSearch-inspired prompt) and `contract-v1` (teammates' contract prompt), authored by isolated Codex `gpt-6.2-sol`, effort `medium`, one response each. Every event stream contained one `agent_message` and no tool events. Seed 2108, frozen agent, judge-public feedback.

| Task | A | C (plan) | D (contract) |
| --- | --- | --- | --- |
| abc391_a (E) | ✓ 40/40 | ✓ | ✓ |
| abc400_b (E) | ✓ 40/40 | ✓ | ✓ |
| arc192_a (M) | ✗ no submission (`RepeatedFormatError`, 3×4096-token truncations, 0 actions) | ✓ 40/40, 3 actions, 18 s | ✗ submitted, 20/40 hidden (passed all 3 public) |
| arc195_a (M) | ✗ submitted, 39/40 hidden (public 3/3 after repairs) | ✓ 40/40, 7 actions, 2 repairs | ✗ no submission (`RepeatedFormatError`, 3×4096-token truncations) |
| **Total** | **2/4** | **4/4** | **2/4** |

Local completion tokens: A 24,431, C 3,012, D 23,899. Length truncations: A 5, C 0, D 5. Local coding time: A 301 s, C 76 s, D 288 s.

**Guidance quality (manual check against the public statement).** Both plans for the medium tasks are correct and contain the decisive insight. arc195_a: earliest/latest greedy embeddings, answer Yes iff they differ. arc192_a: an N mod 4 / parity rule with a constructive justification. The plans are long (451 and 629 words), with no code. The contracts are correct, precise restatements: PRE/POST, M=1 and M=N boundaries, and small hand-derived checks. As the prompt requires, they carry no algorithmic information.

**Trajectory evidence.**
* **A on mediums**: Qwen puts its algorithm search inside `#` comments in the heredoc that writes `solution.py`. Truncated responses run 11–16K characters, mostly comment lines like "Actually, let's use a simpler approach…". arc195_a A then rewrote the same wrong program **six times byte-for-byte**. Each time it saw only `<returncode>0</returncode>`, before eventually passing public tests with a 39/40 program.
* **C**: the first response implements the plan's algorithm directly (arc195_a: forward and backward scans exactly as sketched). The only defect, an index-order bug in the backward list, was found by tracing the failing public case and repaired. No truncation in any C run. The guidance clearly displaced the in-file brainstorming.
* **D**: on arc195_a the contract did not stop the brainstorming, and all three responses truncated. On arc192_a D wrote a wrong heuristic (maximum circular zero-run ≤ 2). It passed the three samples and was submitted without running any of the contract's checks.

**Failure attribution (dev1).** A/D medium failures: mainly (6) output budget exhausted by in-file brainstorming → (4) action-delivery failure, and (3) local algorithmic mistakes. D's arc192_a is also (5) ineffective local testing: available spec checks were unused. No failure was due to incorrect frontier reasoning or infrastructure.

**Decision.** The data support three narrowly scoped Phase IV families, each with a separate control:
1. **aci-v1 (shared A/C/D):** a specific truncation message (the frozen `FORMAT_ERROR` global is rebound) plus `[harness]` notes when `solution.py` is rewritten byte-identically or an already-failed program is retested. *Hypothesis:* fewer RepeatedFormatError exits and identical rewrites in A/D. *Success criterion:* fewer delivery failures with no correctness loss in any condition.
2. **contract-v2 (D only, agent unchanged):** discriminating hand-derived input→output checks, plus an injection line asking the coder to run them before submitting. *Hypothesis:* catches plausible-but-wrong programs like arc192_a D. It cannot address algorithm discovery, by design. *Success criterion:* D correctness up on dev with no new delivery failures.
3. **Seed replication (seed 2109)** of the original A/C/D. This is not an intervention; it measures whether dev1 differences are stable at temperature 0.2.

Plan-v1 is not changed: it was correct and effective on every dev task, and there is no evidence that length matters.

**Validation refinement (23:05).** The first contract-v2 authoring tripped my hard "fenced block" check, because Codex wrapped *test inputs* in ```` ```text ```` blocks. I changed the rule to allow plain-text fences whose content is not code-like, and artifacts are revalidated at load time. Nothing was re-authored, so this is not rejection sampling. I hand-checked all 6 arc195_a and 3 abc400_b contract-v2 expected outputs: all correct.
