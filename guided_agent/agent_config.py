"""Versioned shared-agent configurations (pass 4).

``frozen-v6`` is the original agent byte for byte: profile ``heredoc-v6-16k-common`` (16K context, 4,096 output
tokens, thinking off, T=0.2, top_p 0.9, top_k 40, fixed seed), the frozen prompts and the frozen observation format.

Every other configuration changes exactly ONE mechanism, through the same global-rebinding seam the conditions
already use (``backend.bound_run``). No frozen file is edited, and the 38-file verification still runs. A
configuration is a property of the shared agent: it must apply identically to A, C, D and E in any comparison.

* ``profile``   overlays keys of the frozen profile (the profile dict is what the frozen ``run`` sends to Ollama,
                so ``sampler_wire_verified`` checks the overlay on the wire);
* ``self_plan`` one bounded local planning call before the coding session (same model, same sampler, the
                teammates' plan-v1 planner prompt); its text is added to the first user message. Recorded
                separately (tokens, durations, truncation) and never deducted from the coding budget;
* ``receipt``   a one-line harness state receipt prepended to every observation: action count, whether the
                command changed /workspace/solution.py (version number, diff size, syntax check inside the
                sandbox) and whether this exact version was already tested.
"""
import difflib
import hashlib
import json
import time
from pathlib import Path

from .common import MODEL, PROFILE, sha256_text, utc_now, write_json

AGENT_CONFIGS = {
    'frozen-v6': {},
    'l1-selfplan-v1': {'self_plan': {'prompt_id': 'plan-v1', 'output_tokens': 4096, 'timeout': 180}},
    'l2-think-8k-v1': {'profile': {'thinking': True, 'output_tokens': 8192, 'context': 32768}},
    'l3-out-8k-v1': {'profile': {'output_tokens': 8192, 'context': 32768}},
    'l4-receipt-v1': {'receipt': 'v1'},
}
DEFAULT_AGENT = 'frozen-v6'

SELF_PLAN_BLOCK = ('\n\n## Your own plan, written in a separate planning step\n'
                   'Before this session started, you (the same model) read the problem statement{also} and wrote the '
                   'plan below without running any code. It has not been verified; check it against the statement '
                   'and the public tests.\n\n{{{{selfplan}}}}')
SELF_PLAN_ALSO = {'plan': ' and the stronger model\'s plan', 'contract': ' and the stronger model\'s contract'}


def resolve(agent_id):
    agent_id = agent_id or DEFAULT_AGENT
    if agent_id not in AGENT_CONFIGS:
        raise ValueError(f'Unknown shared-agent configuration {agent_id!r}')
    definition = AGENT_CONFIGS[agent_id]
    return agent_id, definition, sha256_text(json.dumps(definition, sort_keys=True))


def profile_reader(original_read, overlay):
    """Rebinds the frozen ``read`` so the frozen profile gets ``overlay``; every other file is read unchanged."""
    def read(path):
        value = original_read(path)
        if overlay and Path(path).name == 'profiles.json':
            value = dict(value)
            value[PROFILE] = dict(value[PROFILE]) | overlay
        return value
    return read


def self_plan_template(template, kind):
    """First-message template with the self-plan block appended (A/E: the frozen '{{task}}' plus the block)."""
    return (template or '{{task}}') + SELF_PLAN_BLOCK.format(also=SELF_PLAN_ALSO.get(kind, ''))


