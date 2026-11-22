"""Paired analysis of the pass-3 extended benchmark (frozen plan in FREEZE-ext.json; predeclared analysis plan).

usage (repository root):
  python -m reasoning_effectiveness.pass3.diagnostics.ext_analysis <study> <out_dir> [batch ...]
  (default batches: ext-s2108 ext-s2109)

Unit of analysis: (task, seed). Every comparison is paired within (task, seed). Uncertainty: task-clustered
bootstrap (tasks resampled with replacement, all seeds of a resampled task kept), 20,000 resamples, fixed
RNG seed; plus an exact two-sided sign test over TASKS on the per-task net difference. Infrastructure or
setup errors exclude that (task, seed) block for every condition (predeclared). Nothing here is significant
evidence of generalization; the cohort is small and hard-heavy.
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from guided_agent.analysis import attempt_metrics, e_metrics

CONDITIONS = ('A', 'C', 'D', 'E')


def load(study, batches):
    rows = []
    for batch in batches:
        batch_dir = Path(study) / 'runs' / batch
        for result in sorted(batch_dir.glob('*/result.json')):
            record = json.loads(result.read_text(encoding='utf-8'))
            row = attempt_metrics(result.parent, batch_dir / 'eval')
            row.update(e_metrics(record) if record.get('condition') == 'E' else {})
            evaluation = batch_dir / 'eval' / f"{record['run_id']}.json"
            hidden = json.loads(evaluation.read_text(encoding='utf-8')) if evaluation.exists() else {}
            row.update(batch=batch, seed=record.get('seed'), infra=record.get('exit_status') == 'infra_error' or
                       bool(record.get('setup_error')), verdict_counts=hidden.get('verdict_counts'),
                       frontier_wait_seconds=record.get('frontier_wait_seconds') or 0.0,
                       frontier_generation_seconds=record.get('frontier_generation_seconds'),
                       diagnosis_provider=((record.get('diagnosis') or {}).get('provider')))
            rows.append(row)
    return rows


def failure_category(row):
    if row.get('correct'):
        return 'pass'
    if not row.get('candidate'):
        return 'no_program_truncation' if row.get('length_truncations') else 'no_program_other'
    counts = row.get('verdict_counts') or {}
    if row.get('hidden_status') == 'missing_submission':
        return 'no_program_other'
    worst = [v for v in ('CE', 'RE', 'TLE', 'WA') if counts.get(v)]
    passed, total = row.get('hidden_passed') or 0, row.get('hidden_total') or 0
    if worst == ['TLE']:
        return 'tle_only'
    if total and passed == 0:
        return 'wrong_everywhere'
    return 'partial_' + '+'.join(worst) if worst else 'other'


def bootstrap(tasks, diff_by_task, n=20000, rng_seed=2108):
    """95% interval of the mean paired difference, resampling tasks (clusters)."""
    rng = random.Random(rng_seed)
    values = []
    for _ in range(n):
        sample = [rng.choice(tasks) for _ in tasks]
        num = sum(sum(diff_by_task[t]) for t in sample)
        den = sum(len(diff_by_task[t]) for t in sample)
        values.append(num / den if den else 0.0)
    values.sort()
    return round(values[int(0.025 * n)], 3), round(values[int(0.975 * n) - 1], 3)


def sign_test(net):
    """Exact two-sided sign test over tasks with a non-zero net difference."""
    pos, neg = sum(1 for v in net if v > 0), sum(1 for v in net if v < 0)
    m = pos + neg
    if m == 0:
        return pos, neg, 1.0
    k = min(pos, neg)
    p = sum(math.comb(m, i) for i in range(0, k + 1)) / 2 ** m
    return pos, neg, round(min(1.0, 2 * p), 4)


def compare(cells, tasks, seeds, x, y):
    """Paired comparison of condition x against y over complete (task, seed) blocks."""
    gains, harms, ties_pass, ties_fail, diff_by_task = [], [], 0, 0, defaultdict(list)
    for task in tasks:
        for seed in seeds:
            a, b = cells.get((task, seed, x)), cells.get((task, seed, y))
            if a is None or b is None:
                continue
            ca, cb = bool(a['correct']), bool(b['correct'])
            diff_by_task[task].append(int(ca) - int(cb))
            if ca and not cb:
                gains.append(f'{task[12:]}@{seed}')
            elif cb and not ca:
                harms.append(f'{task[12:]}@{seed}')
            elif ca:
                ties_pass += 1
            else:
                ties_fail += 1
    used = [t for t in tasks if diff_by_task[t]]
    n = sum(len(v) for v in diff_by_task.values())
    mean = round(sum(sum(v) for v in diff_by_task.values()) / n, 3) if n else None
    pos, neg, p = sign_test([sum(diff_by_task[t]) for t in used])
    return {'x': x, 'y': y, 'pairs': n, 'gains': gains, 'harms': harms, 'ties_both_pass': ties_pass,
            'ties_both_fail': ties_fail, 'mean_difference': mean,
            'cluster_bootstrap_95': bootstrap(used, diff_by_task) if used else None,
            'sign_test_tasks': {'better': pos, 'worse': neg, 'p_two_sided': p}}


def main(study, out_dir, *batches):
    batches = batches or ('ext-s2108', 'ext-s2109')
    rows = load(study, batches)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze = json.loads((Path(study) / 'FREEZE-ext.json').read_text(encoding='utf-8'))
    tasks = [t['task_id'] for t in freeze['tasks']]
    seeds = sorted({r['seed'] for r in rows})
    excluded_blocks = sorted({(r['task_id'], r['seed']) for r in rows if r['infra']})
    cells = {(r['task_id'], r['seed'], r['condition']): r for r in rows
             if (r['task_id'], r['seed']) not in excluded_blocks}
    complete = [(t, s) for t in tasks for s in seeds if all((t, s, c) in cells for c in CONDITIONS)]
    for r in rows:
        r['failure_category'] = failure_category(r)

    per_condition = {}
    for c in CONDITIONS:
        items = [cells[(t, s, c)] for t, s in complete]
        per_seed = {s: sum(bool(cells[(t, s2, c)]['correct']) for t, s2 in complete if s2 == s) for s in seeds}
        triggered = [r for r in items if r.get('e_trigger')]
        per_condition[c] = {
            'attempts': len(items), 'correct': sum(bool(r['correct']) for r in items), 'correct_by_seed': per_seed,
            'candidate': sum(r['candidate'] for r in items), 'submitted': sum(r['submitted'] for r in items),
            'public_final_pass': sum(r['public_final_pass'] for r in items),
            'runs_with_truncation': sum(r['length_truncations'] > 0 for r in items),
            'length_truncations': sum(r['length_truncations'] for r in items),
            'format_errors': sum(r['format_errors'] for r in items),
            'model_calls': sum(r['model_calls'] for r in items),
            'completion_tokens': sum(r['completion_tokens'] for r in items),
            'median_completion_tokens': sorted(r['completion_tokens'] for r in items)[len(items) // 2] if items else None,
            'local_coding_seconds': round(sum((r['local_coding_seconds'] or 0) - (r['frontier_wait_seconds'] or 0)
                                              for r in items), 1),
            'wall_seconds': round(sum(r['wall_seconds'] or 0 for r in items), 1),
            'frontier_wait_seconds': round(sum(r['frontier_wait_seconds'] or 0 for r in items), 1),
            'actions': sum(r['actions'] or 0 for r in items), 'repairs': sum(r['repairs'] or 0 for r in items),
            'noop_writes': sum(r['noop_writes'] or 0 for r in items),
            'repeated_failed_tests': sum(r['repeated_failed_tests'] or 0 for r in items),
            'manual_runs': sum(r['manual_runs'] or 0 for r in items),
            'failure_categories': dict(Counter(r['failure_category'] for r in items)),
            'exit_status': dict(Counter(r['exit_status'] for r in items)),
        }
        if c == 'E':
            per_condition[c]['e'] = {
                'assigned': len(items), 'triggered': len(triggered),
                'requested': sum(bool(r.get('e_requested')) for r in items),
                'delivered': sum(bool(r.get('e_delivered')) for r in items),
                'errors': dict(Counter(r.get('e_error') for r in items if r.get('e_error'))),
                'untriggered_reasons': dict(Counter(r.get('e_untriggered_reason') for r in items if not r.get('e_trigger'))),
                'changed_after': sum(bool(r.get('e_changed_after')) for r in triggered),
                'public_pass_after': sum(bool(r.get('e_public_pass_after')) for r in triggered),
                'hidden_pass_triggered': sum(bool(r['correct']) for r in triggered),
                'triggered_where_A_failed': sum(1 for r in triggered if not cells[(r['task_id'], r['seed'], 'A')]['correct']),
                'recovered_where_A_failed': sum(1 for r in triggered if r['correct'] and
                                                not cells[(r['task_id'], r['seed'], 'A')]['correct']),
                'wait_seconds': [r.get('e_wait_seconds') for r in triggered]}
    comparisons = [compare(cells, tasks, seeds, x, y) for x, y in
                   (('C', 'A'), ('D', 'A'), ('E', 'A'), ('C', 'D'), ('C', 'E'), ('D', 'E'))]
    consistency = {}
    for c in CONDITIONS:
        same = sum(1 for t in tasks if all((t, s, c) in cells for s in seeds) and
                   len({bool(cells[(t, s, c)]['correct']) for s in seeds}) == 1)
        consistency[c] = {'tasks_with_identical_outcome_across_seeds': same,
                          'tasks_with_both_seeds': sum(1 for t in tasks if all((t, s, c) in cells for s in seeds))}
    data = {'batches': list(batches), 'seeds': seeds, 'complete_blocks': len(complete), 'excluded_blocks': excluded_blocks,
            'per_condition': per_condition, 'comparisons': comparisons, 'seed_consistency': consistency,
            'rows': [{k: v for k, v in r.items() if k not in ('verdict_counts',)} | {'verdict_counts': r.get('verdict_counts')}
                     for r in rows]}
    (out_dir / 'ext-analysis.json').write_text(json.dumps(data, indent=1, default=str) + '\n', encoding='utf-8', newline='\n')
    (out_dir / 'ext-tables.md').write_text(markdown(data, tasks, seeds, cells), encoding='utf-8', newline='\n')
    print(markdown(data, tasks, seeds, cells))


def cell(r):
    if r is None:
        return '—'
    mark = '✓' if r['correct'] else '✗'
    score = f"{r['hidden_passed']}/{r['hidden_total']}" if r.get('hidden_passed') is not None else 'none'
    extra = []
    if r['length_truncations']:
        extra.append(f"{r['length_truncations']}T")
    if r['condition'] == 'E':
        extra.append('trig' if r.get('e_trigger') else 'untrig')
    return f"{mark} {score}" + (f" ({', '.join(extra)})" if extra else '')


def markdown(data, tasks, seeds, cells):
    lines = ['# Pass-3 extended benchmark tables (generated)', '',
             f"Complete (task, seed) blocks: {data['complete_blocks']}; excluded blocks (infrastructure): "
             f"{data['excluded_blocks'] or 'none'}. Cells: hidden ✓/✗, hidden cases passed, T = length truncations; "
             'E: trig/untrig.', '']
    for seed in seeds:
        lines += [f'## Seed {seed}', '', '| # | Task | A | C | D | E |', '| --- | --- | --- | --- | --- | --- |']
        for i, t in enumerate(tasks, 1):
            lines.append(f"| {i} | {t[12:]} | " + ' | '.join(cell(cells.get((t, seed, c))) for c in CONDITIONS) + ' |')
        lines.append('')
    lines += ['## Accuracy', '', '| Condition | ' + ' | '.join(f'seed {s}' for s in seeds) + ' | pooled |',
              '| --- |' + ' --- |' * (len(seeds) + 1)]
    for c, v in data['per_condition'].items():
        lines.append(f"| {c} | " + ' | '.join(f"{v['correct_by_seed'][s]}/{len(tasks)}" for s in seeds) +
                     f" | {v['correct']}/{v['attempts']} |")
    lines += ['', '## Paired comparisons (unit: task × seed)', '',
              '| Comparison | pairs | gains | harms | both pass | both fail | mean diff | task-cluster 95% | sign test (tasks) |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for cmp in data['comparisons']:
        s = cmp['sign_test_tasks']
        lines.append(f"| {cmp['x']} vs {cmp['y']} | {cmp['pairs']} | {len(cmp['gains'])} {cmp['gains']} | "
                     f"{len(cmp['harms'])} {cmp['harms']} | {cmp['ties_both_pass']} | {cmp['ties_both_fail']} | "
                     f"{cmp['mean_difference']} | {cmp['cluster_bootstrap_95']} | {s['better']}+/{s['worse']}- p={s['p_two_sided']} |")
    lines += ['', '## Resources and behaviour (sums over complete blocks)', '',
              '| Condition | candidate | submitted | public pass | runs w/ trunc | truncations | format errors | calls | '
              'completion tokens | median tokens | local s | wall s | frontier wait s | manual self-checks |',
              '| --- |' + ' --- |' * 14]
    for c, v in data['per_condition'].items():
        lines.append(f"| {c} | {v['candidate']} | {v['submitted']} | {v['public_final_pass']} | {v['runs_with_truncation']} | "
                     f"{v['length_truncations']} | {v['format_errors']} | {v['model_calls']} | {v['completion_tokens']} | "
                     f"{v['median_completion_tokens']} | {v['local_coding_seconds']} | {v['wall_seconds']} | "
                     f"{v['frontier_wait_seconds']} | {v['manual_runs']} |")
    lines += ['', '## Failure categories', '']
    for c, v in data['per_condition'].items():
        lines.append(f"* {c}: {v['failure_categories']}")
    if 'e' in data['per_condition'].get('E', {}):
        e = data['per_condition']['E']['e']
        lines += ['', '## Condition E', '', '```', json.dumps(e, indent=1), '```']
    lines += ['', '## Seed consistency', '', '```', json.dumps(data['seed_consistency'], indent=1), '```', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], *sys.argv[3:])
