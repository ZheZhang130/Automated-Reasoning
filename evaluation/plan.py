"""Build the benchmark batch plan from a judge manifest, and freeze the C/D guidance it uses.

A plan is what ``python -m guided_agent batch`` runs. This module only writes JSON; it never runs a model.

* Every attempt gets ``variant = s<seed>``, so run directories never collide across seeds.
* Attempts are ordered seed -> task -> condition block, so a batch stopped part-way still holds whole
  (task, seed) blocks across all conditions, which is what the paired analysis needs.
* Within a block the condition order is counterbalanced (``order='balanced'``, the default): block ``i`` uses row
  ``i mod len(rows)`` of a Williams design, so across blocks every condition appears equally often in every position
  and directly after every other condition. ``order='fixed'`` keeps the alphabetical A, B, C, D, E of earlier plans.
  The order is a deterministic function of the plan, so resuming replays exactly the same schedule.
* The plan records the benchmark it was built from (manifest path, sha256 and the selected task hashes), so later
  steps can prove the tasks they build and score are the selected ones.
* C and D point at the write-once guidance artifacts produced by ``guided_agent author``; ``freeze`` hashes them
  together with the plan and the expected artifact set, and ``check`` proves later that none changed.
"""
import hashlib
import json
from pathlib import Path

CONDITIONS = ('A', 'B', 'C', 'D', 'E')
PRIMARY_AGENT = 'frozen-v6'
PROMPTS = {'C': 'plan-v1', 'D': 'contract-v1'}
PLAN_SCHEMA = 'csc2108-eval-plan-v2'
FREEZE_SCHEMA = 'csc2108-guidance-freeze-v2'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def plan_sha256(plan):
    """Hash of the plan as scheduled (``plan_path``, added by guided_agent when it copies the plan, is ignored)."""
    return canonical_sha256({k: v for k, v in plan.items() if k != 'plan_path'})


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


def benchmark_record(manifest, task_ids, repo=None):
    """What a plan stores about its benchmark: manifest identity and the selected tasks' pinned hashes."""
    manifest = Path(manifest).resolve()
    data = read_json(manifest)
    entries = {e['task_id']: e for e in data['tasks']}
    tasks = {t: {k: entries[t].get(k) for k in ('difficulty', 'n_hidden', 'public_sha256', 'hidden_sha256')}
             for t in task_ids}
    try:
        shown = manifest.relative_to(Path(repo).resolve()).as_posix() if repo else str(manifest)
    except ValueError:
        shown = str(manifest)
    return {'manifest': shown, 'manifest_name': data.get('name'), 'manifest_sha256': sha256_file(manifest),
            'hf_revision': data.get('hf_revision'), 'shards': data.get('shards'),
            'tasks_sha256': canonical_sha256(tasks), 'tasks': tasks}


def guidance_path(study, label, task_id, condition, provider='api'):
    return str(Path(study) / 'guidance' / label / f'{task_id}.{PROMPTS[condition]}.{provider}.json')


def williams(conditions):
    """Rows of a Williams design: each condition once per position, and each ordered pair adjacent equally often.

    Even n needs n rows; odd n needs 2n (the square and its mirror)."""
    n = len(conditions)
    first, low, high = [0], 1, n - 1
    while len(first) < n:
        first.append(low)
        low += 1
        if len(first) < n:
            first.append(high)
            high -= 1
    rows = [[conditions[(x + shift) % n] for x in first] for shift in range(n)]
    if n % 2:
        rows += [list(reversed(row)) for row in rows]
    return rows


def block_orders(conditions, order):
    if order == 'fixed':
        return [list(conditions)]
    if order == 'balanced':
        return williams(list(conditions))
    raise ValueError(f'unknown order {order!r} (fixed or balanced)')


