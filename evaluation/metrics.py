"""Final metrics and statistics over one or more finished batches.

Input per batch directory (written by ``guided_agent batch`` / ``measure`` and ``evaluation score``): ``plan.json``
(the scheduled attempts), ``<run>/result.json``, ``<run>/measurement.json`` (schema csc2108-run-measurement-v1),
``<run>/attempts.jsonl`` (judge-public history) and ``eval/<run_id>.json`` (the hidden verdict). Difficulty and
hidden-test counts come from the judge manifests (and the manifest each plan records); exposure from
``evaluation/data/exposure-registry.json``.

Rules (see evaluation/README.md):

* **Completeness first.** ``evaluation.validate`` gives every scheduled attempt a state. An official report requires
  every attempt hidden-scored with a valid verdict or covered by a documented exclusion, consistent batches and one
  hardware/model cohort; otherwise ``analyze`` raises ``IncompleteEvaluation``. With ``preliminary=True`` the report is
  labelled PRELIMINARY and every (task, seed) block with an unfinished, unscored or invalid attempt is excluded: an
  unscored run is never counted as a failure.
* A run is one scheduled (task, condition, seed). The primary metric is the final pass rate (= pass@1): hidden status
  ``pass`` divided by included runs. A missing submission is a failure.
* Every run gets one failure category (``CATEGORIES``). Infrastructure is decided *before* the outcome is looked at,
  so exclusion never depends on whether the run passed: a hidden ``infrastructure_error`` / ``malformed_record``, a
  frontier provider fault (transport or HTTP error, ledger ceiling reached, provider error; B's coder or E's
  diagnosis), or a runner infrastructure error that is not the model's own (Docker, judge, crashed model server, outer
  timeout). These, documented exclusions and unfinished attempts exclude their (task, seed) block from every condition.
  A local model request that timed out (``local_timeout``: the 180 s request limit, or the 600 s budget ending
  mid-request), a context overflow, truncation, a missing submission and an exhausted budget are the agent's own
  failures and count as failed runs.
* The transition table pairs each condition with A on the same (task, seed): A's category -> the condition's.
* Paired comparisons of each condition against A use the task as the unit (mean over the seeds both have),
  a 10,000-resample bootstrap CI over tasks and an exact/Monte Carlo sign-flip permutation p-value; Holm is applied
  across the primary comparisons C, D and E only. McNemar on (task, seed) pairs is exploratory (pairs of one task are
  not independent), and the E triggered subset is descriptive (it conditions on the trigger).
"""
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from . import efficiency, exposure as exposurelib, passk, provenance, validate
from .plan import read_json, write_json

PRIMARY = ('C', 'D', 'E')
EXPLORATORY = ('B',)
INFRA_HIDDEN = {'infrastructure_error', 'malformed_record'}
LABELS = {'A': 'A — Local', 'B': 'B — Frontier', 'C': 'C — Planning', 'D': 'D — Contract', 'E': 'E — Diagnosis'}
# E diagnosis error categories that are provider faults, not the method's outcome ('incomplete_response', a frontier
# answer cut at the output cap, and 'no_local_budget', no request made, stay E outcomes).
PROVIDER_FAULTS = {'transport_error', 'budget_exhausted', 'provider_error', 'timeout', 'isolation_violation'}
REPO = Path(__file__).resolve().parents[1]


class IncompleteEvaluation(RuntimeError):
    """The batches are not complete and consistent enough for an official report."""

    def __init__(self, problems):
        super().__init__(f'{len(problems)} problems block an official report (pass --preliminary for a labelled '
                         'preliminary report): ' + '; '.join(problems[:8]) + (' ...' if len(problems) > 8 else ''))
        self.problems = problems


# ----------------------------------------------------------------------------- loading
def manifest_entries(manifests):
    found = {}
    for manifest in manifests:
        for entry in read_json(manifest)['tasks']:
            found.setdefault(entry['task_id'], entry)
    return found


def difficulties(manifests):
    return {t: e['difficulty'] for t, e in manifest_entries(manifests).items()}


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


def _hidden_failure_verdict(verdict):
    counts = (verdict or {}).get('verdict_counts') or {}
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
    'infrastructure',           # real infrastructure or provider fault: excluded (rerun first)
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


def frontier_fault(document, agent_error):
    """A frontier provider fault (B's coder or E's diagnosis), or None. Decided without looking at the outcome."""
    diagnosis = (document.get('condition') or {}).get('diagnosis') or {}
    if diagnosis.get('error_category') in PROVIDER_FAULTS:
        return 'frontier_provider:' + diagnosis['error_category']
    if 'FrontierCoderError' in agent_error:
        if 'ceiling' in agent_error or 'spending bound' in agent_error:
            return 'frontier_provider:budget_exhausted'
        if 'API HTTP' in agent_error or 'API transport error' in agent_error:
            return 'frontier_provider:transport_error'
        return 'frontier_provider:provider_error'
    return None


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


def infrastructure_reason(*, hidden, correct, agent_error, fault, record=None):
    """Why a run is an infrastructure failure (None: it is not). Independent of whether it passed."""
    if hidden in INFRA_HIDDEN:
        return f'hidden {hidden}'
    if fault:
        return fault
    timeout = correct.get('exit_status') == 'infra_error' and is_local_model_timeout(agent_error)
    if correct.get('infrastructure_failure') and not timeout and not correct.get('context_overflow'):
        if (record or {}).get('raw_exit_status') == 'OuterTimeout':
            return 'outer timeout (supervisor)'
        if correct.get('setup_error'):
            return 'setup error: ' + str(correct['setup_error'])[:120]
        return 'runner infrastructure error' + (f': {agent_error[:120]}' if agent_error else '')
    return None


def failure_category(*, passed, hidden, correct, inference, agent_error, final_public_pass, candidate, fault=None):
    if infrastructure_reason(hidden=hidden, correct=correct, agent_error=agent_error, fault=fault):
        return 'infrastructure'
    if passed:
        return 'hidden_pass'
    if correct.get('context_overflow'):
        return 'context_overflow'
    if correct.get('exit_status') == 'infra_error' and is_local_model_timeout(agent_error):
        return 'local_timeout_with_program' if candidate else 'local_timeout_no_program'
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


