import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from plan_once import run


class CodingBudgetTests(unittest.TestCase):
    def test_expanded_budget_reaches_model_and_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            task=root/"task";task.mkdir()
            (task/"task.json").write_text(json.dumps({
                "task_id":"fixture","version":"1","statement":"sum",
                "submission_path":"solution.py"}))
            backend=types.SimpleNamespace(
                v3=MagicMock(), Environment=MagicMock(), TextModel=MagicMock(),
                Agent=MagicMock(), RawCapture=MagicMock(),
                FORMAT_ERROR="format", PROMPT="system")
            backend.v3.Budget.return_value.actions=0
            backend.v3.Budget.return_value.repairs=0
            backend.Environment.return_value.last_candidate=b"print(3)"
            backend.Agent.return_value.run.return_value={"exit_status":"Submitted"}
            with patch.dict(sys.modules,{"runtime":backend,"litellm":types.SimpleNamespace()}):
                result=run(root,task,root/"output",None,"qwen","http://localhost",context=16384,coding_tokens=4000)
            self.assertEqual(backend.TextModel.call_args.kwargs["model_kwargs"]["num_predict"],4000)
            self.assertEqual(result["coding_output_limit"],4000)
            self.assertEqual(result["guidance_calls"],0)

    def test_invalid_budget_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"output"
            with self.assertRaises(ValueError):
                run(Path(directory),Path(directory),output,None,"qwen","http://localhost",context=4096,coding_tokens=4096)
            self.assertFalse(output.exists())


if __name__=="__main__":
    unittest.main()
