"""Runtime, frontier cost, frontier requests and tokens, and local compute, aggregated over included runs.

Definitions (see evaluation/README.md, "Measurement definitions"):

* **Warm-start latency**: the attempt's own wall time (``time.wall_seconds``: run_attempt, setup included), with any
  reusable guidance already generated. B's API calls and E's diagnosis wait happen inside it and are counted once.
* **Cold-start end-to-end latency**: what solving a *new* problem takes. A, B, E: the warm-start latency. C, D: plus the
  upfront guidance authoring latency of the artifact the attempt used.
* **Amortized latency**: C, D: warm-start latency + authoring latency / number of included attempts sharing the artifact.
* **Relative runtime**: on matched (task, seed) pairs, the median and IQR of the paired difference (X - ref) and of the
  paired ratio (X / ref), ref = A or B, for the same quantity on both sides; reduction = 1 - median ratio.
* **Frontier cost**: token-derived (``evaluation.pricing``): run-time requests (B coder turns, E diagnosis) of included
  runs, plus upfront guidance (C, D) once per artifact (deduplicated by artifact sha256, never per seed). A request
  without usage makes the total unavailable (None) and is counted; it is never treated as zero.
* **Study expenditure**: every ledger request of the batch (failed calls, excluded runs, reruns included), reconciled
  against the requests attributable to included runs.

Undefined ratios (zero or missing denominators) are None with a reason, never 0.
"""
import statistics
from collections import defaultdict

from . import pricing

PRIMARY_LATENCY = 'cold_start_seconds'


