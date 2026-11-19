# Dynamic-connectivity smoke test

Date: 2026-11-19. This is a synthetic development task, not a selected benchmark.
No frontier provider was called. Qwen3.5 9B MLX was used locally, with a 4096-token
context and thinking disabled. Both conditions used the same public task and
300-second total budget, 20 actions, 3 repair groups, 2000 generated tokens per
coding response. The planner substitute retained the existing 1200-token ceiling.

The task maintains connectivity under undirected multigraph edge insertions,
deletions and queries, with parallel edges and self-loops. N and Q can reach
200000. Six public cases exercise these semantics.

## Results

| Condition | Outcome | Wall seconds | Additional checks |
| --- | --- | ---: | --- |
| Local-only | Repeatedly failed public case 2, then model request timed out at the task deadline | 300.41 | Final saved candidate failed all 30 randomized oracle cases and the one large stress case |
| One upfront plan | The planner response was truncated and rejected before coding started | 49.52 | No candidate, so correctness checks were not executed |

The local-only trajectory records four public checker invocations, each stopping
at the second case. The first case passed and the second failed each time. The
failure output was YES where NO was expected after deleting the last copy of a
parallel edge. The local agent did not resolve this within its budget. Its first
generation also hit the output cap without a complete action fence.

The independent verifier ran after both attempts ended. Randomized cases use a
breadth/depth-first connectivity oracle over 150 mixed operations on 12 vertices,
with fixed seeds 0 through 29. The large case has 25000 vertices and 104999
operations, repeatedly removing/restoring one edge of a chain. These cases were
not supplied to either model. Candidates ran inside separate restricted Docker
containers.

The first setup attempt failed before inference because Docker was stopped.
After Docker and Ollama were restarted, the local-only attempt and the planned
attempt each ran once. The failed setup record is preserved separately.

## Interpretation

The harder task caused a genuine local implementation failure. It also exposed
an existing planner-output limit, so there is no completed guided candidate to
compare against the baseline. This result cannot demonstrate a benefit from
planning. No plan was manually supplied, patched or retried with a larger budget.

The local-only status is currently serialized as generic error/APIConnectionError
at the deadline. Its last candidate and full trajectory are retained; analysis
must inspect wall time and the timeout message rather than assume an arbitrary
provider outage. Error-path records omit action counters, so derive them from the
trajectory when needed. This is an instrumentation limitation discovered by the
smoke test, not evidence of a memory allocation failure.

## Reproduction

Use a new output directory and the same prepared public bundle. The runner now
supports --no-plan to perform a local-only comparison. The original sum fixture
and its evidence remain separate. make_task.py recreates the public bundle under
/tmp/csc2108-dynamic-connectivity. verify_candidates.py runs the independent cases
on the saved submission.py files. Outputs under local/, planned/ and setup-error/
retain the evidence from this test. All missing-candidate planned checks are
explicitly marked missing, not counted as executed tests.
