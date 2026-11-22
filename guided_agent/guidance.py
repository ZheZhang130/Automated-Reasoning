"""Versioned guidance prompts, task-bound artifacts and injection into the agent's first message.

v1 prompts are the teammates' original prompts, imported unchanged. Later versions are
explicit experimental interventions with their own IDs. A saved artifact is loaded through
the teammates' ``SavedPlan``/``SavedContract`` replay classes, which enforce the statement
hash, so the original replay mechanism stays authoritative.
"""
import re
import sys
from pathlib import Path

from .common import REPO, read_json, sha256_text, utc_now, write_json

sys.path.insert(0, str(REPO / 'planning_frontier'))
import planner as _planner  # noqa: E402  (teammates' module, unchanged)
from contract_frontier import contracts as _contracts  # noqa: E402

SCHEMA = 'csc2108-guidance-v1'

# Phase IV prompt versions are added below only after Phase III evidence motivates them.

PROMPTS = {
    'plan-v1': ('plan', _planner.PROMPT),
    'contract-v1': ('contract', _contracts.PROMPT),
}

HEADINGS = {'plan': ('## Observations', '## Solution sketch'),
            'contract': ('## Description', '## Preconditions', '## Postconditions',
                         '## Test suggestions', '## Unspecified behavior')}

# Parallel framing for C and D; A receives the unmodified frozen '{{task}}' template.
INJECTION = {
    'inject-v1': {
        'plan': ('{{task}}\n\n## Implementation plan from a stronger model\n'
                 'A separate, stronger model wrote this plan from the problem statement alone, before any '
                 'code was run. It has not been verified; check it against the statement and the public tests.\n\n'
                 '{{guide}}'),
        'contract': ('{{task}}\n\n## Behavioral contract from a stronger model\n'
                     'A separate, stronger model wrote this contract from the problem statement alone, before '
                     'any code was run. It specifies required behavior, not an algorithm, and has not been '
                     'verified; check it against the statement and the public tests.\n\n{{guide}}'),
    },
}

# Hard failures: fenced blocks or shell writes would hand the coder executable material.
HARD_PATTERNS = [re.compile(p, re.M) for p in (r'^\s*```', r'cat\s*>\s*/workspace', r"<<\s*['\"]?PY")]
# Soft flags are recorded for analysis but never used to resample guidance (no rejection sampling).
SOFT_PATTERNS = [re.compile(p, re.M) for p in (r'^\s*def \w+\(', r'^\s*import \w+', r'^\s*for \w+ in range\(',
                                               r'print\(', r'sys\.stdin')]


def prompt(prompt_id):
    kind, text = PROMPTS[prompt_id]
    return kind, text


def validate(kind, text):
    """Format and leakage checks only; semantic correctness is never claimed."""
    problems = []
    if not isinstance(text, str) or not text.strip():
        return ['empty']
    for heading in HEADINGS[kind]:
        if heading not in text:
            problems.append('missing heading ' + heading)
    for pattern in HARD_PATTERNS:
        if pattern.search(text):
            problems.append('code-like content: ' + pattern.pattern)
    return problems


def soft_flags(text):
    return [pattern.pattern for pattern in SOFT_PATTERNS if pattern.search(text or '')]


def artifact(*, kind, prompt_id, statement, text, task_id, provider, requested_model, observed_model,
             reasoning_effort, generation, usage=None, latency_seconds=None, cost_usd=None, isolation=None,
             label):
    system_prompt = PROMPTS[prompt_id][1]
    record = {
        'schema': SCHEMA, 'kind': kind, 'prompt_id': prompt_id, 'task_id': task_id, 'text': text,
        'statement_sha256': sha256_text(statement), 'system_prompt': system_prompt,
        'system_prompt_sha256': sha256_text(system_prompt), 'user_message_sha256': sha256_text(statement),
        # Compatibility fields read by the teammates' SavedPlan / SavedContract classes.
        ('planning_prompt' if kind == 'plan' else 'contract_prompt'): system_prompt,
        'author': f'{provider}:{requested_model}', 'provider': provider, 'label': label,
        'requested_model': requested_model, 'observed_model': observed_model,
        'reasoning_effort': reasoning_effort, 'generation': generation, 'usage': usage,
        'latency_seconds': latency_seconds, 'cost_usd': cost_usd, 'isolation': isolation,
        'validation_problems': validate(kind, text), 'soft_code_flags': soft_flags(text),
        'word_count': len((text or '').split()), 'created_utc': utc_now(),
    }
    return record


def save_artifact(path, record):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f'{path} exists; guidance artifacts are write-once')
    write_json(path, record)
    return path


def load_for_run(path, statement):
    """Replay through the teammates' classes; returns (generated dict, raw artifact)."""
    raw = read_json(path)
    if raw.get('schema') != SCHEMA:
        raise ValueError('Not a csc2108 guidance artifact')
    if raw['validation_problems']:
        raise ValueError('Guidance artifact failed validation: ' + '; '.join(raw['validation_problems']))
    if raw['kind'] == 'plan':
        provider = _planner.SavedPlan(path)
        generated = _planner.generate_plan(provider, statement, timeout=1)
    else:
        provider = _contracts.SavedContract(path)
        generated = _contracts.generate_contract(provider, statement, timeout=1)
    if generated['text'] != raw['text']:
        raise RuntimeError('Replay altered guidance text')
    return generated, raw
