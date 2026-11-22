"""Build judge-format tasks and the agent's public bundle from the pinned LiveCodeBench shard.

Reuses ``judge/build_data.py`` (Peter's conversion and hash definitions) with its output
directories redirected to the study data root. Hidden tests are written only under
``<study>/judge/hidden`` and are never mounted into the agent container.
"""
import importlib.util
import json
import os
from pathlib import Path

from .common import LCB_REVISION, REPO, normalize_task_id, read_json, sha256_file, sha256_text, write_json

# The agent sees exactly these files at /public (the frozen runtime's allowed bundle schema).
CHECK_STUB = '''"""Public tests are run by the harness through the team judge (judge-public)."""
import sys
print("Run the public tests as a separate action with exactly this command:\\n"
      "python -I /public/check.py\\n"
      "(No other text in the command.) The harness then reports judge-public results.")
sys.exit(2)
'''


class _NoTranslatePath(type(Path())):
    """build_data.py writes with Path.write_text, which turns '\n' into '\r\n' on Windows and breaks
    the manifest hashes (computed on macOS). Writing with newline='' keeps bytes identical everywhere."""
    def write_text(self, data, encoding=None, errors=None, newline=''):
        return super().write_text(data, encoding=encoding, errors=errors, newline=newline)


def build_data_module():
    spec = importlib.util.spec_from_file_location('csc2108_build_data', REPO / 'judge/build_data.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def locate_shard(host_settings, explicit=None):
    bd = build_data_module()
    expected = bd.SHARDS['test6.jsonl']
    candidates = [Path(explicit)] if explicit else []
    if os.environ.get('CSC2108_LCB_SHARD'):
        candidates.append(Path(os.environ['CSC2108_LCB_SHARD']))
    candidates += [REPO / 'judge/.cache' / f'{LCB_REVISION[:12]}-test6.jsonl',
                   host_settings.root / 'eval-v2/cache/test6.jsonl',
                   host_settings.root / 'cache/lcb/test6.jsonl']
    for path in candidates:
        if path.is_file() and sha256_file(path) == expected:
            return path
    # Same pinned revision/sha256 as Peter's setup; downloads into judge/.cache (Git-ignored).
    return bd.fetch('test6.jsonl', LCB_REVISION)


def manifest_entries():
    entries = {}
    for name in ('pilot', 'main'):
        for entry in read_json(REPO / f'judge/manifests/{name}.json')['tasks']:
            entries[entry['task_id']] = entry | {'manifest': name}
    return entries


def rows_by_id(shard):
    rows = {}
    with Path(shard).open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            rows[f"lcb-{row['platform']}-{row['question_id']}"] = row
    return rows


def public_metadata(row):
    """Selection-safe metadata: nothing derived from hidden tests or solutions."""
    return {'task_id': f"lcb-{row['platform']}-{row['question_id']}", 'platform': row['platform'],
            'difficulty': row['difficulty'], 'contest_id': row['contest_id'],
            'contest_date': row['contest_date'], 'title': row['question_title'],
            'n_public': len(json.loads(row['public_test_cases']))}


def prepare(task_ids, study, host_settings, shard=None):
    """Create <study>/judge/{tasks,hidden}/<id> and <study>/bundles/<id>; verify manifest hashes."""
    bd = build_data_module()
    shard = locate_shard(host_settings, shard)
    rows = rows_by_id(shard)
    pinned = manifest_entries()
    judge_root = study / 'judge'
    bd.TASKS_DIR, bd.HIDDEN_DIR = _NoTranslatePath(judge_root / 'tasks'), _NoTranslatePath(judge_root / 'hidden')
    bd.TASKS_DIR.mkdir(parents=True, exist_ok=True)
    bd.HIDDEN_DIR.mkdir(parents=True, exist_ok=True)
    built = {}
    for task_id in task_ids:
        row = rows[task_id]
        if row['platform'] != 'atcoder':
            raise ValueError('Only stdin/stdout AtCoder tasks are supported by the team judge: ' + task_id)
        private = bd.decode_private(row['private_test_cases'])
        entry = pinned.get(task_id) or {'task_id': task_id, 'version': '1', 'n_hidden': len(private),
                                        'public_sha256': None, 'hidden_sha256': None}
        for directory in (bd.TASKS_DIR / task_id, bd.HIDDEN_DIR / task_id):
            if directory.exists():
                raise FileExistsError(f'{directory} exists; use a fresh study root or keep the original')
        errors = bd.build(row, entry, 'test6.jsonl', LCB_REVISION, True)
        public_hash = bd.sha256_dir(bd.TASKS_DIR / task_id / 'tests/public')
        hidden_hash = bd.sha256_dir(bd.HIDDEN_DIR / task_id)
        if task_id in pinned and errors:
            raise RuntimeError(f'{task_id}: hash mismatch against judge manifest: {errors}')
        if task_id not in pinned:  # Record the hashes we computed so later builds can be checked.
            meta_path = bd.TASKS_DIR / task_id / 'task.json'
            meta = read_json(meta_path)
            meta.update(public_sha256=public_hash, hidden_sha256=hidden_hash)
            write_json(meta_path, meta)
        statement = (bd.TASKS_DIR / task_id / 'problem.md').read_text(encoding='utf-8')
        public = json.loads(row['public_test_cases'])
        bundle = study / 'bundles' / task_id
        bundle.mkdir(parents=True, exist_ok=False)
        write_json(bundle / 'task.json', {'task_id': task_id, 'version': '1', 'statement': statement,
                                          'submission_path': 'solution.py'})
        write_json(bundle / 'public_tests.json', [{'input': c['input'], 'output': c['output'],
                                                   'testtype': c.get('testtype', 'stdin')} for c in public])
        (bundle / 'check.py').write_text(CHECK_STUB, encoding='utf-8', newline='\n')
        built[task_id] = public_metadata(row) | {
            'manifest': pinned.get(task_id, {}).get('manifest'), 'public_sha256': public_hash,
            'hidden_sha256': hidden_hash, 'n_hidden': len(private), 'statement_sha256': sha256_text(statement),
            'bundle_sha256': {p.name: sha256_file(p) for p in sorted(bundle.iterdir())}}
    record = {'shard': str(shard), 'shard_sha256': sha256_file(shard), 'hf_revision': LCB_REVISION,
              'tasks': built}
    existing = study / 'tasks-manifest.json'
    if existing.exists():
        prior = read_json(existing)
        prior['tasks'].update(built)
        record['tasks'] = prior['tasks']
    write_json(existing, record)
    return record


def load_statement(study, task_id):
    return read_json(study / 'bundles' / task_id / 'task.json')['statement']


def exclusion_union(extra=()):
    """The 75-ID scored union plus any extra IDs, all normalized to the earlier evaluator form."""
    ids = set(read_json(REPO / 'evidence/agent_delivery_pilot/future_exclusions.json')
              ['exclude_from_future_fresh_validation'])
    return ids | {normalize_task_id(t) for t in extra}
