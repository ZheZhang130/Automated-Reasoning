# mini-SWE-agent delivery-prompt diagnostic

Experimental execution: **complete, 1199.0 / 2,100 seconds**, including CPU controls, both A2 synthetic fixtures, all inference, official judging and cleanup. No repeated benchmark attempts or post-validation tuning.

[Phase 1 failure analysis and source citations](FORENSICS.md) was completed before new inference. The old first replies started immediately with a source-writing command, but long planning comments prevented closing the command before the 4,096-token cap. On leetcode-3677, public failures were recognized and subsequent writes were byte-identical; this was not a repair-counter bug.

**One intervention:** A2 (`heredoc-v6-16k-common-delivery-prompt-v1`) replaces only the system prompt with shorter delivery-focused instructions: compact source without planning commentary, one closed command, then write → visible test → changed repair → submit. Genuine mini-SWE-agent, persistent workspace, parser, strict rejection of malformed commands, feedback, repair accounting and sandbox are unchanged. The prompt is tested as a unit, not as separate independently identified wording effects.

All conditions: local qwen3.5:9b Q4_K_M; nonthinking; 16,384 context; 4,096 output tokens; T=0.2, top-p=0.9, top-k=40, min-p=0, repeat penalty=1/window=64, presence/frequency=0; seed 2108; endpoint 127.0.0.1:11435. A/A2 have the same 120-second outer cap, 10 actions, 3 repair groups and five-second finalization reserve. B is the unchanged original one-shot protocol with one call and no feedback. Both agent conditions are shortened-budget variants, not the 600-second baseline. Model/image/source/package pins and protocol hashes are retained.

Four fresh tasks were deterministically selected before inference: one easy and three medium, excluding all 71 prior IDs. Rank by prior-contest avoidance, within-pilot contest reuse, platform balance, then salted SHA256 (`CSC2108-delivery-pilot-v1:`+ID). Only metadata/public-interface eligibility was examined. All four IDs are fresh, but their contests were previously represented; the deterministic rule found no eligible unevaluated-contest alternative in these strata. This further limits generalization. [Manifest](manifest.json); [future exclusion union](future_exclusions.json).

| Task | Difficulty | A original agent | A2 shorter prompt | B original one-shot |
| --- | --- | --- | --- | --- |
| atcoder-abc392_b | easy | pass | pass | pass |
| atcoder-arc191_a | medium | missing_submission | missing_submission | missing_submission |
| leetcode-3720 | medium | candidate_failure | candidate_failure (unchanged starter) | missing_submission |
| atcoder-abc400_d | medium | missing_submission | missing_submission | missing_submission |

| Condition | Correct/completed (4 planned) | Captured output tokens | Uncaptured upper bound | Calls | Inference wall s | Judge wall s | Format errors | Length replies | Missing | Public recoveries visible/recognized |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 1/4 | 26,336 | ≤12,288 | 15 | 366.6 | 13.5 | 6 | 6 | 2 | 0/0 |
| A2 | 1/4 | 27,173 | ≤8,192 | 11 | 365.8 | 11.0 | 6 | 6 | 2 | 0/0 |
| B | 1/4 | 12,555 | ≤0 | 4 | 161.9 | 9.5 | 3 | 3 | 3 | 0/0 |

Captured token totals include every returned reply; interrupted replies have explicitly unknown counts bounded by 4,096 each. No missing telemetry is treated as zero actual work. Inference wall includes cold loading, startup, tools and finalization; grading is separately timed. Formatting counts mean rejected agent replies or one-shot extraction failures. Both genuine visible and original recognized recovery counts are reported; runtime repair accounting was not altered.

## Time and tokens to first executable action

| Task | A seconds / cumulative tokens | A2 seconds / cumulative tokens |
| --- | ---: | ---: |
| atcoder-abc392_b | 12.1 / 155 | 12.3 / 177 |
| atcoder-arc191_a | not delivered | not delivered |
| leetcode-3720 | 98.9 / 8,750 | not delivered |
| atcoder-abc400_d | not delivered | not delivered |

Missing-file counts alone hide unchanged starters: A/A2/B unchanged-starter attempts = 0/1/0; no authored submission = 2/3/3. Existing judging policy grades a saved file even after deadline termination. Explicit agent submission signals: A 1/4, A2 1/4.

Times are approximate supervisor-start-to-tool-observation timestamps; cumulative tokens include previously rejected replies. Individual successful-action times, first-response comment counts, response indices and trajectory message indices are in results.json. B has no actions by design.

## Outcome and mechanism inspection

