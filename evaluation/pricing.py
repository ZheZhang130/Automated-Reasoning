"""Frontier API prices used for the reported research cost (not for the budget reservation).

The reported cost is **token-derived**: provider-reported usage multiplied by the list prices below. It is not an
invoice. Exact billing can differ (account tier, promotions, regional uplift, rounding), so the report labels it
"token-derived API cost".

Two prices exist in the code base and must not be confused:

* ``guided_agent.providers.PRICE_STANDARD`` ($2 / $10 per 1M input / output, no cached-input rate) is what the agent
  writes into the ledger and the measurement records (``cost_usd``). It charges cached input at the full input rate.
* ``guided_agent.providers.PRICE_CONSERVATIVE`` ($12 / $60) only sizes the ledger's write-ahead spending reservation.
  It is a safety bound (the highest tier on the pricing page), never a research cost.

``cost_usd`` here is cache-aware: ``(input - cached) * input + cached * cached_input + output * output``. OpenAI's
usage object already counts reasoning tokens inside ``completion_tokens`` (``completion_tokens_details`` is a
breakdown), so reasoning tokens are never added a second time.
"""

# USD per 1M tokens. Read from https://developers.openai.com/api/docs/pricing on 2026-11-24 (Standard tab,
# short context <= 272K input tokens). Requests in this study never send a service_tier, so Standard applies, and
# no request comes near 272K input tokens.
PRICES = {
    'gpt-6.2-sol': {'input': 2.00, 'cached_input': 0.10, 'output': 10.00, 'tier': 'standard',
                    'context': 'short (<= 272K input tokens)', 'verified_utc': '2026-11-24',
                    'source': 'https://developers.openai.com/api/docs/pricing'},
}
DEFAULT_MODEL = 'gpt-6.2-sol'


def price(model=None):
    key = (model or DEFAULT_MODEL).split('/', 1)[-1]
    for name, value in PRICES.items():
        if key == name or key.startswith(name + '-'):  # dated snapshots such as gpt-6.2-sol-2026-10-01
            return value
    return None


def request_cost(input_tokens, output_tokens, cached_input_tokens=None, model=None):
    """Cache-aware USD for one request, or None when usage is missing (missing is never zero)."""
    rates = price(model)
    if rates is None or input_tokens is None or output_tokens is None:
        return None
    cached = cached_input_tokens or 0
    cached = min(cached, input_tokens)
    return ((input_tokens - cached) * rates['input'] + cached * rates['cached_input']
            + output_tokens * rates['output']) / 1e6


def cache_unaware_cost(input_tokens, output_tokens, model=None):
    """The agent-side formula (PRICE_STANDARD without a cached-input rate), for reconciliation only."""
    rates = price(model)
    if rates is None or input_tokens is None or output_tokens is None:
        return None
    return (input_tokens * rates['input'] + output_tokens * rates['output']) / 1e6


def assumptions(model=None):
    rates = price(model)
    return {'model': model or DEFAULT_MODEL, 'usd_per_1m_tokens': rates,
            'metric': 'token-derived API cost (provider usage x list price), not invoiced expenditure',
            'reasoning_tokens': 'included in completion/output tokens by the provider; not added again',
            'cached_input': 'priced at the cached-input rate when the provider reports cached tokens'}
