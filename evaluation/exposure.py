"""Historical task exposure: which LiveCodeBench problems earlier development work already ran the agent on.

The registry (``evaluation/data/exposure-registry.json``) is built once from recorded evidence and committed, so the
benchmark selection and the report read the same frozen classification:

* **git sources**: task lists read *structurally* (``tasks[*]`` of a manifest, ``attempts[*]`` of a plan, rows of a
  run list) from the development commit ``900d33f`` (``feat/csc2108-contract-diagnosis-pass2``, an ancestor of this
  branch, which holds every earlier experiment). Files are never grepped as a whole, because several of them embed
  exclusion lists of *other* tasks.
* **local sources**: names of run directories found under the reference host's study roots (``--study-roots``);
  only directory names are read, never outputs, and only root names (no machine paths) are recorded.
* **manual sources**: exposure documented only in prose (commit messages, docs).

Classes (first that applies): ``development`` (an agent/condition development experiment ran it),
``selection_holdout`` (a configuration-selection, screening or held-out validation experiment ran it),
``other_scored`` (another previously scored list, an earlier benchmark evaluation, or an executed run directory),
``uncertain`` (mentioned as used, but no run record), ``none_known`` (absent from every source).

``none_known`` means *potentially unseen*, never *verified unseen*: the registry only covers what this repository and
the reference host recorded (teammates' machines and model pre-training data are not covered).
"""
import fnmatch
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from .tasks import REPO, read_json, write_json

REGISTRY = REPO / 'evaluation/data/exposure-registry.json'
SCHEMA = 'csc2108-exposure-registry-v1'
DEV_COMMIT = '900d33f7c10c6cf24dc647e12033b9dffc9024c2'   # FINALIZATION_MANIFEST.json development_commit
CLASSES = ('development', 'selection_holdout', 'other_scored', 'uncertain', 'none_known')
EXPOSED = frozenset({'development', 'selection_holdout', 'other_scored'})
DEFINITIONS = {
    'development': 'the agent ran on the task in an agent or condition development experiment (outcomes observed)',
    'selection_holdout': 'the agent ran on the task in a configuration-selection, screening or held-out validation '
                         'experiment',
    'other_scored': 'the task is in another previously scored list (an earlier benchmark evaluation or a scored '
                    'union) or has an executed run directory on the reference host',
    'uncertain': 'documented as used, but no run record exists',
    'none_known': 'absent from every registry source: potentially unseen, not verified unseen',
}

# (path pattern at DEV_COMMIT, extractor, class, experiment)
GIT_SOURCES = [
    ('evidence/local_baseline/lcb_manifest.json', 'tasks', 'development', 'mini-SWE local pilot'),
    ('evidence/local_eval_v2/evaluation_manifest.json', 'tasks', 'other_scored', 'local evaluation v2 benchmark'),
    ('local_optimization/development_manifest.json', 'tasks', 'development', 'Qwen local optimization: development split'),
    ('local_optimization/selection_manifest.json', 'tasks', 'selection_holdout', 'Qwen local optimization: selection split'),
    ('local_optimization/heldout_manifest.json', 'tasks', 'selection_holdout', 'Qwen local optimization: held-out split'),
    ('evidence/agent_delivery_pilot/manifest.json', 'tasks', 'development', 'agent delivery pilot'),
    ('evidence/one_shot_ablation/manifest.json', 'tasks', 'development', 'one-shot ablation'),
    ('evidence/agent_delivery_pilot/future_exclusions.json', 'list:exclude_from_future_fresh_validation',
     'other_scored', 'previously scored union (75 IDs)'),
    ('reasoning_effectiveness/evidence/plans/*.json', 'attempts', 'development', 'reasoning effectiveness pass 1'),
    ('reasoning_effectiveness/pass2/evidence/plans/dev*.json', 'attempts', 'development', 'reasoning effectiveness pass 2'),
    ('reasoning_effectiveness/pass2/evidence/plans/b-*.json', 'attempts', 'development', 'reasoning effectiveness pass 2'),
    ('reasoning_effectiveness/pass2/evidence/plans/val*.json', 'attempts', 'selection_holdout',
     'reasoning effectiveness pass 2 validation cohort'),
    ('reasoning_effectiveness/pass3/evidence/plans/*.json', 'attempts', 'development', 'reasoning effectiveness pass 3'),
    ('reasoning_effectiveness/pass3/evidence/runs.json', 'rows', 'development', 'reasoning effectiveness pass 3'),
    ('reasoning_effectiveness/pass4/plans/p4-screen-*.json', 'attempts', 'selection_holdout',
     'pass 4 agent-configuration screening'),
    ('reasoning_effectiveness/pass4/plans/p4-[!s]*.json', 'attempts', 'development', 'reasoning effectiveness pass 4'),
]
MANUAL_SOURCES = [
    {'class': 'development', 'experiment': 'evaluation pipeline pilot (judge/manifests/pilot.json)',
     'manifest': 'judge/manifests/pilot.json',
     'evidence': 'commit 0409ddd: "re-scoring the 80 pilot runs reproduces their eval/ files"; the run records are '
                 'not in git'},
    {'class': 'uncertain', 'experiment': 'orchestration smoke example', 'tasks': ['lcb-atcoder-abc393_a'],
     'evidence': 'guided_agent/selection.py TEAMMATE_USED and orchestration/MERGED_INTEGRATION.md (a documented '
                 'command; the committed orchestration runs use only the synthetic fixture)'},
]
_RUN_DIR = re.compile(r'(?:lcb-)?((?:atcoder|leetcode)-[a-z]*\d+(?:_[a-z0-9]+)?)', re.I)


