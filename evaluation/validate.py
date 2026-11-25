"""Completeness and integrity of a batch: what happened to every scheduled attempt, and whether its hidden verdict
belongs to the submission that was actually evaluated.

Attempt states (``STATES``):

``not_executed``      scheduled, no run directory yet
``incomplete``        a run directory without ``result.json`` (interrupted; ``guided_agent batch`` retries it on resume)
``awaiting_scoring``  finished (``result.json``), no hidden verdict yet
``scored``            finished and hidden-scored with a valid verdict (pass, model failure or infrastructure fault:
                      the metrics decide which, see ``metrics.failure_category``)
``excluded``          its (task, seed) block is listed in ``<batch>/exclusions.json`` with a documented reason
``invalid``           malformed record, or a verdict that does not match the run (wrong run/task/condition, stale or
                      tampered submission, other hidden tests or judge version), or a stale measurement record

A verdict is valid only when: run_id, task_id and condition equal the run record's; the judged ``code_sha256`` equals
the record's ``submission_sha256`` and the sha256 of ``submission.py`` on disk; ``tests_sha256`` equals the judge digest
of the task's hidden suite as built for this study (itself checked against the selected manifest); and the judge version
is the expected one. ``missing_submission`` is valid only when no submission exists. An official report needs every
attempt ``scored`` or ``excluded``.
"""
import hashlib
from collections import Counter
from pathlib import Path

from .plan import read_json, write_json

STATES = ('not_executed', 'incomplete', 'awaiting_scoring', 'scored', 'excluded', 'invalid')
DONE = frozenset({'scored', 'excluded'})
JUDGE_VERSION = '0.2.1'
VERDICT_STATUSES = frozenset({'pass', 'candidate_failure', 'missing_submission', 'infrastructure_error'})
EXCLUSIONS = 'exclusions.json'


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def judge_tests_digest(task_dir):
    """The judge container's per-task digest (``judge/container/judge.py`` ``tests_digest``), computed on the host."""
    digest = hashlib.sha256()
    for inp in sorted(Path(task_dir).glob('*.in')):
        for path in (inp, inp.with_suffix('.out')):
            digest.update(f'{inp.stem}{path.suffix}\0{sha256_bytes(path.read_bytes())}\n'.encode())
    return digest.hexdigest()


def expected_hidden(study, task_ids=None):
    """task_id -> {'judge_sha256', 'hidden_sha256', 'n_hidden'} for the study's built hidden suites (or {})."""
    study = Path(study)
    record = read_json(study / 'tasks-manifest.json') if (study / 'tasks-manifest.json').exists() else {'tasks': {}}
    out = {}
    for task_id, entry in record.get('tasks', {}).items():
        if task_ids is not None and task_id not in task_ids:
            continue
        digest = entry.get('hidden_judge_sha256')
        hidden = study / 'judge/hidden' / task_id
        if digest is None and hidden.is_dir():
            digest = judge_tests_digest(hidden)
        out[task_id] = {'judge_sha256': digest, 'hidden_sha256': entry.get('hidden_sha256'),
                        'n_hidden': entry.get('n_hidden')}
    return out


def read_exclusions(batch_dir):
    path = Path(batch_dir) / EXCLUSIONS
    if not path.exists():
        return {}
    data = read_json(path)
    out = {}
    for item in data.get('exclusions', []):
        if not item.get('reason'):
            raise ValueError(f'{path}: every exclusion needs a reason')
        out[(item['task_id'], int(item['seed']))] = item
    return out


def add_exclusion(batch_dir, task_id, seed, reason, decided_by=None, utc=None):
    path = Path(batch_dir) / EXCLUSIONS
    data = read_json(path) if path.exists() else {'schema': 'csc2108-exclusions-v1', 'exclusions': []}
    if any(e['task_id'] == task_id and int(e['seed']) == int(seed) for e in data['exclusions']):
        raise ValueError(f'({task_id}, {seed}) is already excluded')
    data['exclusions'].append({'task_id': task_id, 'seed': int(seed), 'reason': reason, 'decided_by': decided_by,
                               'utc': utc})
    write_json(path, data)
    return data


