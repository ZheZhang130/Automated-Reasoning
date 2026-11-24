"""Build the study's tasks from the judge manifests: judge suites for the judge and a public bundle for the agent.

The evaluation owns the tasks. The agent only ever reads ``<study>/bundles/<id>`` (statement, public samples and the
``check.py`` stub) and calls judge-public while it runs; it never builds, reads or scores hidden tests.

Layout written under the study root (the interface ``guided_agent batch`` reads):

    judge/tasks/<id>/{task.json, problem.md, tests/public/*.in|*.out}   judge-public loads these
    judge/hidden/<id>/*.in|*.out                                         judge-hidden loads these, only when scoring
    bundles/<id>/{task.json, public_tests.json, check.py}                the agent's read-only /public
    tasks-manifest.json                                                  what was built, with hashes

The conversion and the hash definitions are ``judge/build_data.py``'s own, and only tasks listed in
``judge/manifests/*.json`` are accepted, each checked against its pinned hashes. Every file is written with LF line
endings, so a Windows build is byte-identical to a macOS one. Rebuilding is safe: complete tasks are re-verified and
kept, and a task left half-written by an interrupted build is rebuilt from the pinned shard.
"""
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD_DATA = REPO / 'judge/build_data.py'
SHARD = 'test6.jsonl'

# The agent sees exactly these files at /public. The stub text is part of the agent's interface: the harness
# intercepts this exact command and routes it to judge-public.
CHECK_STUB = '''"""Public tests are run by the harness through the team judge (judge-public)."""
import sys
print("Run the public tests as a separate action with exactly this command:\\n"
      "python -I /public/check.py\\n"
      "(No other text in the command.) The harness then reports judge-public results.")
sys.exit(2)
'''
BUNDLE_FILES = ('check.py', 'public_tests.json', 'task.json')


class _LFPath(type(Path())):
    """build_data.py writes problem.md and task.json with Path.write_text, which on Windows turns '\\n' into '\\r\\n'
    (and so changes the statement the agent reads). Forcing newline='' keeps the bytes identical on every OS."""

    def write_text(self, data, encoding=None, errors=None, newline=''):
        return super().write_text(data, encoding=encoding, errors=errors, newline=newline)


def write_json(path, value):
    """The agent side's JSON format (indent 2, UTF-8, LF), so bundle bytes match guided_agent's exactly."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8',
                    newline='\n')
    os.replace(temp, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_data():
    spec = importlib.util.spec_from_file_location('csc2108_evaluation_build_data', BUILD_DATA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_tasks():
    """task_id -> manifest entry (plus the manifest name), and the one pinned dataset revision."""
    entries, revisions = {}, set()
    for path in sorted((REPO / 'judge/manifests').glob('*.json')):
        manifest = read_json(path)
        revisions.update(manifest['hf_revision'])
        if manifest['shards'] != [SHARD]:
            raise ValueError(f'{path.name}: expected shards [{SHARD}], found {manifest["shards"]}')
        for entry in manifest['tasks']:
            entries[entry['task_id']] = entry | {'manifest': manifest['name']}
    if len(revisions) != 1:
        raise ValueError(f'manifests must pin exactly one dataset revision, found {sorted(revisions)}')
    return entries, revisions.pop()


def locate_shard(bd, revision, explicit=None):
    """A local copy whose sha256 matches the pin, else build_data's own download into judge/.cache."""
    expected = bd.SHARDS[SHARD]
    candidates = [Path(explicit)] if explicit else []
    if os.environ.get('CSC2108_LCB_SHARD'):
        candidates.append(Path(os.environ['CSC2108_LCB_SHARD']))
    candidates.append(bd.CACHE_DIR / f'{revision[:12]}-{SHARD}')
    for path in candidates:
        if path.is_file() and sha256_file(path) == expected:
            return path
    if explicit:
        raise ValueError(f'{explicit}: not the pinned {SHARD} (sha256 {expected})')
    return bd.fetch(SHARD, revision)


def _paths(study, task_id):
    return {'task': study / 'judge/tasks' / task_id, 'hidden': study / 'judge/hidden' / task_id,
            'bundle': study / 'bundles' / task_id}


def _complete(paths):
    return ((paths['task'] / 'task.json').is_file() and (paths['task'] / 'tests/public').is_dir()
            and paths['hidden'].is_dir() and all((paths['bundle'] / f).is_file() for f in BUNDLE_FILES))


