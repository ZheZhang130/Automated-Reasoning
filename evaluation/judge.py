"""The judge side of the evaluation: the judge image, the per-study judge containers, and hidden scoring.

* ``build_image``: ``docker build -t csc2108-judge:<version> judge/`` (no shell script, so it runs in PowerShell too).
* ``client``: one judge-public and one judge-hidden container per study root. The names match the ones
  ``guided_agent`` uses while running, so the agent reuses the judge-public container started here.
* ``score``: hidden scoring after every attempt of a batch finished. Writes ``<batch>/eval/<run_id>.json``.
  judge-hidden is started only here; the agent never talks to it.
"""
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .tasks import REPO, read_json, write_json

JUDGE_DIR = REPO / 'judge'
CONTAINER_NAME = 'csc2108re-judge-{suite}-{suffix}'  # the agent's naming (guided_agent.backend.judge_client)


def judgekit():
    if str(JUDGE_DIR) not in sys.path:
        sys.path.insert(0, str(JUDGE_DIR))
    import judgekit as module
    return module


def utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def container_name(study, suite):
    suffix = hashlib.sha256(str(Path(study).resolve()).encode()).hexdigest()[:8]
    return CONTAINER_NAME.format(suite=suite, suffix=suffix)


def client(study, suite):
    return judgekit().Judge(suite, root=Path(study) / 'judge', name=container_name(study, suite))


def image_id():
    """ID of the local judge image, or None when it has not been built."""
    kit = judgekit()
    proc = subprocess.run([kit.docker_bin(), 'image', 'inspect', '-f', '{{.Id}}', kit.IMAGE], capture_output=True)
    return proc.stdout.decode().strip() if proc.returncode == 0 else None


def build_image(force=False):
    """Build the judge image from judge/Dockerfile (base image pinned by digest). Returns its ID."""
    kit = judgekit()
    existing = image_id()
    if existing and not force:
        return {'image': kit.IMAGE, 'image_id': existing, 'built': False}
    subprocess.run([kit.docker_bin(), 'build', '-t', kit.IMAGE, str(JUDGE_DIR)], check=True)
    return {'image': kit.IMAGE, 'image_id': image_id(), 'built': True}


def up(study):
    """Start judge-public for the study's tasks and run the container selftest."""
    judge = client(study, 'public')
    info = judge.up()
    selftest = judge.selftest()
    return {'container': judge.name, 'image': judgekit().IMAGE, 'image_id': judge._image_id(),
            'n_tasks': info.get('n_tasks'), 'tests_sha256': info.get('tests_sha256'),
            'selftest_ok': bool(selftest.get('ok'))}


def down(study):
    for suite in ('public', 'hidden'):
        client(study, suite).down()


def score_run(judge, result_path, judge_tests_sha256):
    """The hidden verdict for one finished run, in the schema the measurement and metrics read.

    Same fields as ``guided_agent evaluate`` plus ``submission_sha256`` (the run record's), which binds the verdict to
    the record it was written for."""
    record = read_json(result_path)
    run_id = record['run_id']
    record['task_id'], record['condition']  # a record without them is malformed
    submission = result_path.parent / 'submission.py'
    if record.get('submission_sha256') is None or not submission.exists():
        outcome = {'status': 'missing_submission', 'verdict': 'MISSING'}
    else:
        code = submission.read_bytes()
        if hashlib.sha256(code).hexdigest() != record['submission_sha256']:
            outcome = {'status': 'infrastructure_error', 'error': 'submission hash mismatch'}
        else:
            result = judge.run(record['task_id'], code)
            outcome = {k: result.get(k) for k in ('status', 'passed', 'total', 'verdict_counts', 'judge_version',
                                                   'tests_sha256', 'code_sha256', 'error')}
    return run_id, outcome | {'run_id': run_id, 'task_id': record['task_id'], 'condition': record['condition'],
                              'suite': 'hidden', 'judge_tests_sha256': judge_tests_sha256,
                              'submission_sha256': record.get('submission_sha256'), 'evaluated_utc': utc_now()}


class ScoringRefused(RuntimeError):
    """The batch is not ready to score, or a stored verdict no longer matches its run."""


def score(batch_dir, study, judge=None, *, plan=None, allow_incomplete=False, rescore_stale=False):
    """Score every finished run of a batch on the hidden tests. Returns run_id -> outcome.

    * With a plan (``<batch>/plan.json`` when present), scoring is refused while any scheduled attempt has not
      finished (``allow_incomplete`` scores what exists; such a batch can only give a preliminary report).
    * A stored verdict is reused only while it still matches its run (submission hash, hidden-test digest, judge
      version, identity). A stale one stops scoring with a list (``rescore_stale`` moves it to ``eval/stale/`` and
      scores the run again).
    * A malformed or partial record is not scored; its reason is written instead.
    * Every verdict is written atomically, so an interrupted scoring run resumes where it stopped."""
    from . import validate
    batch_dir = Path(batch_dir)
    if plan is None and (batch_dir / 'plan.json').exists():
        plan = read_json(batch_dir / 'plan.json')
    if plan is not None:
        status = validate.batch_status(batch_dir, study, plan)
        waiting = [a['run_dir'].name for a in status['attempts'] if a['state'] in ('not_executed', 'incomplete')]
        if waiting and not allow_incomplete:
            raise ScoringRefused(f'{len(waiting)} scheduled attempts have not finished (e.g. {waiting[:3]}); finish '
                                 'the batch first (rerun `evaluation run`), or pass --allow-incomplete for a '
                                 'preliminary score')
    expected = validate.expected_hidden(study)
    judge = judge or client(study, 'hidden')
    info = judge.up()
    eval_dir = batch_dir / 'eval'
    eval_dir.mkdir(exist_ok=True)
    results, stale = {}, []
    for result_path in sorted(batch_dir.glob('*/result.json')):
        if '.incomplete-' in result_path.parent.name:
            continue
        name = result_path.parent.name
        try:
            record = read_json(result_path)
            run_id = record['run_id']
            cached = eval_dir / f'{run_id}.json'
            if cached.exists():
                verdict = read_json(cached)
                problems = validate.verdict_problems(verdict, record, result_path.parent,
                                                     expected.get(record.get('task_id')))
                # a recorded submission-hash mismatch stays a mismatch: rescoring cannot change it (the report marks
                # such runs invalid); every other problem means the verdict no longer describes the run
                problems = [p for p in problems if 'tampered or replaced submission' not in p]
                if not problems:
                    results[run_id] = verdict
                    continue
                if not rescore_stale:
                    stale.append({'run_id': run_id, 'problems': problems})
                    continue
                (eval_dir / 'stale').mkdir(exist_ok=True)
                cached.replace(eval_dir / 'stale' / f"{run_id}.{utc_now().replace(':', '')}.json")
            run_id, outcome = score_run(judge, result_path, info.get('tests_sha256'))
        except Exception as error:
            outcome = {'status': 'malformed_record', 'error': f'{type(error).__name__}: {error}', 'run_dir': name,
                       'suite': 'hidden', 'evaluated_utc': utc_now()}
            write_json(eval_dir / f'malformed-{name}.json', outcome)
            results['malformed-' + name] = outcome
            continue
        write_json(eval_dir / f'{run_id}.json', outcome)
        results[run_id] = outcome
    if stale:
        raise ScoringRefused(f'{len(stale)} stored verdicts no longer match their runs, e.g. {stale[:2]}; '
                             'investigate, then rerun with --rescore-stale to move them to eval/stale/ and rescore')
    return results