def _ledger_indices(record):
    """Ledger entries the run's own records point at (B coder turns, E diagnosis, the C/D guidance artifact)."""
    found = set()
    for call in (record.get('coder') or {}).get('calls') or []:
        if call.get('ledger_index') is not None:
            found.add(call['ledger_index'])
    response = ((record.get('diagnosis') or {}).get('response') or {})
    if response.get('ledger_index') is not None:
        found.add(response['ledger_index'])
    artifact = (record.get('guidance_provenance') or {}).get('artifact')
    if artifact and Path(artifact).is_file():
        try:
            index = (read_json(artifact).get('generation') or {}).get('ledger_index')
            if index is not None:
                found.add(index)
        except (OSError, ValueError):
            pass
    return sorted(found)


def run_row(run_dir, item, entry, verdict, registry=None, record=None):
    """One included-candidate row (a hidden-scored run). ``verdict`` is the validated eval/<run_id>.json."""
    entry = entry or {}
    document = _measurement(run_dir)
    ident, correct = document['identity'], document['correctness']
    agent, frontier, time_ = document['agent'], document['frontier'], document['time']
    inference = document['local_inference']
    attempts = _attempts(run_dir)
    statuses = [(a.get('result') or {}).get('status') for a in attempts]
    hidden = (verdict or {}).get('status')
    passed = hidden == 'pass'
    final_public_pass = correct.get('final_public_status') == 'pass'
    candidate = bool(correct.get('candidate_produced'))
    agent_error = _agent_error(run_dir)
    responses = _ollama_responses(run_dir)
    fault = frontier_fault(document, agent_error)
    infra_reason = infrastructure_reason(hidden=hidden, correct=correct, agent_error=agent_error, fault=fault,
                                         record=record)
    category = failure_category(passed=passed, hidden=hidden, correct=correct, inference=inference,
                                agent_error=agent_error, final_public_pass=final_public_pass, candidate=candidate,
                                fault=fault)
    infra = category == 'infrastructure'
    if infra:
        outcome = 'infrastructure'
    elif passed:
        outcome = 'hidden_pass'
    elif final_public_pass:
        outcome = f'public_pass_hidden_fail:{_hidden_failure_verdict(verdict)}'
    elif candidate:
        outcome = f'never_passed_public:{_last_public_verdict(attempts)}'
    else:
        outcome = f"no_submission:{correct.get('exit_status')}"
    diagnosis = (document.get('condition') or {}).get('diagnosis') or {}
    exposure_class = exposurelib.classify(item['task_id'], registry)['class'] if registry else entry.get('exposure')
    fields = efficiency.run_fields(document)
    requests = frontier.get('requests') or []
    upfront = [r for r in requests if r.get('upfront')]
    host = ident.get('host') or {}
    return {
        'batch': run_dir.parent.name, 'run_dir': run_dir.name, 'run_id': ident['run_id'],
        'task_id': item['task_id'], 'condition': item['condition'], 'seed': item.get('seed'),
        'difficulty': entry.get('difficulty', 'unknown'), 'n_hidden': entry.get('n_hidden'),
        'exposure': exposure_class or 'none_known', 'exposure_subgroup': exposurelib.subgroup(exposure_class or 'none_known'),
        'status': 'run', 'state': 'scored', 'hidden_status': hidden, 'hidden_passed': (verdict or {}).get('passed'),
        'hidden_total': (verdict or {}).get('total'), 'passed': passed,
        'infrastructure': infra, 'infrastructure_reason': infra_reason if infra else None,
        'context_overflow': bool(correct.get('context_overflow')),
        'exit_status': correct.get('exit_status'), 'candidate': candidate,
        'final_public_pass': final_public_pass, 'had_public_failure': 'candidate_failure' in statuses,
        'public_tests': len(attempts), 'outcome': outcome, 'category': category,
        'local_timeout': category.startswith('local_timeout'), 'agent_error': agent_error[:200] or None,
        'truncated_responses': inference.get('truncated_responses'),
        'first_response_tokens': responses[0]['eval_count'] if responses else None,
        'first_response_seconds': round(responses[0]['total_duration'] / 1e9, 2) if responses else None,
        'seconds_to_first_candidate': agent.get('seconds_to_first_executable_candidate'),
        'host': '/'.join(str(host.get(k)) for k in ('system', 'machine', 'node')),
        '_requests': [(r['eval_count'], r['eval_duration'] / 1e9, r['total_duration'] / 1e9) for r in responses
                      if r.get('eval_count') and r.get('eval_duration') and r.get('total_duration')],
        'actions': agent.get('actions'), 'repairs': agent.get('repairs'),
        'wall_seconds': time_.get('wall_seconds'), 'local_coding_seconds': time_.get('local_coding_seconds'),
        'public_test_seconds': time_.get('public_test_seconds'), 'sandbox_tool_seconds': time_.get('sandbox_tool_seconds'),
        'frontier_wait_seconds': time_.get('frontier_seconds'),
        'frontier_requests': frontier.get('n_requests'), 'frontier_failures': frontier.get('provider_failures') or 0,
        'upfront_cost_usd': (fields['_upfront'] or {}).get('cost_usd') if upfront else 0.0,
        'upfront_input_tokens': _sum_or_none(r.get('input_tokens') for r in upfront) if upfront else 0,
        'upfront_output_tokens': _sum_or_none(r.get('output_tokens') for r in upfront) if upfront else 0,
        'upfront_latency_seconds': _sum_or_none(r.get('latency_seconds') for r in upfront) if upfront else 0.0,
        'e_triggered': diagnosis.get('trigger_observed'), 'e_delivered': diagnosis.get('delivered'),
        'e_error_category': diagnosis.get('error_category'),
        'host_backend': ident.get('host_backend'), 'coding_model': ident.get('coding_model'),
        'coding_model_digest': ident.get('coding_model_digest'), 'agent_config_sha256': ident.get('agent_config_sha256'),
        'profile': ident.get('profile'), 'frontier_requested_model': ident.get('frontier_requested_model'),
        'frontier_observed_model': ident.get('frontier_observed_model'), 'judge_version': (verdict or {}).get('judge_version'),
        '_ledger_indices': _ledger_indices(record or {}),
        **fields,
    }


