"""Experiment provenance: bind an official batch to its exact configuration.

``capture`` records what the batch runs with (git state, benchmark and task hashes, dataset, plan, guidance freeze,
judge image, local model, frontier model, agent profile and budgets, prompt and template hashes, seeds and sampling,
host and hardware cohort, pricing assumptions, software versions). ``evaluation run`` writes it to
``<batch>/provenance.json`` before the first attempt and, on every resume, refuses to continue when a *binding*
field differs (``BINDING``). Fields that may legitimately change between sessions (time, git commit of a docs-only
change, ledger state) are recorded per session in ``<batch>/provenance-sessions.jsonl`` but do not bind.

``compatibility`` is the subset that must agree before batches (a main batch and its rerun batch) are pooled.
"""
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from . import plan as planlib, pricing
from .tasks import REPO, read_json, write_json

SCHEMA = 'csc2108-experiment-provenance-v1'
# Source paths whose bytes determine what an attempt does (tests excluded). Their combined hash is the code fingerprint.
EXECUTION_PATHS = ('guided_agent', 'local_agent', 'local_eval_v2', 'local_baseline', 'local_optimization',
                   'judge/container', 'judge/judgekit', 'judge/Dockerfile', 'planning_frontier', 'contract_frontier',
                   'evaluation/pipeline.py')
PACKAGES = ('mini-swe-agent', 'litellm', 'pydantic', 'pydantic_core', 'numpy', 'requests')
BINDING = ('plan_sha256', 'benchmark', 'built_tasks_sha256', 'dataset', 'guidance_freeze_sha256', 'code_fingerprint',
           'judge', 'local_model', 'frontier', 'agent', 'prompts', 'seeds', 'hardware_cohort', 'software')
COMPATIBILITY = ('benchmark_manifest_sha256', 'dataset', 'code_fingerprint', 'judge', 'local_model', 'frontier',
                 'agent', 'prompts', 'hardware_cohort', 'software')


def _git(*args):
    try:
        proc = subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True, encoding='utf-8')
        return proc.stdout.strip() if proc.returncode == 0 else None
    except OSError:
        return None


def execution_files():
    listed = _git('ls-files', '--', *EXECUTION_PATHS) or ''
    return sorted(p for p in listed.splitlines() if p and '/test_' not in f'/{p}' and not Path(p).name.startswith('test_')
                  and '/fixtures/' not in p)


def code_fingerprint():
    """Hash of the execution sources, line-ending-insensitive (a Windows and a macOS checkout of the same commit agree;
    the 38 frozen files are additionally verified byte for byte by ``local_agent verify`` in every attempt)."""
    files = {}
    for rel in execution_files():
        path = REPO / rel
        if path.is_file():
            files[rel] = hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    return {'sha256': planlib.canonical_sha256(files), 'files': len(files)}


def git_state():
    dirty = _git('status', '--porcelain', '--', *EXECUTION_PATHS)
    return {'commit': _git('rev-parse', 'HEAD'), 'branch': _git('rev-parse', '--abbrev-ref', 'HEAD'),
            'execution_paths_dirty': bool(dirty), 'dirty_paths': (dirty or '').splitlines()[:20],
            'worktree_status_lines': len((_git('status', '--porcelain') or '').splitlines())}


def gpu_name():
    try:
        proc = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=10)
        return proc.stdout.strip() or None if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def hardware_cohort(cohort_label=None):
    """What makes timing comparable: OS, architecture, host and GPU (plus the plan's cohort label)."""
    gpu = gpu_name()
    if gpu is None and platform.system() == 'Darwin':
        gpu = 'apple-silicon:' + platform.machine()
    return {'label': cohort_label, 'system': platform.system(), 'machine': platform.machine(), 'node': platform.node(),
            'gpu': gpu}


def versions():
    found = {}
    for name in PACKAGES:
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            found[name] = None
    return {'python': sys.version.split()[0], 'packages': found}


def frontier_config(plan):
    from guided_agent.providers import env_file, read_env
    try:
        model = read_env(env_file()).get('FRONTIER_MODEL')   # the model name only; the key is never read here
    except OSError:
        model = None
    b = next((a.get('coder') for a in plan['attempts'] if a['condition'] == 'B'), None) or {}
    e = next((a.get('diagnosis') for a in plan['attempts'] if a['condition'] == 'E'), None) or {}
    return {'requested_model': model, 'b_provider': b.get('provider'), 'b_max_requests': b.get('max_requests'),
            'e_provider': e.get('provider'), 'e_timeout_seconds': e.get('timeout', 300),
            'reasoning_effort': 'medium', 'max_completion_tokens': 8000}


def agent_config():
    from guided_agent import agent_config as ac, common
    profiles = read_json(REPO / 'local_optimization/profiles.json')
    selection = read_json(REPO / 'local_optimization/final_selection.json')
    agent_id, definition, digest = ac.resolve(ac.PRIMARY_AGENT)
    return {'agent': agent_id, 'definition_sha256': digest, 'profile': common.PROFILE,
            'profile_config': profiles[common.PROFILE],
            'budgets': {'actions': common.ACTIONS, 'repair_groups': common.REPAIRS, 'coding_seconds': common.SECONDS,
                        'request_seconds': 180},
            'frozen_files': len(selection['runtime_sha256']),
            'selection_sha256': hashlib.sha256((REPO / 'local_optimization/final_selection.json').read_bytes()).hexdigest()}


def prompt_hashes():
    from guided_agent import guidance
    sha = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()   # noqa: E731
    return {'prompts': {k: sha(v[1]) for k, v in sorted(guidance.PROMPTS.items())},
            'injection': {f'{k}/{kind}': sha(t) for k, v in sorted(guidance.INJECTION.items())
                          for kind, t in sorted(v.items())},
            'diagnosis_delivery': {k: sha(v) for k, v in sorted(guidance.DIAGNOSIS_DELIVERY.items())}}


