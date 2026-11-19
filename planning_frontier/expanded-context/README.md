# Original prompt with expanded context and output allowance

These are new development attempts on synthetic-dynamic-connectivity using the
original noncompact planning prompt. Qwen3.5 9B MLX is used as both planner
substitute and coding model. One guide is requested; no local execution feedback
is returned to the planner.

| Attempt | Planning context | Planning output cap | Actual planning output | Outcome |
| --- | ---: | ---: | ---: | --- |
| 8k | 8192 | 3000 | 3000 | Truncated, rejected before coding; 126.18 s |
| 16k | 16384 | 6000 | 5390 | Complete guide delivered; coding failed and reached 600 s |

The 16k attempt also sets local coding context to 16384, total time to 600 s,
and planner request timeout to 360 s. Coding output ceiling remains 2000 tokens,
action cap 20, repair cap 3. Consequently this is not a resource-matched comparison
against the earlier 300-second runs. There was no second guidance round.

The completed guide describes offline edge lifetimes, a segment tree over time
and rollback DSU. Local coding had two output-truncated responses before producing
valid commands. It ran six actions with two repair groups. Three public checker
invocations each failed the first case with TypeError when joining a list
containing None. The final request expired at the remaining task deadline
(recorded as APIConnectionError by the existing adapter). Total wall time 600.41 s.
No public case passed in this run. Independent checking of the final candidate
failed all 30 random cases and one large case, including endpoint-normalization
KeyErrors and the None answer failure. There was no reported memory-allocation
error.

The larger context/output allowance successfully removes planner truncation
on this attempt. It does not establish correct local implementation or an
improvement from planning. No manual edits or reference code were supplied to
the models.

Run from the repository root with a prepared public task bundle and fresh output:

```sh
python planning_frontier/plan_once.py --task /absolute/public-bundle --output /absolute/new-output --local-planner-smoke --plan-context 16384 --plan-tokens 6000 --planning-timeout 360 --context 16384 --seconds 600
```

Artifacts in 8k/ and 16k/ retain raw planner failure, the complete guide, local
trajectory, result and independently checked final candidate as applicable.
