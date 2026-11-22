"""Condition B (frontier only) and scripted coders: a MODEL SUBSTITUTION inside the frozen runtime.

The frozen ``run`` picks ``TextModel`` (LiteLLM text-based model + Ollama finish-reason shim). For B we
rebind that one global to a subclass of the same upstream ``LitellmTextbasedModel`` whose ``_query``
asks a frontier provider instead of Ollama. Everything else is unchanged and shared with A/C/D/E:
the system prompt, the ```mswea_bash_command`` regex action parser, format-error handling, observation
template, sandbox, judge-public routing, action/repair/time budgets, candidate extraction and records.

Providers:
* ``ApiCoder``      direct OpenAI chat completions with the full message history (paid, ledgered,
                    per-run request cap, no retries);
* ``CodexCoder``    fresh isolated tool-less Codex inference per turn with the transcript (free replay);
* ``ScriptedCoder`` predetermined responses for deterministic integration tests.

Codex's own agent tools are never used as the coding interface: every action is produced as text
and executed by the shared environment.
"""
import json
from pathlib import Path

import litellm
from minisweagent.exceptions import InterruptAgentFlow

from .common import utc_now, write_json


class FrontierCoderError(RuntimeError):
    """Provider failure. Listed in abort_exceptions so mini-swe-agent never retries a frontier call."""


def _response(text, finish_reason, model, usage=None):
    usage = usage or {}
    return litellm.ModelResponse(
        model=model, choices=[{'index': 0, 'finish_reason': finish_reason,
                               'message': {'role': 'assistant', 'content': text}}],
        usage={'prompt_tokens': usage.get('prompt_tokens') or 0, 'completion_tokens': usage.get('completion_tokens') or 0,
               'total_tokens': (usage.get('prompt_tokens') or 0) + (usage.get('completion_tokens') or 0)})


def make_coder_class(runtime, provider):
    base = runtime.LitellmTextbasedModel

    class FrontierCoderModel(base):
        abort_exceptions = list(base.abort_exceptions) + [FrontierCoderError, InterruptAgentFlow]
        coder = provider

        def _query(self, messages, **kwargs):
            timeout = float(self.config.model_kwargs.get('timeout') or 180)
            try:
                text, finish_reason, usage = provider(messages, timeout)
            except InterruptAgentFlow:
                raise
            except Exception as error:
                raise FrontierCoderError(f'{type(error).__name__}: {error}') from None
            return _response(text, finish_reason, provider.model_label, usage)

    return FrontierCoderModel


class _Coder:
    model_label = 'frontier'

    def __init__(self, log_dir, max_requests):
        self.log_dir, self.max_requests = Path(log_dir), max_requests
        self.calls = []

    def _limit(self):
        if len(self.calls) >= self.max_requests:
            from minisweagent.exceptions import LimitsExceeded
            raise LimitsExceeded({'role': 'exit', 'content': 'FrontierRequestLimit',
                                  'extra': {'exit_status': 'FrontierRequestLimit', 'submission': ''}})

    def _log(self, entry):
        self.calls.append(entry)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        write_json(self.log_dir / 'coder-calls.json', self.calls)


class ApiCoder(_Coder):
    def __init__(self, *, log_dir, ledger_path, purpose, max_requests, effort='medium', max_completion_tokens=8000):
        super().__init__(log_dir, max_requests)
        self.ledger_path, self.purpose = ledger_path, purpose
        self.effort, self.max_completion_tokens = effort, max_completion_tokens
        from .providers import api_config
        _, configured, self.model_label = api_config()
        self.configured_model = configured

    def __call__(self, messages, timeout):
        from .providers import api_chat
        self._limit()
        clean = [{'role': m['role'], 'content': m.get('content') or ''} for m in messages]
        result = api_chat(messages=clean, ledger_path=self.ledger_path, max_completion_tokens=self.max_completion_tokens,
                          effort=self.effort, timeout=timeout,
                          entry={'kind': 'coder', 'condition': 'B', 'purpose': self.purpose, 'turn': len(self.calls) + 1})
        finish = 'length' if result['finish_reason'] == 'length' else 'stop'
        self._log({'turn': len(self.calls) + 1, 'utc': utc_now(), 'ledger_index': result['ledger_index'],
                   'finish_reason': result['finish_reason'], 'usage': result['usage'],
                   'latency_seconds': result['latency_seconds'], 'cost_usd': result['cost_usd']})
        return result['text'], finish, result['usage']