def verdict_problems(verdict, record, run_dir, expected=None, judge_version=JUDGE_VERSION):
    """Why ``verdict`` is not a valid hidden verdict for the run in ``run_dir`` (empty list: valid)."""
    problems = []
    for key in ('run_id', 'task_id', 'condition'):
        if verdict.get(key) != record.get(key):
            problems.append(f'verdict {key} {verdict.get(key)!r} != run {record.get(key)!r}')
    if verdict.get('suite', 'hidden') != 'hidden':
        problems.append(f"verdict suite {verdict.get('suite')!r} is not hidden")
    status = verdict.get('status')
    if status not in VERDICT_STATUSES:
        return problems + [f'unknown hidden status {status!r}']
    submission = Path(run_dir) / 'submission.py'
    on_disk = sha256_bytes(submission.read_bytes()) if submission.exists() else None
    recorded = record.get('submission_sha256')
    if verdict.get('submission_sha256', recorded) != recorded:
        problems.append('verdict was written for a different run record (submission_sha256 differs)')
    if status == 'missing_submission':
        if recorded is not None or on_disk is not None:
            problems.append('verdict says missing_submission but the run has a submission (stale verdict)')
        return problems
    if status == 'infrastructure_error':
        if verdict.get('error') == 'submission hash mismatch' or (recorded and on_disk and recorded != on_disk):
            problems.append('submission.py does not match the run record (tampered or replaced submission)')
        return problems
    if recorded is None or on_disk is None:
        problems.append('judged verdict but the run has no submission')
    elif not (verdict.get('code_sha256') == recorded == on_disk):
        problems.append('judged code is not the recorded submission (stale verdict or changed submission.py)')
    if verdict.get('judge_version') != judge_version:
        problems.append(f"judge version {verdict.get('judge_version')!r} != {judge_version}")
    if expected:
        if expected.get('judge_sha256') and verdict.get('tests_sha256') != expected['judge_sha256']:
            problems.append('verdict was judged on other hidden tests than the selected benchmark')
        if expected.get('n_hidden') is not None and verdict.get('total') not in (None, expected['n_hidden']):
            problems.append(f"verdict judged {verdict.get('total')} hidden cases, the task has {expected['n_hidden']}")
    if not isinstance(verdict.get('passed'), int) or not isinstance(verdict.get('total'), int):
        problems.append('verdict lacks integer passed/total counts')
    elif (status == 'pass') != (verdict['passed'] == verdict['total'] and verdict['total'] > 0):
        problems.append(f"status {status} disagrees with {verdict['passed']}/{verdict['total']} cases")
    return problems


def attempt_state(batch_dir, item, *, expected=None, exclusions=None, run_name=None):
    """State, run record and validated verdict of one scheduled attempt."""
    if run_name is None:
        from guided_agent.integrity import run_name
    batch_dir = Path(batch_dir)
    run_dir = batch_dir / run_name(item)
    key = (item['task_id'], int(item['seed']))
    out = {'run_dir': run_dir, 'record': None, 'verdict': None, 'problems': []}
    if exclusions and key in exclusions:
        return out | {'state': 'excluded', 'exclusion': exclusions[key]}
    if not run_dir.exists():
        interrupted = sorted(batch_dir.glob(run_dir.name + '.incomplete-*'))
        return out | {'state': 'incomplete' if interrupted else 'not_executed',
                      'problems': [f'{len(interrupted)} interrupted attempt(s), not yet retried'] if interrupted else []}
    if not (run_dir / 'result.json').exists():
        return out | {'state': 'incomplete', 'problems': ['run directory without result.json (interrupted)']}
    try:
        record = read_json(run_dir / 'result.json')
        record['run_id'], record['task_id'], record['condition']
    except Exception as error:
        return out | {'state': 'invalid', 'problems': [f'malformed result.json: {type(error).__name__}: {error}']}
    out['record'] = record
    mismatch = [f'run record {k} {record.get(k)!r} != plan {item.get(k)!r}' for k in ('task_id', 'condition')
                if record.get(k) != item.get(k)]
    if item.get('seed') is not None and record.get('seed') is not None and int(record['seed']) != int(item['seed']):
        mismatch.append(f"run record seed {record.get('seed')} != plan {item['seed']}")
    if mismatch:
        return out | {'state': 'invalid', 'problems': mismatch}
    malformed = batch_dir / 'eval' / f'malformed-{run_dir.name}.json'
    path = batch_dir / 'eval' / f"{record['run_id']}.json"
    if not path.exists():
        if malformed.exists():
            return out | {'state': 'invalid', 'problems': ['hidden scoring recorded a malformed run record']}
        return out | {'state': 'awaiting_scoring'}
    try:
        verdict = read_json(path)
    except Exception as error:
        return out | {'state': 'invalid', 'problems': [f'unreadable verdict {path.name}: {error}']}
    out['verdict'] = verdict
    problems = verdict_problems(verdict, record, run_dir, (expected or {}).get(item['task_id']))
    measurement = run_dir / 'measurement.json'
    if not problems and measurement.exists():
        try:
            hidden = (read_json(measurement).get('correctness') or {}).get('hidden_status')
        except Exception:
            hidden = None
        if hidden != verdict.get('status'):
            problems.append(f"measurement.json says hidden {hidden!r}, the verdict says {verdict.get('status')!r} "
                            '(stale measurement: rerun `evaluation score`, which re-measures)')
    return out | {'state': 'invalid' if problems else 'scored', 'problems': problems}


