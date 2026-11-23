"""Shared helpers: study locations, hashing and UTF-8 JSON I/O (no host-specific logic)."""
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODEL = 'qwen3.5:9b'
PROFILE = 'heredoc-v6-16k-common'
SEED = 2108
ACTIONS, REPAIRS, SECONDS = 20, 3, 600
LCB_REVISION = '0fe84c3912ea0c4d4a78037083943e8f0c4dd505'
# Upfront guidance kind per condition (None = no upfront artifact). E's guidance is generated at run time
# (DYNAMIC), and B substitutes the coding model (CODER); both run on the same frozen agent loop.
CONDITIONS = {'A': None, 'B': None, 'C': 'plan', 'D': 'contract', 'E': None}
DYNAMIC = {'E': 'diagnosis'}
CODER = {'B': 'frontier'}
# Reserved so a later condition can be added without changing artifact schemas.
FUTURE_CONDITIONS = {'F': 'plan+contract'}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode('utf-8'))


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    # newline='\n': identical bytes (and artifact hashes) on Windows and POSIX.
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8', newline='\n')
    os.replace(temp, path)


def append_jsonl(path, value):
    with Path(path).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, default=str) + '\n')


def utc_now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def host_identity():
    return {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine(),
            'node': platform.node(), 'python': sys.version.split()[0]}


def settings(backend='auto'):
    from local_agent.platform_support import Settings
    return Settings.load(backend)


def study_root(host_settings, override=None):
    """Runtime artifacts live under the configured data root, never inside the checkout."""
    root = Path(override or os.environ.get('CSC2108_STUDY_ROOT') or host_settings.root / 'reasoning-effectiveness')
    root = root.expanduser().resolve()
    if root == REPO or root.is_relative_to(REPO):
        raise ValueError('Study artifacts must be outside the checkout')
    root.mkdir(parents=True, exist_ok=True)
    return root


def ledger_path(study):
    """One API ledger per study, or one shared ledger for several study roots (CSC2108_API_LEDGER), so a
    pass-wide request and spending ceiling holds across all of them."""
    return Path(os.environ.get('CSC2108_API_LEDGER') or Path(study) / 'api-ledger.json')


def normalize_task_id(task_id):
    """Earlier evaluator IDs are 'atcoder-abc397_b'; judge IDs add an 'lcb-' prefix."""
    return task_id[4:] if task_id.startswith('lcb-') else task_id