class SelfPlanner:
    """One bounded call to the local model, made after the frozen GPU-exclusivity check and before the agent starts.

    It runs inside the same model lock as the coding session and uses the frozen sampler with the coding session's
    context size, so the loaded model is reused by the session. ``caller`` is injectable for offline tests.
    """
    def __init__(self, *, statement, seed, profile, endpoint, out_dir, prompt_text, output_tokens, timeout,
                 guide=None, caller=None):
        self.statement, self.seed, self.profile, self.endpoint = statement, seed, profile, endpoint
        self.out_dir, self.prompt_text, self.output_tokens, self.timeout = Path(out_dir), prompt_text, output_tokens, timeout
        self.guide, self.caller = guide, caller
        self.text, self.record = None, {'requested': False}

    def body(self):
        options = dict(self.profile.get('sampler') or {}) | {
            'num_ctx': self.profile['context'], 'num_predict': self.output_tokens,
            'temperature': self.profile.get('temperature', 0.0), 'seed': self.seed}
        user = self.statement if self.guide is None else (
            self.statement + '\n\n## Guidance from a stronger model (read it; your plan may follow or correct it)\n\n'
            + self.guide)
        return {'model': MODEL, 'stream': False, 'think': False, 'keep_alive': '10m', 'options': options,
                'messages': [{'role': 'system', 'content': self.prompt_text}, {'role': 'user', 'content': user}]}

    def __call__(self):
        body = self.body()
        self.record = {'requested': True, 'requested_utc': utc_now(), 'request_sha256': sha256_text(json.dumps(body, sort_keys=True)),
                       'options': body['options'], 'error': None}
        started = time.monotonic()
        try:
            if self.caller is not None:
                raw = self.caller(body)
            else:
                import requests
                response = requests.post(self.endpoint.rstrip('/') + '/api/chat', json=body, timeout=self.timeout)
                if response.status_code != 200:
                    raise RuntimeError(f'Ollama HTTP {response.status_code}: {response.text[:500]}')
                raw = response.json()
        except Exception as error:  # recorded; the session then starts without a plan (no retry)
            self.record |= {'error': f'{type(error).__name__}: {error}', 'wall_seconds': round(time.monotonic() - started, 2)}
            write_json(self.out_dir / 'self-plan.json', self.record)
            return None
        text = (raw.get('message') or {}).get('content') or ''
        truncated = raw.get('done_reason') == 'length'
        delivered = text.strip() + ('\n\n[This plan was cut off at the output limit.]' if truncated else '')
        self.text = delivered if text.strip() else None
        self.record |= {'wall_seconds': round(time.monotonic() - started, 2), 'done_reason': raw.get('done_reason'),
                        'truncated': truncated, 'prompt_tokens': raw.get('prompt_eval_count'),
                        'completion_tokens': raw.get('eval_count'),
                        'prompt_eval_seconds': (raw.get('prompt_eval_duration') or 0) / 1e9,
                        'eval_seconds': (raw.get('eval_duration') or 0) / 1e9,
                        'load_seconds': (raw.get('load_duration') or 0) / 1e9,
                        'text_sha256': sha256_text(self.text) if self.text else None,
                        'words': len(text.split()), 'delivered': self.text is not None}
        write_json(self.out_dir / 'self-plan.json', self.record | {'text': text, 'raw_message': raw.get('message')})
        return self.text


def exclusive_then_plan(original_exclusive, planner):
    """Rebinds the frozen ``exclusive_gpu``: the original check/unload first, then the one self-plan call."""
    def exclusive_gpu():
        original_exclusive()
        planner()
    return exclusive_gpu


class Receipts:
    """State receipts for ``l4-receipt-v1``. Pure bookkeeping on harness snapshots; never executes the candidate."""
    def __init__(self, action_limit):
        self.action_limit = action_limit
        self.versions = {}      # sha256 -> version number (order of first appearance)
        self.tested = {}        # sha256 -> (action, verdict text)
        self.count = 0

    def version(self, digest):
        if digest not in self.versions:
            self.versions[digest] = len(self.versions) + 1
        return self.versions[digest]

    def _head(self, actions):
        return f'[harness] Action {actions}/{self.action_limit} done ({max(0, self.action_limit - actions)} left).'

    def after_command(self, *, actions, before, after, syntax):
        self.count += 1
        head = self._head(actions)
        if after is None:
            return head + ' /workspace/solution.py does not exist yet.'
        digest = hashlib.sha256(after).hexdigest()
        known = digest in self.versions
        number = self.version(digest)
        lines = after.decode('utf-8', 'replace').splitlines()
        if before == after:
            text = f' /workspace/solution.py was not changed by this command (still version {number}, {len(lines)} lines).'
        else:
            old = (before or b'').decode('utf-8', 'replace').splitlines()
            diff = list(difflib.unified_diff(old, lines, lineterm='', n=0))
            added = sum(1 for d in diff if d.startswith('+') and not d.startswith('+++'))
            removed = sum(1 for d in diff if d.startswith('-') and not d.startswith('---'))
            text = (f' /workspace/solution.py changed: now version {number}, {len(lines)} lines '
                    f'(+{added}/-{removed} lines).' + (' It is byte-identical to that earlier version.' if known else ''))
            text += ' ' + syntax
        status = self.tested.get(digest)
        text += (f' Version {number} was already tested at action {status[0]}: {status[1]}.' if status
                 else f' Version {number} has not been tested.')
        return head + text

    def after_test(self, *, actions, digest, result):
        head = self._head(actions)
        if digest is None:
            return head + ' There was no /workspace/solution.py to test.'
        number = self.version(digest)
        if result.get('status') == 'pass':
            verdict = 'it passed all public tests'
        else:
            verdict = f"it failed the public tests ({result.get('passed')} of {result.get('total')} cases passed)"
        self.tested[digest] = (actions, verdict)
        return head + f' Tested version {number}: {verdict}.'