def placeholder_row(batch, run_dir, item, entry, state, problems, registry=None, exclusion=None):
    entry = entry or {}
    exposure_class = exposurelib.classify(item['task_id'], registry)['class'] if registry else entry.get('exposure')
    return {'batch': batch.name, 'run_dir': run_dir.name, 'task_id': item['task_id'], 'condition': item['condition'],
            'seed': item.get('seed'), 'difficulty': entry.get('difficulty', 'unknown'), 'n_hidden': entry.get('n_hidden'),
            'exposure': exposure_class or 'none_known',
            'exposure_subgroup': exposurelib.subgroup(exposure_class or 'none_known'),
            'status': 'not_run' if state == 'not_executed' else state, 'state': state, 'passed': False,
            'infrastructure': False, 'outcome': state, 'category': state, 'local_timeout': False, '_requests': [],
            'problems': '; '.join(problems) or None,
            'exclusion_reason': (exclusion or {}).get('reason')}


def _plan_manifests(batch, plan):
    path = (plan.get('benchmark') or {}).get('manifest')
    if not path:
        return []
    path = Path(path)
    path = path if path.is_absolute() else REPO / path
    return [path] if path.is_file() else []


def load(batch_dirs, manifests, registry=None, study=None, statuses=None):
    """Every scheduled attempt of every batch: a full row for hidden-scored runs, a placeholder otherwise."""
    rows = []
    statuses = {} if statuses is None else statuses
    for batch in map(Path, batch_dirs):
        plan = read_json(batch / 'plan.json')
        entries = manifest_entries(list(manifests) + _plan_manifests(batch, plan))
        status = validate.batch_status(batch, study, plan)
        statuses[str(batch)] = status
        for attempt in status['attempts']:
            item, state = attempt['item'], attempt['state']
            entry = entries.get(item['task_id'])
            if state == 'scored':
                rows.append(run_row(attempt['run_dir'], item, entry, attempt['verdict'], registry, attempt['record']))
            else:
                rows.append(placeholder_row(batch, attempt['run_dir'], item, entry, state, attempt['problems'],
                                            registry, attempt.get('exclusion')))
    return rows


def merge_reruns(rows):
    """Later batches rerun earlier infrastructure failures: a later run of the same (task, condition, seed)
    replaces an earlier row only when that row was an infrastructure failure or never produced a usable result."""
    kept, replaced = {}, []
    for row in rows:
        key = (row['task_id'], row['condition'], row['seed'])
        old = kept.get(key)
        if old is None:
            kept[key] = row
        elif old['status'] != 'run' or old['infrastructure']:
            kept[key] = row
            replaced.append({'task_id': key[0], 'condition': key[1], 'seed': key[2], 'old': old['run_dir'],
                             'old_batch': old['batch'], 'old_outcome': old['outcome'], 'new_batch': row['batch']})
        elif row['status'] != 'run':
            continue   # a placeholder never replaces a valid run
        else:
            raise ValueError(f'{key} has two valid runs ({old["batch"]}, {row["batch"]}); pass one of them')
    return list(kept.values()), replaced


# ----------------------------------------------------------------------------- statistics
def _quantiles(values):
    return efficiency.quantiles(values)


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


def ratio_ci(means, resamples=10000, seed=2108):
    """(X - A) / (B - A) over per-task (x, a, b) values, with a task-resampled 95% CI (resamples without a positive
    B - A gap are skipped and counted)."""
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
    return {'rate': round(x, 4), 'base_rate': round(a, 4), 'ceiling_rate': round(b, 4),
            'gap_closed': None if point is None else round(point, 4), 'ci95': ci,
            'resamples_without_gap': resamples - len(valid),
            **({'note': 'undefined: B does not exceed A'} if point is None else {})}


# ----------------------------------------------------------------------------- aggregation
def exclusions(rows):
    """(task, seed) -> reasons, for every block with an unusable or infrastructure run (or a documented exclusion)."""
    blocks = defaultdict(list)
    for row in rows:
        key = (row['task_id'], row['seed'])
        if row['state'] == 'excluded':
            blocks[key].append(f"{row['condition']}:documented ({row.get('exclusion_reason')})")
        elif row['status'] != 'run':
            blocks[key].append(f"{row['condition']}:{'not_run' if row['state'] == 'not_executed' else row['state']}")
        elif row['infrastructure']:
            blocks[key].append(f"{row['condition']}:infrastructure ({row.get('infrastructure_reason')})")
    return dict(blocks)


def condition_summary(rows):
    n = len(rows)
    if not n:
        return None
    passes = sum(r['passed'] for r in rows)
    failed_public = [r for r in rows if r.get('had_public_failure')]
    eff = efficiency.condition(rows, passes)
    shared = efficiency.artifacts(rows)
    latencies = [u.get('latency_seconds') for u, _ in shared.values()]
    tokens = {'run_input': _sum_or_none(r.get('run_input_tokens') for r in rows),
              'run_output': _sum_or_none(r.get('run_output_tokens') for r in rows),
              'upfront_input': eff['tokens']['upfront_input'], 'upfront_output': eff['tokens']['upfront_output'],
              'cached_input': eff['tokens']['cached_input'], 'reasoning': eff['tokens']['reasoning'],
              'total': eff['tokens']['total']}
    tokens['per_pass'] = round(tokens['total'] / passes, 1) if tokens['total'] is not None and passes else None
    cost = eff['cost_usd']
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
        'frontier_cost_usd': {'metric': cost['metric'], 'run_time': cost['runtime'], 'upfront_one_off': cost['upfront'],
                              'total': cost['total'], 'per_pass': cost['per_pass']['value'],
                              'guidance_artifacts': cost['guidance_artifacts'],
                              'requests_missing_usage': eff['requests']['missing_usage']},
        'frontier_tokens': tokens,
        'upfront_guidance': {'artifacts': len(shared), 'cost_usd': cost['upfront'],
                             'input_tokens': tokens['upfront_input'], 'output_tokens': tokens['upfront_output'],
                             'latency_seconds_total': (None if _sum_or_none(latencies) is None
                                                       else round(_sum_or_none(latencies), 2)),
                             'latency_seconds': _quantiles(latencies),
                             'reused_by_attempts': sorted(u for _, u in shared.values())} if shared else None,
        'efficiency': eff,
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
    return {'tasks': len(means)} | ratio_ci(means, resamples, seed)


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
            'mcnemar': {'condition_only': b, 'base_only': c, 'p_exact': round(mcnemar_exact(b, c), 5),
                        'note': 'exploratory: (task, seed) pairs of one task are not independent'}}


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
    """Descriptive only: conditioning on E's trigger is not a randomized comparison."""
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
            if any('E' in v for v in by.values()) else None,
            'note': 'descriptive: selecting on whether the diagnosis triggered is not a randomized comparison'}


