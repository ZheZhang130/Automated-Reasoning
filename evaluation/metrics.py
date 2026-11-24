"""Final metrics and statistics over one or more finished batches.

Input per batch directory (written by ``guided_agent batch`` / ``evaluate`` / ``measure``):
``plan.json`` (the scheduled attempts), ``<run>/measurement.json`` (schema csc2108-run-measurement-v1) and
``<run>/attempts.jsonl`` (judge-public history). Difficulty comes from the judge manifests.

Rules (see evaluation/README.md):

* A run is one scheduled (task, condition, seed). The primary metric is the final pass rate: hidden status
  ``pass`` divided by included runs. A missing submission is a failure.
* Every run gets one failure category (``CATEGORIES``, first that applies). Only ``infrastructure`` (Docker,
  judge, a crashed or unreachable model server; a hidden ``infrastructure_error`` / ``malformed_record``) and runs
  that never happened exclude their (task, seed) block from every condition. A local model request that timed out
  (``local_timeout``: the 180 s request limit, or the 600 s budget ending mid-request) and a context overflow are
  the agent's own failures: the runner records them as ``infra_error``, but they count as failed runs here.
* The transition table pairs each condition with A on the same (task, seed): A's category -> the condition's.
* Paired comparisons of each condition against A use the task as the unit (mean over the seeds both have),
  a 10,000-resample bootstrap CI over tasks, an exact/Monte Carlo sign-flip permutation p-value, and the exact
  McNemar test on (task, seed) pairs. Holm is applied across the primary comparisons C, D and E only.
"""
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from .plan import read_json, write_json

PRIMARY = ('C', 'D', 'E')
EXPLORATORY = ('B',)
INFRA_HIDDEN = {'infrastructure_error', 'malformed_record'}


# ----------------------------------------------------------------------------- loading
def difficulties(manifests):
    found = {}
    for manifest in manifests:
        for entry in read_json(manifest)['tasks']:
            found[entry['task_id']] = entry['difficulty']
    return found


def _attempts(run_dir):
    path = run_dir / 'attempts.jsonl'
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def _measurement(run_dir):
    path = run_dir / 'measurement.json'
    if path.exists():
        return read_json(path)
    from guided_agent import measurement  # rebuild from the run's own artifacts (read-only)
    return measurement.build(run_dir)


def _sum_or_none(values):
    values = list(values)
    return None if any(v is None for v in values) else sum(values)


def _hidden_failure_verdict(run_dir, document):
    batch = run_dir.parent
    run_id = document['identity']['run_id']
    path = batch / 'eval' / f'{run_id}.json'
    counts = (read_json(path).get('verdict_counts') or {}) if path.exists() else {}
    failing = {k: v for k, v in counts.items() if k != 'AC'}
    return max(failing, key=failing.get) if failing else None


def _last_public_verdict(attempts):
    for attempt in reversed(attempts):
        result = attempt.get('result') or {}
        if result.get('status') == 'pass':
            return 'AC'
        if (result.get('first_failure') or {}).get('verdict'):
            return result['first_failure']['verdict']
        if result.get('status'):
            return result['status']
    return 'none'


CATEGORIES = (
    'hidden_pass',              # all hidden cases pass
    'infrastructure',           # real infrastructure fault: excluded (rerun first)
    'local_timeout_no_program',    # a local model request timed out before any program existed
    'local_timeout_with_program',  # timed out after a program existed (it never passed hidden tests)
    'context_overflow',         # the prompt filled the 16K context
    'truncated_no_program',     # hit the output-token cap and never produced a program
    'budget_limit',             # action limit, repair limit, or the 600 s deadline between requests
    'format_errors',            # repeated unparseable responses
    'public_pass_hidden_fail',  # passed the public tests, failed hidden ones
    'never_passed_public',      # produced a program that never passed the public tests
    'no_submission',            # anything else without a program
)
def is_local_model_timeout(error):
    """Only a LiteLLM/Ollama request timeout counts; other 'timed out' errors (Docker, judge) are infrastructure."""
    return 'litellm.Timeout' in error or ('Ollama' in error and 'timed out' in error)


def _agent_error(run_dir):
    for path in run_dir.glob('agent-*/result.json'):
        error = read_json(path).get('error')
        if error:
            return str(error)
    return ''


def _ollama_responses(run_dir):
    for path in run_dir.glob('agent-*/ollama-responses.json'):
        return [r for r in read_json(path) if isinstance(r, dict)]
    return []


