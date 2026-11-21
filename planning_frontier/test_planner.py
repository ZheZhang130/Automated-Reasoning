import unittest
from planner import generate_plan

class PlannerTests(unittest.TestCase):
    def test_exactly_one_statement_only_request(self):
        calls = []
        def fake(statement, timeout):
            calls.append((statement, timeout))
            return '## Observations\n1. Signed addition.\n## Solution sketch\nAdd the integers.', None
        result = generate_plan(fake, "sum task", 12)
        self.assertEqual(calls, [("sum task", 12)])
        self.assertIn("## Solution sketch", result["text"])

    def test_malformed_plan_fails_without_retry(self):
        calls = []
        def fake(statement, timeout):
            calls.append(statement)
            return 'print(1)', None
        with self.assertRaises(ValueError):
            generate_plan(fake, "task", 12)
        self.assertEqual(len(calls), 1)


class CompactPlannerTests(unittest.TestCase):
    def test_compact_ollama_request_retains_token_ceiling(self):
        import json
        from unittest.mock import patch, MagicMock
        from planner import OllamaPlanner, COMPACT_PROMPT
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "message": {"content": "## Observations\nA\n## Solution sketch\nB"},
            "done_reason": "stop", "eval_count": 238}).encode()
        with patch("planner.urlopen", return_value=response) as request:
            result = generate_plan(OllamaPlanner("http://localhost:11435", "qwen", compact=True), "task", 30)
            payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload["options"]["num_predict"], 1200)
        self.assertEqual(payload["messages"][0]["content"], COMPACT_PROMPT)
        self.assertEqual(result["system_prompt"], COMPACT_PROMPT)
        self.assertEqual(request.call_count, 1)

    def test_truncated_plan_is_still_rejected(self):
        import json
        from unittest.mock import patch, MagicMock
        from planner import OllamaPlanner
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "message": {"content": "unfinished"}, "done_reason": "length"}).encode()
        with patch("planner.urlopen", return_value=response), self.assertRaises(ValueError):
            OllamaPlanner("http://localhost:11435", "qwen", compact=True)("task", 30)

class LargerBudgetTests(unittest.TestCase):
    def test_explicit_planning_limits_and_raw_response(self):
        import json
        from unittest.mock import patch, MagicMock
        from planner import OllamaPlanner
        response = MagicMock()
        body = {"message": {"content": "## Observations\nA\n## Solution sketch\nB"},
                "done_reason": "stop", "eval_count": 1400}
        response.__enter__.return_value.read.return_value = json.dumps(body).encode()
        planner = OllamaPlanner("http://localhost:11435", "qwen", context=8192, output_tokens=3600)
        with patch("planner.urlopen", return_value=response) as request:
            generate_plan(planner, "task", 240)
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload["options"]["num_predict"], 3600)
        self.assertEqual(payload["options"]["num_ctx"], 8192)
        self.assertEqual(planner.last_response, body)


class DefaultBudgetTests(unittest.TestCase):
    def test_live_local_and_api_defaults_and_compact_override(self):
        from planner import OllamaPlanner, FrontierPlanner
        self.assertEqual(OllamaPlanner("http://localhost", "qwen").output_tokens, 6000)
        self.assertEqual(OllamaPlanner("http://localhost", "qwen").context, 16384)
        self.assertEqual(FrontierPlanner("provider/model").output_tokens, 6000)
        self.assertEqual(OllamaPlanner("http://localhost", "qwen", compact=True).output_tokens, 1200)
        self.assertEqual(FrontierPlanner("provider/model", compact=True).output_tokens, 1200)
        self.assertEqual(FrontierPlanner("provider/model", output_tokens=2500).output_tokens, 2500)
        with self.assertRaises(ValueError):
            FrontierPlanner("provider/model", output_tokens=0)

if __name__ == '__main__':
    unittest.main()
