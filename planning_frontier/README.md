# Single-call planning frontier

This module implements one planning request before the local coding agent starts.
The planner receives only the public problem statement. The guide is inserted
once into the initial user message. Public test observations remain inside the
coding conversation. There is no path that calls the planner again.

## Paper reading and adaptation

The attached planning paper is Wang et al., *Planning in Natural Language Improves
LLM Search for Code Generation*, ICLR 2025. Section 4 and appendix M.4
(PDF pages 40–41) describe observations followed by a natural-language solution
sketch. Appendix M.4.3 asks for exact quotations of relevant observations before
solution steps. Section 4 also describes later pseudocode and code translation.

planner.py uses an original prompt requesting numbered observations and one
solution sketch whose steps quote those observations. The two artifacts are
produced together in one request. This reduces the paper's multi-call observation
search and combinations to a single plan. There is no diversity search, candidate
selection, pseudocode stage or paper-performance reproduction.

The attached SWE-agent paper, section 3 and appendix C (PDF pages 39–43),
describes the system/task/action/observation interface. The local execution here
imports Sam's TextModel, Agent, Environment, Budget, original PROMPT and
FORMAT_ERROR from local_eval_v2/runtime.py. Thus actual shell actions and tool
observations are handled by mini-SWE-agent, with candidate execution inside
Docker. The plan is added to the task message, while the original shell action
prompt is reused. No frozen source is edited.

## Modules

- planner.py owns the planner prompt, one-call providers and format checks.
- plan_once.py owns the one-way handoff and invokes the existing local backend.
- test_planner.py checks statement-only input and single-call failure handling.

Both providers return prose and usage. FrontierPlanner uses LiteLLM and reads
provider credentials from the usual environment configuration. OllamaPlanner is
an explicitly labeled local substitute for development without frontier access.

## Installation and execution

From the repository root, use a Python environment with
mini-swe-agent==2.4.6 and litellm==1.81.16. Docker must be running and have
python:3.11-slim-bookworm available. The current adapter accepts Sam's trusted
public task bundles (task.json, check.py, public_tests.json, optional solution.py),
as documented in local_agent/README.md. Private rows must remain outside this
directory.

Use a new output directory for every run.

```sh
python planning_frontier/plan_once.py --task /absolute/public-bundle --output /absolute/new-output --local-model qwen3.5:9b --local-planner-smoke
python planning_frontier/plan_once.py --task /absolute/public-bundle --output /absolute/new-output --local-model qwen3.5:9b --frontier-model openai/YOUR_MODEL --context 16384 --seconds 600
```

The first command uses Qwen as both planner and coder. It validates connectivity
and the one-way handoff, not frontier-model effectiveness. For the second command,
set the frontier provider's credentials outside the repository. The local Ollama
endpoint defaults to http://127.0.0.1:11435 and can be changed with --endpoint.
The Mac development default is 4096 context tokens and 300 task seconds.

Artifacts include plan.json (guide, prompt and planner usage), trajectory.json,
captured Ollama responses, result.json and submission.py when extraction succeeds.
A public pass or an agent submission is not private correctness. This standalone
runner uses Sam's public checker interface, not Peter's judgekit task-directory
format. Keep these records separate from Peter's evaluation schema until an
explicit adapter is added.

## Known boundaries

This development command deliberately permits configurable model identity and
context, including Mac MLX Qwen. It does not invoke the frozen local_agent verifier.
It therefore produces a new development configuration, not Sam's frozen baseline.
Model architecture, Docker image identity, provider selection and environment
should be captured before a benchmark batch. The 300/600 second limit is enforced
within the agent; container startup and cleanup can add outer wall time.

## Mac smoke result

On 2026-11-19, Qwen3.5 9B MLX served as both planner substitute and coding model,
with a 4096-token context. The completed run generated exactly one guide, then
executed three mini-SWE-agent actions: write source, test it, submit it.
All three signed-sum public checks passed. Wall time was 58.96 seconds with
zero repairs. There were no local-to-planner feedback calls. The first attempt
failed because Ollama was stopped; after starting it, a new output directory
was used. Pydantic emitted serialization warnings but the trajectory and final
candidate were saved successfully.

The small planner followed both requested headings but paraphrased observations
rather than quoting them verbatim. Format validation currently checks the
headings and truncation, not semantic correctness or quote fidelity. This smoke
result demonstrates the data flow, not benchmark accuracy or frontier benefit.
No paid frontier API was invoked because no provider key was configured.

The test artifacts are saved alongside the project under
planning_frontier/smoke-evidence/. They contain only synthetic tasks and output.