def failure_category(*, passed, hidden, correct, inference, agent_error, final_public_pass, candidate):
    if passed:
        return 'hidden_pass'
    if hidden in INFRA_HIDDEN:
        return 'infrastructure'
    if correct.get('context_overflow'):
        return 'context_overflow'
    if correct.get('exit_status') == 'infra_error' and is_local_model_timeout(agent_error):
        return 'local_timeout_with_program' if candidate else 'local_timeout_no_program'
    if correct.get('infrastructure_failure'):
        return 'infrastructure'
    if not candidate and (inference.get('truncated_responses') or 0) > 0:
        return 'truncated_no_program'
    if correct.get('exit_status') in ('action_limit', 'repair_limit', 'deadline'):
        return 'budget_limit' if not candidate else ('public_pass_hidden_fail' if final_public_pass
                                                     else 'never_passed_public')
    if correct.get('exit_status') == 'format_errors' or correct.get('raw_exit_status') == 'RepeatedFormatError':
        return 'format_errors'
    if final_public_pass:
        return 'public_pass_hidden_fail'
    if candidate:
        return 'never_passed_public'
    return 'no_submission'


def run_row(run_dir, item, difficulty):
    document = _measurement(run_dir)
    ident, correct = document['identity'], document['correctness']
    agent, frontier, time_, cost = document['agent'], document['frontier'], document['time'], document['cost']
    inference = document['local_inference']
    attempts = _attempts(run_dir)
    statuses = [(a.get('result') or {}).get('status') for a in attempts]
    hidden = correct.get('hidden_status')
    passed = hidden == 'pass'
    final_public_pass = correct.get('final_public_status') == 'pass'
    candidate = bool(correct.get('candidate_produced'))
    agent_error = _agent_error(run_dir)
    responses = _ollama_responses(run_dir)
    category = failure_category(passed=passed, hidden=hidden, correct=correct, inference=inference,
                                agent_error=agent_error, final_public_pass=final_public_pass, candidate=candidate)
    infra = category == 'infrastructure'
    if infra:
        outcome = 'infrastructure'
    elif passed:
        outcome = 'hidden_pass'
    elif final_public_pass:
        outcome = f'public_pass_hidden_fail:{_hidden_failure_verdict(run_dir, document)}'
    elif candidate:
        outcome = f'never_passed_public:{_last_public_verdict(attempts)}'
    else:
        outcome = f"no_submission:{correct.get('exit_status')}"
    diagnosis = (document.get('condition') or {}).get('diagnosis') or {}
    requests = frontier.get('requests') or []
    upfront = [r for r in requests if r.get('upfront')]
    return {
        'batch': run_dir.parent.name, 'run_dir': run_dir.name, 'run_id': ident['run_id'],
        'task_id': item['task_id'], 'condition': item['condition'], 'seed': item.get('seed'),
        'difficulty': difficulty, 'status': 'run', 'hidden_status': hidden, 'passed': passed,
        'infrastructure': infra, 'context_overflow': bool(correct.get('context_overflow')),
        'exit_status': correct.get('exit_status'), 'candidate': candidate,
        'final_public_pass': final_public_pass, 'had_public_failure': 'candidate_failure' in statuses,
        'public_tests': len(attempts), 'outcome': outcome, 'category': category,
        'local_timeout': category.startswith('local_timeout'), 'agent_error': agent_error[:200] or None,
        'truncated_responses': inference.get('truncated_responses'),
        'first_response_tokens': responses[0]['eval_count'] if responses else None,
        'first_response_seconds': round(responses[0]['total_duration'] / 1e9, 2) if responses else None,
        'seconds_to_first_candidate': agent.get('seconds_to_first_executable_candidate'),
        'host': '/'.join(str((ident.get('host') or {}).get(k)) for k in ('system', 'machine', 'node')),
        '_requests': [(r['eval_count'], r['eval_duration'] / 1e9, r['total_duration'] / 1e9) for r in responses
                      if r.get('eval_count') and r.get('eval_duration') and r.get('total_duration')],
        'actions': agent.get('actions'), 'repairs': agent.get('repairs'),
        'wall_seconds': time_.get('wall_seconds'), 'local_inference_seconds': time_.get('local_inference_seconds'),
        'local_prompt_tokens': inference.get('prompt_tokens'),
        'local_completion_tokens': inference.get('completion_tokens'),
        'frontier_requests': frontier.get('n_requests'), 'frontier_failures': frontier.get('provider_failures') or 0,
        'frontier_run_cost_usd': cost.get('api_cost_usd_run') if any(not r.get('upfront') for r in requests) else 0.0,
        'upfront_cost_usd': _sum_or_none(r.get('cost_usd') for r in upfront) if upfront else 0.0,
        'guidance_sha256': ident.get('guidance_artifact_sha256'),
        'frontier_input_tokens': _sum_or_none(r.get('input_tokens') for r in requests) if requests else 0,
        'frontier_output_tokens': _sum_or_none(r.get('output_tokens') for r in requests) if requests else 0,
        'run_input_tokens': _sum_or_none(r.get('input_tokens') for r in requests if not r.get('upfront')),
        'run_output_tokens': _sum_or_none(r.get('output_tokens') for r in requests if not r.get('upfront')),
        'upfront_input_tokens': _sum_or_none(r.get('input_tokens') for r in upfront) if upfront else 0,
        'upfront_output_tokens': _sum_or_none(r.get('output_tokens') for r in upfront) if upfront else 0,
        'upfront_latency_seconds': _sum_or_none(r.get('latency_seconds') for r in upfront) if upfront else 0.0,
        'e_triggered': diagnosis.get('trigger_observed'), 'e_delivered': diagnosis.get('delivered'),
        'host_backend': ident.get('host_backend'), 'coding_model': ident.get('coding_model'),
    }


