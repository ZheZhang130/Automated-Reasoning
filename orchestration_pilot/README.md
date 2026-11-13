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
