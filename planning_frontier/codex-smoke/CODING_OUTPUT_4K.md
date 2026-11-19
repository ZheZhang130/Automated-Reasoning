# Codex plan with 4000-token local responses

The runner now accepts --coding-tokens independently of --plan-tokens.
The value is validated and recorded as coding_output_limit in result.json,
then forwarded to Ollama as num_predict. Existing callers default to 2000;
this explicitly configured experiment uses 4000.

## Configuration

Same synthetic dynamic-connectivity task and saved Codex plan as the prior
codex-smoke run. The plan's source SHA256 remains
abc28dac976f8b894cd53207ac92e940c4749f87934f3494c5361c3c023df7b5.
Local model Qwen3.5 9B MLX; context 16384; total task limit 600 seconds;
20 tool actions and 3 accepted repair groups. No additional plan generation,
local-to-Codex feedback, manual code repair or task-specific code was provided.

Only the coding output allowance was changed from 2000 to 4000 for this retry.
The model is sampled, so this one attempt is not a deterministic causal ablation.

## Results

- Wall time 262.14 seconds.
- Nine model responses, all ending with stop; none hit the output cap.
- Generated-token counts: 2521, 17, 1028, 17, 1048, 17, 1072, 17, 1100.
- Nine executed tool actions.
- Four public checker invocations. The first timed out; subsequent versions
  failed on the first public case with segment-tree traversal IndexErrors.
- Termination: RepairLimit. The raw Budget counter is 4 because the attempted
  fourth repair triggers the limit; three repair groups are permitted.
  The environment preserves the pre-limit candidate as its submission.
- Final saved candidate failed all 30 randomized checks and one large stress case.

The increased response budget removes the previously observed truncated-command
failure and allows actual writing, public testing and attempted repair. It does
not produce a correct solution on this run. Independent verification was performed
only after the local run finished and was never returned to the model.

## Reproduce

From the repository root, using a fresh output directory:

```sh
python planning_frontier/plan_once.py --task /absolute/dynamic-connectivity-public-bundle --output /absolute/new-output --plan-file planning_frontier/codex-smoke/codex-plan.json --context 16384 --coding-tokens 4000 --seconds 600
```

Artifacts are in coding-4k/. Planner tests, saved-plan tests and coding-budget
forwarding/validation tests pass (nine tests total).
