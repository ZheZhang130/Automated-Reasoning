"""Strict API ledger guard and hardened isolated Codex replay wrapper for enhanced_de.

Safety invariants:
1. Never falls back silently to the official 2000/$100 ledger ceiling. Any paid
   API call MUST supply an existing ledger file explicitly capped at
   max_requests <= 20 and max_usd <= 10.0.
2. Enforces a conservative input-character cap and max_completion_tokens cap
   before reservation.
3. Hardens isolated Codex replay by auditing the ENTIRE event stream (including
   item.started, malformed JSON lines, missing turn.completed, tool events, and
   non-empty post-run workdir).
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from guided_agent import providers
from guided_agent.common import read_json, sha256_bytes, sha256_text, utc_now, write_json

HARD_MAX_REQUESTS = 20
HARD_MAX_USD = 10.0
MAX_INPUT_CHARS_API = 48000  # ~15k conservative tokens
ALLOWED_EVENT_ITEM_TYPES = {'agent_message', 'reasoning'}


def init_ledger(path, *, max_requests=HARD_MAX_REQUESTS, max_usd=HARD_MAX_USD, note=''):
    """Initialize a fresh study ledger with strict v2 ceilings (refuses overwrite)."""
    path = Path(path)
    if max_requests > HARD_MAX_REQUESTS or max_usd > HARD_MAX_USD:
        raise ValueError(f'Ceilings ({max_requests}, ${max_usd}) exceed hard v2 cap ({HARD_MAX_REQUESTS}, ${HARD_MAX_USD})')
    if path.exists():
        raise FileExistsError(f'Ledger already exists: {path}')
    write_json(path, {
        'max_requests': int(max_requests),
        'max_usd': float(max_usd),
        'price_standard_per_1m': dict(providers.PRICE_STANDARD),
        'price_conservative_per_1m': dict(providers.PRICE_CONSERVATIVE),
        'requests': [],
        'metadata_calls': [],
        'note': note or 'CSC2108 enhanced_de v2 study ledger',
    })
    return path


def verify_ledger(ledger_path):
    """Fail closed if the ledger file is missing or exceeds v2 ceilings."""
    path = Path(ledger_path)
    if not path.is_file():
        raise RuntimeError(f'Refusing paid API call: v2 ledger missing at {path}')
    data = read_json(path)
    max_req = data.get('max_requests')
    max_usd = data.get('max_usd')
    if not isinstance(max_req, int) or max_req <= 0 or max_req > HARD_MAX_REQUESTS:
        raise RuntimeError(f'Refusing paid API call: ledger max_requests={max_req!r} exceeds hard v2 cap {HARD_MAX_REQUESTS}')
    if not isinstance(max_usd, (int, float)) or max_usd <= 0 or max_usd > HARD_MAX_USD:
        raise RuntimeError(f'Refusing paid API call: ledger max_usd={max_usd!r} exceeds hard v2 cap {HARD_MAX_USD}')
    used = len(data.get('requests') or [])
    return {'path': str(path), 'max_requests': max_req, 'max_usd': max_usd, 'requests_used': used}


def guarded_api_chat(*, messages, ledger_path, entry, max_completion_tokens=4096, effort='medium', timeout=300):
    """Execute one paid OpenAI API call strictly under the verified v2 ledger."""
    info = verify_ledger(ledger_path)
    total_chars = sum(len(m.get('content') or '') for m in messages)
    if total_chars > MAX_INPUT_CHARS_API:
        raise RuntimeError(f'Refusing paid API call: input length {total_chars} exceeds cap {MAX_INPUT_CHARS_API}')
    if max_completion_tokens > 8000:
        raise ValueError('max_completion_tokens exceeds 8000')
    tagged = dict(entry) | {'v2_ledger_cap': {'max_requests': info['max_requests'], 'max_usd': info['max_usd']}}
    return providers.api_chat(
        messages=messages,
        ledger_path=ledger_path,
        entry=tagged,
        max_completion_tokens=max_completion_tokens,
        effort=effort,
        timeout=timeout,
    )


def audit_codex_events(stdout_bytes):
    """Strict full-lifecycle audit of a codex exec --json event stream.

    Checks every non-empty line is valid JSON, checks BOTH item.started and
    item.completed for disallowed item types, verifies turn.completed exists,
    and verifies exactly one completed agent_message.
    """
    raw = stdout_bytes.decode('utf-8', 'replace')
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    events = []
    malformed = []
    for idx, ln in enumerate(lines):
        if not ln.startswith('{'):
            malformed.append(f'line {idx}: non-json prefix')
            continue
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError as exc:
            malformed.append(f'line {idx}: {exc}')
    started_types = [e.get('item', {}).get('type') for e in events if e.get('type') == 'item.started']
    completed_types = [e.get('item', {}).get('type') for e in events if e.get('type') == 'item.completed']
    violations = sorted({t for t in (started_types + completed_types) if t not in ALLOWED_EVENT_ITEM_TYPES})
    has_turn_completed = any(e.get('type') == 'turn.completed' for e in events)
    usage = next((e.get('usage') for e in events if e.get('type') == 'turn.completed'), None)
    thread = next((e.get('thread_id') for e in events if e.get('type') == 'thread.started'), None)
    agent_msg_count = completed_types.count('agent_message')
    return {
        'events_count': len(events),
        'malformed_lines': malformed,
        'started_item_types': started_types,
        'completed_item_types': completed_types,
        'violations': violations,
        'has_turn_completed': has_turn_completed,
        'agent_message_count': agent_msg_count,
        'usage': usage,
        'thread_id': thread,
    }


def isolated_codex_infer(*, system, user, evidence, work_root, model='gpt-6.2-sol', effort='medium', timeout=300):
    """Hardened isolated tool-less Codex inference with full event-lifecycle audit."""
    message = providers.CODEX_WRAPPER.format(system=system, user=user)
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    isolated = Path(tempfile.mkdtemp(prefix='iso-v2-', dir=work_root))
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    last = evidence / 'last-message.txt'
    (evidence / 'input.txt').write_text(message, encoding='utf-8')
    command = providers.codex_command(model, effort, isolated, last)
    started_utc, started = utc_now(), time.monotonic()
    try:
        proc = subprocess.run(
            command,
            input=message.encode('utf-8'),
            capture_output=True,
            timeout=timeout,
            cwd=isolated,
            env=providers.child_environment(),
        )
    except subprocess.TimeoutExpired as error:
        (evidence / 'timeout.txt').write_text(f'timeout after {timeout} s\n', encoding='utf-8')
        (evidence / 'events.jsonl').write_bytes(error.stdout or b'')
        shutil.rmtree(isolated, ignore_errors=True)
        raise
    wall = time.monotonic() - started
    (evidence / 'events.jsonl').write_bytes(proc.stdout)
    (evidence / 'stderr.txt').write_bytes(proc.stderr[-20000:])
    audit = audit_codex_events(proc.stdout)
    leftover = sorted(p.name for p in isolated.iterdir())
    text = last.read_text(encoding='utf-8').strip() + '\n' if last.exists() else ''
    shutil.rmtree(isolated, ignore_errors=True)
    if proc.returncode != 0 or not text.strip():
        raise RuntimeError(f'Codex inference failed (rc={proc.returncode}); see {evidence}')
    if (audit['violations'] or audit['malformed_lines'] or leftover
            or not audit['has_turn_completed'] or audit['agent_message_count'] != 1):
        raise providers.CodexIsolationError(
            f"Codex isolation audit failed: violations={audit['violations']} "
            f"malformed={audit['malformed_lines'][:3]} leftover={leftover} "
            f"turn_completed={audit['has_turn_completed']} msgs={audit['agent_message_count']}; see {evidence}"
        )
    isolation = {
        'mechanism': 'hardened isolated codex exec (empty tmpdir, read-only, tool flags disabled, '
                     'credentials stripped, full event-lifecycle audit including item.started)',
        'thread_id': audit['thread_id'],
        'started_item_types': audit['started_item_types'],
        'completed_item_types': audit['completed_item_types'],
        'tool_events': audit['violations'],
        'malformed_lines': audit['malformed_lines'],
        'post_run_workdir_files': leftover,
        'events_sha256': sha256_bytes(proc.stdout),
        'input_sha256': sha256_text(message),
        'wrapper_sha256': sha256_text(providers.CODEX_WRAPPER),
    }
    return {
        'text': text,
        'isolation': isolation,
        'usage': audit['usage'],
        'wall_seconds': round(wall, 2),
        'started_utc': started_utc,
    }
