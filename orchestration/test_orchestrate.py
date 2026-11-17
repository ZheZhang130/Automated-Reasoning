import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrate import CORRECT, WRONG, FIXED, FIXTURE, run_task, scripted_coder


class PilotTests(unittest.TestCase):
    def run_fixture(self, condition, **options):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            output = Path(root) / "run"

            def guide(kind, payload, seconds):
                calls.append((kind, payload))
                return FIXED[kind], None

            record = run_task(FIXTURE, condition, output,
                              options.pop("coder", scripted_coder()), guide,
                              scripted=True, **options)
            self.assertEqual(record, json.loads((output / "result.json").read_text()))
            if record["submission"]:
                self.assertTrue((output / record["submission"]).is_file())
            return record, calls

    def test_core_conditions(self):
        for condition in "ABCDE":
            with self.subTest(condition=condition):
                record, calls = self.run_fixture(condition)
                self.assertEqual(record["stop_reason"], "submitted")
                self.assertEqual(record["repairs"], 1)
                tests = [event for event in record["trace"] if event["event"] == "public_test"]
                self.assertEqual([event["status"] for event in tests], ["candidate_failure", "pass"])
                if condition in "AB":
                    self.assertFalse(calls)
                else:
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(calls[0][0], {"C": "plan", "D": "contract", "E": "diagnosis"}[condition])
                    events = [event["event"] for event in record["trace"]]
                    delivery = events.index("guidance_delivered")
                    if condition == "E":
                        self.assertIn("candidate_code", calls[0][1])
                        self.assertLess(events.index("public_test"), delivery)
                        self.assertLess(delivery, events.index("repair_start"))
                    else:
                        self.assertLess(delivery, events.index("action"))

    def test_no_diagnosis_when_public_tests_pass(self):
        actions = iter([{"action": "write", "code": CORRECT}, {"action": "test"}, {"action": "submit"}])
        record, calls = self.run_fixture("E", coder=lambda messages, seconds: (json.dumps(next(actions)), None))
        self.assertEqual(record["stop_reason"], "submitted")
        self.assertFalse(calls)

    def test_infrastructure_error_does_not_trigger_diagnosis(self):
        with patch("orchestrate.public_test", return_value={"status": "infrastructure_error"}):
            record, calls = self.run_fixture("E")
        self.assertEqual(record["stop_reason"], "infrastructure_error")
        self.assertFalse(calls)

    def test_default_schedule_refreshes_guidance_with_failure_state(self):
        record, calls = self.run_fixture("guided")
        self.assertEqual(record["stop_reason"], "public_tests_passed")
        self.assertEqual([kind for kind, _ in calls], ["plan", "diagnosis"])
        self.assertEqual(calls[1][1]["candidate_code"], WRONG)
        self.assertEqual(calls[1][1]["public_failure"]["actual"].strip(), "3")
        self.assertEqual(calls[1][1]["state"]["actions_left"], 18)
        self.assertEqual(record["actions"], 4)

    def test_custom_schedule_ignores_repeated_failure_and_stops_when_passing(self):
        actions = iter([
            {"action": "write", "code": WRONG}, {"action": "test"}, {"action": "test"},
            {"action": "write", "code": "print(0)"}, {"action": "test"},
            {"action": "write", "code": CORRECT}, {"action": "test"},
        ])
        record, calls = self.run_fixture(
            "guided", guidance_schedule=("contract", "plan", "diagnosis", "contract"),
            coder=lambda messages, seconds: (json.dumps(next(actions)), None),
        )
        self.assertEqual(record["stop_reason"], "public_tests_passed")
        self.assertEqual([kind for kind, _ in calls], ["contract", "plan", "diagnosis"])

    def test_limits_preserve_latest_candidate(self):
        for options, expected in [({"action_limit": 2}, "action_limit"), ({"repair_limit": 0}, "repair_limit")]:
            record, _ = self.run_fixture("A", **options)
            self.assertEqual(record["stop_reason"], expected)
            self.assertIsNotNone(record["submission"])
            self.assertEqual(record["repairs"], 0)


if __name__ == "__main__":
    unittest.main()
