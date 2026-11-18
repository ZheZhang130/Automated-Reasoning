"""Contract checks against the merged judge API; no Docker or credentials."""
import json
import tempfile
import unittest
from pathlib import Path

from integration import PublicJudge, load_task
from orchestrate import FIXTURE, FIXED, scripted_coder, run_task


class IntegrationTests(unittest.TestCase):
    def test_public_judge_handoff_and_multiround_feedback(self):
        calls = []
        def judge(task, candidate, remaining):
            calls.append(candidate.read_text())
            failed = len(calls) == 1
            return {"suite": "public", "task_id": task["task_id"],
                    "status": "candidate_failure" if failed else "pass",
                    "report": "Wrong sign" if failed else "PUBLIC TESTS: 2/2 passed",
                    "first_failure": {"verdict": "WA", "actual": "3"} if failed else None}
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "run"
            guides = []
            def guide(kind, payload, seconds):
                guides.append(payload)
                return FIXED[kind], None
            result = run_task(FIXTURE, "guided", output, scripted_coder(), guide,
                              scripted=True, public_evaluator=judge, repeat=2)
            self.assertEqual(result["exit_status"], "submitted")
            self.assertEqual(result["repeat"], 2)
            self.assertEqual(len(guides), 2)
            self.assertEqual(guides[1]["public_failure"]["report"], "Wrong sign")
            self.assertEqual(result["submission_sha256"], __import__("hashlib").sha256(
                (output / "submission.py").read_bytes()).hexdigest())
            attempts = [json.loads(line) for line in (output / "attempts.jsonl").read_text().splitlines()]
            self.assertEqual([a["seq"] for a in attempts], [1, 2])
            self.assertTrue(all(a["delivered"] for a in attempts))
            self.assertIsNone(result["usage"]["guidance"][0]["cost_usd"])

    def test_task_directory_adapter(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "task.json").write_text(json.dumps({"task_id": "example", "hidden_sha256": "metadata-only"}))
            (root / "problem.md").write_text("Compute a sum")
            public = root / "tests" / "public"
            public.mkdir(parents=True)
            (public / "01.in").write_text("1 2")
            (public / "01.out").write_text("3")
            task = load_task(root)
            self.assertEqual(task["public_tests"][0]["expected"], "3")
            self.assertNotIn("hidden_sha256", task)

    def test_hidden_response_rejected(self):
        judge = PublicJudge(".")
        class WrongSuite:
            def run(self, *args):
                return {"suite": "hidden", "status": "pass"}
        judge.client = WrongSuite()
        with tempfile.TemporaryDirectory() as root:
            candidate = Path(root) / "solution.py"
            candidate.write_text("print(1)")
            self.assertEqual(judge(FIXTURE, candidate, lambda: 10)["status"], "infrastructure_error")


if __name__ == "__main__":
    unittest.main()