def quantiles(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return {'median': round(values[0], 3), 'q1': round(values[0], 3), 'q3': round(values[0], 3), 'n': 1}
    q1, median, q3 = statistics.quantiles(values, n=4, method='inclusive')
    return {'median': round(median, 3), 'q1': round(q1, 3), 'q3': round(q3, 3), 'n': len(values)}


def total(values):
    """Sum, or None when any value is missing (missing is not zero)."""
    values = list(values)
    return None if any(v is None for v in values) else sum(values)


def ratio(numerator, denominator, reason):
    if numerator is None or denominator is None:
        return {'value': None, 'reason': 'missing data'}
    if denominator == 0:
        return {'value': None, 'reason': reason}
    return {'value': round(numerator / denominator, 6)}


# ----------------------------------------------------------------------------- per run
def request_view(request, model=None):
    """One measurement frontier request with its token-derived cost (None when usage or the price is unknown)."""
    provider = request.get('provider') or ''
    api = provider in ('api', 'openai-api')
    cost = pricing.request_cost(request.get('input_tokens'), request.get('output_tokens'),
                                request.get('cached_input_tokens'), model) if api else None
    return {'type': request.get('type'), 'upfront': bool(request.get('upfront')), 'provider': provider,
            'ok': request.get('status') == 'ok', 'input_tokens': request.get('input_tokens'),
            'output_tokens': request.get('output_tokens'), 'cached_input_tokens': request.get('cached_input_tokens'),
            'reasoning_tokens': request.get('reasoning_tokens'), 'latency_seconds': request.get('latency_seconds'),
            'cost_usd': cost, 'recorded_cost_usd': request.get('cost_usd'),
            'usage_known': request.get('input_tokens') is not None and request.get('output_tokens') is not None}


def run_fields(document, model=None):
    """Row fields for one run: latency, run-time frontier usage, the upfront artifact, local compute."""
    requests = [request_view(r, model) for r in (document.get('frontier') or {}).get('requests') or []]
    runtime = [r for r in requests if not r['upfront']]
    upfront = next((r for r in requests if r['upfront']), None)
    inference = document.get('local_inference') or {}
    wall = (document.get('time') or {}).get('wall_seconds')
    authoring = upfront['latency_seconds'] if upfront else 0.0
    sha = (document.get('identity') or {}).get('guidance_artifact_sha256')
    return {
        'warm_start_seconds': wall,
        'cold_start_seconds': None if wall is None or authoring is None else round(wall + authoring, 3),
        'frontier_run_requests': len(runtime), 'frontier_run_failed_requests': sum(not r['ok'] for r in runtime),
        'frontier_run_cost_usd': total(r['cost_usd'] for r in runtime),
        'frontier_run_recorded_cost_usd': total(r['recorded_cost_usd'] for r in runtime),
        'frontier_run_missing_usage': sum(not r['usage_known'] for r in runtime),
        'run_input_tokens': total(r['input_tokens'] for r in runtime),
        'run_output_tokens': total(r['output_tokens'] for r in runtime),
        'run_cached_input_tokens': total(r['cached_input_tokens'] for r in runtime),
        'run_reasoning_tokens': total(r['reasoning_tokens'] for r in runtime),
        'frontier_run_latency_seconds': total(r['latency_seconds'] for r in runtime) if runtime else 0.0,
        'guidance_sha256': sha if upfront else None,
        '_upfront': (upfront | {'sha256': sha}) if upfront else None,
        'local_calls': inference.get('calls'),
        'local_prompt_tokens': inference.get('prompt_tokens'),
        'local_completion_tokens': inference.get('completion_tokens'),
        'local_inference_seconds': (document.get('time') or {}).get('local_inference_seconds'),
    }


# ----------------------------------------------------------------------------- per condition
def artifacts(rows):
    """sha256 -> (upfront request, number of included attempts that used it)."""
    found, uses = {}, defaultdict(int)
    for r in rows:
        upfront = r.get('_upfront')
        if upfront and upfront.get('sha256'):
            found[upfront['sha256']] = upfront
            uses[upfront['sha256']] += 1
    return {sha: (found[sha], uses[sha]) for sha in found}


def amortized(row, shared):
    upfront = row.get('_upfront')
    if not upfront:
        return row.get('warm_start_seconds'), row.get('frontier_run_cost_usd')
    _, uses = shared[upfront['sha256']]
    wall, latency = row.get('warm_start_seconds'), upfront.get('latency_seconds')
    seconds = None if wall is None or latency is None else wall + latency / uses
    run_cost, cost = row.get('frontier_run_cost_usd'), upfront.get('cost_usd')
    usd = None if run_cost is None or cost is None else run_cost + cost / uses
    return seconds, usd


def cold_start_cost(row):
    """Frontier cost of one attempt when its guidance must be generated first (C, D: run-time + artifact)."""
    run, upfront = row.get('frontier_run_cost_usd'), row.get('_upfront')
    if run is None:
        return None
    if not upfront:
        return run
    return None if upfront.get('cost_usd') is None else run + upfront['cost_usd']


def condition(rows, passes):
    """Latency, cost, requests and tokens of one condition's included runs."""
    shared = artifacts(rows)
    upfront = [u for u, _ in shared.values()]
    run_cost = total(r.get('frontier_run_cost_usd') for r in rows)
    upfront_cost = total(u['cost_usd'] for u in upfront) if upfront else 0.0
    cost = None if run_cost is None or upfront_cost is None else run_cost + upfront_cost
    amort = [amortized(r, shared) for r in rows]
    cold_cost = [cold_start_cost(r) for r in rows]
    tokens = {
        'input': total([total(r.get('run_input_tokens') for r in rows)] + [u['input_tokens'] for u in upfront]),
        'output': total([total(r.get('run_output_tokens') for r in rows)] + [u['output_tokens'] for u in upfront]),
        'cached_input': total([total(r.get('run_cached_input_tokens') for r in rows)]
                              + [u['cached_input_tokens'] for u in upfront]),
        'reasoning': total([total(r.get('run_reasoning_tokens') for r in rows)] + [u['reasoning_tokens'] for u in upfront]),
        'upfront_input': total(u['input_tokens'] for u in upfront) if upfront else 0,
        'upfront_output': total(u['output_tokens'] for u in upfront) if upfront else 0,
    }
    tokens['total'] = None if tokens['input'] is None or tokens['output'] is None else tokens['input'] + tokens['output']
    run_requests = sum(r.get('frontier_run_requests') or 0 for r in rows)
    requests = {'runtime': run_requests, 'upfront': len(upfront), 'total': run_requests + len(upfront),
                'failed_runtime': sum(r.get('frontier_run_failed_requests') or 0 for r in rows),
                'failed_upfront': sum(not u['ok'] for u in upfront),
                'missing_usage': sum(r.get('frontier_run_missing_usage') or 0 for r in rows)
                + sum(not u['usage_known'] for u in upfront)}
    requests['successful'] = requests['total'] - requests['failed_runtime'] - requests['failed_upfront']
    n = len(rows)
    return {
        'latency': {'warm_start_seconds': quantiles(r.get('warm_start_seconds') for r in rows),
                    'cold_start_seconds': quantiles(r.get('cold_start_seconds') for r in rows),
                    'amortized_seconds': quantiles(s for s, _ in amort),
                    'upfront_authoring_seconds': quantiles(u['latency_seconds'] for u in upfront) if upfront else None,
                    'frontier_wait_seconds_during_run': quantiles(r.get('frontier_run_latency_seconds') for r in rows),
                    'local_inference_seconds': quantiles(r.get('local_inference_seconds') for r in rows)},
        'cost_usd': {'metric': 'token-derived API cost (provider usage x list price), not invoiced',
                     'runtime': None if run_cost is None else round(run_cost, 6),
                     'upfront': None if upfront_cost is None else round(upfront_cost, 6),
                     'total': None if cost is None else round(cost, 6),
                     'per_included_attempt': ratio(cost, n, 'no included attempts'),
                     'per_pass': ratio(cost, passes, 'no passing attempt'),
                     'cold_start_per_attempt': quantiles(cold_cost),
                     'amortized_per_attempt': quantiles(u for _, u in amort),
                     'recorded_runtime_cache_unaware': total(r.get('frontier_run_recorded_cost_usd') for r in rows),
                     'guidance_artifacts': len(upfront)},
        'requests': requests | {'per_attempt': ratio(requests['total'], n, 'no included attempts'),
                                'per_pass': ratio(requests['total'], passes, 'no passing attempt')},
        'tokens': tokens | {'per_pass': ratio(tokens['total'], passes, 'no passing attempt'),
                            'note': 'output tokens include reasoning tokens (provider usage); reasoning is a breakdown'},
        'local': {'calls': total(r.get('local_calls') for r in rows),
                  'prompt_tokens': total(r.get('local_prompt_tokens') for r in rows),
                  'completion_tokens': total(r.get('local_completion_tokens') for r in rows),
                  'calls_per_attempt': quantiles(r.get('local_calls') for r in rows),
                  'note': 'a condition without frontier spend still uses local compute (A: zero API cost, not zero '
                          'computational cost)'},
    }


def relative(summary, base):
    """Cost and token reductions and extra passes per dollar against a reference condition's summary."""
    def reduction(x, b):
        if x is None or b is None:
            return {'value': None, 'reason': 'missing data'}
        if b == 0:
            return {'value': None, 'reason': 'reference has zero frontier usage'}
        return {'value': round(1 - x / b, 4)}
    return {'cost_reduction': reduction(summary['cost_usd']['total'], base['cost_usd']['total']),
            'token_reduction': reduction(summary['tokens']['total'], base['tokens']['total'])}


def passes_per_dollar(passes, cost, base_passes, base_cost):
    """Additional successful solutions per dollar against A: (passes - A passes) / (cost - A cost)."""
    if cost is None or base_cost is None:
        return {'value': None, 'reason': 'missing data'}
    spent = cost - base_cost
    if spent <= 0:
        return {'value': None, 'reason': 'no additional frontier spend'}
    gain = passes - base_passes
    return {'value': round(gain / spent, 4), 'additional_passes': gain, 'additional_usd': round(spent, 6),
            **({'note': 'negative: fewer passes than A'} if gain < 0 else {})}


def paired_runtime(rows, cond, ref, key=PRIMARY_LATENCY):
    """Matched (task, seed) pairs: median and IQR of X - ref and X / ref for the same latency quantity."""
    by = defaultdict(dict)
    for r in rows:
        by[(r['task_id'], r['seed'])][r['condition']] = r.get(key)
    pairs = [(v[cond], v[ref]) for v in by.values() if v.get(cond) is not None and v.get(ref) is not None]
    if not pairs:
        return None
    ratios = [x / a for x, a in pairs if a > 0]
    median_ratio = statistics.median(ratios) if ratios else None
    return {'quantity': key, 'pairs': len(pairs), 'difference_seconds': quantiles(x - a for x, a in pairs),
            'ratio': quantiles(ratios), 'reduction': None if median_ratio is None else round(1 - median_ratio, 4)}


# ----------------------------------------------------------------------------- ledger
def ledger_report(ledger, purposes, attributed):
    """Actual study expenditure from the ledger, split into requests attributable to included runs and the rest."""
    from guided_agent.providers import PRICE_CONSERVATIVE
    rows = []
    for index, item in enumerate(ledger.get('requests', [])):
        if purposes and item.get('purpose') not in purposes:
            continue
        usage = item.get('usage') or {}
        cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens')
        cost = pricing.request_cost(usage.get('prompt_tokens'), usage.get('completion_tokens'), cached,
                                    item.get('api_model'))
        reserve = (usage['prompt_tokens'] * PRICE_CONSERVATIVE['input'] + usage['completion_tokens']
                   * PRICE_CONSERVATIVE['output']) / 1e6 if usage.get('prompt_tokens') is not None and \
            usage.get('completion_tokens') is not None else item.get('bound_usd_conservative')
        rows.append({'index': index, 'purpose': item.get('purpose'), 'kind': item.get('kind'), 'state': item.get('state'),
                     'cost_usd': cost, 'reservation_usd': reserve, 'observed_model': item.get('observed_model'),
                     'attributed': index in attributed})

    def block(items):
        known = [i['cost_usd'] for i in items if i['cost_usd'] is not None]
        return {'requests': len(items), 'states': dict(sorted(_count(i['state'] for i in items).items())),
                'token_cost_usd_known': round(sum(known), 6), 'requests_without_usage': len(items) - len(known),
                'reservation_usd': round(sum(i['reservation_usd'] or 0 for i in items), 4)}
    by_purpose = defaultdict(list)
    for r in rows:
        by_purpose[r['purpose']].append(r)
    return {'all': block(rows), 'attributable_to_included_runs': block([r for r in rows if r['attributed']]),
            'not_attributable': block([r for r in rows if not r['attributed']]),
            'by_purpose': {p: block(v) for p, v in sorted(by_purpose.items(), key=lambda kv: str(kv[0]))},
            'observed_models': sorted({r['observed_model'] for r in rows if r['observed_model']}),
            'note': 'not_attributable = failed or incomplete calls, excluded or rerun runs, and requests of runs not '
                    'in this report'}


def _count(values):
    out = defaultdict(int)
    for v in values:
        out[str(v)] += 1
    return dict(out)
