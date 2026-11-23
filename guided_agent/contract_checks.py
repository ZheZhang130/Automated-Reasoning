"""D-active (pass 4): the contract's concrete checks are EXECUTED against the candidate, not just read.

Flow (still one upfront frontier call, the contract): the contract's K-checks are parsed once before the session;
whenever the agent runs the recognized public test, the harness also runs the SAME judged candidate on every
accepted check input inside the agent's own sandbox container (network-less, read-only, unprivileged) and appends
the results below the judge-public report. No action, model call or frontier request is added.

What the model sees is always labelled by its trust level:

* judge-public report   authoritative (the team judge, real expected outputs);
* contract checks       "expected output proposed by the stronger model, NOT verified" (mode ``active``), or only
                        the program's own output on the contract's inputs (control mode ``inputs-only``).

Harness-side validation without any reference solution (benchmark-safe): a check is dropped if it is malformed, a
duplicate, too large, or if its input equals a public-test input while its expected output contradicts the public
expected output (``contradicts_public``). Everything else stays ``unverified``. Reference-based correctness labels
for development analysis are computed offline and never shown to the model.
"""
import json
import re
import time

from .checkers import outputs_match

MAX_CHECKS = 6
MAX_INPUT_CHARS = 2000
MAX_SHOW = 300
CASE_TIMEOUT = 3.0
FENCE = re.compile(r'```[a-z-]*\n(.*?)\n\s*```', re.S)
MODES = ('active', 'inputs-only')


def _section(text, name):
    match = re.search(r'^## ' + name + r'\s*$(.*?)(?=^## |\Z)', text, re.S | re.M)
    return match.group(1) if match else ''


def parse_checks(text):
    """(stdin, expected) pairs from a contract-v3 'Test suggestions' section (same rule as pass-2 scoring)."""
    checks = []
    for chunk in re.split(r'(?=K-\d)', _section(text, 'Test suggestions')):
        if not chunk.startswith('K-'):
            continue
        fences = [re.sub(r'(?m)^\s{0,4}', '', f) for f in FENCE.findall(chunk)]
        purpose = ''
        for line in chunk.split('```', 1)[0].splitlines():
            text = re.sub(r'^K-\d+\W*', '', line.strip()) if line.strip().startswith('K-') else line.strip()
            text = re.sub(r'\(?\bPOST-\d+(?:\s*,\s*POST-\d+)*\)?[:.]?', '', text)
            text = re.sub(r'^[\s*_:\-–—.]+|[\s*_]+$', '', text)
            if text and not re.match(r'(?i)^(stdin|input|expected)', text):
                purpose = text
                break
        entry = {'id': chunk.split()[0].rstrip(':'), 'purpose': purpose[:160]}
        if len(fences) >= 2:
            entry |= {'stdin': fences[0].strip() + '\n', 'expected': fences[1].strip()}
        checks.append(entry)
    return checks


def validate(checks, public_cases):
    """Benchmark-safe validation. Returns (accepted, all_with_status)."""
    public = {c['input'].strip(): c['output'] for c in public_cases}
    accepted, seen, labelled = [], set(), []
    for check in checks:
        status = 'unverified'
        if 'stdin' not in check or not check['stdin'].strip() or not check.get('expected', '').strip():
            status = 'malformed'
        elif len(check['stdin']) > MAX_INPUT_CHARS:
            status = 'too_large'
        elif check['stdin'].strip() in seen:
            status = 'duplicate'
        elif check['stdin'].strip() in public:
            ok = outputs_match(check['expected'], public[check['stdin'].strip()])
            status = 'matches_public' if ok else 'contradicts_public'
        if status in ('unverified', 'matches_public') and len(accepted) < MAX_CHECKS:
            accepted.append(check | {'status': status})
            seen.add(check['stdin'].strip())
        elif status in ('unverified', 'matches_public'):
            status = 'over_limit'
        labelled.append({k: check.get(k) for k in ('id', 'purpose')} | {'status': status})
    return accepted, labelled


