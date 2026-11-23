"""Frontier guidance providers: isolated Codex replay authoring and the direct OpenAI API.

Both receive exactly the same system prompt and user message (the public statement) and
produce the same task-bound artifact. Neither ever sees candidates, tests, results or other
conditions' guidance. Credentials are read only by the API provider, only from the configured
.env file, and are never written to artifacts, logs or child-process environments.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from .common import REPO, read_json, sha256_bytes, sha256_text, utc_now, write_json
from . import guidance

CODEX_WRAPPER = """You are being used as a single-response text model, not as a coding agent.
Do not use any tools. Do not read, write or list files, run commands, browse, or delegate.
Produce exactly one response to the request below: follow the SYSTEM PROMPT as your
instructions and treat the USER MESSAGE as the user's input. Output only the response text.

=== SYSTEM PROMPT ===
{system}
=== END SYSTEM PROMPT ===

=== USER MESSAGE ===
{user}
=== END USER MESSAGE ===
"""

CODEX_DISABLED = ('shell_tool', 'apps', 'plugins', 'multi_agent', 'image_generation', 'browser_use',
                  'computer_use', 'hooks', 'skill_search', 'tool_suggest', 'goals', 'in_app_browser')
ALLOWED_ITEMS = {'agent_message', 'reasoning'}


def codex_command(model, effort, workdir, output):
    command = [shutil.which('codex') or 'codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
               '--skip-git-repo-check', '--strict-config', '-s', 'read-only', '-C', str(workdir), '-m', model,
               '-c', f'model_reasoning_effort="{effort}"', '-c', 'web_search="disabled"', '--json',
               '-o', str(output)]
    for feature in CODEX_DISABLED:
        command += ['--disable', feature]
    return command + ['-']


class CodexIsolationError(RuntimeError):
    """The event stream showed a tool, command, file or search item, or extra files appeared."""


def child_environment():
    """Strip credentials and repository hints from any frontier child process."""
    return {k: v for k, v in os.environ.items()
            if not k.upper().startswith(('OPENAI', 'ANTHROPIC', 'CSC2108', 'FRONTIER', 'GITHUB', 'GH_'))}


def codex_infer(*, system, user, evidence, work_root, model='gpt-6.2-sol', effort='medium', timeout=900):
    """One fresh, ephemeral, tool-less Codex session in an empty directory; exactly one model response.

    Returns {'text', 'isolation', 'usage', 'wall_seconds', 'started_utc'}. Raises subprocess.TimeoutExpired,
    RuntimeError (no response) or CodexIsolationError. No retries.
    """
    message = CODEX_WRAPPER.format(system=system, user=user)
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    isolated = Path(tempfile.mkdtemp(prefix='iso-', dir=work_root))
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    last = evidence / 'last-message.txt'
    (evidence / 'input.txt').write_text(message, encoding='utf-8')
    command = codex_command(model, effort, isolated, last)
    started_utc, started = utc_now(), time.monotonic()
    try:
        proc = subprocess.run(command, input=message.encode('utf-8'), capture_output=True, timeout=timeout,
                              cwd=isolated, env=child_environment())
    except subprocess.TimeoutExpired as error:
        (evidence / 'timeout.txt').write_text(f'timeout after {timeout} s\n', encoding='utf-8')
        (evidence / 'events.jsonl').write_bytes(error.stdout or b'')
        shutil.rmtree(isolated, ignore_errors=True)
        raise
    wall = time.monotonic() - started
    (evidence / 'events.jsonl').write_bytes(proc.stdout)
    (evidence / 'stderr.txt').write_bytes(proc.stderr[-20000:])
    events = [json.loads(line) for line in proc.stdout.decode('utf-8', 'replace').splitlines() if line.strip().startswith('{')]
    items = [e.get('item', {}).get('type') for e in events if e.get('type') == 'item.completed']
    usage = next((e.get('usage') for e in events if e.get('type') == 'turn.completed'), None)
    thread = next((e.get('thread_id') for e in events if e.get('type') == 'thread.started'), None)
    violations = sorted({i for i in items if i not in ALLOWED_ITEMS})
    leftover = sorted(p.name for p in isolated.iterdir())
    text = last.read_text(encoding='utf-8').strip() + '\n' if last.exists() else ''
    if proc.returncode != 0 or not text.strip():
        raise RuntimeError(f'Codex inference failed (rc={proc.returncode}); see {evidence}')
    if violations or leftover or items.count('agent_message') != 1:
        raise CodexIsolationError(f'Codex isolation violated: items={items} files={leftover}; see {evidence}')
    isolation = {
        'mechanism': 'codex exec, fresh ephemeral session, empty temporary working directory, user config '
                     'and exec rules ignored, read-only sandbox, web search and listed features disabled, '
                     'credential-like variables removed from the environment',
        'codex_cli_version': subprocess.run([command[0], '--version'], capture_output=True, text=True).stdout.strip(),
        # Pass 3: provenance without machine paths (binary basename, placeholder working directory).
        'command': [Path(command[0]).name] + ['<isolated-empty-tmpdir>' if c == str(isolated) else c
                                               for c in command[1:] if c != str(last)],
        'disabled_features': list(CODEX_DISABLED),
        'thread_id': thread, 'completed_item_types': items, 'tool_events': violations,
        'post_run_workdir_files': leftover, 'events_sha256': sha256_bytes(proc.stdout),
        'input_sha256': sha256_text(message), 'wrapper_sha256': sha256_text(CODEX_WRAPPER),
        'limits': 'Codex harness instructions and its own tool descriptions remain in the model context; '
                  'they cannot be removed. Tool isolation is verified post hoc from the event stream, '
                  'which contained no tool, command, file or search events.',
    }
    shutil.rmtree(isolated, ignore_errors=True)
    return {'text': text, 'isolation': isolation, 'usage': usage, 'wall_seconds': round(wall, 2),
            'started_utc': started_utc}


def codex_author(*, kind, prompt_id, statement, task_id, out_path, work_root, model='gpt-6.2-sol',
                 effort='medium', label='codex-replay', timeout=900):
    """One fresh, ephemeral Codex session in an empty directory; one model response."""
    system_prompt = guidance.PROMPTS[prompt_id][1]
    result = codex_infer(system=system_prompt, user=statement, evidence=Path(str(out_path) + '.codex'),
                         work_root=work_root, model=model, effort=effort, timeout=timeout)
    record = guidance.artifact(
        kind=kind, prompt_id=prompt_id, statement=statement, text=result['text'], task_id=task_id,
        provider='codex-replay', requested_model=model, observed_model=None, reasoning_effort=effort,
        generation={'interface': 'codex exec --json', 'started_utc': result['started_utc'],
                    'harness_wall_seconds': result['wall_seconds'],
                    'max_output_tokens': None, 'note': 'Harness wall time includes Codex startup; not API latency.'},
        usage={'codex_reported': result['usage'],
               'note': 'Codex token counts include its harness context; not comparable to API usage.'},
        latency_seconds=None, cost_usd=None, isolation=result['isolation'], label=label)
    guidance.save_artifact(out_path, record)
    return record


# ----------------------------------------------------------------------------- direct API
PRICE_STANDARD = {'input': 2.00, 'output': 10.00}        # USD per 1M tokens, verified 2026-11-21
PRICE_CONSERVATIVE = {'input': 12.00, 'output': 60.00}   # highest unlabeled tier on the pricing page
MAX_REQUESTS, MAX_USD = 20, 10.00  # pass 4 brief: at most 20 paid requests and $10 in total


def read_env(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_file():
    return Path(os.environ.get('CSC2108_ENV_FILE') or REPO.parent / '.env')


class Ledger:
    """Write-ahead ledger: a request is recorded as pending before it is sent.

    Pass 3: every read-modify-write holds an exclusive lock file and re-reads the ledger, so concurrent
    processes (for example an E run and a B run) can never lose a reservation or exceed the ceilings.
    """
    LOCK_TIMEOUT = 60

    def __init__(self, path):
        self.path = Path(path)
        with self._locked():  # loads under the lock (Windows cannot read a file while it is being replaced)
            pass

    def _load(self):
        return read_json(self.path) if self.path.exists() else {
            'max_requests': MAX_REQUESTS, 'max_usd': MAX_USD, 'price_standard_per_1m': PRICE_STANDARD,
            'price_conservative_per_1m': PRICE_CONSERVATIVE, 'requests': [], 'metadata_calls': []}

    def _locked(self):
        ledger = self

        class _Lock:
            def __enter__(self):
                lock = ledger.path.with_name(ledger.path.name + '.lock')
                lock.parent.mkdir(parents=True, exist_ok=True)
                deadline = time.monotonic() + ledger.LOCK_TIMEOUT
                while True:
                    try:
                        self.fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        self.lock = lock
                        break
                    except (FileExistsError, PermissionError):  # Windows: a lock being deleted is PermissionError
                        if time.monotonic() > deadline:
                            raise RuntimeError(f'ledger lock {lock} held for over {ledger.LOCK_TIMEOUT} s; no paid call')
                        time.sleep(0.05)
                ledger.data = ledger._load()
                return ledger

            def __exit__(self, *exc):
                os.close(self.fd)
                os.unlink(self.lock)
                return False

        return _Lock()

    def spent_conservative(self):
        total = 0.0
        for item in self.data['requests']:
            usage = item.get('usage') or {}
            if usage.get('prompt_tokens') is not None and usage.get('completion_tokens') is not None:
                total += (usage['prompt_tokens'] * PRICE_CONSERVATIVE['input'] +
                          usage['completion_tokens'] * PRICE_CONSERVATIVE['output']) / 1e6
            else:  # Unknown usage: charge the full pre-request bound.
                total += item['bound_usd_conservative']
        return total

    def reserve(self, entry):
        with self._locked():
            if len(self.data['requests']) >= min(self.data.get('max_requests', MAX_REQUESTS), MAX_REQUESTS):
                raise RuntimeError('API request ceiling reached; no further paid calls')
            if self.spent_conservative() + entry['bound_usd_conservative'] > min(self.data.get('max_usd', MAX_USD), MAX_USD):
                raise RuntimeError('Conservative spending bound would exceed the ceiling')
            self.data['requests'].append(entry | {'state': 'pending'})
            write_json(self.path, self.data)
            return len(self.data['requests']) - 1

    def finish(self, index, **fields):
        with self._locked():
            self.data['requests'][index].update(fields)
            write_json(self.path, self.data)


def api_model_metadata(ledger_path):
    """GET /v1/models/{model}: no inference, no billing; confirms key and model access before paid calls."""
    config = read_env(env_file())
    model = config['FRONTIER_MODEL']
    api_model = model.split('/', 1)[1] if model.startswith('openai/') else model
    request = urllib.request.Request('https://api.openai.com/v1/models/' + api_model,
                                     headers={'Authorization': 'Bearer ' + config['OPENAI_API_KEY']})
    del config
    ledger = Ledger(ledger_path)
    entry = {'route': 'GET /v1/models/' + api_model, 'utc': utc_now(), 'billable_inference': False}
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
            entry.update(http_status=response.status, model=payload.get('id'), owned_by=payload.get('owned_by'))
    except urllib.error.HTTPError as error:
        entry.update(http_status=error.code, error=error.read()[:1000].decode('utf-8', 'replace'))
    with ledger._locked():
        ledger.data['metadata_calls'].append(entry)
        write_json(ledger.path, ledger.data)
    return entry


class ApiRequestError(RuntimeError):
    """A reserved paid request failed (HTTP or transport). It is never retried."""


def api_config():
    config = read_env(env_file())
    model = config['FRONTIER_MODEL']
    return config, model, (model.split('/', 1)[1] if model.startswith('openai/') else model)


def api_chat(*, messages, ledger_path, entry, max_completion_tokens=8000, effort='medium', timeout=600):
    """One reserved, ledgered POST /v1/chat/completions. No retries, no fallback.

    ``entry`` holds ledger metadata (purpose, condition, task...). Returns
    {'payload', 'text', 'finish_reason', 'usage', 'latency_seconds', 'cost_usd', 'request_id',
    'ledger_index', 'api_model', 'configured_model', 'started_utc'}.
    """
    config, model, api_model = api_config()
    body = {'model': api_model, 'messages': messages, 'max_completion_tokens': max_completion_tokens,
            'reasoning_effort': effort}
    characters = sum(len(m.get('content') or '') for m in messages)
    estimated_input = characters // 3 + 50 * len(messages)  # conservative (~3 chars/token)
    bound = (estimated_input * PRICE_CONSERVATIVE['input'] + max_completion_tokens * PRICE_CONSERVATIVE['output']) / 1e6
    ledger = Ledger(ledger_path)
    index = ledger.reserve(dict(entry) | {
        'configured_model': model, 'api_model': api_model, 'reasoning_effort': effort,
        'max_completion_tokens': max_completion_tokens, 'estimated_input_tokens': estimated_input,
        'bound_usd_conservative': round(bound, 4), 'reserved_utc': utc_now(),
        'request_body_sha256': sha256_text(json.dumps(body, sort_keys=True))})
    request = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json',
                                              'Authorization': 'Bearer ' + config['OPENAI_API_KEY']})
    del config
    started_utc, started = utc_now(), time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # no retries by design
            payload = json.load(response)
            request_id = response.headers.get('x-request-id')
            status = response.status
    except urllib.error.HTTPError as error:
        detail = error.read()[:4000].decode('utf-8', 'replace')
        ledger.finish(index, state='http_error', http_status=error.code, error=detail,
                      latency_seconds=round(time.monotonic() - started, 2), request_id=error.headers.get('x-request-id'))
        raise ApiRequestError(f'API HTTP {error.code}: {detail[:500]}') from None
    except Exception as error:
        ledger.finish(index, state='transport_error', error=f'{type(error).__name__}: {error}',
                      latency_seconds=round(time.monotonic() - started, 2))
        raise ApiRequestError(f'API transport error: {type(error).__name__}: {error}') from None
    latency = time.monotonic() - started
    usage = payload.get('usage') or {}
    choice = payload['choices'][0]
    text = (choice['message'].get('content') or '').strip() + '\n'
    cost = None
    if usage.get('prompt_tokens') is not None and usage.get('completion_tokens') is not None:
        cost = (usage['prompt_tokens'] * PRICE_STANDARD['input'] + usage['completion_tokens'] * PRICE_STANDARD['output']) / 1e6
    ledger.finish(index, state='completed', http_status=status, request_id=request_id,
                  observed_model=payload.get('model'), finish_reason=choice.get('finish_reason'),
                  usage=usage, latency_seconds=round(latency, 2), cost_usd_standard=None if cost is None else round(cost, 5),
                  completed_utc=utc_now())
    return {'payload': payload, 'text': text, 'finish_reason': choice.get('finish_reason'), 'usage': usage,
            'latency_seconds': round(latency, 2), 'cost_usd': cost, 'request_id': request_id, 'ledger_index': index,
            'api_model': api_model, 'configured_model': model, 'started_utc': started_utc}


def api_author(*, kind, prompt_id, statement, task_id, out_path, ledger_path, max_completion_tokens=8000,
               effort='medium', label='openai-api', purpose, timeout=600):
    system_prompt = guidance.PROMPTS[prompt_id][1]
    result = api_chat(messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': statement}],
                      ledger_path=ledger_path, max_completion_tokens=max_completion_tokens, effort=effort,
                      timeout=timeout, entry={'task_id': task_id, 'kind': kind, 'prompt_id': prompt_id,
                                              'purpose': purpose})
    raw_path = Path(str(out_path) + '.response.json')
    write_json(raw_path, result['payload'])
    if result['finish_reason'] != 'stop':
        raise RuntimeError(f"API response finish_reason={result['finish_reason']}; raw saved at {raw_path}")
    record = guidance.artifact(
        kind=kind, prompt_id=prompt_id, statement=statement, text=result['text'], task_id=task_id,
        provider='openai-api', requested_model=result['api_model'], observed_model=result['payload'].get('model'),
        reasoning_effort=effort,
        generation={'interface': 'POST /v1/chat/completions', 'max_completion_tokens': max_completion_tokens,
                    'started_utc': result['started_utc'], 'finish_reason': result['finish_reason'],
                    'request_id': result['request_id'], 'retries': 0, 'ledger_index': result['ledger_index']},
        usage=result['usage'], latency_seconds=result['latency_seconds'], cost_usd=result['cost_usd'],
        isolation={'mechanism': 'direct HTTPS request; statement-only input'}, label=label)
    guidance.save_artifact(out_path, record)
    return record
