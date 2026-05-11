import math

# RBI repo rate as of 2025 — update as needed
DEFAULT_RISK_FREE_RATE = 0.065


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes_greeks(spot, strike, days_to_expiry, volatility,
                         option_type='CE',
                         risk_free_rate=DEFAULT_RISK_FREE_RATE):
    """
    Black-Scholes theoretical price and Greeks for a European option.

    Args:
        spot            : current spot / underlying price (e.g. 22500)
        strike          : option strike price (e.g. 22550)
        days_to_expiry  : calendar days until expiry (e.g. 7)
        volatility      : implied volatility as decimal (e.g. 0.15 for 15%)
        option_type     : 'CE' for call, 'PE' for put
        risk_free_rate  : annualised risk-free rate (default 6.5% RBI rate)

    Returns:
        dict: price, delta, gamma, theta (per day), vega (per 1% IV move)
    """
    if days_to_expiry <= 0 or volatility <= 0:
        return {'price': 0.0, 'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}

    T  = days_to_expiry / 365.0
    sq = math.sqrt(T)

    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * T) / (volatility * sq)
    d2 = d1 - volatility * sq

    pdf_d1 = _norm_pdf(d1)
    disc   = math.exp(-risk_free_rate * T)

    if option_type == 'CE':
        price = spot * _norm_cdf(d1)  - strike * disc * _norm_cdf(d2)
        delta = _norm_cdf(d1)
        theta = (
            -(spot * pdf_d1 * volatility) / (2 * sq)
            - risk_free_rate * strike * disc * _norm_cdf(d2)
        ) / 365
    else:  # PE
        price = strike * disc * _norm_cdf(-d2) - spot * _norm_cdf(-d1)
        delta = _norm_cdf(d1) - 1
        theta = (
            -(spot * pdf_d1 * volatility) / (2 * sq)
            + risk_free_rate * strike * disc * _norm_cdf(-d2)
        ) / 365

    gamma = pdf_d1 / (spot * volatility * sq)
    vega  = spot * pdf_d1 * sq / 100   # per 1% change in IV

    return {
        'price': round(max(price, 0.0), 2),
        'delta': round(delta,           4),
        'gamma': round(gamma,           6),
        'theta': round(theta,           2),
        'vega':  round(vega,            2),
    }