def merge_reruns(rows):
    """Later batches rerun earlier infrastructure failures: a later run of the same (task, condition, seed)
    replaces an earlier row only when that row was an infrastructure failure or never ran."""
    kept, replaced = {}, []
    for row in rows:
        key = (row['task_id'], row['condition'], row['seed'])
        old = kept.get(key)
        if old is None:
            kept[key] = row
        elif old['status'] == 'not_run' or old['infrastructure']:
            kept[key] = row
            replaced.append({'task_id': key[0], 'condition': key[1], 'seed': key[2], 'old': old['run_dir'],
                             'old_batch': old['batch'], 'old_outcome': old['outcome'], 'new_batch': row['batch']})
        else:
            raise ValueError(f'{key} has two valid runs ({old["batch"]}, {row["batch"]}); pass one of them')
    return list(kept.values()), replaced


def load(batch_dirs, manifests):
    from guided_agent.integrity import run_name
    levels = difficulties(manifests)
    rows = []
    for batch in map(Path, batch_dirs):
        plan = read_json(batch / 'plan.json')
        for item in plan['attempts']:
            run_dir = batch / run_name(item)
            difficulty = levels.get(item['task_id'], 'unknown')
            if (run_dir / 'result.json').exists():
                rows.append(run_row(run_dir, item, difficulty))
            else:
                rows.append({'batch': batch.name, 'run_dir': run_dir.name, 'task_id': item['task_id'],
                             'condition': item['condition'], 'seed': item.get('seed'), 'difficulty': difficulty,
                             'status': 'not_run', 'passed': False, 'infrastructure': False, 'outcome': 'not_run',
                             'category': 'not_run', 'local_timeout': False, '_requests': []})
    return rows


# ----------------------------------------------------------------------------- statistics
def _quantiles(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return {'median': values[0], 'q1': values[0], 'q3': values[0], 'n': 1}
    q1, median, q3 = statistics.quantiles(values, n=4, method='inclusive')
    return {'median': round(median, 3), 'q1': round(q1, 3), 'q3': round(q3, 3), 'n': len(values)}


def _mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.fmean(values), 3) if values else None


def bootstrap_ci(diffs, resamples=10000, seed=2108, level=0.95):
    if not diffs:
        return None
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(n)) / n for _ in range(resamples))
    lo = means[int(math.floor((1 - level) / 2 * resamples))]
    hi = means[min(resamples - 1, int(math.ceil((1 + level) / 2 * resamples)) - 1)]
    return [round(lo, 4), round(hi, 4)]


def sign_flip_p(diffs, resamples=10000, seed=2108):
    """Two-sided paired permutation test of mean(diffs) = 0 (exact up to 2^16 sign patterns)."""
    nonzero = [d for d in diffs if d != 0]
    if not nonzero:
        return 1.0
    observed = abs(sum(nonzero))
    n = len(nonzero)
    if n <= 16:
        hits = 0
        for mask in range(1 << n):
            total = sum(-d if mask >> i & 1 else d for i, d in enumerate(nonzero))
            hits += abs(total) >= observed - 1e-12
        return hits / (1 << n)
    rng = random.Random(seed)
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in nonzero)) >= observed - 1e-12
               for _ in range(resamples))
    return (hits + 1) / (resamples + 1)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def holm(pvalues):
    order = sorted(pvalues, key=pvalues.get)
    adjusted, running = {}, 0.0
    for rank, key in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * pvalues[key]))
        adjusted[key] = running
    return adjusted


# ----------------------------------------------------------------------------- aggregation
def exclusions(rows):
    blocks = defaultdict(list)
    for row in rows:
        if row['status'] == 'not_run':
            blocks[(row['task_id'], row['seed'])].append(f"{row['condition']}:not_run")
        elif row['infrastructure']:
            blocks[(row['task_id'], row['seed'])].append(f"{row['condition']}:infrastructure")
    return dict(blocks)


