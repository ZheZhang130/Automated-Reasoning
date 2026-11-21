# Single-round behavioral contract frontier

This provider generates a semi-formal specification before local coding starts.
The input is the public task statement. The contract is injected once into the
initial coding context; tool output remains within the local coding conversation.

## Paper adaptation

The attached paper is Tufano et al., Grounding AI Agents in Contracts:
An Empirical Evaluation of Spec-Driven Test Generation, SpecOps 2026.
Section 2 and Listing 1 (PDF pages 2–3) define a .spec.md artifact with
description, preconditions, postconditions, and condition-linked test suggestions.
Conditions are assigned tested/untested states. The abstract and phase-I
description also discuss documenting undefined behavior.

The original method extracts contracts from existing source code, optionally
inspects existing tests, then generates a test suite. This reduced project
implementation instead derives the intended behavior from a public programming
task and uses the contract to guide code generation. All conditions are marked
Unverified, since the contract author receives no source or test outcomes.
Unspecified behavior is explicitly recorded without inventing validation rules.
Test suggestions are prose tied to condition IDs, not executed tests.
The generator checks required sections but does not formally verify contracts,
their completeness, condition IDs, or semantic accuracy.

## Components

- contracts.py contains the contract prompt, Ollama/API providers, saved artifact
  replay and section validation.
- run_contract.py selects a provider and calls the shared planning_frontier runner
  with guidance_kind=contract and generate_contract.
- test_contracts.py checks replay isolation, statement binding, format failures
  and one-time delivery through the shared runner.
- smoke-inputs/ contains reusable Codex-authored contracts and their provenance.

The shared runner retains Sam's original mini-SWE-agent model/environment/action
interfaces. Contract runs are labeled D-single-contract and emit contract.json
and contract.spec.md. Legacy planner_model/planner_provider/planning_timeout
and saved_plan_provenance fields describe the active guidance provider for
backward compatibility; guidance_kind identifies it as a contract.

## Commands

Use an environment with the pinned mini-swe-agent/LiteLLM requirements from
planning_frontier/requirements.txt. Docker and a local Ollama endpoint must run.

From the repository root, choose exactly one contract source:

```sh
python -m contract_frontier.run_contract --task /absolute/public-bundle --output /absolute/new-output --contract-file contract_frontier/smoke-inputs/simple.json
python -m contract_frontier.run_contract --task /absolute/public-bundle --output /absolute/new-output --frontier-model openai/YOUR_MODEL
python -m contract_frontier.run_contract --task /absolute/public-bundle --output /absolute/new-output --local-contract-smoke
```

Provider credentials are read by LiteLLM from the environment, never from
committed configuration. SavedContract compares the exact UTF-8 statement hash
before replay. An input for another statement is rejected.

Defaults for this new command: local Qwen3.5 9B, 16384 coding context, 4000 coding
output tokens, 600 task seconds, 20 actions and 3 permitted repair groups.
The live local contract generator defaults to 8192 context, 3000 output tokens,
and 180-second request timeout. These are development choices, not paper settings.
Saved Codex artifacts require no provider API call in the runner. Their authoring
time and cost are unknown and excluded from measured local run time.

The public task interface is Sam's trusted bundle:
task.json with task_id/version/statement/submission_path, check.py,
public_tests.json when required, optional solution.py. This is distinct from
Peter's judgekit task-directory interface. Public feedback comes from the
prepared checker. Independent synthetic validation runs after local execution;
no private correctness result is fed to any model.

Run tests with:

```sh
python -m unittest contract_frontier.test_contracts -v
(cd planning_frontier && python -m unittest -v)
```

The signed-sum fixture is planning_frontier/fixtures/signed_sum.
The difficult fixture is recreated by planning_frontier/complex-smoke/make_task.py.
These inputs are synthetic smoke tests, not a benchmark accuracy comparison.
Generated run artifacts are retained locally in smoke-evidence/ and ignored by Git.

## Output budget rationale

The current contract-output default is 3000 tokens for both API and Ollama
providers, configurable with --contract-tokens. Local contract context remains
8192 tokens, and local coding uses 4000 output tokens within 16384 context tokens.
This is a provisional headroom allowance for the five specification sections.
The contract smoke tests used saved Codex artifacts, so live-provider contract
truncation was not measured and this value is not an experimentally established
minimum. The 180-second contract request timeout still applies within the total
600-second deadline. Saved contracts are replayed in full without a model call.
Historical reports preserve their original settings. No additional inference was
performed for this default change.
