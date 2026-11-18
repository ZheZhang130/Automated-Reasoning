"""Public judge and evaluation handoffs for the merged repository."""
import hashlib
import json
import platform
import sys
from pathlib import Path


def load_task(path):
    """Read Peter's task directory or the original self-contained pilot JSON."""
    path = Path(path)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    meta = json.loads((path / "task.json").read_text(encoding="utf-8"))
    tests = []
    for source in sorted((path / "tests" / "public").glob("*.in")):
        tests.append({"stdin": source.read_text(encoding="utf-8"),
                      "expected": source.with_suffix(".out").read_text(encoding="utf-8")})
    return {
        "task_id": meta["task_id"], "version": str(meta.get("version", "1")),
        "statement": (path / "problem.md").read_text(encoding="utf-8"),
        "submission_type": "stdin_stdout", "submission_path": "solution.py",
        "public_tests": tests,
    }


class PublicJudge:
    """Lazy startup lets a judge failure be recorded inside the scheduled run."""
    def __init__(self, repo):
        self.repo = Path(repo)
        self.client = None

    def __call__(self, task, candidate, remaining):
        remaining()
        try:
            if self.client is None:
                sys.path.insert(0, str(self.repo / "judge"))
                from judgekit import Judge
                self.client = Judge.public()
            result = self.client.run(task["task_id"], candidate.read_bytes())
        except Exception as error:
            return {"status": "infrastructure_error", "error": type(error).__name__}
        if result.get("suite") != "public":
            return {"status": "infrastructure_error", "error": "Unexpected judge suite"}
        if result.get("task_id") != task["task_id"] or result.get("status") not in (
            "pass", "candidate_failure", "infrastructure_error"
        ):
            return {"status": "infrastructure_error", "error": "Invalid judge response"}
        return result


def export_handoff(output, record, attempts, repeat):
    """Add Peter's schema without losing the existing diagnostic fields."""
    source = record["submission"]
    digest = None
    if source:
        data = (output / source).read_bytes()
        (output / "submission.py").write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
    statuses = {"public_tests_passed": "submitted", "execution_error": "agent_error",
                "infrastructure_error": "infra_error"}
    reason = record["stop_reason"]
    record.update(
        repeat=repeat, exit_status=statuses.get(reason, reason), raw_exit_status=reason,
        submission_sha256=digest, n_actions=record["actions"], n_repairs=record["repairs"],
        wall_seconds=record["elapsed_seconds"], host=platform.node(),
    )
    record["guidance"]["triggered"] = record["guidance"]["diagnosis_triggered"]

    def usage(item):
        item = item or {}
        tokens = item.get("tokens") or {}
        return {"prompt_tokens": tokens.get("prompt_tokens"),
                "completion_tokens": tokens.get("completion_tokens"),
                "cost_usd": item.get("cost_usd")}

    record["usage"] = {
        "coding": [usage(item) for item in record["coding_usage"]],
        "guidance": [usage(entry["usage"]) for entry in record["guidance_rounds"]],
    }
    (output / "attempts.jsonl").write_text(
        "".join(json.dumps(attempt) + "\n" for attempt in attempts), encoding="utf-8")
