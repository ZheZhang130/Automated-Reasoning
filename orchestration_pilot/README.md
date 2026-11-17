# CSC2108 orchestration pilot

This implementation uses a shared Python coding loop with three actions: write a complete candidate, run public tests, and submit. The pilot uses a narrow JSON interface to validate the experiment protocol independently of mini-SWE-agent. Wiring in mini-SWE-agent is a separate integration step. The shared loop supports all five core conditions. Condition F remains optional.

## Run the deterministic pilot

From this directory:

```sh
python3 orchestrate.py --scripted --condition all
python3 -m unittest -v
```

The built-in task computes the signed sum of two integers. The scripted agent writes an incorrect solution, tests it, repairs it, tests again, and submits. A and B have no guidance, C and D receive fixed upfront guidance, and E receives a fixed diagnosis after the first candidate failure. Scripted mode runs only the built-in candidate sources using the local Python interpreter.

## Run real models

Use Python 3.12, a running Docker daemon, a local model endpoint, and provider credentials for any frontier calls. Model-generated candidates run in a restricted container with networking disabled. Prepare the image and install the model client:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install litellm
docker pull python:3.12-slim
```

Set `LOCAL_MODEL` and `FRONTIER_MODEL` to LiteLLM model identifiers and configure the corresponding endpoints and credentials. Then run:

```sh
python orchestrate.py --condition A --local-model "$LOCAL_MODEL"
python orchestrate.py --condition E --local-model "$LOCAL_MODEL" --fixed-guidance
python orchestrate.py --condition all --local-model "$LOCAL_MODEL" --frontier-model "$FRONTIER_MODEL" --task public-task.json
```

Repeat `--task` to run a pilot batch. Pilot defaults are 20 actions (including invalid responses), up to three repairs, and 600 seconds. Adjust with `--actions`, `--repairs`, and `--timeout`. The pilot tests stdin/stdout tasks using trimmed output comparison. A custom adapter will be needed for function-call tasks and judge-specific comparison rules.

## Integration handoffs

**Peter.** Supply a JSON object matching this example. The runner rejects extra fields to keep the public task interface narrow. Private evaluation runs separately and joins on the unique `run_id`. Each run writes `result.json` plus a candidate when available. The record includes the submission path relative to the result directory, stop reason, model identifiers, limits, public test outcomes, guidance events, runtime, and usage.

```json
{
  "task_id": "signed-sum",
  "version": "1",
  "statement": "Read two signed integers and print their sum.",
  "submission_type": "stdin_stdout",
  "submission_path": "solution.py",
  "public_tests": [{"stdin": "-4 1\n", "expected": "-3\n"}]
}
```

**Sam.** Pass a callable as `guide` to `run_task`. It accepts the guidance kind, public task payload, and remaining seconds. It returns guidance text plus usage metadata (or `None` when unavailable). In E, the payload includes `candidate_code` and `public_failure`. The runner calls the adapter at most once, logs adapter errors, and resumes the same local coding conversation. Prompt text in the default adapter is provisional.

The live path has not been tested against a real local endpoint, frontier provider, or running Docker daemon. The deterministic suite checks the orchestration protocol independently of those services.

## Configurable guidance rounds

```sh
python3 orchestrate.py --scripted --condition guided
python3 orchestrate.py --scripted --condition guided --guidance contract diagnosis plan
python orchestrate.py --condition guided --local-model "$LOCAL_MODEL" --frontier-model "$FRONTIER_MODEL" --task public-task.json
```

The guide list sets the maximum number of frontier calls. The default is two
(`plan diagnosis`). An initial plan or contract arrives before the first coding
action. An initial diagnosis waits for public failure evidence. Later rounds
consume the next guide after a qualifying public test failure on a changed
candidate. Each round uses the same conversation, workspace and task-wide action,
repair and time limits. Repeating a test on the same candidate does not trigger
another call. A provider error consumes its scheduled call. After the guide list
is exhausted the coder can finish within its remaining budget.

Guided mode ends on a public pass. A submit action also checks the candidate
against the public suite. Private correctness stays with the independent judge.
A–E retain their single-intervention baseline schedules. Multi-round guided mode
is a separate condition.

The round policy and evidence packet live in `guidance_rounds.py`.
`run_task` owns the execution loop, workspace and budgets. The injected
`guide(kind, payload, timeout)` owns the frontier request. For follow-up rounds
the payload includes the current candidate, recognized public failure, the
last 12 events, and remaining action and repair budgets. Per-round requests,
feedback, guide text, usage and failures appear in `result.json`.

## Paper notes and integration with the measured runner

[CUDAnalyst, sections 3.1–3.2 and appendices D.4 and E](https://arxiv.org/html/2605.26720v1)
normalizes debugger, analyzer and profiler evidence, optionally summarizes it,
and supplies it to a dedicated planner with fixed prompts. Its controlled
experiments freeze program states while varying the planner inputs. Our reduced
version uses one structured public feedback packet and short natural-language
guides. There are no CUDA profiles, summarization calls or attribution studies.
For a later diagnosis ablation, replay a saved candidate and its public
observation with the same remaining budget in each branch.

[SWE-agent, sections 2–3 and appendix C](https://arxiv.org/html/2405.15793)
defines the coding agent interface through task prompts, tool actions and
execution observations. Appendix C includes formatting instructions, example
trajectories and recovery messages for malformed actions. Treat the frontier
guide as an additional message after the normal public observation. Keep the
coding action syntax consistent across guidance schedules.

The measured mini-SWE-agent runner in `local_eval_v2` is a separate backend.
A future adapter should use its recognized public test events, snapshot the
candidate that caused the observation, and deliver guide text before the next
model query. The pilot uses its own JSON coding interface and stdin/stdout task
schema. The measured runner's LeetCode function submissions require its own
public evaluator. Run a fresh guided batch when integrating the adapter.