def condition_summary(rows):
    n = len(rows)
    if not n:
        return None
    passes = sum(r['passed'] for r in rows)
    failed_public = [r for r in rows if r.get('had_public_failure')]
    artifacts = {}  # one entry per guidance artifact: authored once, shared by every seed
    for r in rows:
        if r.get('guidance_sha256'):
            artifacts[r['guidance_sha256']] = r
    run_cost = _sum_or_none(r.get('frontier_run_cost_usd') for r in rows)
    upfront_cost = _sum_or_none(a.get('upfront_cost_usd') for a in artifacts.values()) if artifacts else 0.0
    upfront_cost = None if upfront_cost is None else round(upfront_cost, 6)
    tokens = {'run_input': _sum_or_none(r.get('run_input_tokens') for r in rows),
              'run_output': _sum_or_none(r.get('run_output_tokens') for r in rows),
              'upfront_input': _sum_or_none(a.get('upfront_input_tokens') for a in artifacts.values()) if artifacts else 0,
              'upfront_output': _sum_or_none(a.get('upfront_output_tokens') for a in artifacts.values()) if artifacts
              else 0}
    known = [v for v in tokens.values() if v is not None]
    tokens['total'] = sum(known) if len(known) == len(tokens) else None
    tokens['per_pass'] = round(tokens['total'] / passes, 1) if tokens['total'] is not None and passes else None
    latencies = [a.get('upfront_latency_seconds') for a in artifacts.values()]
    total_cost = None if run_cost is None or upfront_cost is None else round(run_cost + upfront_cost, 6)
    return {
        'runs': n, 'passes': passes, 'pass_rate': round(passes / n, 4),
        'public_hidden_gap': round(sum(r['final_public_pass'] and not r['passed'] for r in rows) / n, 4),
        'failure_recovery': {'runs_with_public_failure': len(failed_public),
                             'recovered': sum(r['passed'] for r in failed_public),
                             'rate': round(sum(r['passed'] for r in failed_public) / len(failed_public), 4)
                             if failed_public else None},
        'context_overflow': sum(r['context_overflow'] for r in rows),
        'local_timeout': sum(r['local_timeout'] for r in rows),
        'categories': {c: n for c in CATEGORIES if (n := sum(r['category'] == c for r in rows))},
        'guidance_error_runs': sum(r['frontier_failures'] > 0 for r in rows),
        'exit_status': dict(Counter(r['exit_status'] for r in rows)),
        'outcomes': dict(Counter(r['outcome'] for r in rows)),
        'actions_mean': _mean(r['actions'] for r in rows), 'repairs_mean': _mean(r['repairs'] for r in rows),
        'repairs_distribution': dict(sorted(Counter(r['repairs'] for r in rows).items(), key=lambda kv: str(kv[0]))),
        'wall_seconds': _quantiles(r['wall_seconds'] for r in rows),
        'local_inference_seconds': _quantiles(r['local_inference_seconds'] for r in rows),
        'local_prompt_tokens': _quantiles(r['local_prompt_tokens'] for r in rows),
        'local_completion_tokens': _quantiles(r['local_completion_tokens'] for r in rows),
        'first_response_tokens': _quantiles(r['first_response_tokens'] for r in rows),
        'seconds_to_first_candidate': _quantiles(r['seconds_to_first_candidate'] for r in rows),
        'runs_with_truncation': sum((r['truncated_responses'] or 0) > 0 for r in rows),
        'runs_with_candidate': sum(r['candidate'] for r in rows),
        'frontier_cost_usd': {'run_time': run_cost, 'upfront_one_off': upfront_cost, 'total': total_cost,
                              'per_pass': round(total_cost / passes, 6) if total_cost is not None and passes else None,
                              'guidance_artifacts': len(artifacts)},
        'frontier_tokens': tokens,
        'upfront_guidance': {'artifacts': len(artifacts), 'cost_usd': upfront_cost,
                             'input_tokens': tokens['upfront_input'], 'output_tokens': tokens['upfront_output'],
                             'latency_seconds_total': (None if _sum_or_none(latencies) is None
                                                       else round(_sum_or_none(latencies), 2)),
                             'latency_seconds': _quantiles(latencies)} if artifacts else None,
        'seed_consistency': seed_consistency(rows),
    }


def seed_consistency(rows):
    """Per task, how the seeds agree: all pass, mixed, all fail (tasks with at least two seeds only).

    ``mean_seed_variance`` is the mean over tasks of p(1-p), p the task's pass rate over seeds: 0 when every task is
    decided the same way on every seed, 0.25 at most."""
    by_task = defaultdict(list)
    for r in rows:
        by_task[r['task_id']].append(r['passed'])
    multi = {t: v for t, v in by_task.items() if len(v) >= 2}
    if not multi:
        return None
    rates = [statistics.fmean(v) for v in multi.values()]
    return {'tasks': len(multi), 'all_pass': sum(all(v) for v in multi.values()),
            'mixed': sum(any(v) and not all(v) for v in multi.values()),
            'all_fail': sum(not any(v) for v in multi.values()),
            'mean_seed_variance': round(statistics.fmean(p * (1 - p) for p in rates), 4)}


