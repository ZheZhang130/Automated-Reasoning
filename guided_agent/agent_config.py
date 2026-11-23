"""Versioned shared-agent configurations.

* ``frozen-v6``: the original agent byte for byte. Profile ``heredoc-v6-16k-common`` (16K context, 4,096 output
  tokens, thinking off, T=0.2, top_p 0.9, top_k 40, fixed seed), the frozen prompts and observation format. It is
  the historical reference of passes 1–3.
* ``l1-selfplan-v1``: the frozen agent plus **one bounded local planning step** before the coding session. Qwen
  itself answers the teammates' plan-v1 prompt, with the frozen sampler, seed and context, 4,096 tokens and no
  thinking; for C and D it reads the frontier guidance too. Its text is added to the first user message. The call is
  recorded separately (tokens, durations, truncation), and the coding deadline is moved back by its duration, so
  every condition keeps the same 600-second coding budget.

The configuration is a property of the shared agent: it applies identically to A, C, D and E in any comparison,
and B (frontier coder) never uses it. ``PRIMARY_AGENT`` is what frozen benchmark plans must use: ``frozen-v6``.
``l1-selfplan-v1`` is the documented alternative (pass 4: A 7/16 against 4/16 on development tasks, but C 12/16 against
14/16, and its extra context can overflow the 16K window in long C sessions). Adopting it is a team decision; it
would apply to every local condition and needs its own validation, probably with a larger context. The screening
evidence and the alternatives that were not promoted (thinking, 8K output, state receipts) are on the development
branch (``reasoning_effectiveness/pass4``).
"""
import json
import time
from pathlib import Path

from .common import MODEL, sha256_text, utc_now, write_json

AGENT_CONFIGS = {
    'frozen-v6': {},
    'l1-selfplan-v1': {'self_plan': {'prompt_id': 'plan-v1', 'output_tokens': 4096, 'timeout': 180}},
}
DEFAULT_AGENT = 'frozen-v6'
PRIMARY_AGENT = 'frozen-v6'

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