def build_plan(*, batch, task_ids, seeds, study, conditions=CONDITIONS, plan_label='final-plans',
               contract_label='final-contracts', guidance_provider='api', b_provider='api', b_max_requests=28,
               e_provider='api', outer_timeout=1000, frozen=True, cohort=None, order='balanced', benchmark=None):
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        raise ValueError(f'unknown conditions {unknown}')
    if len(set(conditions)) != len(conditions) or len(set(task_ids)) != len(task_ids) or len(set(seeds)) != len(seeds):
        raise ValueError('conditions, tasks and seeds must not repeat')
    if not task_ids or not seeds:
        raise ValueError('a plan needs at least one task and one seed')
    rows = block_orders(conditions, order)
    attempts = []
    block = 0
    for seed in seeds:
        for task_id in task_ids:
            for condition in rows[block % len(rows)]:
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
            block += 1
    plan = {'schema': PLAN_SCHEMA, 'batch': batch, 'frozen': frozen, 'outer_timeout': outer_timeout,
            'order': {'scheme': order, 'rows': rows}, 'seeds': [int(s) for s in seeds],
            'conditions': list(conditions), 'attempts': attempts}
    if benchmark:
        plan['benchmark'] = benchmark
    if cohort:
        plan['cohort'] = cohort
    return plan


def guidance_artifacts(plan):
    return sorted({a['guidance'] for a in plan['attempts'] if a.get('guidance')})


def _artifact_meta(path):
    data = read_json(path)
    return {k: data.get(k) for k in ('task_id', 'kind', 'prompt_id', 'provider', 'requested_model', 'observed_model',
                                     'statement_sha256', 'system_prompt_sha256', 'label')}


def freeze(plan, out):
    """Hash every guidance artifact the plan uses, bound to the plan. Refuses if one is missing or the file exists."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f'{out} exists; a freeze is written once')
    expected = guidance_artifacts(plan)
    missing = [p for p in expected if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'{len(missing)} guidance artifacts missing, e.g. {missing[:3]}')
    record = {'schema': FREEZE_SCHEMA, 'batch': plan['batch'], 'plan_sha256': plan_sha256(plan),
              'expected_artifacts': expected,
              'artifacts': {p: sha256_file(p) for p in expected},
              'artifact_meta': {p: _artifact_meta(p) for p in expected}}
    write_json(out, record)
    return record


def check(freeze_file, plan=None, study=None):
    """Problems found when re-checking a freeze: an empty list means the guidance is exactly what was frozen.

    With ``plan``: the freeze must belong to this plan and cover exactly the artifacts it schedules, and every
    artifact must belong to its attempt's task and prompt. With ``study`` as well: each artifact's statement hash must
    match the statement the agent will read (``<study>/bundles/<task>/task.json``)."""
    record = read_json(freeze_file)
    problems = []
    for path, digest in record['artifacts'].items():
        if not Path(path).is_file():
            problems.append(f'missing: {path}')
        elif sha256_file(path) != digest:
            problems.append(f'changed: {path}')
    if plan is None:
        return problems
    if record.get('schema') != FREEZE_SCHEMA:
        return problems + [f'{freeze_file}: freeze schema {record.get("schema")} is not bound to a plan '
                           f'(write a new {FREEZE_SCHEMA} freeze with `evaluation guidance`)']
    if record.get('plan_sha256') != plan_sha256(plan):
        problems.append(f'{freeze_file} was written for a different plan')
    expected = guidance_artifacts(plan)
    if sorted(record['artifacts']) != expected:
        extra = sorted(set(record['artifacts']) - set(expected))
        absent = sorted(set(expected) - set(record['artifacts']))
        problems.append(f'freeze artifact set differs from the plan (not in plan: {extra[:3]}, not frozen: {absent[:3]})')
    for item in plan['attempts']:
        path = item.get('guidance')
        if not path or not Path(path).is_file():
            continue
        meta = _artifact_meta(path)
        if meta['task_id'] != item['task_id'] or meta['prompt_id'] != PROMPTS.get(item['condition']):
            problems.append(f"{path}: belongs to {meta['task_id']}/{meta['prompt_id']}, not "
                            f"{item['task_id']}/{PROMPTS.get(item['condition'])}")
        if study is not None:
            bundle = Path(study) / 'bundles' / item['task_id'] / 'task.json'
            if bundle.is_file():
                statement = read_json(bundle)['statement']
                if hashlib.sha256(statement.encode('utf-8')).hexdigest() != meta['statement_sha256']:
                    problems.append(f'{path}: authored for a different statement than {bundle}')
    return sorted(set(problems))