def gap_closed(rows, condition, base='A', ceiling='B', resamples=10000, seed=2108):
    """Share of the base-to-ceiling gap a condition closes: (X - A) / (B - A), on (task, seed) pairs that have all
    three conditions, with task-level means. 1 means the condition reached the frontier coder; 0 means no gain.
    The 95% CI resamples tasks; resamples whose B - A gap is not positive are skipped and counted."""
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r['passed']
    per_task = defaultdict(list)
    for (task, _seed), v in by.items():
        if {condition, base, ceiling} <= set(v):
            per_task[task].append((v[condition], v[base], v[ceiling]))
    if not per_task:
        return None
    means = [tuple(statistics.fmean(x[i] for x in items) for i in range(3)) for items in per_task.values()]

    def ratio(sample):
        x, a, b = (statistics.fmean(m[i] for m in sample) for i in range(3))
        return (x - a) / (b - a) if b - a > 0 else None
    point = ratio(means)
    rng = random.Random(seed)
    draws = [ratio([rng.choice(means) for _ in means]) for _ in range(resamples)]
    valid = sorted(d for d in draws if d is not None)
    ci = [round(valid[int(0.025 * len(valid))], 4), round(valid[min(len(valid) - 1, int(0.975 * len(valid)))], 4)] \
        if len(valid) >= 100 else None
    x, a, b = (statistics.fmean(m[i] for m in means) for i in range(3))
    return {'tasks': len(means), 'rate': round(x, 4), 'base_rate': round(a, 4), 'ceiling_rate': round(b, 4),
            'gap_closed': None if point is None else round(point, 4), 'ci95': ci,
            'resamples_without_gap': resamples - len(valid)}


def paired(rows, condition, base='A'):
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r['passed']
    per_task, b, c = defaultdict(lambda: ([], [])), 0, 0
    for (task, _seed), outcome in by.items():
        if condition in outcome and base in outcome:
            per_task[task][0].append(outcome[condition])
            per_task[task][1].append(outcome[base])
            b += outcome[condition] and not outcome[base]
            c += outcome[base] and not outcome[condition]
    diffs = [statistics.fmean(x) - statistics.fmean(a) for x, a in per_task.values()]
    if not diffs:
        return None
    return {'tasks': len(diffs), 'pairs': sum(len(x) for x, _ in per_task.values()),
            'pass_rate': round(statistics.fmean(statistics.fmean(x) for x, _ in per_task.values()), 4),
            'base_pass_rate': round(statistics.fmean(statistics.fmean(a) for _, a in per_task.values()), 4),
            'difference': round(statistics.fmean(diffs), 4), 'ci95': bootstrap_ci(diffs),
            'p_permutation': round(sign_flip_p(diffs), 5),
            'mcnemar': {'condition_only': b, 'base_only': c, 'p_exact': round(mcnemar_exact(b, c), 5)}}


def transitions(rows, condition, base='A'):
    """(task, seed) pairs: base category -> condition category, plus how many of each base failure the condition
    fixed (passed hidden)."""
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r['category']
    pairs = [(v[base], v[condition]) for v in by.values() if base in v and condition in v]
    if not pairs:
        return None
    matrix = defaultdict(Counter)
    for a, x in pairs:
        matrix[a][x] += 1
    order = [c for c in CATEGORIES if any(c in (a, x) for a, x in pairs)]
    return {'pairs': len(pairs), 'categories': order,
            'matrix': {a: dict(matrix[a]) for a in order if a in matrix},
            'fixed': {a: {'base_failures': sum(matrix[a].values()), 'passed': matrix[a]['hidden_pass']}
                      for a in order if a in matrix and a != 'hidden_pass'},
            'broken': sum(1 for a, x in pairs if a == 'hidden_pass' and x != 'hidden_pass')}


def paired_process(rows, condition, base='A'):
    """How a condition changes the local agent's work on the same (task, seed): median paired differences."""
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r
    pairs = [(v[condition], v[base]) for v in by.values() if condition in v and base in v]
    if not pairs:
        return None

    def median_diff(key):
        diffs = [x[key] - a[key] for x, a in pairs if x.get(key) is not None and a.get(key) is not None]
        return {'median': round(statistics.median(diffs), 2), 'pairs': len(diffs)} if diffs else None
    return {'pairs': len(pairs),
            'local_completion_tokens': median_diff('local_completion_tokens'),
            'first_response_tokens': median_diff('first_response_tokens'),
            'seconds_to_first_candidate': median_diff('seconds_to_first_candidate'),
            'candidate_only_in_condition': sum(x['candidate'] and not a['candidate'] for x, a in pairs),
            'candidate_only_in_base': sum(a['candidate'] and not x['candidate'] for x, a in pairs)}