def sensitivity_exclude_timeouts(included):
    """Secondary analysis: drop every (task, seed) block in which any run timed out locally."""
    blocks = {(r['task_id'], r['seed']) for r in included if r['local_timeout']}
    return _subset_summary([r for r in included if (r['task_id'], r['seed']) not in blocks]) | {
        'excluded_blocks': len(blocks)}


def _subset_summary(kept):
    conditions = sorted({r['condition'] for r in kept})
    summary = {}
    for c in conditions:
        items = [r for r in kept if r['condition'] == c]
        summary[c] = {'runs': len(items), 'passes': sum(r['passed'] for r in items),
                      'pass_rate': round(sum(r['passed'] for r in items) / len(items), 4)}
    return {'included_runs': len(kept), 'tasks': len({r['task_id'] for r in kept}), 'summary': summary,
            'paired_vs_A': {c: paired(kept, c) for c in conditions if c != 'A'} if 'A' in conditions else {}}


def hidden_coverage(included, threshold):
    """Distribution of hidden-test counts over included tasks, and a sensitivity analysis without low-coverage tasks."""
    per_task = {r['task_id']: r.get('n_hidden') for r in included}
    low = sorted(t for t, n in per_task.items() if n is not None and n < threshold)
    out = {'threshold': threshold, 'tasks': len(per_task),
           'distribution': {str(k): v for k, v in sorted(Counter(per_task.values()).items(), key=lambda kv: str(kv[0]))},
           'unknown': sorted(t for t, n in per_task.items() if n is None), 'below_threshold': low}
    if not low:
        return out | {'sensitivity': {'applicable': False,
                                      'note': f'every included task has at least {threshold} hidden tests'}}
    return out | {'sensitivity': {'applicable': True} | _subset_summary([r for r in included if r['task_id'] not in low])}


def exposure_breakdown(included, ks):
    """Pass rate, pass@k and paired comparisons per historical-exposure subgroup (descriptive)."""
    out = {}
    for group in ('exposed', 'potentially_unseen', 'uncertain'):
        items = [r for r in included if r.get('exposure_subgroup') == group]
        if not items:
            continue
        out[group] = _subset_summary(items) | {
            'classes': dict(Counter(e for _, e in {(r['task_id'], r['exposure']) for r in items})),
            'pass_at_k': {c: passk.summary(items, c, ks, bootstrap_ci) for c in sorted({r['condition'] for r in items})}}
    return out


def pass_at_k_report(included, ks, levels):
    conditions = sorted({r['condition'] for r in included})
    report = {'ks': ks, 'primary': 'pass@1', 'by_level': {}, 'versus_A': {}, 'gap_closed_vs_B': {}}
    for level in levels:
        items = [r for r in included if level == 'all' or r['difficulty'] == level]
        report['by_level'][level] = {c: passk.summary(items, c, ks, bootstrap_ci) for c in conditions}
        if 'A' in conditions:
            report['versus_A'][level] = {c: {f'pass@{k}': passk.versus(items, c, 'A', k, bootstrap_ci) for k in ks}
                                         for c in conditions if c != 'A'}
        if {'A', 'B'} <= set(conditions):
            report['gap_closed_vs_B'][level] = {
                c: {f'pass@{k}': passk.gap_closed(items, c, k, ratio_ci) for k in ks}
                for c in conditions if c not in ('A', 'B')}
    report['notes'] = [
        'pass@1 is the primary outcome; pass@2 and pass@3 are secondary (the benefit of repeated attempts)',
        'confidence intervals resample tasks; repeated attempts on one task are not independent problems',
        'C and D reuse one upfront guidance artifact per task across seeds: their pass@k describes repeated local '
        'execution given shared guidance, not independently regenerated frontier guidance',
        'pass@k counts a task as solved when any of k attempts passes the hidden tests; it does not imply that an agent '
        'could identify the correct submission without the hidden tests',
    ]
    return report


def cohort_problems(included):
    """Distinct hardware hosts, local model digests, agent configurations or frontier models among included runs."""
    problems, warnings = [], []
    checks = {'host': 'hardware hosts (timing would be pooled)',
              'coding_model_digest': 'local model digests', 'agent_config_sha256': 'shared-agent configurations',
              'profile': 'agent profiles', 'frontier_requested_model': 'requested frontier models'}
    for key, label in checks.items():
        relevant = [r for r in included if not (r['condition'] == 'B' and key in ('coding_model_digest', 'profile',
                                                                                 'agent_config_sha256'))
                    and not (r['condition'] == 'A' and key == 'frontier_requested_model')]
        values = sorted({str(r.get(key)) for r in relevant if r.get(key) is not None})
        if len(values) > 1:
            problems.append(f'included runs mix {len(values)} {label}: {values[:4]}')
    observed = sorted({r['frontier_observed_model'] for r in included if r.get('frontier_observed_model')})
    if len(observed) > 1:
        warnings.append(f'the provider reported {len(observed)} frontier model snapshots: {observed}')
    return problems, warnings


def _batch_provenance(batch_dirs):
    out = []
    for batch in map(Path, batch_dirs):
        path = batch / 'provenance.json'
        out.append((batch.name, read_json(path) if path.exists() else None))
    return out