def batch_status(batch_dir, study=None, plan=None):
    """Every scheduled attempt's state, the counts, and batch-level problems (orphan or duplicate verdicts)."""
    batch_dir = Path(batch_dir)
    plan = plan or read_json(batch_dir / 'plan.json')
    if study is None and batch_dir.parent.name == 'runs':   # the standard <study>/runs/<batch> layout
        study = batch_dir.parent.parent
    task_ids = {a['task_id'] for a in plan['attempts']}
    expected = expected_hidden(study, task_ids) if study else {}
    benchmark = (plan.get('benchmark') or {}).get('tasks') or {}
    problems = []
    for task_id, pinned in benchmark.items():
        built = expected.get(task_id)
        if not built or not built.get('judge_sha256'):
            problems.append(f'{task_id}: hidden-test provenance cannot be verified (no built suite in the study '
                            'tasks-manifest.json)')
        elif built.get('hidden_sha256') != pinned.get('hidden_sha256'):
            problems.append(f'{task_id}: the study built other hidden tests than the plan selected')
    exclusions = read_exclusions(batch_dir)
    attempts = []
    for item in plan['attempts']:
        state = attempt_state(batch_dir, item, expected=expected, exclusions=exclusions)
        attempts.append(state | {'item': item})
    run_ids = Counter(a['record']['run_id'] for a in attempts if a['record'])
    problems += [f'run_id {r} appears in {n} run directories' for r, n in run_ids.items() if n > 1]
    known = {a['record']['run_id'] for a in attempts if a['record']}
    orphans = sorted(p.stem for p in (batch_dir / 'eval').glob('*.json')
                     if not p.name.startswith('malformed-') and p.stem not in known) if (batch_dir / 'eval').is_dir() else []
    counts = Counter(a['state'] for a in attempts)
    return {'batch': str(batch_dir), 'scheduled': len(attempts), 'counts': {s: counts.get(s, 0) for s in STATES},
            'complete': all(a['state'] in DONE for a in attempts) and not problems,
            'problems': problems, 'orphan_verdicts': orphans, 'attempts': attempts}


def summary(status, limit=10):
    """JSON-friendly view of ``batch_status`` (no records)."""
    bad = [{'run': a['run_dir'].name, 'state': a['state'], 'problems': a['problems']}
           for a in status['attempts'] if a['state'] not in DONE]
    return {'batch': status['batch'], 'scheduled': status['scheduled'], 'counts': status['counts'],
            'complete': status['complete'], 'problems': status['problems'],
            'orphan_verdicts': len(status['orphan_verdicts']), 'not_done': bad[:limit],
            'not_done_total': len(bad)}
