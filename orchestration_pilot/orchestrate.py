"""CSC2108 pilot orchestration for Python programming tasks."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

GUIDANCE = {"C": "plan", "D": "contract", "E": "diagnosis"}
FIXTURE = {
    "task_id": "fixture-sum-signed", "version": "1",
    "statement": "Read two signed integers from stdin and print their sum.",
    "submission_type": "stdin_stdout", "submission_path": "solution.py",
    "public_tests": [{"stdin": "2 3\n", "expected": "5\n"},
                     {"stdin": "-4 1\n", "expected": "-3\n"}],
}
CORRECT = "a, b = map(int, input().split())\nprint(a + b)\n"
WRONG = "a, b = map(int, input().split())\nprint(abs(a + b))\n"
FIXED = {
    "plan": "Read both integers, add them and check a negative sum.",
    "contract": "Print the exact signed sum followed by a newline.",
    "diagnosis": "The negative-sum case returned a positive number. Check whether the implementation discards the sign.",
}
SYSTEM = """Solve the Python task. Return one JSON object per turn.
Actions: {"action":"write","code":"complete Python source"}, {"action":"test"},
or {"action":"submit"}. Use the public test feedback to revise your candidate."""
GUIDANCE_SYSTEM = {
    "plan": "Provide a concise implementation plan without replacement code.",
    "contract": "Specify required behavior, preconditions, postconditions and edge cases.",
    "diagnosis": "Use the candidate and public failure to suggest repairs without replacement code.",
}


def validate_task(task):
    fields = {"task_id", "version", "statement", "submission_type",
              "submission_path", "public_tests", "starter_code"}
    if set(task) - fields:
        raise ValueError("Unexpected task fields. Supply only the public task bundle.")
    for key in ("task_id", "version", "statement", "submission_path"):
        if not isinstance(task.get(key), str) or not task[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if task.get("submission_type") != "stdin_stdout":
        raise ValueError("Pilot supports stdin_stdout tasks")
    if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*\.py", task["submission_path"]):
        raise ValueError("submission_path must be a Python filename")
    cases = task.get("public_tests")
    if not isinstance(cases, list) or not cases:
        raise ValueError("At least one public test is required")
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"stdin", "expected"} or not all(
            isinstance(value, str) for value in case.values()
        ):
            raise ValueError("Each public test needs string stdin and expected fields")
    if "starter_code" in task and not isinstance(task["starter_code"], str):
        raise ValueError("starter_code must be a string")


def complete(model, messages, timeout):
    import litellm

    reply = litellm.completion(model=model, messages=messages, timeout=timeout,
                               num_retries=0)
    usage = reply.usage.model_dump() if reply.usage else None
    try:
        cost = litellm.completion_cost(completion_response=reply)
    except Exception:
        cost = None
    return reply.choices[0].message.content or "", {"tokens": usage, "cost_usd": cost}


def model_guidance(model):
    def generate(kind, payload, timeout):
        return complete(model, [
            {"role": "system", "content": GUIDANCE_SYSTEM[kind]},
            {"role": "user", "content": json.dumps(payload)},
        ], timeout)
    return generate


def scripted_coder():
    actions = iter(
        [{"action": "write", "code": WRONG}, {"action": "test"}]
        + [{"action": "write", "code": CORRECT}, {"action": "test"}, {"action": "submit"}]
    )

    def query(messages, timeout):
        return json.dumps(next(actions)), None
    return query


def public_test(task, candidate, remaining, *, image, scripted):
    """Run each public input separately. The model receives bounded feedback."""
    for index, case in enumerate(task["public_tests"], 1):
        name = "csc2108-" + uuid.uuid4().hex
        command = [sys.executable, str(candidate)] if scripted else [
            "docker", "run", "--rm", "--name", name, "--pull", "never", "-i",
            "--network", "none", "--read-only", "--memory", "256m",
            "--cpus", "1", "--pids-limit", "32", "--user", "65534:65534",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--mount", f"type=bind,src={candidate},dst=/solution.py,readonly",
            image, "python", "-I", "/solution.py",
        ]
        try:
            timeout = remaining()
            result = subprocess.run(command, input=case["stdin"], text=True,
                                    errors="replace", capture_output=True,
                                    timeout=min(10, timeout), cwd=candidate.parent)
        except subprocess.TimeoutExpired:
            if not scripted:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True,
                               timeout=5)
            return {"status": "candidate_failure", "case": index, "reason": "test_timeout"}
        except OSError as error:
            return {"status": "infrastructure_error", "reason": str(error)}
        status = "pass"
        if not scripted and result.returncode in (125, 126, 127):
            status = "infrastructure_error"
        elif result.returncode or result.stdout.strip() != case["expected"].strip():
            status = "candidate_failure"
        if status != "pass":
            return {"status": status, "case": index, "stdin": case["stdin"][:2000],
                    "expected": case["expected"][:2000], "actual": result.stdout[:2000],
                    "stderr": result.stderr[:2000], "returncode": result.returncode}
    return {"status": "pass", "cases": len(task["public_tests"])}


class DeadlineReached(Exception):
    pass


def run_task(task, condition, output, coder, guide=None, *, coding_model="scripted",
             guidance_model=None, action_limit=20, repair_limit=3,
             timeout=600, image="python:3.12-slim", scripted=False):
    """Adapters take the remaining seconds and return (text, usage_or_none)."""
    validate_task(task)
    if condition not in "ABCDE" or len(condition) != 1:
        raise ValueError("Expected condition A, B, C, D or E")
    if action_limit < 1 or repair_limit < 0 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Invalid run limits")
    if condition in GUIDANCE and guide is None:
        raise ValueError("This condition requires a guidance adapter")
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    candidate = workspace / task["submission_path"]
    if task.get("starter_code"):
        candidate.write_text(task["starter_code"], encoding="utf-8")

    start = time.monotonic()
    config = {"condition": condition, "coding_model": coding_model,
              "guidance_model": guidance_model, "action_limit": action_limit,
              "repair_limit": repair_limit, "timeout_seconds": timeout,
              "image": None if scripted else image, "scripted": scripted}
    record = {
        "run_id": output.name, "task_id": task["task_id"], "task_version": task["version"],
        "config_version": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        **config, "submission_type": task["submission_type"], "submission": None,
        "actions": 0, "repairs": 0, "stop_reason": None, "trace": [],
        "guidance": {"kind": GUIDANCE.get(condition), "requested": False,
                     "diagnosis_triggered": False, "delivered": False, "error": None},
        "coding_usage": [], "guidance_usage": None,
    }
    public_context = {key: task[key] for key in (
        "task_id", "statement", "submission_path", "public_tests")}
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps({**public_context,
                    "starter_code": task.get("starter_code")})}]

    def remaining():
        seconds = timeout - (time.monotonic() - start)
        if seconds <= 0:
            raise DeadlineReached()
        return seconds

    def log(event, **data):
        record["trace"].append({"event": event, "seconds": time.monotonic() - start, **data})

    def deliver(kind, **data):
        seconds = remaining()
        record["guidance"].update(requested=True, diagnosis_triggered=kind == "diagnosis")
        log("guidance_request", kind=kind, **data)
        try:
            guidance, usage = guide(kind, {**public_context, **data}, seconds)
            record["guidance_usage"] = usage
            remaining()
            if not isinstance(guidance, str) or not guidance.strip():
                raise ValueError("Empty guidance")
        except DeadlineReached:
            raise
        except Exception as error:
            record["guidance"]["error"] = type(error).__name__
            log("guidance_error", error_type=type(error).__name__)
            return
        record["guidance"]["delivered"] = True
        messages.append({"role": "user", "content": f"Frontier {kind}: {guidance}"})
        log("guidance_delivered", kind=kind, text=guidance)

    failed_candidate = None
    repairing = False
    try:
        if condition in ("C", "D"):
            deliver(GUIDANCE[condition])
        while record["actions"] < action_limit:
            response, usage = coder(messages.copy(), remaining())
            if not isinstance(response, str):
                response = ""
            record["coding_usage"].append(usage)
            remaining()
            record["actions"] += 1
            messages.append({"role": "assistant", "content": response})
            try:
                action = json.loads(response)
                if not isinstance(action, dict) or action.get("action") not in ("write", "test", "submit"):
                    raise ValueError("Unknown action")
                if action["action"] == "write" and not isinstance(action.get("code"), str):
                    raise ValueError("Write requires code text")
            except (ValueError, TypeError):
                log("invalid_action", response=response[:2000])
                messages.append({"role": "user", "content": "Return a valid JSON action."})
                continue

            kind = action["action"]
            log("action", action=kind)
            if kind == "submit" and candidate.is_file():
                record["stop_reason"] = "submitted"
                break
            if kind == "write":
                code = action["code"]
                if failed_candidate is not None and not repairing and code != failed_candidate:
                    if record["repairs"] >= repair_limit:
                        record["stop_reason"] = "repair_limit"
                        break
                    record["repairs"] += 1
                    repairing = True
                    log("repair_start", number=record["repairs"])
                candidate.write_text(code, encoding="utf-8")
                log("candidate_written", code=code)
                feedback = "Candidate saved."
            elif kind == "test" and candidate.is_file():
                tested_code = candidate.read_text(encoding="utf-8")
                result = public_test(task, candidate, remaining, image=image, scripted=scripted)
                log("public_test", **result)
                remaining()
                if result["status"] == "infrastructure_error":
                    record["stop_reason"] = "infrastructure_error"
                    break
                if tested_code != failed_candidate:
                    repairing = False
                failed_candidate = tested_code if result["status"] == "candidate_failure" else None
                messages.append({"role": "user", "content": json.dumps(result)})
                if (condition == "E" and failed_candidate is not None
                        and not record["guidance"]["requested"] and record["actions"] < action_limit):
                    deliver("diagnosis", candidate_code=tested_code, public_failure=result)
                continue
            else:
                feedback = "Write a candidate before testing or submitting."
                log("missing_candidate", action=kind)
            messages.append({"role": "user", "content": feedback})
        if record["stop_reason"] is None:
            record["stop_reason"] = "action_limit"
    except DeadlineReached:
        record["stop_reason"] = "deadline"
    except Exception as error:
        record["stop_reason"] = "deadline" if time.monotonic() - start >= timeout else "execution_error"
        log("execution_error", error_type=type(error).__name__)
    finally:
        record["elapsed_seconds"] = time.monotonic() - start
        if candidate.is_file():
            record["submission"] = str(candidate.relative_to(output))
        (output / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=["A", "B", "C", "D", "E", "all"], default="all")
    parser.add_argument("--task", type=Path, action="append", help="Public task JSON; repeat for a pilot batch.")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument("--local-model")
    parser.add_argument("--frontier-model")
    parser.add_argument("--fixed-guidance", action="store_true")
    parser.add_argument("--scripted", action="store_true", help="Use only the built-in deterministic fixture.")
    parser.add_argument("--image", default="python:3.12-slim")
    parser.add_argument("--actions", type=int, default=20)
    parser.add_argument("--repairs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    conditions = "ABCDE" if args.condition == "all" else args.condition
    if args.scripted and args.task:
        parser.error("--scripted runs only the built-in fixture")
    if not args.scripted:
        if any(condition != "B" for condition in conditions) and not args.local_model:
            parser.error("--local-model is required for local coding conditions")
        if ("B" in conditions or (set(conditions) & set(GUIDANCE) and not args.fixed_guidance)) and not args.frontier_model:
            parser.error("--frontier-model is required for frontier coding or live guidance")
    tasks = [json.loads(path.read_text(encoding="utf-8")) for path in args.task] if args.task else [FIXTURE]
    for task in tasks:
        validate_task(task)
    batch = args.output / uuid.uuid4().hex
    for index, task in enumerate(tasks, 1):
        for condition in conditions:
            model = args.frontier_model if condition == "B" else args.local_model

            def coder(messages, seconds):
                return complete(model, messages, seconds)

            def fixed(kind, payload, seconds):
                return FIXED[kind], None

            use_fixed = args.scripted or args.fixed_guidance
            guide = fixed if use_fixed else model_guidance(args.frontier_model)
            output = batch / f"{batch.name}-{index:03d}-{condition}"
            result = run_task(task, condition, output,
                              scripted_coder() if args.scripted else coder,
                              guide, coding_model="scripted" if args.scripted else model,
                              guidance_model=("fixed" if use_fixed else args.frontier_model)
                              if condition in GUIDANCE else None,
                              action_limit=args.actions, repair_limit=args.repairs,
                              timeout=args.timeout, image=args.image, scripted=args.scripted)
            print(f"{result['task_id']} {condition}: {result['stop_reason']} ({output / 'result.json'})")


if __name__ == "__main__":
    main()
