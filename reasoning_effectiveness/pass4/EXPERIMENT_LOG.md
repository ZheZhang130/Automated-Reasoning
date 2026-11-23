# Pass 4 experiment log (chronological, EST, 2026-11-23)

Every batch, probe, failure, cost and decision of pass 4. Study roots (outside Git):

* `E:/CSC2108Local/reasoning-effectiveness-pass4`: local-model batches and probes;
* `…-pass4-b`: B coder runs. A separate root gives them separate judge containers, so B can run beside the GPU
  batches;
* `…-pass4-tests`: Docker integration tests.

| Time | Event |
| --- | --- |
| 00:52 | Start. Branch `feat/csc2108-contract-diagnosis-pass2` at `0f18f59`, identical to origin, clean. `feat/csc2108-final-agent` does not exist. |
| 00:55 | Project Ollama restarted on 127.0.0.1:11435 (0.40.17, same as pass 3), without touching user-level environment variables. The user's endpoint 11434 had no loaded model. |
| 00:57 | **Wire probe** (direct Ollama and LiteLLM, no agent): thinking is returned separately and mapped to `reasoning_content`; `num_predict` caps thinking and answer together (a 128-token cap gave empty content). See `BOTTLENECK_AUDIT.md` §3. |
| 00:58 | **Trace check:** aci-v2's repeat guard did remove duplicate assistant messages; this corrects the pass-3 report (audit §4). |
| 01:00 | Commit `f590787`: versioned shared-agent configurations (`agent_config.py`: frozen-v6, l1–l4) and the screening pre-registration. |
| 01:02 | **Batch `p4-screen-s2108`** started: 8 development tasks × 5 agent configurations, condition A, seed 2108 (40 attempts). The first block, abc400_b, served as the live smoke test: all five configurations ran, with wire-verified samplers, 38 frozen files verified and the digest matched. |
| 01:05 | contract-v3 authored by isolated Codex for abc400_b, abc389_f and abc397_f, the only dev tasks without one (one call each, no validation problems, no regeneration). |
| 01:08 | Commit `9107f17`: D-active (`contract_checks.py`), diagnosis-v2, no GPU lock for substituted coders, `test_pass4.py`. 10 offline tests and 4 Docker integration tests pass. The first integration run failed because the GPU lock was held by the batch; scripted and remote coders now skip the lock, which they never needed. |
| 01:10 | **Batch `p4-b-codex`** started (study `-pass4-b`): B with the isolated Codex coder on 6 hard development tasks. It runs beside the GPU batch. |
| 01:11 | Commit `a270e0e`: stage-C plans (D-active with two controls; E probe at 11 frozen trigger states) pre-registered. The chain starts them automatically after screening. |
| 01:13 | One-shot probe (Phase I §5.5) queued after stage C. Bottleneck evidence over the 217 original-agent runs of passes 1–3 computed. |
| 01:16 | **Batch `p4-b-codex2`** queued: B Codex on the other 6 tasks of the pass-3 hard cohort, so B and C are compared on all 12. |
| 01:16 | `p4-b-codex` finished: 6/6 submitted in 3 actions. Hidden 5/6 (arc190_c failed hidden after passing the public tests). |
| 01:22 | `p4-b-codex2` finished: 6/6 submitted in 3 actions, hidden 6/6. **B (Codex) on the 12-task hard cohort: 11/12**, 0 tool events in 36 coder turns. |
| 01:23 | Contract-check validity (`check_validity.py`, sandboxed): 32/32 proposed outputs correct against reference programs; 20/27 natural wrong programs caught; abc398_d 0/6 (its wrong programs fail only by TLE). |
| 01:24 | Pricing rechecked (gpt-6.2-sol standard $2/$10 per 1M; cache writes $2.50) and model identity checked (`GET /v1/models/gpt-6.2-sol` 200, free). Pass-wide ledger `reasoning-effectiveness-pass4/api-ledger.json` created with 20 requests / $10. |
| 01:25 | **Batch `p4-b-api`** (paid): B direct API on arc194_e (4 requests, $0.0433, hidden pass) and arc190_c (7 requests, $0.0964, public pass, hidden fail; B ran its own brute-force comparison and patched twice). Ledger: 11 requests, $0.1397 standard. |
| 01:29 | Cost comparison computed (`cost_comparison.py`). A Codex artifact usage-nesting bug in `measurement._usage` was found and fixed (the modelled plan cost went from $0.0016 to $0.0165). |
| 01:20 | **Incident:** an edit to `guided_agent/__main__.py` briefly contained a syntax error (shell-escaping). The running batch spawns a fresh process per attempt; no attempt started during the window (verified: the next attempt's directory and log are complete). From then on, every edit is followed immediately by an import check. |
| 02:38 | `p4-screen-s2108` finished (40/40 attempts, 0 infrastructure failures); hidden evaluation 02:41. **l1 self-plan 4/8 against frozen 1/8 (+3, 0 losses)**; l2 1/8 at 2.1× tokens; l3 2/8 at 1.7×; l4 1/8 with repeats 5→0. l1 qualifies under the pre-registered rule. |
| 02:41 | Frozen reruns confirmed byte-identical to the historical runs (same submissions, actions and token counts). Stage-D plan reuses historical frozen cells and runs only the missing ones. Stage D pre-registered (commit `0061a12`). |
| 02:41 | Stage C (`p4-dactive-s2108`, 24 attempts) started automatically. |
| 03:17 | D-active finished: active 3/8, inputs control 3/8, v3passive 2/8 (historical D-v1 3/8, A 1/8). abc397_f solved only by active; abc388_e public-passing wrong program detected by K-3 three times, not repaired. **Not promoted** (+1 / 0 net). |
| 03:20 | Final-branch preparation started in a scratch export (not a worktree): archive-only material removed, ACI/receipts/D-active code pruned. |
| 03:35 | Stage-D D/E batch switched from D-active to the primary D-v1 under the candidate (historical contract-v1 artifacts verified by sha256). |
| 04:03 | E probe finished (17 attempts; all 11 states reproduced by candidate hash). Hidden passes: A 3, diagnosis-v1 6, neutral 2 (2 harms), diagnosis-v2 5. **diagnosis-v1 retained**; diagnosis content, not interruption, explains E's rescues on the hard states. |
| 04:06 | One-shot probe started (chain 3); stage D (chain 4) and D/E under l1 (chain 5) queued. |
| 04:14 | One-shot probe finished: 3/8 (abc400_b, abc393_d, arc195_a); the other 5 hit 8,192 tokens without a final program. Two tasks are interface failures of the original agent (the model solves them one-shot). |
| 04:15 | **Stage D** (`p4-stageD-agent`, 31 attempts) started. |
| 04:28 | Direct API authoring for the end-to-end validation: plan-v1 and contract-v3 for arc192_a (2 requests). Ledger 13 requests, $0.168. |
| 04:53 | Stage D finished. A-l1 7/16 against frozen 4/16; C-l1 12/16 against C-frozen 14/16; seed-2109 A net 0. Criteria 1 and 3 fail, so **frozen-v6 stays primary**. Both determinism spot checks were byte-identical. |
| 04:55 | 3 C-l1 runs and 1 E (diagnosis-v2) probe run ended `infra_error`. Diagnosed as **context overflow**: the prompt reached 15.4–16.1K tokens, then an Ollama connection error. They are deterministic agent failures, not infrastructure (outside the pre-registered infrastructure categories), and are counted as failures. Sensitivity: excluding them would not change the decision. The measurement record gained `correctness.context_overflow`. |
| 04:53 | `p4-stageD-de` (D-v1 and E-v1 under l1, 16 attempts) started; the API validation (`p4-api-validation`, under frozen-v6) is queued after it. |
| 05:00 | Final-branch tree prepared and tested in a scratch export: 71 offline tests, 8 Docker integration tests, `local_agent.test_portable` (9) and `verify --offline` all pass. A plumbing dry run (temporary index, no checkout) built the expected commit. |
| 05:20 | `p4-stageD-de` finished (16 attempts). D-v1 under l1 4/8 (frozen 3/8); E-v1 under l1 4/8 (frozen 2/8), but triggered only 1/8 times (frozen 3/8). |
| 05:25 | **API validation** (`p4-api-validation`, frozen-v6, arc192_a): C with the API plan passed (40/40, 3 actions). D-active and E produced no program (truncation), so the checks never ran and no diagnosis request was made. |
| 05:28 | **API validation of E** (`p4-api-validation-e`, abc393_d, seed 2108, a known trigger state): triggered on the reproduced candidate `d099a73c6a`; the API diagnosis was delivered in 6.4 s for $0.0070; repaired in the same session; hidden pass. Ledger final: **14 requests, $0.1748** (conservative $1.05), no retries. |
| 05:35 | Final development documents written. The handoff documents (also on the final branch) are copied to `pass4/handoff/`. `make_final_branch.sh` builds the final branch from the prepared tree with a temporary index, without checking it out. |