- **atcoder-abc392_b** (same official outcome): A/A2 first-reply comment lines 0/0; formatting rejections 0/0; visible recoveries False/False. A: pass (Submitted); A2: pass (Submitted). See [A replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-abc392_b-A/ollama-responses.json), [A2 replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-abc392_b-A2/ollama-responses.json) and their adjacent trajectory.json files; exact action/response mapping is in results.json.
- **atcoder-arc191_a** (same official outcome): A/A2 first-reply comment lines 179/188; formatting rejections 2/2; visible recoveries False/False. A: missing_submission (ModelTimeout); A2: missing_submission (ModelTimeout). See [A replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-arc191_a-A/ollama-responses.json), [A2 replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-arc191_a-A2/ollama-responses.json) and their adjacent trajectory.json files; exact action/response mapping is in results.json.
- **leetcode-3720** (same official outcome): A/A2 first-reply comment lines 205/274; formatting rejections 2/2; visible recoveries False/False. A: candidate_failure (ModelTimeout); A2: candidate_failure (Deadline). See [A replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-leetcode-3720-A/ollama-responses.json), [A2 replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-leetcode-3720-A2/ollama-responses.json) and their adjacent trajectory.json files; exact action/response mapping is in results.json.
- **atcoder-abc400_d** (same official outcome): A/A2 first-reply comment lines 124/230; formatting rejections 2/2; visible recoveries False/False. A: missing_submission (ModelTimeout); A2: missing_submission (ModelTimeout). See [A replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-abc400_d-A/ollama-responses.json), [A2 replies](E:/CSC2108Local/agent-delivery-pilot/runs/osa-atcoder-abc400_d-A2/ollama-responses.json) and their adjacent trajectory.json files; exact action/response mapping is in results.json.

### Compound actions and the sanity gate

Both actual A2 synthetic fixtures passed public and independent tests, but grouped write/test commands (one also printed a submit marker). The initial sanity gate incorrectly demanded recognition by the narrow original repair matcher. Two bookkeeping checks were corrected, with original statuses/controller sources retained; both completed fixtures were skipped and the original 35-minute clock continued without reset, including the pauses. The frozen A2 prompt/worker, parser, sampler and budgets never changed. CPU controls separately verified a recognized failed test, changed repair and successful retest.
Posthoc genuine visible-check events outside budget recognition: A 0, A2 1. Visible/recognized recovery counts are shown separately. Compound checker calls expose an existing accounting limitation; it was not fixed alongside the prompt. Reconstructed changed repair groups per attempt and ambiguity flags are in metrics.csv; any intended-cap violation must qualify the comparison rather than be hidden.


A2 minus A: **+0 correct**. This is a diagnostic observation on four tasks, not a statistically definitive result. Delivery improvements are not automatically implementation or algorithm improvements; official correctness, public feedback/recovery, and the saved trajectories must support those stronger claims separately. The original one-shot condition remains a comparator, not a source of agent solutions. This four-task set must not be pooled with the previous six-task pilot to manufacture an improvement claim.

### Mechanism assessment and limits

There were **no changed official outcomes**: all three conditions solved only the easy task. No validation run recovered from a visible failure to a later public pass. Thus this comparison supplies no evidence of better implementation correctness, test-driven repair or algorithmic reasoning under A2.

The delivery change is negative on `leetcode-3720`: original A replies[0,1] truncate, but reply[2] is complete (558 tokens) and executes at 98.9 s after 8,750 captured tokens (trajectory messages[4,5]). A2 replies[0,1] also truncate; reply[2] is complete but much larger (2,401 tokens/109 comment lines), arrives at the active-budget boundary and never executes. Its candidate file is byte-identical to the initial starter, not a Qwen-authored implementation. A's actual authored candidate is independently recorded as Wrong Answer. These are different failure mechanisms despite the same coarse candidate_failure label.

On `arc191_a` and `abc400_d`, both agents' replies[0,1] hit 4,096 tokens with an unclosed command fence; no action executes. A2's first-reply comment counts are higher on all three medium tasks: 188 vs 179, 274 vs 205, 230 vs 124. The instruction to omit planning comments did not reliably control those outputs. On the easy task, A2 groups writing and testing into reply[0], reducing one call without improving first-action latency (12.3 vs 12.1 seconds) or correctness.

The apparent lower A2 median first-action time in machine-readable totals is **not a gain**: it conditions on delivery on only the easy task, while A also delivers a late action on one medium. The paired per-task table is the relevant comparison. Runtime is effectively unchanged; token ranges overlap because of missing timeout replies, so no total-token saving is established. All reconstructed visible changed-repair counts are zero in validation, so no observed three-repair cap violation occurred. The compound-check recognition gap remains an engineering limitation and was not silently fixed as a second intervention.

## Recommendation

**Do not promote this prompt version.** In this pilot it did not demonstrate better correctness, formatting reliability or useful delivery. Keep mini-SWE-agent and the original control; do not replace the agent with one-shot on the basis of this diagnostic. Verdict: **no demonstrated benefit; harmful to delivery on one observed task, with the general effect uncertain**. The command-delivery regression is evidence against adopting A2 v1. No further tuning or inference is performed.

No private cases or official solutions were used to construct the prompt. No one-shot-generated program was placed in an agent prompt or workspace. No weights, quantization, thinking, sampler, context/output caps or security settings changed. The source was never auto-repaired and malformed commands were never executed. Tests use only existing synthetic fixtures before the frozen validation.

Final checks: all 12 benchmark attempts and both A2 synthetic fixtures are complete, with no retries; shared task text, model, sampler, seed, private rows, candidate bytes and image/source pins verify. All 172 protected repository files, 30 cited prior raw artifacts and 240 audited baseline evidence files are unchanged. [Verification](verification.json). All original source/results and directories are preserved. Raw artifacts: `E:\CSC2108Local\agent-delivery-pilot`. Future experiments must exclude the recorded 75-ID union; these four tasks will not be used for another tuning iteration. No push or merge.
