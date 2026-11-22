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

# Phase IV (added after dev1 evidence): contract-v2 targets the observed D failure where a plausible but
# wrong program passed the public samples (arc192_a: 20/40 hidden) and no contract check was ever run.
# It must remain a behavioral specification: discriminating examples, never an algorithm.
CONTRACT_V2 = """Document a semi-formal behavioral contract for the supplied programming task. A separate
coding model will implement and test the program; the contract states WHAT a correct program must
output, never HOW to compute it. Use exactly these headings:
## Description
One or two sentences on the externally observable input/output behavior.
## Preconditions
PRE-1 etc: input format, value ranges and guarantees from the statement. Mark each Unverified.
## Postconditions
POST-1 etc: exact properties of a correct output, including boundary behavior, ties, ordering,
multiplicity, invariants and output format. Prefer properties that separate a correct answer from
plausible but wrong answers. Mark each Unverified.
## Test suggestions
4-6 concrete checks, each tied to PRE/POST IDs, written as a small stdin input and the exact
expected stdout that you derived by hand from the statement alone. Choose inputs that a plausible
but wrong program would answer incorrectly (beyond the statement's own samples), plus at least one
boundary input. Keep every input small enough to check by hand. Do not claim tests were run.
## Unspecified behavior
List behavior outside the task's guarantees, without inventing validation rules.
Use natural language. Do not provide code, pseudocode, algorithms, data structures or complexity
advice, and do not hint at how to compute the answer. No existing implementation or tests have been
inspected. Do not mark any condition Tested or Verified. Keep the contract within about 400 words.
"""

PROMPTS = {
    'plan-v1': ('plan', _planner.PROMPT),
    'contract-v1': ('contract', _contracts.PROMPT),
    'contract-v2': ('contract', CONTRACT_V2),
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
    # contract-v2 family: D additionally asks the coder to execute the contract's own checks (C unchanged).
    'inject-v2-contract-checks': {
        'plan': None,
        'contract': ('{{task}}\n\n## Behavioral contract from a stronger model\n'
                     'A separate, stronger model wrote this contract from the problem statement alone, before '
                     'any code was run. It specifies required behavior, not an algorithm, and has not been '
                     'verified; check it against the statement and the public tests. Before submitting, run '
                     'its concrete test suggestions against your program, for example '
                     "`printf 'INPUT LINES' | python /workspace/solution.py` as separate commands, and compare "
                     'with the expected output.\n\n'
                     '{{guide}}'),
    },
}

# Hard failures: fenced blocks or shell writes would hand the coder executable material.
HARD_PATTERNS = [re.compile(p, re.M) for p in (r'cat\s*>\s*/workspace', r"<<\s*['\"]?PY")]
FENCE = re.compile(r'^[ \t]*```([^\n`]*)\n(.*?)^[ \t]*```', re.M | re.S)
TEXT_FENCES = {'text', 'txt', 'plaintext', 'console-input', 'input', 'stdin'}
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
    # Fenced blocks are allowed only as plain-text data (e.g. a test input), never code.
    # (Refined 23:05 after dev2: v1 rejected all fences, which misclassified ```text test inputs.)
    for info, body in FENCE.findall(text):
        if info.strip().lower() not in TEXT_FENCES or soft_flags(body):
            problems.append('fenced code block: ' + (info.strip() or '(no language)'))
    if text.count('```') % 2:
        problems.append('unbalanced code fence')
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
    problems = validate(raw['kind'], raw['text'])  # current rules; creation-time result stays in the artifact
    if problems:
        raise ValueError('Guidance artifact failed validation: ' + '; '.join(problems))
    if raw['kind'] == 'plan':
        provider = _planner.SavedPlan(path)
        generated = _planner.generate_plan(provider, statement, timeout=1)
    else:
        provider = _contracts.SavedContract(path)
        generated = _contracts.generate_contract(provider, statement, timeout=1)
    if generated['text'] != raw['text']:
        raise RuntimeError('Replay altered guidance text')
    return generated, raw
