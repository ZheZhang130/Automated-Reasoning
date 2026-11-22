"""Endres-style evaluation of contract test suggestions (correctness and discriminative power).

Endres et al. (FSE'24, Sec. 2.1) score a generated postcondition by (i) test-set correctness against a
reference implementation and (ii) bug-completeness: the fraction of distinct *natural* buggy
implementations it rejects. We adapt both to the contract's concrete checks (K-checks / v2 test
suggestions), using pass-1 programs for the same task as the natural implementations:

* reference  = a pass-1 submission that passed all 40 hidden cases (judge 0.2.1);
* mutants    = distinct pass-1 submissions that failed hidden cases (natural, plausible-but-wrong).

A check is CORRECT if the reference's output equals the check's expected output (token-wise, as the
judge compares). A correct check KILLS a mutant if the mutant's output differs (or it errors/times out).
Every program runs inside a network-less, read-only, unprivileged Docker container, never on the host.
Programs and outputs are not written to Git; only counts are reported.

usage: python -I contract_checks.py <pass1_study> <pass2_study> <out.json>
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

IMAGE = 'python:3.11-slim-bookworm'
HARNESS = r'''
import json, subprocess, sys
cases = json.load(open('/c/cases.json'))
out = []
for case in cases:
    try:
        p = subprocess.run([sys.executable, '-I', '/c/program.py'], input=case.encode(), capture_output=True, timeout=5)
        out.append({'rc': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace')[:2000]})
    except subprocess.TimeoutExpired:
        out.append({'rc': 'TLE', 'stdout': ''})
print(json.dumps(out))
'''
FENCE = re.compile(r'```[a-z-]*\n(.*?)\n\s*```', re.S)


def section(text, name):
    match = re.search(r'^## ' + name + r'\s*$(.*?)(?=^## |\Z)', text, re.S | re.M)
    return match.group(1) if match else ''


def parse_checks(text, prompt_id):
    """Machine-checkable (stdin, expected stdout) pairs. v1 prose suggestions are not machine-checkable."""
    body = section(text, 'Test suggestions')
    checks = []
    if prompt_id == 'contract-v3':
        for chunk in re.split(r'(?=K-\d)', body):
            fences = [re.sub(r'(?m)^\s{0,4}', '', f) for f in FENCE.findall(chunk)]
            if len(fences) >= 2 and chunk.startswith('K-'):
                checks.append({'id': chunk.split()[0].rstrip(':'), 'stdin': fences[0].strip() + '\n',
                               'expected': fences[1].strip()})
    elif prompt_id == 'contract-v2':
        for chunk in re.split(r'\n(?=- )', body):
            expected = re.search(r'Expected (?:stdout )?`([^`]*)`', chunk)
            fences = [re.sub(r'(?m)^\s{0,4}', '', f) for f in FENCE.findall(chunk)]
            if expected and fences:
                checks.append({'id': f'T-{len(checks) + 1}', 'stdin': fences[0].strip() + '\n',
                               'expected': expected.group(1).strip()})
        if not checks:  # alternative v2 layout: "Stdin ```text …``` Stdout ```text …```" pairs
            fences = [re.sub(r'(?m)^\s{0,4}', '', f) for f in FENCE.findall(body)]
            for i in range(0, len(fences) - 1, 2):
                checks.append({'id': f'T-{i // 2 + 1}', 'stdin': fences[i].strip() + '\n',
                               'expected': fences[i + 1].strip()})
    return checks


def tokens(text):
    return [line.split() for line in text.strip().splitlines() if line.strip()]


def run_program(program, inputs):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'program.py').write_bytes(program)
        Path(tmp, 'cases.json').write_text(json.dumps(inputs), encoding='utf-8')
        Path(tmp, 'harness.py').write_text(HARNESS, encoding='utf-8')
        proc = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '512m',
                               '--cpus', '1', '--pids-limit', '64', '--user', '65534:65534', '--cap-drop', 'ALL',
                               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                               '-v', f'{tmp}:/c:ro', IMAGE, 'python', '-I', '/c/harness.py'],
                              capture_output=True, text=True, timeout=60 + 6 * len(inputs))
        return json.loads(proc.stdout)


def programs(pass1, task_id):
    """Distinct pass-1 submissions for the task with their hidden status."""
    seen = {}
    for result in pass1.glob('runs/*/*/result.json'):
        record = json.loads(result.read_text(encoding='utf-8'))
        if record.get('task_id') != task_id or not (result.parent / 'submission.py').exists():
            continue
        evaluation = result.parent.parent / 'eval' / (record['run_id'] + '.json')
        if not evaluation.exists():
            continue
        hidden = json.loads(evaluation.read_text(encoding='utf-8'))
        code = (result.parent / 'submission.py').read_bytes()
        seen.setdefault(record.get('submission_sha256'), {'code': code, 'status': hidden.get('status'),
                                                          'passed': hidden.get('passed'), 'runs': []})
        seen[record.get('submission_sha256')]['runs'].append(result.parent.name)
    return seen


def main(pass1, pass2, out):
    pass1, pass2 = Path(pass1), Path(pass2)
    artifacts = sorted(pass1.glob('guidance/*/*.contract-v*.json')) + sorted(pass2.glob('guidance/*/*.contract-v*.json'))
    report = []
    for path in artifacts:
        raw = json.loads(path.read_text(encoding='utf-8'))
        if raw.get('schema') != 'csc2108-guidance-v1':  # e.g. raw API *.response.json next to an artifact
            continue
        checks = parse_checks(raw['text'], raw['prompt_id'])
        pool = programs(pass1, raw['task_id'])
        references = [p for p in pool.values() if p['status'] == 'pass']
        mutants = [p for p in pool.values() if p['status'] == 'candidate_failure']
        entry = {'artifact': path.name, 'provider': raw.get('provider'), 'prompt_id': raw['prompt_id'],
                 'task_id': raw['task_id'], 'words': raw.get('word_count'), 'checks': len(checks),
                 'references': len(references), 'mutants': len(mutants)}
        if checks and references:
            inputs = [c['stdin'] for c in checks]
            reference = run_program(references[0]['code'], inputs)
            correct = [tokens(r['stdout']) == tokens(c['expected']) and r['rc'] == 0 for r, c in zip(reference, checks)]
            entry['correct_checks'] = sum(correct)
            entry['incorrect_check_ids'] = [c['id'] for c, ok in zip(checks, correct) if not ok]
            killed = 0
            for mutant in mutants:
                outputs = run_program(mutant['code'], inputs)
                if any(ok and (o['rc'] != 0 or tokens(o['stdout']) != tokens(c['expected']))
                       for o, c, ok in zip(outputs, checks, correct)):
                    killed += 1
            entry['mutants_killed'] = killed
        report.append(entry)
        print(json.dumps(entry), flush=True)
    Path(out).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')


def score_runs(pass1, pass2, out):
    """Do final programs satisfy the task's contract-v3 K-checks (only checks verified correct vs a reference)?

    This measures prevention of K-detectable mistakes, independently of whether Qwen ran any check itself.
    """
    pass1, pass2 = Path(pass1), Path(pass2)
    report = []
    for path in sorted(pass2.glob('guidance/*/*.contract-v3.codex.json')):
        raw = json.loads(path.read_text(encoding='utf-8'))
        task = raw['task_id']
        checks = parse_checks(raw['text'], 'contract-v3')
        references = [p for p in programs(pass1, task).values() if p['status'] == 'pass']
        if not checks or not references:
            continue
        inputs = [c['stdin'] for c in checks]
        reference = run_program(references[0]['code'], inputs)
        checks = [c for r, c in zip(reference, checks) if r['rc'] == 0 and tokens(r['stdout']) == tokens(c['expected'])]
        inputs = [c['stdin'] for c in checks]
        for study in (pass1, pass2):
            for result in study.glob('runs/*/*/result.json'):
                record = json.loads(result.read_text(encoding='utf-8'))
                if record.get('task_id') != task or record.get('condition') not in ('A', 'C', 'D', 'E') or record.get('aci'):
                    continue
                spec = json.loads((result.parent / 'spec.json').read_text(encoding='utf-8')) if (result.parent / 'spec.json').exists() else {}
                label = record['condition'] + (('/' + spec['variant']) if spec.get('variant') else '') + \
                    ('' if study == pass2 else ' (pass 1)')
                if record.get('seed', 2108) != 2108:
                    label += f" s{record['seed']}"
                submission = result.parent / 'submission.py'
                if not submission.exists():
                    report.append({'task_id': task, 'run': label, 'program': False})
                    continue
                outputs = run_program(submission.read_bytes(), inputs)
                ok = sum(o['rc'] == 0 and tokens(o['stdout']) == tokens(c['expected']) for o, c in zip(outputs, checks))
                report.append({'task_id': task, 'run': label, 'program': True, 'k_satisfied': ok, 'k_total': len(checks)})
    Path(out).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    for row in sorted(report, key=lambda r: (r['task_id'], r['run'])):
        print(row['task_id'].replace('lcb-atcoder-', ''), row['run'], f"{row.get('k_satisfied')}/{row.get('k_total')}"
              if row['program'] else 'no program')


if __name__ == '__main__':
    if sys.argv[1] == '--score-runs':
        score_runs(*sys.argv[2:5])
    else:
        main(*sys.argv[1:4])
