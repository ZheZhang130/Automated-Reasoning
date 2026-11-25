"""API budget preflight: how many paid requests a plan needs and what the ledger will reserve for them.

Nothing here sends a request. ``assess`` combines the plan (what remains to run), the study ledger (what was already
spent and which ceilings apply) and request-size assumptions measured in the four development ledgers (42 completed
direct-API requests, passes 1-4). It reports three scenarios:

* ``expected``: historical means (B ~3.2 requests per run; E triggers in half of its runs; mean request sizes);
* ``high``: high request counts (B 7 requests per run, the historical maximum; every E run triggers) at mean sizes;
* ``stress``: the same high counts with every request at the largest size observed;
* ``worst``: the code limits (B ``max_requests`` per run, every request at the 8,000-token output cap).

Two dollar figures are given for each, because the ledger and the research report price requests differently:

* ``reservation_usd``: the ledger's own accounting (``guided_agent.providers.PRICE_CONSERVATIVE``, $12 / $60 per 1M,
  cached input not discounted). The ceiling ``max_usd`` is checked against *this* number, so it decides whether the
  study can finish;
* ``token_cost_usd``: the token-derived research cost at Standard list prices with cached input
  (``evaluation.pricing``), which is what the provider is expected to bill. It is an estimate, not a guarantee.

No scenario guarantees completion: requests per B run and E's trigger rate are outcomes of the experiment.
"""
import math
from pathlib import Path

from . import pricing
from .plan import read_json

# Per request, from the development ledgers: mean and max (input tokens, output tokens incl. reasoning, cached input).
HISTORY = {
    'plan': {'n': 7, 'input': (801, 1069), 'output': (975, 1497), 'cached': 0},
    'contract': {'n': 9, 'input': (843, 1267), 'output': (581, 877), 'cached': 0},
    'diagnosis': {'n': 6, 'input': (1670, 1994), 'output': (278, 305), 'cached': 0},
    'coder': {'n': 20, 'input': (1837, 4265), 'output': (453, 3553), 'cached': 1241},
}
B_REQUESTS_PER_RUN = {'expected': 3.24, 'high': 7}     # 21 historical B runs: 19 used 3, max 7
E_TRIGGER_RATE = {'expected': 0.5, 'high': 1.0}        # at most one diagnosis per E run
MAX_COMPLETION_TOKENS = 8000
WORST_INPUT_TOKENS = {'plan': 2000, 'contract': 2000, 'diagnosis': 4000, 'coder': 30000}


def _remaining(plan, batch_dir):
    from guided_agent.integrity import run_name
    done = set()
    if batch_dir and Path(batch_dir).is_dir():
        done = {a['task_id'] + a['condition'] + str(a.get('seed')) for a in plan['attempts']
                if (Path(batch_dir) / run_name(a) / 'result.json').exists()}
    return [a for a in plan['attempts'] if a['task_id'] + a['condition'] + str(a.get('seed')) not in done]


def _cost(kind, n, scenario, conservative):
    from guided_agent.providers import PRICE_CONSERVATIVE
    h = HISTORY[kind]
    if scenario == 'worst':
        tokens_in, tokens_out, cached = WORST_INPUT_TOKENS[kind], MAX_COMPLETION_TOKENS, 0
    else:
        i = 1 if scenario == 'stress' else 0
        tokens_in, tokens_out, cached = h['input'][i], h['output'][i], 0 if scenario == 'stress' else h['cached']
    if conservative:
        return n * (tokens_in * PRICE_CONSERVATIVE['input'] + tokens_out * PRICE_CONSERVATIVE['output']) / 1e6
    return n * pricing.request_cost(tokens_in, tokens_out, cached)


