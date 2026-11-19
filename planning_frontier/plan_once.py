"""One upfront plan followed by Sam's mini-SWE-agent execution loop."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from planner import FrontierPlanner, OllamaPlanner, SavedPlan, generate_plan


def run(repo, task_dir, output, planner, model, endpoint, context=4096, seconds=300, planning_timeout=120, coding_tokens=2000):
    if context < 1024 or seconds < 1:
        raise ValueError("context must be >=1024 and seconds must be positive")
    if not isinstance(coding_tokens, int) or not 0 < coding_tokens < context:
        raise ValueError("coding_tokens must be a positive integer smaller than context")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    task_dir = Path(task_dir).resolve(strict=True)
    started = time.monotonic()
    record = {"condition": "C-single-plan" if planner else "A-local-only", "guidance_calls": 0,
              "local_model": model, "endpoint": endpoint, "context": context,
              "status": "setup_error", "planner_model": planner.model if planner else None,
              "planner_provider": type(planner).__name__ if planner else None, "guidance_feedback_enabled": False}
    record["coding_output_limit"] = coding_tokens
    record["planning_context"] = getattr(planner, "context", None)
    record["planning_output_limit"] = getattr(planner, "output_tokens", None)
    record["planning_timeout"] = planning_timeout
    if isinstance(planner, SavedPlan):
        record["saved_plan_provenance"] = planner.provenance()
    env = agent = budget = None
    events = []
    try:
        task = json.loads((task_dir / "task.json").read_text())
        if set(task) != {"task_id", "version", "statement", "submission_path"}:
            raise ValueError("Use Sam's prepared public bundle schema")
        if task["submission_path"] != "solution.py":
            raise ValueError("Expected solution.py")
        if any(p.is_symlink() or not p.is_file() or p.name not in {
            "task.json", "solution.py", "public_tests.json", "check.py"
        } for p in task_dir.iterdir()):
            raise ValueError("Unexpected public task files")
        record["task_id"] = task["task_id"]
        # Only the statement crosses this boundary, before local execution exists.
        plan = None
        if planner:
            record["guidance_calls"] = 1
            plan = generate_plan(planner, task["statement"], min(planning_timeout, seconds))
            (output / "plan.json").write_text(json.dumps(plan, indent=2))
        os.environ.setdefault("MSWEA_GLOBAL_CONFIG_DIR", str(output / "config"))
        os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
        sys.path.insert(0, str(repo / "local_eval_v2"))
        import runtime as backend
        budget = backend.v3.Budget(20, 3)
        events = []
        image = "python:3.11-slim-bookworm"
        deadline = started + seconds
        if time.monotonic() >= deadline:
            raise TimeoutError("Planning exhausted the task deadline")
        env = backend.Environment(
            budget=budget, deadline=deadline, evidence=events, image=image,
            cwd="/workspace", run_args=backend.v3.container_args(task_dir),
            container_timeout=str(seconds + 60) + "s", env={"HOME": "/tmp"})
        if (task_dir / "solution.py").exists():
            backend.v3.docker("exec", env.container_id, "cp", "/public/solution.py", "/workspace/solution.py")
        coding_model = backend.TextModel(
            model_name="ollama_chat/" + model, cost_tracking="ignore_errors",
            model_kwargs={"api_base": endpoint, "num_ctx": context, "num_predict": coding_tokens,
                          "think": False, "temperature": 0.2, "timeout": 120, "num_retries": 0},
            action_regex=r'```(?:mswea_bash_command|bash)\s*\n(.*?)\n```',
            format_error_template=backend.FORMAT_ERROR,
            observation_template="<returncode>{{output.returncode}}</returncode>\n{{output.output[:6000]}}")
        import litellm
        capture = backend.RawCapture(output / "ollama-responses.json")
        litellm.callbacks = [capture]
        coding_model.capture = capture
        agent = backend.Agent(
            coding_model, env, system_template=backend.PROMPT,
            instance_template="{{task}}\n\nUpfront implementation guide:\n{{guide}}" if plan else "{{task}}",
            step_limit=28, cost_limit=0, wall_time_limit_seconds=seconds,
            output_path=output / "trajectory.json")
        result = agent.run(task["statement"], guide=plan["text"] if plan else "")
        record.update(status=result.get("exit_status"), actions=budget.actions,
                      repairs=budget.repairs, public_events=events)
    except Exception as error:
        record.update(status="error", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if env:
            candidate = env.last_candidate
            if candidate is None and env.container_id:
                candidate = env.snapshot()
            if candidate is not None:
                (output / "submission.py").write_bytes(candidate)
            env.cleanup()
        if planner and getattr(planner, "last_response", None) is not None:
            (output / "planner-response.json").write_text(json.dumps(planner.last_response, indent=2))
        if budget:
            record.update(actions=budget.actions, repairs=budget.repairs, public_events=events)
        record["wall_seconds"] = time.monotonic() - started
        (output / "result.json").write_text(json.dumps(record, indent=2))
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--compact-plan", action="store_true", help="Request a guide of at most 250 words.")
    p.add_argument("--local-model", default="qwen3.5:9b")
    p.add_argument("--endpoint", default="http://127.0.0.1:11435")
    p.add_argument("--plan-tokens", type=int, default=1200)
    p.add_argument("--plan-context", type=int, default=4096)
    p.add_argument("--planning-timeout", type=int, default=120)
    p.add_argument("--coding-tokens", type=int, default=2000, help="Maximum output tokens per local coding response; independent of --plan-tokens.")
    p.add_argument("--context", type=int, default=4096)
    p.add_argument("--seconds", type=int, default=300)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan-file", type=Path, help="Replay a task-bound externally authored plan JSON.")
    group.add_argument("--no-plan", action="store_true")
    group.add_argument("--frontier-model")
    group.add_argument("--local-planner-smoke", action="store_true")
    args = p.parse_args()
    if args.plan_file:
        planner = SavedPlan(args.plan_file)
    elif args.no_plan:
        planner = None
    elif args.frontier_model:
        planner = FrontierPlanner(args.frontier_model, compact=args.compact_plan, output_tokens=args.plan_tokens)
    else:
        planner = OllamaPlanner(args.endpoint, args.local_model, args.plan_context,
                                compact=args.compact_plan, output_tokens=args.plan_tokens)
    print(json.dumps(run(Path(__file__).resolve().parents[1], args.task, args.output,
                         planner, args.local_model, args.endpoint, args.context, args.seconds, args.planning_timeout, args.coding_tokens)))


if __name__ == "__main__":
    main()
