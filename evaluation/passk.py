"""pass@k: the unbiased estimator of HumanEval / LiveCodeBench, per task and condition, averaged over tasks.

For a task with ``n`` valid attempts (hidden-scored, not excluded) of which ``c`` pass every hidden test,
``pass@k = 1 - C(n - c, k) / C(n, k)``: the probability that at least one of ``k`` attempts drawn without replacement
from the ``n`` passes. A task with fewer than ``k`` valid attempts has no pass@k (it is reported as unavailable, never
as a failure).

* pass@1 is the primary correctness outcome; pass@2 and pass@3 are secondary (the benefit of repeated attempts).
* The task is the statistical unit: confidence intervals resample tasks, never (task, seed) pairs.
* Comparisons are matched: for X against A (or the gap toward B), each task uses only the seeds every compared condition
  has, so infrastructure exclusions shrink both sides alike.
* C and D reuse one upfront guidance artifact per task across seeds, so their pass@k describes repeated *local*
  execution given the same guidance, not independently regenerated frontier guidance.
* pass@k counts a task as solved when any of k attempts passes the *hidden* tests; it does not mean an agent could pick
  that attempt without the hidden tests.
"""
import math
import statistics
from collections import defaultdict


def pass_at_k(n, c, k):
    """Unbiased pass@k for one task, or None when fewer than k attempts exist."""
    if k < 1 or n < k:
        return None
    if c < 0 or c > n:
        raise ValueError(f'c={c} outside 0..n={n}')
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def _by_task(rows, condition):
    out = defaultdict(dict)
    for r in rows:
        if r['condition'] == condition:
            out[r['task_id']][r['seed']] = bool(r['passed'])
    return out


def task_values(rows, condition, k, seeds_by_task=None):
    """task_id -> pass@k (tasks with at least k valid attempts; restricted to ``seeds_by_task`` when given)."""
    values = {}
    for task, outcomes in _by_task(rows, condition).items():
        if seeds_by_task is not None:
            outcomes = {s: v for s, v in outcomes.items() if s in seeds_by_task.get(task, ())}
        value = pass_at_k(len(outcomes), sum(outcomes.values()), k)
        if value is not None:
            values[task] = value
    return values


def summary(rows, condition, ks, bootstrap):
    """pass@k for one condition: mean over eligible tasks, task-bootstrap CI, and how many tasks contributed."""
    by_task = _by_task(rows, condition)
    if not by_task:
        return None
    out = {'tasks': len(by_task), 'attempts': sum(len(v) for v in by_task.values()),
           'all_attempts_successful': round(statistics.fmean(all(v.values()) for v in by_task.values()), 4),
           'all_attempts_failed': round(statistics.fmean(not any(v.values()) for v in by_task.values()), 4)}
    for k in ks:
        values = list(task_values(rows, condition, k).values())
        out[f'pass@{k}'] = ({'value': round(statistics.fmean(values), 4), 'ci95': bootstrap(values),
                             'eligible_tasks': len(values)} if values
                            else {'value': None, 'ci95': None, 'eligible_tasks': 0,
                                  'note': f'no task has {k} valid attempts'})
    return out


def common_seeds(rows, conditions):
    """task_id -> seeds that every condition in ``conditions`` has (matched repetition sets)."""
    seeds = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r['condition'] in conditions:
            seeds[r['task_id']][r['condition']].add(r['seed'])
    return {t: set.intersection(*(by[c] for c in conditions)) for t, by in seeds.items()
            if all(c in by for c in conditions)}


def versus(rows, condition, base, k, bootstrap):
    """Matched pass@k difference (condition - base) over tasks where both have at least k common seeds."""
    seeds = common_seeds(rows, (condition, base))
    x, a = task_values(rows, condition, k, seeds), task_values(rows, base, k, seeds)
    tasks = sorted(set(x) & set(a))
    if not tasks:
        return {'tasks': 0, 'difference': None, 'ci95': None, 'note': f'no matched task with {k} common attempts'}
    diffs = [x[t] - a[t] for t in tasks]
    return {'tasks': len(tasks), 'rate': round(statistics.fmean(x[t] for t in tasks), 4),
            'base_rate': round(statistics.fmean(a[t] for t in tasks), 4),
            'difference': round(statistics.fmean(diffs), 4), 'ci95': bootstrap(diffs)}


def gap_closed(rows, condition, k, ratio_ci, base='A', ceiling='B'):
    """(X - A) / (B - A) on matched task-level pass@k; undefined (None) when B does not exceed A."""
    seeds = common_seeds(rows, (condition, base, ceiling))
    x, a, b = (task_values(rows, c, k, seeds) for c in (condition, base, ceiling))
    tasks = sorted(set(x) & set(a) & set(b))
    if not tasks:
        return {'tasks': 0, 'gap_closed': None, 'ci95': None}
    triples = [(x[t], a[t], b[t]) for t in tasks]
    return ratio_ci(triples) | {'tasks': len(tasks)}
