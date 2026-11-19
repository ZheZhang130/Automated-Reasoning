import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from planner import SavedPlan, generate_plan


class SavedPlanTests(unittest.TestCase):
    def make(self, root):
        artifact={"text":"## Observations\n1. A.\n## Solution sketch\n1. B.",
                  "statement_sha256":hashlib.sha256(b"task").hexdigest(),
                  "planning_prompt":"public planning prompt", "author":"Codex isolated planning agent"}
        path=Path(root)/"plan.json"
        path.write_text(json.dumps(artifact))
        return path

    def test_replay_has_no_provider_call_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as root:
            path=self.make(root)
            with patch("planner.urlopen", side_effect=AssertionError("network forbidden")):
                result=generate_plan(SavedPlan(path), "task", 10)
            self.assertIsNone(result["usage"])
            self.assertEqual(result["provenance"]["provider_calls_in_runner"],0)
            self.assertEqual(result["provenance"]["source_sha256"],hashlib.sha256(path.read_bytes()).hexdigest())

    def test_rejects_different_task(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                generate_plan(SavedPlan(self.make(root)), "different", 10)


if __name__=="__main__":
    unittest.main()
