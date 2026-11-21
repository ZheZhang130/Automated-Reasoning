import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contract_frontier.contracts import SavedContract, generate_contract, PROMPT

TEXT = """## Description
Signed sum.
## Preconditions
PRE-1 Unverified: two integers.
## Postconditions
POST-1 Unverified: output their sum.
## Test suggestions
Check POST-1 with a negative sum.
## Unspecified behavior
Malformed input.
"""


class ContractTests(unittest.TestCase):
    def test_statement_bound_replay_requires_no_provider_call(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"contract.json"
            path.write_text(json.dumps({"text":TEXT,"statement_sha256":hashlib.sha256(b"task").hexdigest(),
                                        "contract_prompt":PROMPT,"author":"Codex isolated contract author"}))
            provider=SavedContract(path)
            with patch("planning_frontier.planner.urlopen",side_effect=AssertionError("no network")):
                result=generate_contract(provider,"task",10)
            self.assertEqual(result["provenance"]["provider_calls_in_runner"],0)
            self.assertIsNone(result["usage"])
            self.assertIn("Unverified",result["verification"])
            with self.assertRaises(ValueError):
                generate_contract(provider,"other task",10)

    def test_missing_section_is_rejected(self):
        class Provider:
            prompt=PROMPT
            def __call__(self, statement, timeout):
                return "## Description\nIncomplete", None
        with self.assertRaises(ValueError):
            generate_contract(Provider(),"task",10)


    def test_contract_flows_through_shared_runner_once(self):
        import sys
        import types
        from unittest.mock import MagicMock
        from contract_frontier.run_contract import run
        calls=[]
        class Provider:
            model="fake"
            prompt=PROMPT
            def __call__(self, statement, timeout):
                calls.append(statement)
                return TEXT,None
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            task=root/"task";task.mkdir()
            (task/"task.json").write_text(json.dumps({
                "task_id":"sum","version":"1","statement":"sum",
                "submission_path":"solution.py"}))
            backend=types.SimpleNamespace(v3=MagicMock(),Environment=MagicMock(),
                TextModel=MagicMock(),Agent=MagicMock(),RawCapture=MagicMock(),
                FORMAT_ERROR="error",PROMPT="original shell prompt")
            backend.v3.Budget.return_value.actions=0
            backend.v3.Budget.return_value.repairs=0
            backend.Environment.return_value.last_candidate=b"print(3)"
            backend.Agent.return_value.run.return_value={"exit_status":"Submitted"}
            with patch.dict(sys.modules,{"runtime":backend,"litellm":types.SimpleNamespace()}):
                result=run(root,task,root/"output",Provider(),"qwen","http://localhost",
                    context=16384,coding_tokens=4000,guidance_kind="contract",
                    guidance_generator=generate_contract)
            self.assertEqual(calls,["sum"])
            self.assertEqual(result["condition"],"D-single-contract")
            self.assertTrue((root/"output"/"contract.spec.md").exists())
            self.assertFalse((root/"output"/"plan.json").exists())
            kwargs=backend.Agent.return_value.run.call_args.kwargs
            self.assertEqual(kwargs["guide"],TEXT)
            self.assertEqual(kwargs["guidance_label"],"behavioral contract")


    def test_contract_provider_defaults_match_and_allow_override(self):
        from contract_frontier.contracts import OllamaContract, FrontierContract
        local=OllamaContract("http://localhost", "qwen")
        self.assertEqual(local.output_tokens,3000)
        self.assertEqual(local.context,8192)
        self.assertEqual(FrontierContract("provider/model").output_tokens,3000)
        self.assertEqual(FrontierContract("provider/model", output_tokens=2500).output_tokens,2500)


if __name__=="__main__":
    unittest.main()