def local_model(endpoint=None):
    selection = read_json(REPO / 'local_optimization/final_selection.json')
    observed = None
    try:
        import urllib.request
        url = (endpoint or os.environ.get('CSC2108_OLLAMA_ENDPOINT', 'http://127.0.0.1:11435')).rstrip('/') + '/api/tags'
        with urllib.request.urlopen(url, timeout=5) as response:
            observed = next((m.get('digest') for m in json.load(response).get('models', [])
                             if m.get('name') == 'qwen3.5:9b'), None)
    except Exception:
        observed = None
    return {'model': 'qwen3.5:9b', 'expected_digest': selection['model_digest'], 'observed_digest': observed}


def built_tasks_sha256(study, task_ids):
    path = Path(study) / 'tasks-manifest.json'
    if not path.exists():
        return None
    tasks = read_json(path)['tasks']
    return planlib.canonical_sha256({t: {k: tasks.get(t, {}).get(k) for k in ('public_sha256', 'hidden_sha256',
                                                                                 'hidden_judge_sha256', 'bundle_sha256',
                                                                                 'statement_sha256')}
                                     for t in sorted(task_ids)})


def capture(plan_path, study, *, judge_image_id=None, ledger=None):
    plan = planlib.read_json(plan_path)
    study = Path(study)
    task_ids = sorted({a['task_id'] for a in plan['attempts']})
    freeze = Path(plan_path).with_suffix('.freeze.json')
    tasks_manifest = read_json(study / 'tasks-manifest.json') if (study / 'tasks-manifest.json').exists() else {}
    from .validate import JUDGE_VERSION
    benchmark = plan.get('benchmark') or {}
    ledger_data = read_json(ledger) if ledger and Path(ledger).exists() else None
    from guided_agent import providers
    cohort = hardware_cohort(plan.get('cohort'))
    model = local_model()
    record = {
        'schema': SCHEMA, 'batch': plan['batch'],
        'git': git_state(), 'code_fingerprint': code_fingerprint(),
        'plan': str(Path(plan_path).resolve()), 'plan_sha256': planlib.plan_sha256(plan),
        'benchmark': {k: benchmark.get(k) for k in ('manifest', 'manifest_name', 'manifest_sha256', 'tasks_sha256')},
        'benchmark_manifest_sha256': benchmark.get('manifest_sha256'),
        'built_tasks_sha256': built_tasks_sha256(study, task_ids),
        'dataset': {'name': 'livecodebench/code_generation_lite', 'revision': tasks_manifest.get('hf_revision'),
                    'shard': 'test6.jsonl', 'shard_sha256': tasks_manifest.get('shard_sha256')},
        'guidance_freeze': str(freeze) if freeze.exists() else None,
        'guidance_freeze_sha256': planlib.sha256_file(freeze) if freeze.exists() else None,
        'judge': {'version': JUDGE_VERSION, 'image': f'csc2108-judge:{JUDGE_VERSION}', 'image_id': judge_image_id},
        'local_model': {k: v for k, v in model.items() if k != 'observed_digest'},
        'local_model_observed_digest': model['observed_digest'],
        'frontier': frontier_config(plan), 'agent': agent_config(), 'prompts': prompt_hashes(),
        'seeds': {'seeds': plan.get('seeds') or sorted({a['seed'] for a in plan['attempts']}),
                  'order': (plan.get('order') or {}).get('scheme', 'fixed'),
                  'sampling': read_json(REPO / 'local_optimization/profiles.json')['heredoc-v6-16k-common']},
        'hardware_cohort': cohort, 'host': {'release': platform.release(), 'processor': platform.processor()},
        'software': versions(),
        'pricing': {'research_cost': pricing.assumptions(),
                    'reservation': {'price_conservative_per_1m': providers.PRICE_CONSERVATIVE,
                                    'code_ceiling': {'max_requests': providers.MAX_REQUESTS, 'max_usd': providers.MAX_USD},
                                    'ledger_ceiling': {k: (ledger_data or {}).get(k) for k in ('max_requests', 'max_usd')}}},
    }
    return record


def binding(record):
    return {k: record.get(k) for k in BINDING}


def differences(old, new, keys=BINDING):
    return sorted(k for k in keys if old.get(k) != new.get(k))


def bind(batch_dir, record, utc):
    """Write ``provenance.json`` on the first session; on later sessions refuse a changed binding field."""
    batch_dir = Path(batch_dir)
    path = batch_dir / 'provenance.json'
    if path.exists():
        stored = read_json(path)
        changed = differences(binding(stored), binding(record))
        if changed:
            return [f'{path} was recorded with another configuration ({", ".join(changed)}); resuming would mix '
                    'configurations in one batch: start a new batch (new --batch name) instead']
    else:
        write_json(path, record | {'first_session_utc': utc})
    batch_dir.mkdir(parents=True, exist_ok=True)
    with (batch_dir / 'provenance-sessions.jsonl').open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps({'utc': utc, 'git': record['git'],
                                 'binding_sha256': planlib.canonical_sha256(binding(record)),
                                 'local_model_observed_digest': record.get('local_model_observed_digest')}) + '\n')
    return []


def compatible(records):
    """Problems pooling batches whose provenance disagrees on a compatibility field (empty: poolable)."""
    records = [(name, r) for name, r in records if r]
    if len(records) < 2:
        return []
    base_name, base = records[0]
    problems = []
    for name, record in records[1:]:
        diff = differences(base, record, COMPATIBILITY)
        if diff:
            problems.append(f'{name} and {base_name} differ in {", ".join(diff)}; they are different cohorts '
                            'and are not pooled in an official report')
    return problems