def normalize(task_id):
    """Every historical form ('atcoder-abc390_a', 'lcb-atcoder-abc390_a') -> the judge form 'lcb-atcoder-abc390_a'."""
    task_id = str(task_id).strip()
    return task_id if task_id.startswith('lcb-') else 'lcb-' + task_id


def _git(*args):
    proc = subprocess.run(['git', *args], cwd=REPO, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f'git {" ".join(args)}: {proc.stderr.decode(errors="replace").strip()}')
    return proc.stdout.decode('utf-8')


def _extract(data, how):
    if how == 'tasks':
        return [t['task_id'] for t in data['tasks']]
    if how == 'attempts':
        return [a['task_id'] for a in data['attempts']]
    if how == 'rows':
        return [r['task_id'] for r in data]
    if how.startswith('list:'):
        return list(data[how[5:]])
    raise ValueError(how)


def scan_study_roots(roots):
    """task_id -> sorted root names, from run directory names only (never reads run outputs)."""
    found = defaultdict(set)
    for root in map(Path, roots):
        if not root.is_dir():
            continue
        for dirpath, dirnames, _ in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            for name in dirnames:
                match = _RUN_DIR.search(name)
                if match and not name.startswith('agent-'):
                    found[normalize(match.group(1))].add(root.name)
            # run directories sit a few levels down; never descend into agent outputs or test suites
            dirnames[:] = [d for d in dirnames if depth < 5 and not d.startswith('agent-')
                           and d not in ('judge', 'bundles', 'hidden', 'tasks', '.venv', 'node_modules')]
    return {t: sorted(v) for t, v in found.items()}


def build(study_roots=(), commit=DEV_COMMIT):
    files = _git('ls-tree', '-r', '--name-only', commit).splitlines()
    tasks = defaultdict(list)
    git_sources = []
    for pattern, how, category, experiment in GIT_SOURCES:
        matched = [f for f in files if fnmatch.fnmatchcase(f, pattern)]
        if not matched:
            raise RuntimeError(f'exposure source {pattern} not found at {commit[:7]}')
        for path in matched:
            ids = sorted({normalize(t) for t in _extract(json.loads(_git('show', f'{commit}:{path}')), how)})
            blob = _git('rev-parse', f'{commit}:{path}').strip()
            git_sources.append({'commit': commit, 'path': path, 'blob': blob, 'class': category,
                                'experiment': experiment, 'n_tasks': len(ids)})
            for t in ids:
                tasks[t].append({'class': category, 'experiment': experiment, 'evidence': f'{commit[:7]}:{path}'})
    manual = []
    for source in MANUAL_SOURCES:
        ids = source.get('tasks') or [e['task_id'] for e in read_json(REPO / source['manifest'])['tasks']]
        manual.append({k: v for k, v in source.items() if k != 'tasks'} | {'tasks': sorted(ids)})
        for t in ids:
            tasks[normalize(t)].append({'class': source['class'], 'experiment': source['experiment'],
                                        'evidence': source['evidence']})
    local = scan_study_roots(study_roots)
    for t, roots in local.items():
        tasks[t].append({'class': 'other_scored', 'experiment': 'executed run directory on the reference host',
                         'evidence': 'study roots: ' + ', '.join(roots)})
    return {
        'schema': SCHEMA, 'definitions': DEFINITIONS,
        'git_sources': git_sources, 'manual_sources': manual,
        'local_sources': {'description': 'run directory names under the Windows reference host data root',
                          'roots': sorted({Path(r).name for r in study_roots}), 'n_tasks': len(local)},
        'limitations': [
            'none_known means potentially unseen: only this repository and the reference host were searched',
            'teammates may have used tasks on other machines without a committed record',
            'model pre-training data may contain the problems (contest dates 2025-01 to 2025-04)',
        ],
        'tasks': {t: {'class': classify_sources(s), 'sources': s} for t, s in sorted(tasks.items())},
    }


def classify_sources(sources):
    classes = {s['class'] for s in sources}
    return next((c for c in CLASSES if c in classes), 'none_known')


def load(path=REGISTRY):
    data = read_json(path)
    if data.get('schema') != SCHEMA:
        raise ValueError(f'{path}: not a {SCHEMA} file')
    return data


def classify(task_id, registry=None):
    registry = registry or load()
    entry = registry['tasks'].get(normalize(task_id))
    if not entry:
        return {'class': 'none_known', 'sources': []}
    return entry


def subgroup(exposure_class):
    """Reporting subgroup: development-exposed, potentially unseen, or uncertain."""
    if exposure_class in EXPOSED:
        return 'exposed'
    return 'potentially_unseen' if exposure_class == 'none_known' else 'uncertain'


def write(registry, path=REGISTRY):
    write_json(path, registry)
    return path
