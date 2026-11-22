"""Sanitize evidence before it is committed: no usernames, home directories, host names or credentials.

Private originals stay outside Git with their full provenance (and their recorded hashes). Committed copies
are passed through ``sanitize``; every replacement is a fixed placeholder, so a copy still shows *what kind*
of value was recorded (for example ``<HOME>\\AppData\\Roaming\\npm\\codex.CMD``) without the identifying part.
``scan`` is used by the tests and by the exporters to refuse a leaking copy.
"""
import getpass
import json
import os
import platform
import re
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}'),          # OpenAI-style keys
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),                # GitHub tokens
    re.compile(r'Bearer\s+[A-Za-z0-9._-]{20,}'),
    re.compile(r'(?i)(?:api[_-]?key|token|secret|password)\s*[=:]\s*["\']?[A-Za-z0-9._-]{16,}'),
]
HOME_PATTERNS = [  # group 1 is kept, the user-name component after it is replaced
    re.compile(r'(?i)(\b[A-Z]:[\\/]+Users[\\/]+)(?!<USER>)[^\\/"\s<>]+'),
    re.compile(r'(/(?:Users|home)/)(?!<USER>)[A-Za-z0-9._-]+'),
]


def _identity():
    values = {}
    try:
        values['<USER>'] = getpass.getuser()
    except Exception:
        pass
    values['<HOST>'] = platform.node()
    home = str(Path.home())
    values['<HOME>'] = home
    return {k: v for k, v in values.items() if v and len(v) >= 3}


def sanitize_text(text, identity=None):
    identity = _identity() if identity is None else identity
    home = identity.get('<HOME>')
    if home:
        for variant in {home, home.replace('\\', '\\\\'), home.replace('\\', '/')}:
            text = re.sub(re.escape(variant), '<HOME>', text, flags=re.I)
    for pattern in HOME_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) + '<USER>', text)
    for placeholder in ('<USER>', '<HOST>'):
        value = identity.get(placeholder)
        if value:
            text = re.sub(r'(?<![A-Za-z0-9])' + re.escape(value) + r'(?![A-Za-z0-9])', placeholder, text, flags=re.I)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub('<REDACTED-SECRET>', text)
    return text


def sanitize(value, identity=None):
    identity = _identity() if identity is None else identity
    if isinstance(value, str):
        return sanitize_text(value, identity)
    if isinstance(value, list):
        return [sanitize(v, identity) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v, identity) for k, v in value.items()}
    return value


def scan(text, identity=None):
    """Findings (kind, excerpt) of identifying or secret material in ``text``."""
    identity = _identity() if identity is None else identity
    findings = []
    for pattern in HOME_PATTERNS:
        findings += [('home_path', m.group(0)) for m in pattern.finditer(text)]
    for pattern in SECRET_PATTERNS:
        findings += [('secret', m.group(0)[:12] + '...') for m in pattern.finditer(text)]
    for placeholder in ('<USER>', '<HOST>'):
        value = identity.get(placeholder)
        if value and re.search(r'(?<![A-Za-z0-9])' + re.escape(value) + r'(?![A-Za-z0-9])', text, re.I):
            findings.append((placeholder.strip('<>').lower(), placeholder))
    for name in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        secret = os.environ.get(name)
        if secret and len(secret) > 12 and secret in text:
            findings.append(('secret', name))
    return findings


def copy_sanitized_json(source, target):
    data = json.loads(Path(source).read_text(encoding='utf-8'))
    clean = sanitize(data)
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(clean, indent=2, ensure_ascii=False) + '\n'
    if scan(text):
        raise ValueError(f'sanitized copy of {source} still leaks: {scan(text)[:3]}')
    Path(target).write_text(text, encoding='utf-8', newline='\n')
    return clean
