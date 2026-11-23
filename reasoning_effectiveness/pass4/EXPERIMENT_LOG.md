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
