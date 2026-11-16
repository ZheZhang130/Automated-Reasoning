"""Protocol and boundary checks. No model-authored program runs on the host."""
import unittest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path

from minisweagent.exceptions import InterruptAgentFlow
from runner import Budget, container_args, isolation_preflight
from prepare_lcb import export


class RunnerTests(unittest.TestCase):
    def test_dispatched_actions_stop_at_limit(self):
        budget = Budget(actions=2)
        budget.before()
        budget.before()
        with self.assertRaises(InterruptAgentFlow):
            budget.before()
        self.assertEqual(budget.actions, 2)

    def test_repeated_unchanged_failed_tests_do_not_consume_repairs(self):
        budget = Budget()
        budget.tested("a", 1)
        budget.changed(b"a", b"a")
        budget.tested("a", 1)
        self.assertEqual(budget.repairs, 0)
        budget.changed(b"a", b"b")
        budget.changed(b"b", b"c")
        self.assertEqual(budget.repairs, 1)
        budget.tested("c", 1)
        budget.changed(b"c", b"d")
        self.assertEqual(budget.repairs, 2)
        budget.tested("d", 0)
        budget.changed(b"d", b"e")
        self.assertEqual(budget.repairs, 2)

    def test_fourth_repair_stops(self):
        budget = Budget(repairs=0)
        budget.tested("a", 1)
        with self.assertRaises(InterruptAgentFlow):
            budget.changed(b"a", b"b")

    def test_container_has_only_public_readonly_mount(self):
        args = container_args(Path("E:/public"))
        self.assertEqual(args.count("--mount"), 1)
        self.assertIn("readonly", args[args.index("--mount") + 1])
        for key, value in [("--network", "none"), ("--user", "65534:65534"),
                           ("--cap-drop", "ALL"), ("--memory", "512m")]:
            self.assertEqual(args[args.index(key) + 1], value)
        self.assertIn("--read-only", args)
        self.assertNotIn("--privileged", args)

    def test_storage_check_precedes_any_docker_invocation(self):
        with patch("runner.docker") as command:
            with self.assertRaises((ValueError, FileNotFoundError)):
                isolation_preflight("python:test", Path("C:/"))
            command.assert_not_called()

    def test_private_fields_never_enter_exported_public_bundles(self):
        rows = [{"difficulty": difficulty, "platform": "fixture", "question_id": difficulty,
                 "metadata": "{}", "question_content": "Synthetic protocol fixture.",
                 "public_test_cases": json.dumps([{"testtype": "stdin", "input": "", "output": ""}]),
                 "private_test_cases": "PRIVATE_SENTINEL_DO_NOT_EXPOSE"}
                for difficulty in ("easy", "medium", "hard")]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "bundles"
            export(rows, root)
            public_files = list((root / "public").rglob("*"))
            self.assertTrue(public_files)
            for file in public_files:
                if file.is_file():
                    self.assertNotIn("PRIVATE_SENTINEL", file.read_text(encoding="utf-8"))
            self.assertEqual(len(list((root / "evaluator_private").glob("*.json"))), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
