# Original prompt retry with a 3600-token output allowance

The user's requested larger-token retry was interpreted as increasing generated
planning output from 1200 to 3600 tokens. A total context of 3600 would instead
reduce the original 4096 context. The actual settings were therefore:
planning output 3600, planning context 8192, local coding context 4096,
original non-compact prompt, one planning call, no return feedback,
planning timeout 240 seconds, total task budget 300 seconds.

Task: the same synthetic dynamic-connectivity problem and six public cases.
Provider: local Ollama Qwen3.5 9B MLX acting as a planner substitute, not a paid
frontier provider.

Result: Ollama returned done_reason=length, eval_count=3600 and
prompt_eval_count=325. Wall time was 153.48 seconds. The raw response contains
observations and a long solution discussion, but repeatedly reconsiders the
algorithm and ends mid-discussion. It was rejected as incomplete, so local
coding did not start, no candidate was generated, and no tests were executed.

The truncated response is now preserved in plan3600-evidence/planner-response.json.
The prior 1200-token failure and compact 238-token run are separate artifacts.
This was one retry, without prompt tuning or manual algorithm assistance.

The CLI exposes the limits separately:
```sh
python planning_frontier/plan_once.py --task /tmp/csc2108-dynamic-connectivity --output /absolute/new-output --local-planner-smoke --plan-tokens 3600 --plan-context 8192 --planning-timeout 240 --seconds 300
```

Default limits remain unchanged for existing callers. Five provider tests pass,
including exact wire settings for the larger allowance and raw-response retention.
