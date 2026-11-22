"""Visible use of upfront guidance (C plan, D contract) in Qwen's first response (observable text only).

usage (repository root):  python -m reasoning_effectiveness.pass3.diagnostics.guidance_uptake OUT.json STUDY[@BATCH,...] ...

For each C/D run of the original agent: the distinctive words of the guidance artifact (length >= 6, absent
from the statement) and the share of them that reappear in the first model response, split into comment lines
and code lines; the first response's length, truncation and whether it already wrote a complete program;
whether any command executed a guidance check by hand (``printf ... | python solution.py``).
"""
import json
import re
import sys
from pathlib import Path

from guided_agent.analysis import MANUAL_RUN
from reasoning_effectiveness.pass3.diagnostics.failure_mechanisms import FENCE, HEREDOC

WORD = re.compile(r'[A-Za-z_][A-Za-z_]{5,}')
GENERIC = {'output', 'outputs', 'should', 'program', 'return', 'values', 'number', 'numbers', 'integer', 'integers',
           'example', 'length', 'answer', 'answers', 'string', 'strings', 'before', 'within'}


def words(text):
    return {w.lower() for w in WORD.findall(text or '')}


def main(out, *specs):
    rows = []
    for spec in specs:
        study, _, batches = spec.partition('@')
        study = Path(study)
        wanted = batches.split(',') if batches else None
        for result in sorted(study.glob('runs/*/*/result.json')):
            run_dir = result.parent
            if wanted and run_dir.parent.name not in wanted:
                continue
            record = json.loads(result.read_text(encoding='utf-8'))
            if record.get('condition') not in ('C', 'D') or record.get('aci') or 'incomplete' in run_dir.name:
                continue
            artifact = (record.get('guidance_provenance') or {}).get('artifact')
            if not artifact or not Path(artifact).exists():
                continue
            guidance = json.loads(Path(artifact).read_text(encoding='utf-8'))
            statement = json.loads((study / 'bundles' / record['task_id'] / 'task.json').read_text(encoding='utf-8'))['statement']
            distinctive = words(guidance['text']) - words(statement) - GENERIC
            agents = sorted(run_dir.glob('agent-*'))
            if not agents:
                continue
            responses = json.loads((agents[0] / 'ollama-responses.json').read_text(encoding='utf-8'))
            first = (responses[0].get('message') or {}).get('content') or '' if responses else ''
            fence = FENCE.search(first)
            heredoc = HEREDOC.search(first[fence.end():]) if fence else None
            body = heredoc.group(2) if heredoc else ''
            comment = words('\n'.join(l for l in body.split('\n') if l.strip().startswith('#')))
            code = words('\n'.join(l for l in body.split('\n') if l.strip() and not l.strip().startswith('#')))
            trajectory = json.loads((agents[0] / 'trajectory.json').read_text(encoding='utf-8'))['messages']
            commands = [m.get('content') or '' for m in trajectory if m.get('role') == 'assistant']
            rows.append({'run': f'{study.name}/{run_dir.parent.name}/{run_dir.name}', 'task_id': record['task_id'],
                         'condition': record['condition'], 'seed': record.get('seed'),
                         'prompt_id': guidance.get('prompt_id'), 'guidance_words': len(guidance['text'].split()),
                         'distinctive_guidance_words': len(distinctive),
                         'first_tokens': responses[0].get('eval_count') if responses else None,
                         'first_truncated': bool(responses) and responses[0].get('done_reason') == 'length',
                         'uptake_comments': round(len(distinctive & comment) / len(distinctive), 3) if distinctive else None,
                         'uptake_code': round(len(distinctive & code) / len(distinctive), 3) if distinctive else None,
                         'manual_checks_run': sum(bool(MANUAL_RUN.search(c)) for c in commands)})
    Path(out).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8', newline='\n')
    for condition in ('C', 'D'):
        items = [r for r in rows if r['condition'] == condition]
        if not items:
            continue
        med = lambda key: sorted(r[key] for r in items if r[key] is not None)[len(items) // 2]
        print(condition, len(items), 'runs; median uptake comments', med('uptake_comments'), 'code', med('uptake_code'),
              '; first truncated', sum(r['first_truncated'] for r in items), '; manual checks', sum(r['manual_checks_run'] for r in items))


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
