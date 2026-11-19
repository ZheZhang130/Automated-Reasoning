# Compact planning smoke test

Use --compact-plan with --local-planner-smoke or --frontier-model.
The prompt retains Observations and Solution sketch headings and requests at most
three observations, four steps and 250 words. Ollama's hard 1200-token ceiling,
single planning request, and absence of local-to-planner feedback remain in place.
The word target is a prompt instruction, not a guaranteed token bound. Truncated
outputs are still rejected. The saved plan.json records the actual prompt.

The dynamic-connectivity task was retried once with this explicit prompt change.
Qwen3.5 9B MLX produced a complete 238-token guide, and the mini-SWE-agent coding
loop started successfully. The guide contained a deficient algorithm sketch:
it proposed rollback DSU without supplying an offline interval-processing
strategy or another valid mechanism for arbitrary edge deletion. The local
candidate repeatedly failed public case 2 and reached the 300-second task
deadline. No claim of improved correctness is supported.

This is a separately labeled development retry, not a replacement for the
original truncated-plan result. There were no additional planner calls during
execution. The final candidate and trajectory are preserved in compact-evidence/.
The two original planner tests and two added compact-provider checks pass.
