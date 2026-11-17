"""Paths and fixed pilot configuration; existing experiment sources are read-only."""
import os
import sys
from pathlib import Path

os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP','True')
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
sys.path.insert(0,str(REPO/'local_optimization'))
sys.path.insert(0,str(REPO/'local_eval_v2'))
from common import read,save,digest,Lock
import runtime as baseline
from dataset import CACHE,REVISION,EVALUATOR
from optlib import MODEL,MODEL_DIGEST,JUDGE,VENDOR,GPU_LOCK

DATA=Path('E:/CSC2108Local/one-shot-ablation')
PROFILE='heredoc-v6-16k-common'
CONFIG=read(REPO/'local_eval_v2/profiles.json')[PROFILE]
SEED=2108
ONE_SHOT_PROMPT=('Solve the supplied programming problem yourself. Return one complete Python solution, '
 'including all required imports and the required interface. You have no tools or execution feedback. '
 'Return the source in one closed ```python code block, without explanations. Do not emit shell commands.')


def options():
    return CONFIG['sampler']|{'num_ctx':CONFIG['context'],'num_predict':CONFIG['output_tokens'],
                            'temperature':CONFIG['temperature'],'seed':SEED}


def extract(text):
    """Remove one wrapper only. Never repair, join, or rewrite generated source."""
    import re
    if not text.strip():return None,'empty_response'
    if '```' not in text:return text,'raw_source'
    blocks=list(re.finditer(r'```(?:python|py)?[ \t]*\r?\n(.*?)\r?\n```',text,re.S))
    if len(blocks)!=1 or text.count('```')!=2:return None,'ambiguous_or_unclosed_fence'
    block=blocks[0]
    return block.group(1)+'\n',('single_fence' if not (text[:block.start()]+text[block.end():]).strip() else 'single_fence_with_extra_text')
