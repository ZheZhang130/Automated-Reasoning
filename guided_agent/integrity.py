"""Batch-plan validation: refuse a plan that could mislabel, collide or silently change a run.

``validate_plan`` returns a list of problems; ``cmd_batch`` refuses to start when it is non-empty. A plan with
``"frozen": true`` (a benchmark cohort) must additionally use only the primary configuration: the primary shared
agent (``agent_config.PRIMARY_AGENT``, named explicitly; B: the plain interface), no smoke budgets or test hooks,
C = plan-v1 + inject-v1, D = contract-v1 + inject-v1, E = diagnosis-v1 + deliver-v1, and an explicit integer seed on
every attempt.
"""
import json
import re
from pathlib import Path

from .agent_config import AGENT_CONFIGS, PRIMARY_AGENT
from .common import CODER, CONDITIONS, DYNAMIC, read_json

FROZEN_PROMPTS = {'C': 'plan-v1', 'D': 'contract-v1'}
FROZEN_E = {'prompt_id': 'diagnosis-v1', 'delivery': 'deliver-v1'}
E_PROVIDERS = {'codex', 'api', 'fixed', 'replay'}
SAFE_NAME = re.compile(r'^[A-Za-z0-9._-]+$')


def run_name(item):
    return f"{item['task_id']}-{item['condition']}" + (f"-{item['variant']}" if item.get('variant') else '')


def validate_plan(plan):
    problems = []
    batch = plan.get('batch')
    if not isinstance(batch, str) or not SAFE_NAME.match(batch or ''):
        problems.append(f'batch name {batch!r} is missing or unsafe')
    attempts = plan.get('attempts')
    if not isinstance(attempts, list) or not attempts:
        return problems + ['plan has no attempts']
    frozen = bool(plan.get('frozen'))
    seen = {}
    for index, item in enumerate(attempts):
        where = f'attempt {index}'
        condition = item.get('condition')
        if condition not in CONDITIONS:
            problems.append(f'{where}: unknown condition {condition!r}')
            continue
        if not isinstance(item.get('task_id'), str):
            problems.append(f'{where}: task_id missing')
            continue
        name = run_name(item)
        if not SAFE_NAME.match(name):
            problems.append(f'{where}: unsafe run name {name!r}')
        if name in seen:
            problems.append(f'{where}: run name {name} duplicates attempt {seen[name]} (a seed or variant must differ '
                            'in the name, or the second attempt would be skipped as already complete)')
        seen.setdefault(name, index)
        if item.get('agent') is not None and item['agent'] not in AGENT_CONFIGS:
            problems.append(f"{where}: unknown shared-agent configuration {item['agent']!r}")
        if item.get('test_hooks') and (frozen or (item.get('coder') or {}).get('provider') != 'scripted'):
            problems.append(f'{where}: test_hooks are only allowed with a scripted coder outside frozen plans')
        if 'seed' in item and (not isinstance(item['seed'], int) or isinstance(item['seed'], bool)):
            problems.append(f'{where}: seed must be an integer')
        kind = CONDITIONS[condition]
        if kind and not item.get('guidance'):
            problems.append(f'{where}: condition {condition} needs a {kind} guidance artifact')
        if not kind and item.get('guidance'):
            problems.append(f'{where}: condition {condition} must not carry upfront guidance')
        if condition in DYNAMIC:
            spec = item.get('diagnosis') or {}
            if spec.get('provider', 'codex') not in E_PROVIDERS:
                problems.append(f"{where}: unknown diagnosis provider {spec.get('provider')!r}")
        elif item.get('diagnosis'):
            problems.append(f'{where}: only condition E may carry a diagnosis specification')
        if condition in CODER and not item.get('coder'):
            problems.append(f'{where}: condition B needs a coder specification')
        if condition not in CODER and item.get('coder') and (frozen or item['coder'].get('provider') != 'scripted'):
            # A scripted coder is a test device (never in a frozen plan); a frontier coder is B only.
            problems.append(f'{where}: condition {condition} must not substitute the coding model')
        if frozen:
            problems += _frozen_problems(where, condition, item)
    return problems


def _frozen_problems(where, condition, item):
    problems = []
    agent = item.get('agent')
    if condition in CODER:
        if agent not in (None, 'frozen-v6'):
            problems.append(f'{where}: B uses the plain shared interface (agent frozen-v6 or none), not {agent}')
    elif agent is None:
        problems.append(f'{where}: a frozen plan needs an explicit agent (the primary shared agent is {PRIMARY_AGENT})')
    elif agent != PRIMARY_AGENT:
        problems.append(f'{where}: frozen plans use the primary shared agent {PRIMARY_AGENT}, not {agent}')
    for key in ('aci', 'contract_checks', 'test_hooks'):
        if item.get(key):
            problems.append(f'{where}: {key} is not part of the final configuration')
    if item.get('smoke'):
        problems.append(f'{where}: smoke budgets are not allowed in a frozen benchmark plan')
    if not isinstance(item.get('seed'), int):
        problems.append(f'{where}: a frozen plan needs an explicit integer seed on every attempt')
    if condition in FROZEN_PROMPTS:
        if item.get('injection', 'inject-v1') != 'inject-v1':
            problems.append(f'{where}: frozen injection is inject-v1')
        path = Path(item.get('guidance') or '')
        if path.is_file():
            artifact = read_json(path)
            if artifact.get('prompt_id') != FROZEN_PROMPTS[condition]:
                problems.append(f"{where}: guidance prompt {artifact.get('prompt_id')} is not {FROZEN_PROMPTS[condition]}")
            if artifact.get('task_id') != item['task_id']:
                problems.append(f'{where}: guidance artifact belongs to {artifact.get("task_id")}')
        else:
            problems.append(f'{where}: guidance artifact {path} does not exist')
    if condition in DYNAMIC:
        spec = item.get('diagnosis') or {}
        for key, value in FROZEN_E.items():
            if spec.get(key, value) != value:
                problems.append(f'{where}: frozen E uses {key}={value}')
    return problems


def comparable(plan):
    return json.dumps({k: v for k, v in plan.items() if k != 'plan_path'}, sort_keys=True)


def check_unchanged(batch_dir, plan):
    """A batch directory keeps the plan it was started with; resuming with a different plan is refused."""
    stored = Path(batch_dir) / 'plan.json'
    if stored.exists() and comparable(read_json(stored)) != comparable(plan):
        return [f'{stored} holds a different plan; start a new batch instead of changing this one']
    return []
