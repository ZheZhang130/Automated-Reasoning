"""Read-only reuse of the prior pilot; only A2's system prompt is changed."""
import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
sys.path.insert(0,str(REPO/'one_shot_ablation'))
import shared as previous
from shared import read,save,digest,Lock,baseline,MODEL,MODEL_DIGEST,CONFIG,PROFILE,SEED,JUDGE,VENDOR,GPU_LOCK,CACHE,EVALUATOR,REVISION,options

DATA=Path('E:/CSC2108Local/agent-delivery-pilot')
OLD=Path('E:/CSC2108Local/one-shot-ablation')
A2_PROFILE='heredoc-v6-16k-common-delivery-prompt-v1'
A2_PROMPT='''You are a Python coding agent in a persistent Linux workspace.
Solve the supplied task yourself and honor its required interface.
Reply with exactly ONE complete current shell command in this format:
```mswea_bash_command
command
```
Output only that block. Keep source compact: omit planning, alternatives, running commentary and explanatory comment blocks.
First write a complete runnable /workspace/solution.py using a literal heredoc. Close both the heredoc and command fence in the same response.
Next run the separate command python -I /public/check.py and read its feedback.
If a test fails, change the implementation before testing again. Wait for each command result before choosing the next action.
After saving and testing the source, submit with the separate command echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT.
'''


def old_module(name):
    spec=importlib.util.spec_from_file_location('original_ablation_'+name,REPO/'one_shot_ablation'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
