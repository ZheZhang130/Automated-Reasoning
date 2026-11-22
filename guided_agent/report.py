"""Aggregate cohorts into machine-readable results and paired markdown tables.

  python -m guided_agent.report <study> <out_dir> cohort=batch[,batch...] ...

Cohorts are never pooled: each named cohort gets its own table.
"""
import json
import sys
from pathlib import Path

from .analysis import summarize
from .common import write_json


def mark(row):
    if row is None:
        return '—'
    if row['correct']:
        return '✓'
    if not row['candidate']:
        return f"✗ no submission ({row['raw_exit_status']})"
    detail = f"{row['hidden_passed']}/{row['hidden_total']}" if row['hidden_passed'] is not None else 'unscored'
    return f"✗ {detail} ({row['raw_exit_status']})"


def cohort_markdown(name, summary):
    rows = summary['rows']
    keys = sorted({r['condition'] + (f"/{r['variant']}" if r['variant'] else '') for r in rows})
    tasks = sorted({r['task_id'] for r in rows})
    index = {(r['task_id'], r['condition'] + (f"/{r['variant']}" if r['variant'] else '')): r for r in rows}
    lines = [f'### {name}', '', '| Task | ' + ' | '.join(keys) + ' |', '| --- |' + ' --- |' * len(keys)]
    for task in tasks:
        lines.append(f'| {task[12:]} | ' + ' | '.join(mark(index.get((task, k))) for k in keys) + ' |')
    lines += ['', '| Metric | ' + ' | '.join(keys) + ' |', '| --- |' + ' ---: |' * len(keys)]
    table = summary['table']
    for metric in ('correct', 'submitted', 'candidate', 'public_final_pass', 'repeated_format_exit',
                   'length_truncations', 'completion_tokens', 'local_coding_seconds'):
        lines.append(f'| {metric} | ' + ' | '.join(str(table[k][metric]) for k in keys) + ' |')
    return '\n'.join(lines) + '\n'


def main(argv):
    study, out = Path(argv[0]), Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    markdown, combined = [], {}
    for spec in argv[2:]:
        name, batches = spec.split('=', 1)
        summary = summarize([study / 'runs' / b for b in batches.split(',')], out / name)
        combined[name] = {'batches': batches.split(','), 'table': summary['table'], 'paired_correct': summary['paired_correct']}
        markdown.append(cohort_markdown(name, summary))
    write_json(out / 'cohorts.json', combined)
    (out / 'tables.md').write_text('\n'.join(markdown), encoding='utf-8')
    print('\n'.join(markdown))


if __name__ == '__main__':
    main(sys.argv[1:])