def _verify(bd, task_id, entry, paths):
    """Problems with an already built task: its test hashes must still match the manifest."""
    problems = []
    if bd.sha256_dir(paths['task'] / 'tests/public') != entry['public_sha256']:
        problems.append(f'{task_id}: public tests differ from the manifest')
    if bd.sha256_dir(paths['hidden']) != entry['hidden_sha256']:
        problems.append(f'{task_id}: hidden tests differ from the manifest')
    return problems


def _write_bundle(bundle, task_id, statement, public):
    bundle.mkdir(parents=True)
    write_json(bundle / 'task.json', {'task_id': task_id, 'version': '1', 'statement': statement,
                                      'submission_path': 'solution.py'})
    write_json(bundle / 'public_tests.json', [{'input': c['input'], 'output': c['output'],
                                               'testtype': c.get('testtype', 'stdin')} for c in public])
    (bundle / 'check.py').write_text(CHECK_STUB, encoding='utf-8', newline='\n')


def _record(bd, task_id, entry, paths):
    meta = read_json(paths['task'] / 'task.json')
    statement = (paths['task'] / 'problem.md').read_text(encoding='utf-8')
    source = meta['source']
    return {'task_id': task_id, 'platform': source['platform'], 'difficulty': meta['difficulty'],
            'contest_id': source['contest_id'], 'contest_date': source['contest_date'], 'title': source['title'],
            'n_public': meta['n_public'], 'manifest': entry['manifest'],
            'public_sha256': bd.sha256_dir(paths['task'] / 'tests/public'),
            'hidden_sha256': bd.sha256_dir(paths['hidden']), 'n_hidden': entry['n_hidden'],
            'statement_sha256': hashlib.sha256(statement.encode('utf-8')).hexdigest(),
            'bundle_sha256': {p.name: sha256_file(p) for p in sorted(paths['bundle'].iterdir())}}


def prepare(study, task_ids, shard=None):
    """Build (or re-verify) ``task_ids`` under ``study``. Returns {'built': [...], 'verified': [...]}.

    Raises on a task outside the manifests, on any hash mismatch, and on a complete task whose tests changed
    (that study root is then not trustworthy; use a fresh one)."""
    study = Path(study)
    entries, revision = pinned_tasks()
    unknown = sorted(set(task_ids) - set(entries))
    if unknown:
        raise ValueError(f'not in judge/manifests: {unknown}')
    bd = build_data()
    paths = {t: _paths(study, t) for t in task_ids}
    done = [t for t in task_ids if _complete(paths[t])]
    problems = [p for t in done for p in _verify(bd, t, entries[t], paths[t])]
    if problems:
        raise RuntimeError('; '.join(problems) + ' (use a fresh study root)')
    todo = [t for t in task_ids if t not in done]
    records = {t: _record(bd, t, entries[t], paths[t]) for t in done}
    shard_path = None
    if todo:
        shard_path = locate_shard(bd, revision, shard)
        rows = {}
        with Path(shard_path).open(encoding='utf-8') as stream:
            for line in stream:
                row = json.loads(line)
                task_id = f"lcb-{row['platform']}-{row['question_id']}"
                if task_id in todo:
                    rows[task_id] = row
        missing = sorted(set(todo) - set(rows))
        if missing:
            raise ValueError(f'not in the pinned shard: {missing}')
        bd.TASKS_DIR, bd.HIDDEN_DIR = _LFPath(study / 'judge/tasks'), _LFPath(study / 'judge/hidden')
        bd.TASKS_DIR.mkdir(parents=True, exist_ok=True)
        bd.HIDDEN_DIR.mkdir(parents=True, exist_ok=True)
        for task_id in todo:
            for directory in paths[task_id].values():  # left half-written by an interrupted build
                shutil.rmtree(directory, ignore_errors=True)
            row = rows[task_id]
            errors = bd.build(row, entries[task_id], SHARD, revision, True)
            if errors:
                raise RuntimeError(f'{task_id}: hash mismatch against the judge manifest: {errors}')
            statement = (paths[task_id]['task'] / 'problem.md').read_text(encoding='utf-8')
            _write_bundle(paths[task_id]['bundle'], task_id, statement, json.loads(row['public_test_cases']))
            records[task_id] = _record(bd, task_id, entries[task_id], paths[task_id])
    manifest_path = study / 'tasks-manifest.json'
    record = read_json(manifest_path) if manifest_path.exists() else {'tasks': {}}
    record['hf_revision'] = revision
    record['shard_sha256'] = bd.SHARDS[SHARD]
    if shard_path:
        record['shard'] = str(shard_path)
    record['tasks'].update(records)
    write_json(manifest_path, record)
    return {'built': todo, 'verified': done}