def _ledger(batch_dirs, ledger, purposes, attributed):
    path = Path(ledger) if ledger else None
    if path is None:
        first = Path(batch_dirs[0])
        if first.parent.name == 'runs' and (first.parent.parent / 'api-ledger.json').exists():
            path = first.parent.parent / 'api-ledger.json'
    if path is None or not path.exists():
        return None
    return {'ledger': str(path)} | efficiency.ledger_report(read_json(path), purposes, attributed)


def main_table(summary, gaps, passk_report):
    rows = []
    for c, s in summary.items():
        if not s:
            continue
        eff = s['efficiency']
        p1 = ((passk_report['by_level'].get('all') or {}).get(c) or {}).get('pass@1') or {}
        rows.append({'condition': c, 'label': LABELS.get(c, c), 'runs': s['runs'], 'hidden_pass_rate': s['pass_rate'],
                     'pass@1': p1.get('value'), 'pass@1_ci95': p1.get('ci95'),
                     'e2e_latency_seconds': eff['latency']['cold_start_seconds'],
                     'frontier_cost_usd': eff['cost_usd']['total'], 'cost_per_pass_usd': eff['cost_usd']['per_pass'],
                     'frontier_tokens': eff['tokens']['total'],
                     'gap_closed': (gaps.get(c) or {}).get('gap_closed') if c not in ('A', 'B') else None})
    return rows


def analyze(batch_dirs, manifests, *, preliminary=False, ledger=None, registry=None, study=None, ks=None,
            low_coverage_threshold=40):
    registry = registry if registry is not None else (exposurelib.load() if exposurelib.REGISTRY.exists() else None)
    statuses = {}
    rows, replaced = merge_reruns(load(batch_dirs, manifests, registry, study, statuses))
    problems = []
    for name, status in statuses.items():
        problems += [f'{Path(name).name}: {p}' for p in status['problems']]
    unusable = [r for r in rows if r['state'] not in validate.DONE]
    if unusable:
        counts = Counter(r['state'] for r in unusable)
        problems.append(f'{len(unusable)} scheduled attempts are not hidden-scored or excluded: {dict(counts)}')
        problems += [f"{r['run_dir']}: {r['state']}" + (f" ({r['problems']})" if r.get('problems') else '')
                     for r in unusable[:5]]
    problems += provenance.compatible(_batch_provenance(batch_dirs))
    excluded = exclusions(rows)
    included = [r for r in rows if (r['task_id'], r['seed']) not in excluded]
    cohort, warnings = cohort_problems(included)
    problems += cohort
    if problems and not preliminary:
        raise IncompleteEvaluation(problems)
    conditions = sorted({r['condition'] for r in included})
    levels = ['all'] + sorted({r['difficulty'] for r in included})
    summary = {level: {c: condition_summary([r for r in included if r['condition'] == c
                                             and (level == 'all' or r['difficulty'] == level)])
                       for c in conditions} for level in levels}
    comparisons = {level: {c: paired([r for r in included if level == 'all' or r['difficulty'] == level], c)
                           for c in conditions if c != 'A'} for level in levels} if 'A' in conditions else {}
    primary = {c: v['p_permutation'] for c, v in comparisons.get('all', {}).items() if c in PRIMARY and v}
    hosts = Counter((r.get('host_backend'), r.get('coding_model')) for r in included)
    seeds = sorted({r['seed'] for r in rows if r.get('seed') is not None})
    ks = ks or list(range(1, max(1, max(Counter((r['task_id'], r['condition']) for r in included).values(),
                                        default=1)) + 1))
    passk_report = pass_at_k_report(included, ks, levels)
    gaps = {c: gap_closed(included, c) for c in conditions if c not in ('A', 'B')} if {'A', 'B'} <= set(conditions) else {}
    all_summary = summary.get('all', {})
    relative = {}
    for c in conditions:
        s = all_summary.get(c)
        if not s:
            continue
        rel = {}
        if 'B' in all_summary and c != 'B':
            rel['vs_B'] = efficiency.relative(s['efficiency'], all_summary['B']['efficiency'])
        if 'A' in all_summary and c != 'A':
            a = all_summary['A']
            rel['additional_passes_per_usd_vs_A'] = efficiency.passes_per_dollar(
                s['passes'], s['efficiency']['cost_usd']['total'], a['passes'], a['efficiency']['cost_usd']['total'])
        rel['runtime'] = {ref: {key: efficiency.paired_runtime(included, c, ref, key)
                                for key in ('cold_start_seconds', 'warm_start_seconds')}
                          for ref in ('A', 'B') if ref in conditions and ref != c}
        relative[c] = rel
    purposes = {f"{read_json(Path(b) / 'plan.json')['batch']} {suffix}" for b in batch_dirs
                for suffix in ('B', 'E', 'guidance')}
    attributed = {i for r in included for i in r.get('_ledger_indices') or []}
    reasons = Counter(reason.split(':', 1)[1].split(' (')[0] for v in excluded.values() for reason in v)
    report = {
        'schema': 'csc2108-evaluation-report-v2', 'status': 'preliminary' if preliminary else 'official',
        'problems': problems, 'warnings': warnings, 'batches': [str(b) for b in batch_dirs],
        'completeness': {Path(k).name: validate.summary(v) for k, v in statuses.items()},
        'scheduled_runs': len(rows), 'included_runs': len(included), 'replaced_by_rerun': replaced,
        'sample_sizes': {
            'scheduled': len(rows), 'included': len(included), 'excluded_runs': len(rows) - len(included),
            'excluded_blocks': len(excluded), 'excluded_block_reasons': dict(reasons),
            'states': dict(Counter(r['state'] for r in rows)),
            'by_condition': {c: {'scheduled': sum(r['condition'] == c for r in rows),
                                 'included': sum(r['condition'] == c for r in included)}
                             for c in sorted({r['condition'] for r in rows})},
            'tasks_included': len({r['task_id'] for r in included}), 'seeds': seeds},
        'excluded_blocks': [{'task_id': t, 'seed': s, 'reasons': v} for (t, s), v in sorted(excluded.items(),
                                                                                             key=lambda kv: str(kv[0]))],
        'hosts': [{'backend': b, 'coding_model': m, 'runs': n} for (b, m), n in hosts.items()],
        'main_table': main_table(all_summary, gaps, passk_report),
        'summary': summary, 'paired_vs_A': comparisons, 'holm_adjusted_p': holm(primary) if primary else {},
        'pass_at_k': passk_report,
        'relative_efficiency': relative,
        'e_subset': e_subset(included) if {'A', 'E'} <= set(conditions) else None,
        'transitions_from_A': {c: transitions(included, c) for c in conditions if c != 'A'} if 'A' in conditions else {},
        'process_vs_A': {c: paired_process(included, c) for c in conditions if c != 'A'} if 'A' in conditions else {},
        'sensitivity_exclude_timeouts': sensitivity_exclude_timeouts(included),
        'gap_closed_vs_B': gaps,
        'exposure': exposure_breakdown(included, ks),
        'hidden_coverage': hidden_coverage(included, low_coverage_threshold),
        'study_expenditure': _ledger(batch_dirs, ledger, purposes, attributed),
        'host_speed': host_speed(rows),
        'provenance': {name: ({k: p.get(k) for k in ('plan_sha256', 'benchmark', 'git', 'code_fingerprint',
                                                     'hardware_cohort', 'local_model', 'frontier', 'pricing')}
                              if p else None) for name, p in _batch_provenance(batch_dirs)},
        'definitions': 'evaluation/README.md (Measurement definitions); evaluation/efficiency.py; evaluation/passk.py',
    }
    return report, rows