CODEX_CODER_REQUEST = """The conversation so far between a coding harness (USER) and you (ASSISTANT) is below.
Write ONLY the next ASSISTANT message, following the system prompt's response format exactly.

{transcript}
"""


class CodexCoder(_Coder):
    def __init__(self, *, log_dir, work_root, max_requests, model='gpt-6.2-sol', effort='medium'):
        super().__init__(log_dir, max_requests)
        self.work_root, self.model_label, self.effort = Path(work_root), model, effort

    def __call__(self, messages, timeout):
        from .providers import codex_infer
        self._limit()
        system = messages[0]['content'] if messages and messages[0]['role'] == 'system' else ''
        transcript = '\n\n'.join(f"=== {m['role'].upper()} ===\n{m.get('content') or ''}" for m in messages[1:])
        turn = len(self.calls) + 1
        result = codex_infer(system=system, user=CODEX_CODER_REQUEST.format(transcript=transcript),
                             evidence=self.log_dir / f'turn-{turn:02d}', work_root=self.work_root,
                             model=self.model_label, effort=self.effort, timeout=timeout)
        self._log({'turn': turn, 'utc': utc_now(), 'harness_wall_seconds': result['wall_seconds'],
                   'usage': result['usage'], 'tool_events': result['isolation']['tool_events']})
        return result['text'], 'stop', None


class ScriptedCoder(_Coder):
    """Deterministic fake model: returns the given responses in order (tests and synthetic fixtures)."""
    def __init__(self, responses, log_dir, max_requests=None):
        super().__init__(log_dir, max_requests or len(responses))
        self.responses, self.model_label = list(responses), 'scripted'
        self.seen = []

    def __call__(self, messages, timeout):
        self._limit()
        self.seen.append(json.loads(json.dumps(messages, default=str)))
        text = self.responses[len(self.calls)]
        self._log({'turn': len(self.calls) + 1, 'n_messages': len(messages)})
        return text, 'stop', None


def make_coder(spec, study, log_dir):
    provider = spec.get('provider')
    if provider == 'api':
        if not spec.get('purpose') or not spec.get('max_requests'):
            raise ValueError('API coder requires purpose and max_requests')
        return ApiCoder(log_dir=log_dir, ledger_path=study / 'api-ledger.json', purpose=spec['purpose'],
                        max_requests=int(spec['max_requests']), effort=spec.get('effort', 'medium'),
                        max_completion_tokens=spec.get('max_completion_tokens', 8000))
    if provider == 'codex':
        return CodexCoder(log_dir=log_dir, work_root=study / 'codex-work', max_requests=int(spec.get('max_requests', 28)),
                          model=spec.get('model', 'gpt-6.2-sol'), effort=spec.get('effort', 'medium'))
    if provider == 'scripted':
        return ScriptedCoder(spec['responses'], log_dir, spec.get('max_requests'))
    raise ValueError('Unknown coder provider ' + str(provider))


def non_ollama_globals(base_globals, coder_cls, model_label):
    """Globals for a coder that is not the local Ollama model (B, scripted tests).

    The GPU-exclusivity check and the Ollama model metadata calls are replaced by records saying that no local
    model was used; the frozen model-name allow-list gains exactly this coder label. ``base_globals`` are the
    host-adapted globals of the frozen function (Windows or portable), so the remaining telemetry is unchanged.
    """
    original_api = base_globals['api']

    def api(port, route, payload=None, timeout=15):
        if route in ('/api/show', '/api/tags'):
            return {'non_ollama_coder': model_label, 'route': route}
        return original_api(port, route, payload, timeout)

    return {'TextModel': coder_cls, 'MODELS': tuple(base_globals['MODELS']) + (model_label,),
            'exclusive_gpu': lambda: None, 'api': api}
