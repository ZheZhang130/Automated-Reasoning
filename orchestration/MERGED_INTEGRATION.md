# Merged interface review and handoff

## Changes reviewed

Peter's judge branch introduces a public Python API and evaluation export schema,
specified in ../timeline/judge_1114.md. Task directories now contain problem.md,
task.json, and tests/public/*.in/*.out. Public feedback must use Judge.public().
Its result contains status, report, first_failure, hashes and verdict details.
The old pilot's inline test comparator differs from this judge's decimal-aware
comparison.

Sam's local_eval_v2 and local_optimization directories contain measured local
mini-SWE-agent baselines. agent_delivery_pilot reports a negative prompt-only
trial and retains the original agent prompt. Preserve those frozen sources,
profiles and results for comparisons.

## Implemented adaptation

integration.py loads Peter's generated public task directories and supplies a
lazy Judge.public() adapter. Live orchestration runs require that adapter.
Scripted fixtures keep their original local checker for offline testing.
Every judge call appears in attempts.jsonl with the original result and delivery
flag. result.json includes Peter's required fields, usage with unknown values
as null, host, repeat, exit status, counts and submission hash. submission.py
is exported even at a budget stop if a candidate exists.

The existing default two-round schedule remains plan then diagnosis. Feedback
includes the judge's report and first_failure plus code, recent events and
remaining limits. Passing public tests stops guided execution. Hidden evaluation
remains Peter's separate process.

## Teammate execution

Run from orchestration after Peter's judge/setup.sh prepares data and starts
the public judge. Supply provider configuration via environment variables.
LOCAL_MODEL and FRONTIER_MODEL below are LiteLLM identifiers.

```sh
python3 -m unittest discover -v
python3 orchestrate.py --condition guided --local-model "$LOCAL_MODEL" --frontier-model "$FRONTIER_MODEL" --task ../judge/tasks/lcb-atcoder-abc393_a --output ../runs --repeat 1
```

--repeat labels the attempt. Invoke again with a different repeat value for
additional repetitions. Every invocation creates a new batch ID.

## Remaining backend integration

The current live CLI still uses the pilot JSON write/test/submit coding interface.
It does not execute Sam's mini-SWE-agent backend. Consequently these runs must
have a new experimental label and cannot be pooled with Sam's measured A runs.

The next mini-SWE integration should use a new backend, importing the original
control rather than altering frozen files. It must retain the shell parser,
model profile, action limits and persistent workspace. Route recognized public
checks through Peter's adapter. Feed its result back into the same agent history,
then request and insert the next guide before the next model query. Capture
the source snapshot associated with that judge call. Judge task IDs and bundles
differ from Sam's earlier evaluator bundles, so the backend must load Peter's
stdin/stdout public bundles explicitly.

A live teammate validation must cover failed public tests -> diagnosis -> changed
candidate -> public pass, no diagnosis after a public pass, provider failure,
judge infrastructure failure, and candidate extraction at budget exhaustion.
The judge client has its own Docker call timeouts, which may exceed the remaining
task deadline. This pilot checks the deadline on return; a hard outer supervisor
is needed for strict wall-clock experiments.
