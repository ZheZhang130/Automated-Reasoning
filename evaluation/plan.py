"""Build the benchmark batch plan from a judge manifest, and freeze the C/D guidance it uses.

A plan is what ``python -m guided_agent batch`` runs. This module only writes JSON; it never runs a model.

* Every attempt gets ``variant = s<seed>``, so run directories never collide across seeds.
* Attempts are ordered seed -> task -> condition, so a batch stopped part-way still holds whole
  (task, seed) blocks across all conditions, which is what the paired analysis needs.
* C and D point at the write-once guidance artifacts produced by ``guided_agent author``; ``freeze`` hashes
  them before the first attempt and ``check`` proves later that none changed.
"""
import hashlib
import json
from pathlib import Path

CONDITIONS = ('A', 'B', 'C', 'D', 'E')
PRIMARY_AGENT = 'frozen-v6'
PROMPTS = {'C': 'plan-v1', 'D': 'contract-v1'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest_tasks(manifest, tasks=None, per_difficulty=None):
    """Task IDs from a judge manifest, optionally filtered to ``tasks`` or the first N of each difficulty."""
    entries = read_json(manifest)['tasks']
    if tasks:
        known = {e['task_id'] for e in entries}
        unknown = [t for t in tasks if t not in known]
        if unknown:
            raise ValueError(f'not in {manifest}: {unknown}')
        entries = [e for e in entries if e['task_id'] in set(tasks)]
    if per_difficulty:
        taken, kept = {}, []
        for entry in entries:
            if taken.get(entry['difficulty'], 0) < per_difficulty:
                taken[entry['difficulty']] = taken.get(entry['difficulty'], 0) + 1
                kept.append(entry)
        entries = kept
    return [e['task_id'] for e in entries]


def guidance_path(study, label, task_id, condition, provider='api'):
    return str(Path(study) / 'guidance' / label / f'{task_id}.{PROMPTS[condition]}.{provider}.json')


def build_plan(*, batch, task_ids, seeds, study, conditions=CONDITIONS, plan_label='final-plans',
               contract_label='final-contracts', guidance_provider='api', b_provider='api', b_max_requests=28,
               e_provider='api', outer_timeout=1000, frozen=True, cohort=None):
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        raise ValueError(f'unknown conditions {unknown}')
    if not task_ids or not seeds:
        raise ValueError('a plan needs at least one task and one seed')
    attempts = []
    for seed in seeds:
        for task_id in task_ids:
            for condition in conditions:
                item = {'task_id': task_id, 'condition': condition, 'seed': int(seed), 'variant': f's{seed}'}
                if condition == 'B':
                    item['coder'] = {'provider': b_provider, 'max_requests': b_max_requests,
                                     'purpose': f'{batch} B'}
                else:
                    item['agent'] = PRIMARY_AGENT
                if condition == 'C':
                    item['guidance'] = guidance_path(study, plan_label, task_id, 'C', guidance_provider)
                if condition == 'D':
                    item['guidance'] = guidance_path(study, contract_label, task_id, 'D', guidance_provider)
                if condition == 'E':
                    item['diagnosis'] = {'provider': e_provider, 'purpose': f'{batch} E',
                                         'prompt_id': 'diagnosis-v1', 'delivery': 'deliver-v1'}
                attempts.append(item)
    plan = {'batch': batch, 'frozen': frozen, 'outer_timeout': outer_timeout,
            'attempts': attempts}
    if cohort:
        plan['cohort'] = cohort
    return plan


def guidance_artifacts(plan):
    return sorted({a['guidance'] for a in plan['attempts'] if a.get('guidance')})


def freeze(plan, out):
    """Hash every guidance artifact the plan uses. Refuses if one is missing or the freeze file exists."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f'{out} exists; a freeze is written once')
    missing = [p for p in guidance_artifacts(plan) if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'{len(missing)} guidance artifacts missing, e.g. {missing[:3]}')
    record = {'schema': 'csc2108-guidance-freeze-v1', 'batch': plan['batch'],
              'artifacts': {p: sha256_file(p) for p in guidance_artifacts(plan)}}
    write_json(out, record)
    return record


def check(freeze_file):
    """Problems found when re-hashing a freeze: an empty list means every artifact is unchanged."""
    problems = []
    for path, digest in read_json(freeze_file)['artifacts'].items():
        if not Path(path).is_file():
            problems.append(f'missing: {path}')
        elif sha256_file(path) != digest:
            problems.append(f'changed: {path}')
    return problems