RUNNER = '\n'.join([
    'import json, subprocess, sys',
    'cases = json.loads(sys.stdin.read())',
    'out = []',
    'for case in cases:',
    '    try:',
    "        p = subprocess.run([sys.executable, '-I', '/workspace/solution.py'], input=case.encode(),",
    '                           capture_output=True, timeout=%s)' % CASE_TIMEOUT,
    "        out.append({'rc': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace')[:4000],",
    "                    'stderr': p.stderr.decode('utf-8', 'replace')[-600:]})",
    '    except subprocess.TimeoutExpired:',
    "        out.append({'rc': 'timeout', 'stdout': '', 'stderr': ''})",
    'print(json.dumps(out))', ''])


def _clip(text, cap=MAX_SHOW):
    text = text.rstrip('\n')
    return text if len(text) <= cap else text[:cap] + f'... [{len(text)} characters]'


class ContractChecker:
    def __init__(self, checks, mode):
        if mode not in MODES:
            raise ValueError(f'unknown contract-check mode {mode!r}')
        self.checks, self.mode = checks, mode
        self.runs = []

    def run(self, docker, container_id):
        """Run every accepted check on /workspace/solution.py inside the agent sandbox. Never on the host."""
        started = time.monotonic()
        try:
            proc = docker('exec', '-i', container_id, 'python', '-I', '-c', RUNNER,
                          input=json.dumps([c['stdin'] for c in self.checks]),
                          timeout=10 + CASE_TIMEOUT * len(self.checks) + 5)
            outputs = json.loads(proc.stdout)
        except Exception as error:
            entry = {'error': f'{type(error).__name__}: {error}'[:300], 'seconds': round(time.monotonic() - started, 3)}
            self.runs.append(entry)
            return entry, '[Contract checks] The harness could not run the contract checks this time.'
        results = []
        for check, output in zip(self.checks, outputs):
            if output['rc'] != 0:
                outcome = 'timeout' if output['rc'] == 'timeout' else 'error'
            elif self.mode == 'active':
                outcome = 'same' if outputs_match(output['stdout'], check['expected']) else 'different'
            else:
                outcome = 'ran'
            results.append({'id': check['id'], 'outcome': outcome, 'rc': output['rc']})
        entry = {'seconds': round(time.monotonic() - started, 3), 'results': results}
        self.runs.append(entry)
        return entry, self.render(outputs, results)

    def render(self, outputs, results):
        if self.mode == 'active':
            lines = ['[Contract checks: supplementary, NOT verified] A stronger model proposed these extra inputs and '
                     'derived their expected outputs by hand from the statement alone. They may be wrong. The '
                     'judge-public result above is authoritative; treat a difference as a reason to re-check the '
                     'requirement, not as proof.']
        else:
            lines = ['[Extra inputs: supplementary] The harness ran your program on these extra inputs. No expected '
                     'outputs are given; check the outputs against the statement yourself.']
        for check, output, result in zip(self.checks, outputs, results):
            head = f"{check['id']}" + (f" ({check['purpose']})" if check.get('purpose') and self.mode == 'active' else '')
            lines.append(f'{head}\n  input:\n{_indent(_clip(check["stdin"]))}')
            if self.mode == 'active':
                lines.append(f'  expected (proposed, unverified):\n{_indent(_clip(check["expected"]))}')
            if result['outcome'] in ('error', 'timeout'):
                detail = 'timed out' if result['outcome'] == 'timeout' else \
                    f"exited with code {output['rc']}: {_clip(output.get('stderr', ''), 200)}"
                lines.append(f'  your program {detail}')
            else:
                lines.append(f'  your program printed:\n{_indent(_clip(output["stdout"]) or "(nothing)")}')
                if self.mode == 'active':
                    lines.append('  -> same as proposed' if result['outcome'] == 'same' else '  -> DIFFERENT from proposed')
        if self.mode == 'active':
            different = sum(r['outcome'] != 'same' for r in results)
            lines.append(f'{different} of {len(results)} contract checks differ from the proposed output or failed.')
        return '\n'.join(lines)

    def summary(self):
        last = next((r for r in reversed(self.runs) if 'results' in r), None)
        return {'mode': self.mode, 'checks': len(self.checks), 'runs': len(self.runs),
                'seconds_total': round(sum(r.get('seconds', 0) for r in self.runs), 3),
                'errors': sum('error' in r for r in self.runs),
                'final_outcomes': [r['outcome'] for r in last['results']] if last else None}


def _indent(text):
    return '\n'.join('    ' + line for line in (text.splitlines() or ['']))