# ----------------------------------------------------------------------------- output
def _pct(x):
    return '–' if x is None else f'{100 * x:.1f}%'


def _q(q, digits=1):
    return '–' if not q else f"{q['median']:.{digits}f} ({q['q1']:.{digits}f}–{q['q3']:.{digits}f})"


def _usd(x):
    return '–' if x is None else f'${x:.4f}'


def _val(v, fmt='{:.3f}'):
    if isinstance(v, dict):
        v = v.get('value')
    return '–' if v is None else fmt.format(v)


def markdown(report):
    preliminary = report.get('status') == 'preliminary'
    lines = ['# PRELIMINARY evaluation report (incomplete or inconsistent data; not for the research report)'
             if preliminary else '# Evaluation report', '']
    if preliminary:
        lines += ['**Problems that block an official report:**', ''] + [f'* {p}' for p in report['problems']] + ['']
    lines += [f"Scheduled runs: {report['scheduled_runs']}; included: {report['included_runs']}; "
              f"excluded (task, seed) blocks: {len(report['excluded_blocks'])}.", '']
    for w in report.get('warnings') or []:
        lines.append(f'* warning: {w}')
    sizes = report.get('sample_sizes') or {}
    if sizes:
        lines += ['', '## Sample sizes and exclusions', '',
                  f"Tasks included: {sizes['tasks_included']}; seeds: {sizes['seeds']}; attempt states: {sizes['states']}; "
                  f"excluded-block reasons: {sizes['excluded_block_reasons'] or 'none'}.", '',
                  '| Condition | Scheduled | Included |', '| --- | --- | --- |']
        for c, v in sizes['by_condition'].items():
            lines.append(f"| {c} | {v['scheduled']} | {v['included']} |")
    for block in report['excluded_blocks']:
        lines.append(f"* excluded {block['task_id']} seed {block['seed']}: {', '.join(block['reasons'])}")
    for item in report.get('replaced_by_rerun') or []:
        lines.append(f"* rerun: {item['task_id']} {item['condition']} seed {item['seed']} ({item['old_outcome']} in "
                     f"{item['old_batch']}) replaced by {item['new_batch']}")
    if report.get('main_table'):
        lines += ['', '## Main results (all tasks)', '',
                  '| Condition | Hidden pass rate | E2E latency s, median (IQR) | Frontier cost | Cost/pass | '
                  'Frontier tokens | Gap closed |', '| --- | --- | --- | --- | --- | --- | --- |']
        for r in report['main_table']:
            lines.append(f"| {r['label']} | {_pct(r['hidden_pass_rate'])} | {_q(r['e2e_latency_seconds'])} | "
                         f"{_usd(r['frontier_cost_usd'])} | {_usd(r['cost_per_pass_usd'].get('value'))} | "
                         f"{r['frontier_tokens'] if r['frontier_tokens'] is not None else '–'} | "
                         f"{_val(r['gap_closed'])} |")
        lines += ['', 'E2E latency is cold-start (C, D include their upfront guidance authoring); frontier cost is '
                      'token-derived (usage x list price), not invoiced; frontier tokens are input + output '
                      '(reasoning included in output).']
    pk = report.get('pass_at_k') or {}
    if pk.get('by_level'):
        ks = pk['ks']
        lines += ['', '## pass@k (primary: pass@1; pass@2 and pass@3 secondary)', '',
                  '| Condition | ' + ' | '.join(f'Pass@{k}' for k in ks) + ' | All attempts successful | Tasks |',
                  '| --- |' + ' --- |' * (len(ks) + 2)]
        for c, s in (pk['by_level'].get('all') or {}).items():
            if s:
                cells = [f"{_val(s[f'pass@{k}'])} {s[f'pass@{k}']['ci95'] or ''}".strip() for k in ks]
                lines.append(f"| {LABELS.get(c, c)} | " + ' | '.join(cells)
                             + f" | {_pct(s['all_attempts_successful'])} | {s['tasks']} |")
        for level, table in pk['by_level'].items():
            if level == 'all':
                continue
            lines += ['', f'pass@k, {level}:', '', '| Condition | ' + ' | '.join(f'Pass@{k} (tasks)' for k in ks) + ' |',
                      '| --- |' + ' --- |' * len(ks)]
            for c, s in table.items():
                if s:
                    lines.append(f'| {c} | ' + ' | '.join(f"{_val(s[f'pass@{k}'])} ({s[f'pass@{k}']['eligible_tasks']})"
                                                         for k in ks) + ' |')
        versus = (pk.get('versus_A') or {}).get('all') or {}
        if versus:
            lines += ['', 'Matched pass@k difference vs A (95% task-bootstrap CI):', '',
                      '| Condition | ' + ' | '.join(f'Δ pass@{k}' for k in ks) + ' |', '| --- |' + ' --- |' * len(ks)]
            for c, v in versus.items():
                lines.append(f'| {c} | ' + ' | '.join(
                    f"{_val(v[f'pass@{k}'].get('difference'), '{:+.3f}')} {v[f'pass@{k}'].get('ci95') or ''}".strip()
                    for k in ks) + ' |')
        gaps = (pk.get('gap_closed_vs_B') or {}).get('all') or {}
        if gaps:
            lines += ['', 'Gap closed toward B per k, (X − A) / (B − A):', '',
                      '| Condition | ' + ' | '.join(f'pass@{k}' for k in ks) + ' |', '| --- |' + ' --- |' * len(ks)]
            for c, v in gaps.items():
                lines.append(f'| {c} | ' + ' | '.join(
                    f"{_val(v[f'pass@{k}'].get('gap_closed'))} {v[f'pass@{k}'].get('ci95') or ''}".strip()
                    for k in ks) + ' |')
        lines += [''] + [f'* {n}' for n in pk.get('notes', [])]
    for level, table in report['summary'].items():
        lines += ['', f'## Final pass rate: {level}', '',
                  '| Condition | Runs | Pass | Pass rate | Public–hidden gap | Recovery | Overflow | '
                  'Frontier $ total | $ per pass | Wall s median (IQR) |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for condition, s in table.items():
            if not s:
                continue
            rec = s['failure_recovery']
            lines.append(
                f"| {condition} | {s['runs']} | {s['passes']} | {_pct(s['pass_rate'])} | {_pct(s['public_hidden_gap'])} "
                f"| {rec['recovered']}/{rec['runs_with_public_failure']} | {s['context_overflow']} "
                f"| {_usd(s['frontier_cost_usd']['total'])} | {_usd(s['frontier_cost_usd']['per_pass'])} "
                f"| {_q(s['wall_seconds'])} |")
    for level, table in report['paired_vs_A'].items():
        lines += ['', f'## Paired vs A: {level}' + (' (primary: C, D, E with Holm)' if level == 'all' else
                                                     ' (exploratory)'), '',
                  '| Condition | Tasks | Pairs | Rate | A rate | Δ | 95% CI | p (perm) | Holm p | McNemar b/c, p (exploratory) |',
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
    table = report['summary'].get('all', {})
    if any(table.values()):
        lines += ['', '## Runtime (all): seconds, median (IQR)', '',
                  '| Condition | Cold-start E2E | Warm-start | Amortized | Upfront authoring | Frontier wait in run | '
                  'Local inference |', '| --- | --- | --- | --- | --- | --- | --- |']
        for c, s in table.items():
            if s:
                lat = s['efficiency']['latency']
                lines.append(f"| {c} | {_q(lat['cold_start_seconds'])} | {_q(lat['warm_start_seconds'])} | "
                             f"{_q(lat['amortized_seconds'])} | {_q(lat['upfront_authoring_seconds'])} | "
                             f"{_q(lat['frontier_wait_seconds_during_run'])} | {_q(lat['local_inference_seconds'])} |")
        rel = report.get('relative_efficiency') or {}
        lines += ['', 'Matched runtime vs A and B (cold-start E2E): median paired ratio X/ref (IQR), reduction = 1 − '
                      'median ratio:', '', '| Condition | vs A ratio | vs A reduction | vs B ratio | vs B reduction |',
                  '| --- | --- | --- | --- | --- |']
        for c, v in rel.items():
            cells = []
            for ref in ('A', 'B'):
                p = ((v.get('runtime') or {}).get(ref) or {}).get('cold_start_seconds')
                cells += [_q(p['ratio'], 2) if p else '–', _val(p['reduction'], '{:+.3f}') if p else '–']
            lines.append(f'| {c} | ' + ' | '.join(cells) + ' |')
        lines += ['', '## Frontier cost, requests and tokens (all; token-derived cost, not invoiced)', '',
                  '| Condition | Total $ | Upfront $ | Run-time $ | $/attempt | $/pass | Cold-start $/attempt (median) | '
                  'Amortized $/attempt (median) | Cost reduction vs B | Extra passes per $ vs A |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for c, s in table.items():
            if s:
                cost, r = s['efficiency']['cost_usd'], rel.get(c) or {}
                lines.append(f"| {c} | {_usd(cost['total'])} | {_usd(cost['upfront'])} | {_usd(cost['runtime'])} | "
                             f"{_usd(cost['per_included_attempt'].get('value'))} | {_usd(cost['per_pass'].get('value'))} | "
                             f"{_usd((cost['cold_start_per_attempt'] or {}).get('median'))} | "
                             f"{_usd((cost['amortized_per_attempt'] or {}).get('median'))} | "
                             f"{_val((r.get('vs_B') or {}).get('cost_reduction'), '{:+.3f}')} | "
                             f"{_val(r.get('additional_passes_per_usd_vs_A'), '{:+.2f}')} |")
        lines += ['', '| Condition | Requests (upfront / run-time) | Failed | Missing usage | Requests/attempt | '
                      'Requests/pass | Input tokens | Cached input | Output (incl. reasoning) | Reasoning | Tokens/pass | '
                      'Token reduction vs B | Local calls | Local in/out tokens |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for c, s in table.items():
            if s:
                e, r = s['efficiency'], rel.get(c) or {}
                q, t, loc = e['requests'], e['tokens'], e['local']
                lines.append(f"| {c} | {q['total']} ({q['upfront']} / {q['runtime']}) | "
                             f"{q['failed_runtime'] + q['failed_upfront']} | {q['missing_usage']} | "
                             f"{_val(q['per_attempt'], '{:.2f}')} | {_val(q['per_pass'], '{:.2f}')} | {t['input']} | "
                             f"{t['cached_input']} | {t['output']} | {t['reasoning']} | {_val(t['per_pass'], '{:.0f}')} | "
                             f"{_val((r.get('vs_B') or {}).get('token_reduction'), '{:+.3f}')} | {loc['calls']} | "
                             f"{loc['prompt_tokens']}/{loc['completion_tokens']} |")
        lines += ['', 'A has zero frontier API spend, not zero computational cost (local inference above). Upfront '
                      'guidance is counted once per artifact, not once per seed.']
    spend = report.get('study_expenditure')
    if spend:
        lines += ['', '## Study expenditure (API ledger)', '',
                  f"Ledger: {spend['ledger']}. Observed frontier models: {spend['observed_models'] or '–'}.", '',
                  '| Requests | Count | States | Token-derived $ (known) | Without usage | Reservation $ |',
                  '| --- | --- | --- | --- | --- | --- |']
        for name in ('all', 'attributable_to_included_runs', 'not_attributable'):
            b = spend[name]
            lines.append(f"| {name} | {b['requests']} | {b['states']} | {_usd(b['token_cost_usd_known'])} | "
                         f"{b['requests_without_usage']} | {b['reservation_usd']} |")
        lines += ['', spend['note']]
    exposure = report.get('exposure') or {}
    if exposure:
        lines += ['', '## Historical exposure subgroups (descriptive)', '',
                  '| Subgroup | Tasks | Condition | Runs | Pass rate | Δ vs A (CI) |', '| --- | --- | --- | --- | --- | --- |']
        for group, g in exposure.items():
            for c, s in g['summary'].items():
                p = (g.get('paired_vs_A') or {}).get(c)
                lines.append(f"| {group} | {g['tasks']} | {c} | {s['runs']} | {_pct(s['pass_rate'])} | "
                             + (f"{p['difference']:+.3f} {p['ci95']}" if p else '–') + ' |')
        lines += ['', '"exposed": the agent ran on the task during development; "potentially_unseen": no recorded '
                      'exposure (not verified unseen).']
    coverage = report.get('hidden_coverage')
    if coverage:
        lines += ['', f"## Hidden-test coverage: {coverage['distribution']} (hidden tests: tasks)", '']
        sens = coverage['sensitivity']
        lines.append(sens['note'] if not sens['applicable'] else
                     f"Sensitivity without the {len(coverage['below_threshold'])} tasks below {coverage['threshold']} "
                     f"hidden tests: " + ', '.join(f"{c} {_pct(v['pass_rate'])}" for c, v in sens['summary'].items()))
    if report.get('e_subset'):
        e = report['e_subset']
        lines += ['', '## E triggered subset (descriptive)', '', f"Trigger rate: {_pct(e['trigger_rate'])}"]
        for key in ('triggered', 'triggered_and_A_failed_public'):
            if e[key]:
                lines.append(f"* {key}: {e[key]['pairs']} pairs, E {_pct(e[key]['E_pass_rate'])} vs "
                             f"A {_pct(e[key]['A_pass_rate'])}")
        lines.append(f"* {e['note']}")
    gaps = {c: g for c, g in (report.get('gap_closed_vs_B') or {}).items() if g}
    if gaps:
        lines += ['', '## Gap closed toward B: (X − A) / (B − A)', '',
                  '| Condition | Tasks | Rate | A rate | B rate | Gap closed | 95% CI | resamples without a gap |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- |']
        for c, g in gaps.items():
            lines.append(f"| {c} | {g['tasks']} | {_pct(g['rate'])} | {_pct(g['base_rate'])} | {_pct(g['ceiling_rate'])} "
                         f"| {'–' if g['gap_closed'] is None else g['gap_closed']} | {g['ci95'] or '–'} "
                         f"| {g['resamples_without_gap']} |")
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
                         f"| {_usd(u['cost_usd']) if u else _usd(0.0)} | "
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
            q = lambda k: s[k]['median'] if s.get(k) else '–'   # noqa: E731
            lines.append(f"| {c} | {s['runs_with_candidate']}/{s['runs']} | {s['runs_with_truncation']} | "
                         f"{q('first_response_tokens')} | {q('local_completion_tokens')} | {q('seconds_to_first_candidate')} |")
    if report.get('process_vs_A'):
        lines += ['', '| Paired vs A | Pairs | Δ local tokens (median) | Δ first response tokens | '
                      'Δ s to first program | program only here / only in A |', '| --- | --- | --- | --- | --- | --- |']
        for c, p in report['process_vs_A'].items():
            if p:
                m = lambda k: f"{p[k]['median']:+} ({p[k]['pairs']})" if p.get(k) else '–'   # noqa: E731
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


def task_rows(report_rows):
    """One row per (task, condition) of included runs: n, c and pass@k, for plots and per-task analysis."""
    groups = defaultdict(list)
    for r in report_rows:
        groups[(r['task_id'], r['condition'])].append(r)
    out = []
    for (task, condition), items in sorted(groups.items()):
        n, c = len(items), sum(r['passed'] for r in items)
        first = items[0]
        out.append({'task_id': task, 'condition': condition, 'difficulty': first['difficulty'],
                    'n_hidden': first.get('n_hidden'), 'exposure': first.get('exposure'),
                    'exposure_subgroup': first.get('exposure_subgroup'), 'attempts': n, 'passes': c,
                    **{f'pass@{k}': passk.pass_at_k(n, c, k) for k in range(1, n + 1)}})
    return out


def write(report, rows, out_dir):
    out_dir = Path(out_dir)
    write_json(out_dir / 'report.json', report)
    (out_dir / 'report.md').write_text(markdown(report), encoding='utf-8', newline='\n')
    fields = sorted({k for r in rows for k in r if not k.startswith('_')})
    with (out_dir / 'runs.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    excluded = {(b['task_id'], b['seed']) for b in report['excluded_blocks']}
    included = [r for r in rows if r['status'] == 'run' and (r['task_id'], r['seed']) not in excluded]
    per_task = task_rows(included)
    if per_task:
        task_fields = sorted({k for r in per_task for k in r}, key=lambda k: (k.startswith('pass@'), k))
        with (out_dir / 'tasks.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=task_fields)
            writer.writeheader()
            writer.writerows(per_task)
