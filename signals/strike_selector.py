# Strike intervals (points) for major NSE instruments
STRIKE_INTERVALS = {
    'NIFTY':      50,
    'BANKNIFTY':  100,
    'FINNIFTY':   50,
    'MIDCPNIFTY': 25,
    'default':    50,
}

# NSE F&O lot sizes (update periodically as SEBI revises them)
LOT_SIZES = {
    'NIFTY':      75,
    'BANKNIFTY':  15,
    'FINNIFTY':   40,
    'MIDCPNIFTY': 75,
    'default':    1,
}


def _interval(symbol):
    return STRIKE_INTERVALS.get(symbol.upper(), STRIKE_INTERVALS['default'])


def _lot_size(symbol):
    return LOT_SIZES.get(symbol.upper(), LOT_SIZES['default'])


def get_atm_strike(spot_price, symbol='NIFTY'):
    interval = _interval(symbol)
    return round(spot_price / interval) * interval


def recommend_strike(spot_price, signal, symbol='NIFTY', expiry='weekly'):
    """
    Recommend an options trade based on the equity signal.

    Args:
        spot_price : current spot / LTP of the underlying
        signal     : 1 (bullish), -1 (bearish), 0 (neutral)
        symbol     : instrument name e.g. 'NIFTY', 'RELIANCE'
        expiry     : 'weekly' or 'monthly'

    Returns:
        dict with option_type, atm_strike, recommended_strike,
        lot_size, expiry, action, reasoning
    """
    interval = _interval(symbol)
    atm      = get_atm_strike(spot_price, symbol)
    lot      = _lot_size(symbol)

    if signal == 1:
        rec_strike  = atm + interval           # 1 OTM call for leverage
        option_type = 'CE'
        action      = 'BUY'
        reasoning   = (
            f"Bullish consensus signal.  "
            f"Buy {symbol} {rec_strike} CE ({expiry} expiry). "
            f"1 strike OTM gives leveraged upside with capped risk."
        )
    elif signal == -1:
        rec_strike  = atm - interval           # 1 OTM put for leverage
        option_type = 'PE'
        action      = 'BUY'
        reasoning   = (
            f"Bearish consensus signal.  "
            f"Buy {symbol} {rec_strike} PE ({expiry} expiry). "
            f"1 strike OTM gives leveraged downside with capped risk."
        )
    else:
        return {
            'option_type':        None,
            'atm_strike':         atm,
            'recommended_strike': None,
            'lot_size':           lot,
            'expiry':             None,
            'action':             'WAIT',
            'reasoning':          'No clear directional consensus. Stay on the sidelines.',
        }

    return {
        'option_type':        option_type,
        'atm_strike':         atm,
        'recommended_strike': rec_strike,
        'lot_size':           lot,
        'expiry':             expiry,
        'action':             action,
        'reasoning':          reasoning,
    }
