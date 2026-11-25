"""The steps around the agent, all driven by one plan file.

The plan (``evaluation plan``) is the single source of which tasks, conditions and seeds a study runs. Every later
step reads it, so the task list is never typed twice:

    tasks     build or re-verify the plan's tasks (evaluation.tasks)
    judge     build the judge image, start judge-public, selftest (evaluation.judge)
    guidance  author the missing C/D guidance with ``guided_agent author``, then freeze it (bound to the plan)
    ready     every readiness check, without running anything (``readiness``)
    run       readiness, provenance binding, then ``guided_agent batch`` (the agent as a black box)
    score     hidden scoring after every attempt finished (evaluation.judge.score), then ``guided_agent measure``

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


def plan_manifests(plan):
    """The benchmark manifest a plan was built from (if any), as a path; checked against its recorded sha256."""
    benchmark = plan.get('benchmark') or {}
    if not benchmark.get('manifest'):
        return []
    path = Path(benchmark['manifest'])
    path = path if path.is_absolute() else taskslib.REPO / path
    if not path.is_file():
        raise FileNotFoundError(f'benchmark manifest {path} (recorded in the plan) does not exist')
    if planlib.sha256_file(path) != benchmark.get('manifest_sha256'):
        raise ValueError(f'{path} changed after the plan was built (sha256 differs from the plan)')
    return [path]


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
        raise RuntimeError(f'guidance still missing after authoring: {still} (failed requests are in the ledger; '
                           'rerun `evaluation guidance --yes` to author only these)')
    freeze = freeze_path(plan_path)
    if not freeze.exists():
        planlib.freeze(plan, freeze)
    problems = planlib.check(freeze, plan, study)
    if problems:
        raise RuntimeError(f'guidance does not match {freeze}: {problems}')
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


def _task_problems(plan, study):
    """Built tasks must be the selected ones: manifest hashes, the plan's benchmark record, bundle bytes."""
    problems = []
    record_path = Path(study) / 'tasks-manifest.json'
    built = planlib.read_json(record_path)['tasks'] if record_path.exists() else {}
    pinned = (plan.get('benchmark') or {}).get('tasks') or {}
    for task_id in plan_tasks(plan):
        entry = built.get(task_id)
        if not entry:
            continue
        if task_id in pinned and (entry.get('public_sha256'), entry.get('hidden_sha256')) != (
                pinned[task_id].get('public_sha256'), pinned[task_id].get('hidden_sha256')):
            problems.append(f'{task_id}: built tests differ from the plan benchmark')
        bundle = Path(study) / 'bundles' / task_id
        for name, digest in (entry.get('bundle_sha256') or {}).items():
            if not (bundle / name).is_file() or planlib.sha256_file(bundle / name) != digest:
                problems.append(f'{task_id}: agent bundle file {name} changed since `evaluation tasks`')
    return problems


