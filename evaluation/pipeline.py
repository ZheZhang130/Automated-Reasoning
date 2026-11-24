"""The steps around the agent, all driven by one plan file.

The plan (``evaluation plan``) is the single source of which tasks, conditions and seeds a study runs. Every later
step reads it, so the task list is never typed twice:

    tasks     build or re-verify the plan's tasks (evaluation.tasks)
    judge     build the judge image, start judge-public, selftest (evaluation.judge)
    guidance  author the missing C/D guidance with ``guided_agent author``, then freeze it
    run       preflight, then ``guided_agent batch`` (the agent as a black box)
    score     hidden scoring (evaluation.judge.score), then ``guided_agent measure``

The agent's own commands run as subprocesses with an explicit ``--study``, so they execute Sam's code unchanged.
"""
import os
import subprocess
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

from . import judge as judgelib, plan as planlib, tasks as taskslib


def plan_tasks(plan):
    return list(dict.fromkeys(a['task_id'] for a in plan['attempts']))


def batch_dir(plan, study):
    return Path(study) / 'runs' / plan['batch']


def freeze_path(plan_path):
    return Path(plan_path).with_suffix('.freeze.json')


def agent(study, *args, backend='auto'):
    """``python -m guided_agent --study STUDY --backend BACKEND ARGS...`` in the repository root."""
    command = [sys.executable, '-m', 'guided_agent', '--study', str(study), '--backend', backend, *map(str, args)]
    return subprocess.run(command, cwd=taskslib.REPO).returncode


def parse_guidance(path):
    """<study>/guidance/<label>/<task_id>.<prompt_id>.<provider>.json -> (label, task_id, prompt_id, provider)."""
    path = Path(path)
    task_id, prompt_id, provider = path.name[:-len('.json')].rsplit('.', 2)
    return path.parent.name, task_id, prompt_id, provider


def missing_guidance(plan, study):
    """(label, prompt_id, provider) -> task IDs whose guidance artifact the plan needs and does not exist yet."""
    groups = defaultdict(list)
    for path in planlib.guidance_artifacts(plan):
        label, task_id, prompt_id, provider = parse_guidance(path)
        expected = Path(study).resolve() / 'guidance' / label / Path(path).name
        if Path(path).resolve() != expected:
            raise ValueError(f'{path}: guidance outside this study root ({study})')
        if not Path(path).is_file():
            groups[(label, prompt_id, provider)].append(task_id)
    return dict(groups)


def guidance(plan_path, study, *, yes=False, backend='auto'):
    """Author what is missing (paid when provider is api: needs ``yes``), then write the freeze once."""
    plan = planlib.read_json(plan_path)
    missing = missing_guidance(plan, study)
    requests = sum(len(t) for t in missing.values())
    summary = {'missing': {f'{label} {prompt} {provider}': len(t) for (label, prompt, provider), t in missing.items()},
               'requests': requests}
    if missing and not yes:
        return summary | {'authored': False, 'note': 'rerun with --yes to author them (one request per artifact)'}
    for (label, prompt_id, provider), task_ids in missing.items():
        code = agent(study, 'author', '--provider', provider, '--prompt-id', prompt_id, '--label', label,
                     '--purpose', f"{plan['batch']} guidance", '--tasks', *task_ids, backend=backend)
        if code:
            raise RuntimeError(f'guided_agent author exited with {code}')
    still = missing_guidance(plan, study)
    if still:
        raise RuntimeError(f'guidance still missing after authoring: {still}')
    freeze = freeze_path(plan_path)
    if not freeze.exists():
        planlib.freeze(plan, freeze)
    problems = planlib.check(freeze)
    if problems:
        raise RuntimeError(f'guidance changed since {freeze}: {problems}')
    return summary | {'authored': bool(missing), 'freeze': str(freeze),
                      'artifacts': len(planlib.guidance_artifacts(plan))}


def ollama_endpoint():
    """The project's dedicated Ollama endpoint, as local_agent resolves it."""
    return os.environ.get('CSC2108_OLLAMA_ENDPOINT', 'http://127.0.0.1:11435').rstrip('/')


def ollama_up(endpoint=None, timeout=5):
    try:
        with urllib.request.urlopen((endpoint or ollama_endpoint()) + '/api/tags', timeout=timeout):
            return True
    except Exception:
        return False


def preflight(plan_path, study):
    """Problems that would make a batch invalid or fail on its first attempt. Empty means ready."""
    plan = planlib.read_json(plan_path)
    problems = []
    missing = [t for t in plan_tasks(plan) if not taskslib._complete(taskslib._paths(Path(study), t))]
    if missing:
        problems.append(f'{len(missing)} tasks not built (run `evaluation tasks`), e.g. {missing[:3]}')
    if planlib.guidance_artifacts(plan):
        freeze = freeze_path(plan_path)
        if not freeze.exists():
            problems.append(f'no guidance freeze at {freeze} (run `evaluation guidance`)')
        else:
            problems += planlib.check(freeze)
    if not ollama_up():  # the frozen runtime checks it before every attempt, B included
        problems.append(f'Ollama endpoint {ollama_endpoint()} not reachable (start the project Ollama server)')
    try:
        if judgelib.image_id() is None:
            problems.append(f'judge image {judgelib.judgekit().IMAGE} not built (run `evaluation judge`)')
    except Exception as error:  # no docker CLI at all
        problems.append(f'docker: {error}')
    return problems


def run(plan_path, study, backend='auto'):
    problems = preflight(plan_path, study)
    if problems:
        raise RuntimeError('not ready: ' + '; '.join(problems))
    return agent(study, 'batch', Path(plan_path).resolve(), backend=backend)


def score(plan_path, study, backend='auto', measure=True):
    plan = planlib.read_json(plan_path)
    directory = batch_dir(plan, study)
    results = judgelib.score(directory, study)
    counts = defaultdict(int)
    for outcome in results.values():
        counts[outcome.get('status')] += 1
    if measure:  # refresh every run's measurement.json with its hidden verdict
        code = agent(study, 'measure', directory, backend=backend)
        if code:
            raise RuntimeError(f'guided_agent measure exited with {code}')
    return {'batch': str(directory), 'scored': len(results), 'status': dict(counts)}
