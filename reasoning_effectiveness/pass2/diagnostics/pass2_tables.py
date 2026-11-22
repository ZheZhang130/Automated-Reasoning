"""Build pass-2 comparison tables (markdown + JSON) from run records. Counts only; no candidate code or tests.

usage: python -m reasoning_effectiveness.pass2.diagnostics.pass2_tables <pass1_study> <pass2_study> <out_dir>
(run from the repository root so `guided_agent` imports)
"""
import json
import sys
from pathlib import Path

from guided_agent.analysis import attempt_metrics


def rows(study, batch):
    batch_dir = Path(study) / 'runs' / batch
    out = []
    for result in sorted(batch_dir.glob('*/result.json')):
        try:
            out.append(attempt_metrics(result.parent, batch_dir / 'eval'))
        except Exception as error:  # keep going; report the broken record
            out.append({'run_id': result.parent.name, 'error': f'{type(error).__name__}: {error}'})
    return out


def key(row):
    return row.get('condition', '?') + (f"/{row['variant']}" if row.get('variant') else '')


def cell(row):
    if row is None:
        return '—'
    if row.get('error'):
        return 'record error'
    hidden = row.get('hidden_status')
    score = f"{row['hidden_passed']}/{row['hidden_total']}" if row.get('hidden_passed') is not None else 'no program'
    mark = '✓' if hidden == 'pass' else '✗'
    extra = []
    if row.get('format_errors'):
        extra.append(f"{row['format_errors']} fmt")
    extra.append(f"{row.get('actions')} act")
    if row.get('manual_runs'):
        extra.append(f"{row['manual_runs']} self-checks")
    return f"{mark} {score} ({', '.join(extra)})"


def table(title, tasks, columns):
    lines = [f'### {title}', '', '| Task | ' + ' | '.join(name for name, _ in columns) + ' |',
             '| --- |' + ' --- |' * len(columns)]
    for task in tasks:
        lines.append(f"| {task.replace('lcb-atcoder-', '')} | " + ' | '.join(cell(lookup(task)) for _, lookup in columns) + ' |')
    return '\n'.join(lines) + '\n'


def pick(rs, condition, variant=None, provider=None, seed=None):
    def lookup(task):
        for r in rs:
            if r.get('task_id') == task and r.get('condition') == condition and (r.get('variant') or None) == variant \
                    and (provider is None or r.get('guidance_provider') == provider):
                return r
        return None
    return lookup


def main(pass1, pass2, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p1 = {b: rows(pass1, b) for b in ('dev1-A', 'dev1-CD', 'mb1', 'mb2')}
    p2 = {b: rows(pass2, b) for b in ('dev-e', 'dev-e-api', 'dev-d', 'val')}
    p1_all = [r for b in p1.values() for r in b]
    dev_tasks = ['lcb-atcoder-' + t for t in ('arc192_a', 'arc195_a', 'abc393_d', 'abc394_c', 'abc390_c', 'abc388_g',
                                             'abc391_e', 'abc391_a')]
    md = ['# Pass-2 tables (generated)', '',
          'Cells: ✓/✗ hidden pass, hidden cases passed, then format errors (fmt), actions and manual self-checks. '
          'Pass-1 columns are the pass-1 runs at the same seed (2108) on the same frozen agent.', '']
    md.append(table('Development: contract versions (seed 2108)', dev_tasks, [
        ('A (pass 1)', pick(p1_all, 'A')),
        ('C plan-v1 (pass 1)', pick(p1_all, 'C')),
        ('D-v1 (pass 1)', pick(p1_all, 'D')),
        ('D-v1 Codex (pass 2)', pick(p2['dev-d'], 'D', 'v1codex')),
        ('D-v3 Codex (pass 2)', pick(p2['dev-d'], 'D', 'v3')),
    ]))
    e_tasks = ['lcb-atcoder-' + t for t in ('arc195_a', 'abc393_d', 'abc390_c', 'arc192_a')]
    md.append(table('Development: E (seed 2108)', e_tasks, [
        ('A (pass 1)', pick(p1_all, 'A')), ('E-v1 Codex', pick(p2['dev-e'], 'E')),
        ('E-v1 API', pick(p2['dev-e-api'], 'E', 'api'))]))
    e_lines = ['### E mechanism details', '', '| Run | trigger | at action | local s left | wait s | delivered | '
               'actions after | public tests after | changed | public pass after | hidden |', '|' + ' --- |' * 11]
    for r in p2['dev-e'] + p2['dev-e-api'] + [r for r in p2['val'] if r.get('condition') == 'E']:
        if r.get('error'):
            continue
        e_lines.append('| ' + ' | '.join(str(x) for x in (
            r['task_id'].replace('lcb-atcoder-', '') + (' (API)' if r.get('variant') == 'api' else ''),
            r.get('e_trigger'), r.get('e_trigger_action'), r.get('e_seconds_left'), r.get('e_wait_seconds'),
            r.get('e_delivered'), r.get('e_actions_after'), r.get('e_tests_after'), r.get('e_changed_after'),
            r.get('e_public_pass_after'), r.get('hidden_status'))) + ' |')
    md.append('\n'.join(e_lines) + '\n')
    val = p2['val']
    val_tasks = sorted({r['task_id'] for r in val if r.get('task_id')}, key=lambda t: (t != 'lcb-atcoder-abc394_b', t))
    md.append(table('Validation (fresh, outcome-blind; Codex guidance; seed 2108)', val_tasks, [
        ('A', pick(val, 'A')), ('C plan-v1', pick(val, 'C')), ('D-v1', pick(val, 'D', 'v1')),
        ('D-v3', pick(val, 'D', 'v3')), ('E-v1', pick(val, 'E'))]))
    res = ['### Resources by condition (pass-2 runs)', '',
           '| Cohort / condition | runs | hidden pass | completion tokens | format errors | local s (net) | frontier wait s |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for name, rs in p2.items():
        groups = {}
        for r in rs:
            if not r.get('error'):
                groups.setdefault(key(r), []).append(r)
        for k, items in sorted(groups.items()):
            res.append(f"| {name} {k} | {len(items)} | {sum(r.get('hidden_status') == 'pass' for r in items)} | "
                       f"{sum(r.get('completion_tokens') or 0 for r in items)} | {sum(r.get('format_errors') or 0 for r in items)} | "
                       f"{round(sum((r.get('local_coding_seconds') or 0) - (r.get('e_wait_seconds') or 0) for r in items), 1)} | "
                       f"{round(sum(r.get('e_wait_seconds') or 0 for r in items), 1)} |")
    md.append('\n'.join(res) + '\n')
    (out_dir / 'pass2-tables.md').write_text('\n'.join(md), encoding='utf-8', newline='\n')
    (out_dir / 'pass2-rows.json').write_text(json.dumps({'pass1': p1, 'pass2': p2}, indent=1, default=str) + '\n',
                                             encoding='utf-8', newline='\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main(*sys.argv[1:4])
