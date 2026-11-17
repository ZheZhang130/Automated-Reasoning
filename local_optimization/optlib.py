"""Optimization paths; reuse immutable v2 primitives without changing their globals."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
V2 = REPO / 'local_eval_v2'
sys.path.insert(0, str(V2))
from common import BASELINE, ENDPOINT, Lock, alive, digest, on_e, read, save

DATA = Path('E:/CSC2108Local/optimization')
MODEL = 'qwen3.5:9b'
MODEL_DIGEST = '56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
GPU_LOCK = Path('E:/CSC2108Local/eval-v2/gpu.lock')
VENDOR = Path('E:/CSC2108Local/vendor/LiveCodeBench')
JUDGE = 'csc2108-lcb-judge:v2'


def sources():
    paths = list(ROOT.glob('*.py')) + [ROOT / 'profiles.json']
    paths += [V2 / n for n in ('runtime.py', 'common.py', 'public_check.py', 'profiles.json', 'dataset.py')]
    paths += [BASELINE / n for n in ('runner.py', 'probe.py', 'pilot.py', 'judge_lcb.py', 'prepare_lcb.py', 'models.json', 'requirements.lock', 'judge-requirements.lock', 'env.ps1')]
    return {str(p.relative_to(REPO)): digest(p) for p in sorted(paths)}