def readiness(plan_path, study, *, services=True, ledger=None):
    """Every check that would make a batch invalid or fail on its first attempt. Nothing is run or written.

    ``problems`` block ``run``; ``warnings`` are reported only."""
    from . import budget as budgetlib, provenance
    plan = planlib.read_json(plan_path)
    study = Path(study)
    problems, warnings, checks = [], [], {}
    from guided_agent.integrity import validate_plan
    plan_problems = validate_plan(plan)
    unauthored = [p for p in plan_problems if p.endswith('does not exist') and 'guidance artifact' in p]
    problems += [f'plan: {p}' for p in plan_problems if p not in unauthored]
    if unauthored:
        problems.append(f'{len(unauthored)} scheduled C/D attempts have no guidance artifact yet '
                        '(run `evaluation guidance PLAN --yes`)')
    try:
        manifests = plan_manifests(plan)
        checks['benchmark_manifest'] = str(manifests[0]) if manifests else None
    except (OSError, ValueError) as error:
        problems.append(str(error))
    if not plan.get('benchmark'):
        warnings.append('the plan records no benchmark manifest (built before plan schema v2)')
    missing = [t for t in plan_tasks(plan) if not taskslib._complete(taskslib._paths(study, t))]
    if missing:
        problems.append(f'{len(missing)} tasks not built (run `evaluation tasks`), e.g. {missing[:3]}')
    problems += _task_problems(plan, study)
    if planlib.guidance_artifacts(plan):
        freeze = freeze_path(plan_path)
        if not freeze.exists():
            problems.append(f'no guidance freeze at {freeze} (run `evaluation guidance`)')
        else:
            problems += planlib.check(freeze, plan, study)
    git = provenance.git_state()
    checks['git'] = git
    if git['execution_paths_dirty']:
        (problems if plan.get('frozen') else warnings).append(
            'uncommitted changes in agent/judge/evaluation execution paths: commit them so the batch is reproducible '
            f'({git["dirty_paths"][:3]})')
    try:
        from local_agent.cli import verify
        result = verify(services=False)
        checks['frozen_files_verified'] = result['frozen_files_verified']
    except Exception as error:
        problems.append(f'local_agent verify failed: {type(error).__name__}: {error} (use the project Python 3.11 '
                        'environment with the recorded packages)')
    if services:
        if not ollama_up():  # the frozen runtime checks it before every attempt, B included
            problems.append(f'Ollama endpoint {ollama_endpoint()} not reachable (start the project Ollama server)')
        else:
            model = provenance.local_model(ollama_endpoint())
            checks['local_model'] = model
            if model['observed_digest'] != model['expected_digest']:
                problems.append(f"Ollama serves qwen3.5:9b with digest {model['observed_digest']}, expected the frozen "
                                f"{model['expected_digest']}")
        try:
            image = judgelib.image_id()
            checks['judge_image_id'] = image
            if image is None:
                problems.append(f'judge image {judgelib.judgekit().IMAGE} not built (run `evaluation judge`)')
        except Exception as error:  # no docker CLI at all
            problems.append(f'docker: {error}')
    if any(a['condition'] in ('B', 'C', 'D', 'E') for a in plan['attempts']):
        try:
            from guided_agent.providers import env_file, read_env
            config = read_env(env_file())
            if not config.get('FRONTIER_MODEL') or not config.get('OPENAI_API_KEY'):
                problems.append(f'{env_file()} lacks FRONTIER_MODEL or OPENAI_API_KEY')
            checks['frontier_model'] = config.get('FRONTIER_MODEL')
            del config
        except OSError:
            from guided_agent.providers import env_file
            problems.append(f'no frontier configuration file at {env_file()} (set CSC2108_ENV_FILE)')
        from guided_agent.common import ledger_path
        assessment = budgetlib.assess(plan_path, study, ledger or ledger_path(study))
        checks['budget'] = {k: assessment[k] for k in ('ceilings', 'used', 'room', 'fits_within_ceilings')} | {
            'expected_requests': assessment['scenarios']['expected']['requests']['total'],
            'expected_reservation_usd': assessment['scenarios']['expected']['reservation_usd']}
        if not assessment['fits_within_ceilings']['expected']:
            problems.append('the expected paid requests do not fit in the ledger ceilings (see `evaluation budget`)')
        elif not assessment['fits_within_ceilings']['high']:
            warnings.append('the high-usage scenario would exceed the ledger ceilings; some runs may end as '
                            'budget-exhausted infrastructure failures (see `evaluation budget`)')
    stored = batch_dir(plan, study) / 'provenance.json'
    if stored.exists() and services:
        current = provenance.capture(plan_path, study, judge_image_id=checks.get('judge_image_id'))
        changed = provenance.differences(provenance.binding(planlib.read_json(stored)), provenance.binding(current))
        if changed:
            problems.append(f'{stored} was recorded with another configuration ({", ".join(changed)}): start a new '
                            'batch instead of resuming this one')
        checks['resume'] = True
    return {'ready': not problems, 'problems': problems, 'warnings': warnings, 'checks': checks}


def preflight(plan_path, study):
    """Problems that would make a batch invalid or fail on its first attempt. Empty means ready."""
    return readiness(plan_path, study)['problems']


def run(plan_path, study, backend='auto'):
    from . import provenance
    from .judge import utc_now
    report = readiness(plan_path, study)
    if report['problems']:
        raise RuntimeError('not ready: ' + '; '.join(report['problems']))
    plan = planlib.read_json(plan_path)
    record = provenance.capture(plan_path, study, judge_image_id=report['checks'].get('judge_image_id'))
    problems = provenance.bind(batch_dir(plan, study), record, utc_now())
    if problems:
        raise RuntimeError('; '.join(problems))
    return agent(study, 'batch', Path(plan_path).resolve(), backend=backend)


def score(plan_path, study, backend='auto', measure=True, allow_incomplete=False, rescore_stale=False):
    from . import validate
    plan = planlib.read_json(plan_path)
    directory = batch_dir(plan, study)
    if not (directory / 'plan.json').exists():
        raise RuntimeError(f'{directory} has no plan.json: nothing of this plan has run yet')
    results = judgelib.score(directory, study, plan=planlib.read_json(directory / 'plan.json'),
                             allow_incomplete=allow_incomplete, rescore_stale=rescore_stale)
    counts = defaultdict(int)
    for outcome in results.values():
        counts[outcome.get('status')] += 1
    if measure:  # refresh every run's measurement.json with its hidden verdict
        code = agent(study, 'measure', directory, backend=backend)
        if code:
            raise RuntimeError(f'guided_agent measure exited with {code}')
    status = validate.summary(validate.batch_status(directory, study))
    return {'batch': str(directory), 'scored': len(results), 'status': dict(counts), 'completeness': status}
