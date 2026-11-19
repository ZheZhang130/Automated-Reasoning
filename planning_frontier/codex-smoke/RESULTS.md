# Codex-authored plan to local Qwen smoke test

## Method

On 2026-11-19, one isolated Codex planning agent was created with no inherited
chat history. It received the public dynamic-connectivity statement and a
PlanSearch-inspired prompt requesting observations and a solution sketch,
with a 450–650 word target. It was instructed to use no tools and returned
one natural-language plan. It saw no previous candidates, public checker
outputs or independent evaluation results. No further planning turn occurred.
Blank lines between observation items were normalized when saving; the prose
was not manually repaired.

codex-plan.json stores the statement, its SHA256, the planning prompt, the guide
and authoring provenance. It does not claim a provider API model identifier.
Codex harness cost and generation latency are unknown.

SavedPlan validates the task-statement hash and replays the saved plan.
The local runner sends it once in the initial mini-SWE-agent user context,
preserving the original coding system prompt. There are zero planner provider
calls inside this process and zero local-to-planner feedback calls.
guidance_calls=1 in result.json counts the handoff, not a billed generation.

## Execution and outcome

- Local model: Qwen3.5 9B MLX on the Mac, Ollama 0.40.16.
- Local context: 16384 tokens; output cap: 2000 tokens per coding response.
- Limits: 20 actions, 3 repair groups, 600 task seconds.
- Result: RepeatedFormatError after 291.48 seconds.
- Model calls: 3. Each generated exactly 2000 tokens and ended with length.
- Executed tool actions: 0. Repairs: 0.
- Public test invocations: 0. Independent checks: not run, no candidate.
- No final submission was produced.

The coder attempted complete source-writing commands, but each response
exhausted its output allowance before a complete command fence was available.
The existing parser rejected those responses and the agent stopped after
three consecutive format errors. The guide itself was complete and delivered.
This validates the saved-plan handoff and failure handling, but does not
establish solution correctness or a benefit from stronger planning.

The run duration excludes the separately authored Codex plan. It therefore
cannot be used as total frontier-plus-local latency or pooled with earlier
runs that included local planner generation inside the task deadline.

## Reproduction

Use the environment with mini-swe-agent==2.4.6 and litellm==1.81.16.
Run from repository root, with Docker and Ollama available:

```sh
python planning_frontier/plan_once.py --task /absolute/dynamic-connectivity-public-bundle --output /absolute/new-output --plan-file planning_frontier/codex-smoke/codex-plan.json --context 16384 --seconds 600
```

The matching public bundle can be recreated by complex-smoke/make_task.py.
Saved plans are task-bound. Wrong-statement plans fail before coding.
The two new SavedPlan unit tests check that no network request is needed and
that a mismatched task is rejected. All seven planner tests passed.

Results and the trajectory are retained under evidence/. The existing
2000-token coding output ceiling was kept for this test. A future attempt
with a larger coding response budget or shorter source-writing actions
must be labeled as a different configuration.
