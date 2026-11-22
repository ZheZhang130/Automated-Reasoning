"""Offline counterfactual: would salvaging a truncated heredoc have produced a usable program?

usage (repository root):  python -m reasoning_effectiveness.pass3.diagnostics.salvage_probe OUT.json STUDY ...

For every truncated (done_reason == 'length') response of a Qwen run (original agent only: no ACI, no probe)
that opened a heredoc to /workspace/solution.py, take the longest line prefix that ``ast.parse`` accepts. If
that prefix both reads input and prints, run it on the task's PUBLIC tests in a network-less, read-only,
unprivileged Docker container and compare with judge 0.2.1's comparator. Hidden tests are never used. No
model is called; nothing is written back into any run. Model-generated code never runs on the host.
"""
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from guided_agent.checkers import outputs_match
from reasoning_effectiveness.pass3.diagnostics.failure_mechanisms import FENCE, HEREDOC, PRINTS, READS, parsable_prefix

IMAGE = 'python:3.11-slim-bookworm'
HARNESS = r'''
import json, subprocess, sys
cases = json.load(open('/c/cases.json'))
out = []
for case in cases:
    try:
        p = subprocess.run([sys.executable, '-I', '/c/program.py'], input=case.encode(), capture_output=True, timeout=6)
        out.append({'rc': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace')[:20000]})
    except subprocess.TimeoutExpired:
        out.append({'rc': 'TLE', 'stdout': ''})
print(json.dumps(out))
'''


def run_public(program, cases):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'program.py').write_text(program, encoding='utf-8', newline='\n')
        Path(tmp, 'cases.json').write_text(json.dumps([c['input'] for c in cases]), encoding='utf-8')
        Path(tmp, 'harness.py').write_text(HARNESS, encoding='utf-8')
        proc = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only', '--memory', '512m',
                               '--cpus', '1', '--pids-limit', '64', '--user', '65534:65534', '--cap-drop', 'ALL',
                               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                               '-v', f'{tmp}:/c:ro', IMAGE, 'python', '-I', '/c/harness.py'],
                              capture_output=True, text=True, timeout=60 + 8 * len(cases))
        results = json.loads(proc.stdout)
    return sum(1 for r, c in zip(results, cases) if r['rc'] == 0 and outputs_match(r['stdout'], c['output']))


def main(out, *studies):
    rows, cache = [], {}
    for study in map(Path, studies):
        for result in sorted(study.glob('runs/*/*/result.json')):
            run_dir = result.parent
            if run_dir.parent.name.startswith(('integration', 'b-', 'probe')) or 'incomplete' in run_dir.name:
                continue
            record = json.loads(result.read_text(encoding='utf-8'))
            if record.get('aci') or record.get('coder') or str(record.get('coding_model', '')).startswith('frontier'):
                continue
            agents = sorted(run_dir.glob('agent-*'))
            bundle = study / 'bundles' / record['task_id'] / 'public_tests.json'
            if not agents or not (agents[0] / 'ollama-responses.json').exists() or not bundle.exists():
                continue
            cases = json.loads(bundle.read_text(encoding='utf-8'))
            responses = json.loads((agents[0] / 'ollama-responses.json').read_text(encoding='utf-8'))
            for index, response in enumerate(responses):
                if response.get('done_reason') != 'length':
                    continue
                text = (response.get('message') or {}).get('content') or ''
                fence = FENCE.search(text)
                heredoc = HEREDOC.search(text[fence.end():]) if fence else None
                row = {'run': f'{study.name}/{run_dir.parent.name}/{run_dir.name}', 'task_id': record['task_id'],
                       'condition': record.get('condition'), 'response_index': index, 'heredoc': bool(heredoc)}
                if heredoc:
                    n, prefix = parsable_prefix(heredoc.group(2))
                    code_lines = sum(1 for l in prefix.split('\n') if l.strip() and not l.strip().startswith('#'))
                    row.update(prefix_lines=n, prefix_code_lines=code_lines,
                               reads_and_prints=bool(READS.search(prefix) and PRINTS.search(prefix)))
                    if row['reads_and_prints']:
                        key = (record['task_id'], prefix)
                        if key not in cache:
                            try:
                                cache[key] = run_public(prefix, cases)
                            except Exception as error:  # report, never hide
                                cache[key] = f'error: {type(error).__name__}'
                        row.update(public_passed=cache[key], public_total=len(cases))
                rows.append(row)
    summary = Counter()
    for r in rows:
        summary['truncated'] += 1
        summary['with_heredoc'] += r['heredoc']
        summary['reads_and_prints_prefix'] += bool(r.get('reads_and_prints'))
        if isinstance(r.get('public_passed'), int):
            summary['prefix_passes_all_public'] += r['public_passed'] == r['public_total']
            summary['prefix_passes_some_public'] += 0 < r['public_passed'] < r['public_total']
    runs_rescuable = {r['run'] for r in rows if isinstance(r.get('public_passed'), int) and r['public_passed'] == r['public_total']}
    data = {'summary': dict(summary), 'distinct_programs_run': len(cache), 'runs_with_a_public_passing_salvage':
            sorted(runs_rescuable), 'rows': rows}
    Path(out).write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(data['summary']), len(cache), 'programs;', len(runs_rescuable), 'runs with a public-passing salvage')


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