def assess(plan_path, study=None, ledger=None, missing_guidance=None):
    """Request and dollar estimates for what the plan still has to do, against the ledger's remaining room."""
    from guided_agent import providers
    plan = read_json(plan_path)
    batch_dir = Path(study) / 'runs' / plan['batch'] if study else None
    remaining = _remaining(plan, batch_dir)
    b_runs = [a for a in remaining if a['condition'] == 'B' and (a.get('coder') or {}).get('provider') == 'api']
    e_runs = [a for a in remaining if a['condition'] == 'E' and (a.get('diagnosis') or {}).get('provider') == 'api']
    if missing_guidance is None:
        missing_guidance = {'C': len({a['guidance'] for a in plan['attempts'] if a['condition'] == 'C'
                                      and not Path(a['guidance']).is_file()}),
                            'D': len({a['guidance'] for a in plan['attempts'] if a['condition'] == 'D'
                                      and not Path(a['guidance']).is_file()})}
    b_cap = max([int((a.get('coder') or {}).get('max_requests', 28)) for a in b_runs] or [28])
    scenarios = {}
    for name in ('expected', 'high', 'stress', 'worst'):
        level = 'expected' if name == 'expected' else 'high'
        per_b = b_cap if name == 'worst' else B_REQUESTS_PER_RUN[level]
        e_rate = 1.0 if name == 'worst' else E_TRIGGER_RATE[level]
        counts = {'plan': missing_guidance.get('C', 0), 'contract': missing_guidance.get('D', 0),
                  'coder': math.ceil(len(b_runs) * per_b), 'diagnosis': math.ceil(len(e_runs) * e_rate)}
        scenarios[name] = {
            'requests': counts | {'total': sum(counts.values())},
            'reservation_usd': round(sum(_cost(k, n, name, True) for k, n in counts.items()), 2),
            'token_cost_usd': round(sum(_cost(k, n, name, False) for k, n in counts.items()), 2)}
    data = read_json(ledger) if ledger and Path(ledger).exists() else None
    ceilings = {'max_requests': min((data or {}).get('max_requests', providers.MAX_REQUESTS), providers.MAX_REQUESTS),
                'max_usd': min((data or {}).get('max_usd', providers.MAX_USD), providers.MAX_USD)}
    used = {'requests': 0, 'reservation_usd': 0.0}
    if data is not None:
        ledger_obj = providers.Ledger.__new__(providers.Ledger)
        ledger_obj.data = data
        used = {'requests': len(data['requests']), 'reservation_usd': round(ledger_obj.spent_conservative(), 2)}
    room = {'requests': ceilings['max_requests'] - used['requests'],
            'reservation_usd': round(ceilings['max_usd'] - used['reservation_usd'], 2)}
    headroom = round((WORST_INPUT_TOKENS['coder'] * providers.PRICE_CONSERVATIVE['input']
                      + MAX_COMPLETION_TOKENS * providers.PRICE_CONSERVATIVE['output']) / 1e6, 2)
    fits = {name: s['requests']['total'] <= room['requests'] and s['reservation_usd'] + headroom <= room['reservation_usd']
            for name, s in scenarios.items()}
    return {
        'plan': str(plan_path), 'remaining_attempts': len(remaining),
        'paid_runs_remaining': {'B': len(b_runs), 'E': len(e_runs)}, 'missing_guidance': missing_guidance,
        'ledger': str(ledger) if ledger else None, 'ledger_exists': data is not None,
        'ceilings': ceilings | {'code_maximum': {'max_requests': providers.MAX_REQUESTS, 'max_usd': providers.MAX_USD}},
        'used': used, 'room': room, 'scenarios': scenarios,
        'single_request_reservation_usd_max': headroom, 'fits_within_ceilings': fits,
        'assumptions': {
            'history': HISTORY, 'b_requests_per_run': B_REQUESTS_PER_RUN | {'worst': b_cap},
            'e_trigger_rate': E_TRIGGER_RATE | {'worst': 1.0},
            'reservation_prices_per_1m': providers.PRICE_CONSERVATIVE,
            'research_prices_per_1m': pricing.price(),
            'note': 'estimates only: requests per B run and E trigger rate are experimental outcomes; the ledger '
                    'refuses (never exceeds) a request that would pass a ceiling, and that run is then an '
                    'infrastructure failure to rerun after the ceiling is raised'},
    }


def init_ledger(path, max_requests, max_usd):
    """Create a fresh study ledger with ceilings at or below the code maximum (a ledger can lower, never raise)."""
    from guided_agent import providers
    path = Path(path)
    if path.exists():
        raise FileExistsError(f'{path} exists; ceilings are fixed when a ledger is created (use a new ledger)')
    if max_requests > providers.MAX_REQUESTS or max_usd > providers.MAX_USD:
        raise ValueError(f'the code maximum is {providers.MAX_REQUESTS} requests / ${providers.MAX_USD}; '
                         'raising it is a reviewed code change in guided_agent/providers.py')
    if max_requests <= 0 or max_usd <= 0:
        raise ValueError('ceilings must be positive')
    from guided_agent.common import write_json
    data = {'max_requests': int(max_requests), 'max_usd': float(max_usd),
            'price_standard_per_1m': providers.PRICE_STANDARD, 'price_conservative_per_1m': providers.PRICE_CONSERVATIVE,
            'requests': [], 'metadata_calls': []}
    write_json(path, data)
    return data