def host_speed(rows, near=150.0):
    """Local generation speed per (host, model), and how close requests come to the 180 s request limit."""
    groups = defaultdict(list)
    for r in rows:
        if r['status'] == 'run' and r['condition'] != 'B':
            groups[(r.get('host'), r.get('coding_model'))].append(r)
    out = []
    for (host, model), items in sorted(groups.items(), key=lambda kv: str(kv[0])):
        requests = [q for r in items for q in r['_requests']]
        speeds = sorted(n / s for n, s, _ in requests if s > 0)
        timeouts = sum(r['local_timeout'] for r in items)
        slow = sum(total >= near for _, _, total in requests)
        out.append({'host': host, 'coding_model': model, 'runs': len(items), 'requests': len(requests),
                    'decode_tok_s_median': round(statistics.median(speeds), 1) if speeds else None,
                    'decode_tok_s_p10': round(speeds[len(speeds) // 10], 1) if speeds else None,
                    'requests_over_near_s': slow, 'timed_out_requests': timeouts, 'near_seconds': near,
                    'near_limit_share': round((slow + timeouts) / (len(requests) + timeouts), 4)
                    if requests or timeouts else None})
    return out


def e_subset(rows):
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r
    triggered = [(v['E'], v['A']) for v in by.values() if 'E' in v and 'A' in v and v['E'].get('e_triggered')]
    def rates(pairs):
        return {'pairs': len(pairs), 'E_pass_rate': round(statistics.fmean(e['passed'] for e, _ in pairs), 4),
                'A_pass_rate': round(statistics.fmean(a['passed'] for _, a in pairs), 4)} if pairs else None
    return {'triggered': rates(triggered),
            'triggered_and_A_failed_public': rates([(e, a) for e, a in triggered if a.get('had_public_failure')]),
            'trigger_rate': round(len(triggered) / sum('E' in v for v in by.values()), 4)
            if any('E' in v for v in by.values()) else None}


def sensitivity_exclude_timeouts(included):
    """Secondary analysis: drop every (task, seed) block in which any run timed out locally."""
    blocks = {(r['task_id'], r['seed']) for r in included if r['local_timeout']}
    kept = [r for r in included if (r['task_id'], r['seed']) not in blocks]
    conditions = sorted({r['condition'] for r in kept})
    summary = {}
    for c in conditions:
        items = [r for r in kept if r['condition'] == c]
        summary[c] = {'runs': len(items), 'passes': sum(r['passed'] for r in items),
                      'pass_rate': round(sum(r['passed'] for r in items) / len(items), 4)}
    return {'excluded_blocks': len(blocks), 'included_runs': len(kept), 'summary': summary,
            'paired_vs_A': {c: paired(kept, c) for c in conditions if c != 'A'} if 'A' in conditions else {}}


def analyze(batch_dirs, manifests):
    rows, replaced = merge_reruns(load(batch_dirs, manifests))
    excluded = exclusions(rows)
    included = [r for r in rows if (r['task_id'], r['seed']) not in excluded]
    conditions = sorted({r['condition'] for r in included})
    levels = ['all'] + sorted({r['difficulty'] for r in included})
    summary = {level: {c: condition_summary([r for r in included if r['condition'] == c
                                             and (level == 'all' or r['difficulty'] == level)])
                       for c in conditions} for level in levels}
    comparisons = {level: {c: paired([r for r in included if level == 'all' or r['difficulty'] == level], c)
                           for c in conditions if c != 'A'} for level in levels} if 'A' in conditions else {}
    primary = {c: v['p_permutation'] for c, v in comparisons.get('all', {}).items() if c in PRIMARY and v}
    hosts = Counter((r.get('host_backend'), r.get('coding_model')) for r in included)
    return {
        'schema': 'csc2108-evaluation-report-v1', 'batches': [str(b) for b in batch_dirs],
        'scheduled_runs': len(rows), 'included_runs': len(included), 'replaced_by_rerun': replaced,
        'excluded_blocks': [{'task_id': t, 'seed': s, 'reasons': v} for (t, s), v in sorted(excluded.items(),
                                                                                             key=lambda kv: str(kv[0]))],
        'hosts': [{'backend': b, 'coding_model': m, 'runs': n} for (b, m), n in hosts.items()],
        'summary': summary, 'paired_vs_A': comparisons, 'holm_adjusted_p': holm(primary) if primary else {},
        'e_subset': e_subset(included) if {'A', 'E'} <= set(conditions) else None,
        'transitions_from_A': {c: transitions(included, c) for c in conditions if c != 'A'} if 'A' in conditions else {},
        'process_vs_A': {c: paired_process(included, c) for c in conditions if c != 'A'} if 'A' in conditions else {},
        'sensitivity_exclude_timeouts': sensitivity_exclude_timeouts(included),
        'gap_closed_vs_B': {c: gap_closed(included, c) for c in conditions if c not in ('A', 'B')}
        if {'A', 'B'} <= set(conditions) else {},
        'host_speed': host_speed(rows),
    }, rows


# ----------------------------------------------------------------------------- output
def _pct(x):
    return '–' if x is None else f'{100 * x:.1f}%'


def markdown(report):
    lines = ['# Evaluation report', '',
             f"Scheduled runs: {report['scheduled_runs']}; included: {report['included_runs']}; "
             f"excluded (task, seed) blocks: {len(report['excluded_blocks'])}.", '']
    for block in report['excluded_blocks']:
        lines.append(f"* excluded {block['task_id']} seed {block['seed']}: {', '.join(block['reasons'])}")
    for item in report.get('replaced_by_rerun') or []:
        lines.append(f"* rerun: {item['task_id']} {item['condition']} seed {item['seed']} ({item['old_outcome']} in "
                     f"{item['old_batch']}) replaced by {item['new_batch']}")
    for level, table in report['summary'].items():
        lines += ['', f'## Final pass rate: {level}', '',
                  '| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | '
                  'Frontier $ total | $ per pass | Wall s median (IQR) |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for condition, s in table.items():
            if not s:
                continue
            wall = s['wall_seconds']
            rec = s['failure_recovery']
            lines.append(
                f"| {condition} | {s['runs']} | {s['passes']} | {_pct(s['pass_rate'])} | {_pct(s['public_hidden_gap'])} "
                f"| {rec['recovered']}/{rec['runs_with_public_failure']} | {s['context_overflow']} "
                f"| {s['frontier_cost_usd']['total']} | {s['frontier_cost_usd']['per_pass']} "
                f"| {wall['median'] if wall else '–'} ({wall['q1'] if wall else '–'}–{wall['q3'] if wall else '–'}) |")
    for level, table in report['paired_vs_A'].items():
        lines += ['', f'## Paired vs A: {level}' + (' (primary: C, D, E with Holm)' if level == 'all' else
                                                     ' (exploratory)'), '',
                  '| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for condition, v in table.items():
            if not v:
                continue
            holm_p = report['holm_adjusted_p'].get(condition) if level == 'all' else None
            lines.append(
                f"| {condition} | {v['tasks']} | {v['pairs']} | {_pct(v['pass_rate'])} | {_pct(v['base_pass_rate'])} "
                f"| {v['difference']:+.3f} | {v['ci95']} | {v['p_permutation']} | "
                f"{'–' if holm_p is None else round(holm_p, 5)} | {v['mcnemar']['condition_only']}/"
                f"{v['mcnemar']['base_only']}, {v['mcnemar']['p_exact']} |")
    if report.get('e_subset'):
        e = report['e_subset']
        lines += ['', '## E triggered subset', '', f"Trigger rate: {_pct(e['trigger_rate'])}"]
        for key in ('triggered', 'triggered_and_A_failed_public'):
            if e[key]:
                lines.append(f"* {key}: {e[key]['pairs']} pairs, E {_pct(e[key]['E_pass_rate'])} vs "
                             f"A {_pct(e[key]['A_pass_rate'])}")
    gaps = {c: g for c, g in (report.get('gap_closed_vs_B') or {}).items() if g}
    if gaps:
        lines += ['', '## Gap closed toward B: (X − A) / (B − A)', '',
                  '| Condition | Tasks | Rate | A rate | B rate | Gap closed | 95% CI | resamples without a gap |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- |']
        for c, g in gaps.items():
            lines.append(f"| {c} | {g['tasks']} | {_pct(g['rate'])} | {_pct(g['base_rate'])} | {_pct(g['ceiling_rate'])} "
                         f"| {'–' if g['gap_closed'] is None else g['gap_closed']} | {g['ci95'] or '–'} "
                         f"| {g['resamples_without_gap']} |")
    table = report['summary'].get('all', {})
    if any(s and s.get('seed_consistency') for s in table.values()):
        lines += ['', '## Seed consistency (all): tasks with every seed passing, mixed, or failing', '',
                  '| Condition | Tasks | All pass | Mixed | All fail | Mean seed variance p(1−p) |',
                  '| --- | --- | --- | --- | --- | --- |']
        for c, s in table.items():
            k = s and s.get('seed_consistency')
            if k:
                lines.append(f"| {c} | {k['tasks']} | {k['all_pass']} | {k['mixed']} | {k['all_fail']} "
                             f"| {k['mean_seed_variance']} |")
    lines += ['', '## Frontier usage (all): tokens, and the one-off guidance cost', '',
              '| Condition | Run-time tokens in/out | Upfront tokens in/out | Tokens per pass | Guidance artifacts '
              '| Upfront $ | Authoring s median (total) |', '| --- | --- | --- | --- | --- | --- | --- |']
    for c, s in table.items():
        if s:
            t, u = s['frontier_tokens'], s.get('upfront_guidance')
            lat = u['latency_seconds'] if u else None
            lines.append(f"| {c} | {t['run_input']}/{t['run_output']} | {t['upfront_input']}/{t['upfront_output']} "
                         f"| {t['per_pass'] if t['per_pass'] is not None else '–'} | {u['artifacts'] if u else 0} "
                         f"| {u['cost_usd'] if u else 0.0} | "
                         + (f"{lat['median']} ({u['latency_seconds_total']})" if lat else '–') + ' |')
    sens = report.get('sensitivity_exclude_timeouts')
    if sens:
        lines += ['', f"## Sensitivity: local timeouts excluded ({sens['excluded_blocks']} (task, seed) blocks dropped, "
                      f"{sens['included_runs']} runs kept)", '',
                  '| Condition | Runs | Pass | Pass rate | Δ vs A | 95% CI | p (perm) |', '| --- | --- | --- | --- | --- | --- | --- |']
        for c, s in sens['summary'].items():
            p = sens['paired_vs_A'].get(c)
            lines.append(f"| {c} | {s['runs']} | {s['passes']} | {_pct(s['pass_rate'])} | "
                         + (f"{p['difference']:+.3f} | {p['ci95']} | {p['p_permutation']} |" if p else '– | – | – |'))
    lines += ['', '## Process (all): what the local agent did', '',
              '| Condition | Runs with a program | Runs truncated | First response tokens median | '
              'Local tokens median | s to first program median |', '| --- | --- | --- | --- | --- | --- |']
    for c, s in report['summary'].get('all', {}).items():
        if s:
            q = lambda k: s[k]['median'] if s.get(k) else '–'
            lines.append(f"| {c} | {s['runs_with_candidate']}/{s['runs']} | {s['runs_with_truncation']} | "
                         f"{q('first_response_tokens')} | {q('local_completion_tokens')} | {q('seconds_to_first_candidate')} |")
    if report.get('process_vs_A'):
        lines += ['', '| Paired vs A | Pairs | Δ local tokens (median) | Δ first response tokens | '
                      'Δ s to first program | program only here / only in A |', '| --- | --- | --- | --- | --- | --- |']
        for c, p in report['process_vs_A'].items():
            if p:
                m = lambda k: f"{p[k]['median']:+} ({p[k]['pairs']})" if p.get(k) else '–'
                lines.append(f"| {c} | {p['pairs']} | {m('local_completion_tokens')} | {m('first_response_tokens')} | "
                             f"{m('seconds_to_first_candidate')} | {p['candidate_only_in_condition']} / "
                             f"{p['candidate_only_in_base']} |")
    if report.get('host_speed'):
        lines += ['', '## Host speed (local requests)', '',
                  '| Host | Model | Runs | Requests | tok/s median | tok/s p10 | ≥150 s | timed out | near-limit share |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for h in report['host_speed']:
            lines.append(f"| {h['host']} | {h['coding_model']} | {h['runs']} | {h['requests']} | "
                         f"{h['decode_tok_s_median']} | {h['decode_tok_s_p10']} | {h['requests_over_near_s']} | "
                         f"{h['timed_out_requests']} | {_pct(h['near_limit_share'])} |")
    lines += ['', '## Failure categories (all)', '',
              '| Condition | ' + ' | '.join(CATEGORIES) + ' |', '| --- |' + ' --- |' * len(CATEGORIES)]
    for condition, s in report['summary'].get('all', {}).items():
        if s:
            lines.append(f'| {condition} | ' + ' | '.join(str(s['categories'].get(c, 0)) for c in CATEGORIES) + ' |')
    for condition, t in (report.get('transitions_from_A') or {}).items():
        if not t:
            continue
        cols = t['categories']
        lines += ['', f"## Transitions A -> {condition} ({t['pairs']} pairs; rows: A, columns: {condition}; "
                      f"A passes that {condition} lost: {t['broken']})", '',
                  f'| A \\ {condition} | ' + ' | '.join(cols) + ' | fixed |', '| --- |' + ' --- |' * (len(cols) + 1)]
        for a in cols:
            if a not in t['matrix']:
                continue
            fixed = t['fixed'].get(a)
            fixed_text = f"{fixed['passed']}/{fixed['base_failures']}" if fixed else '–'
            lines.append(f'| {a} | ' + ' | '.join(str(t['matrix'][a].get(x, 0)) for x in cols) + f' | {fixed_text} |')
    lines += ['', '## Outcomes (all)', '']
    for condition, s in report['summary'].get('all', {}).items():
        if s:
            lines.append(f"* {condition}: " + ', '.join(f'{k} {v}' for k, v in sorted(s['outcomes'].items())))
    return '\n'.join(lines) + '\n'


def write(report, rows, out_dir):
    out_dir = Path(out_dir)
    write_json(out_dir / 'report.json', report)
    (out_dir / 'report.md').write_text(markdown(report), encoding='utf-8', newline='\n')
    fields = sorted({k for r in rows for k in r if not k.startswith('_')})
    with (out_dir / 'runs.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
