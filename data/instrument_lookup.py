"""
Angel One instrument master lookup.

Downloads the NSE/NFO instruments file from Angel One once every 8 hours
and caches it locally. Used to resolve tickers → tokens and to find
option contract symbols by strike + expiry.
"""
import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

INSTRUMENTS_URL  = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
CACHE_PATH       = os.path.join(os.path.dirname(__file__), '../.instruments_cache.json')
CACHE_TTL_HOURS  = 8

# Pre-defined tokens for major indices — avoids a cache lookup for common symbols
INDEX_TOKENS = {
    'NIFTY':      {'token': '99926000', 'exchange': 'NSE', 'symbol': 'Nifty 50'},
    'BANKNIFTY':  {'token': '99926009', 'exchange': 'NSE', 'symbol': 'Nifty Bank'},
    'FINNIFTY':   {'token': '99926037', 'exchange': 'NSE', 'symbol': 'Nifty Fin Service'},
    'MIDCPNIFTY': {'token': '99926074', 'exchange': 'NSE', 'symbol': 'NIFTY MID SELECT'},
    'SENSEX':     {'token': '1',        'exchange': 'BSE', 'symbol': 'SENSEX'},
}


def _load_instruments() -> pd.DataFrame:
    """Return instruments DataFrame, using the local cache when fresh."""
    if os.path.exists(CACHE_PATH):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(CACHE_PATH))
        if age < timedelta(hours=CACHE_TTL_HOURS):
            with open(CACHE_PATH) as f:
                return pd.DataFrame(json.load(f))

    logger.info("Downloading Angel One instruments master…")
    resp = requests.get(INSTRUMENTS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    with open(CACHE_PATH, 'w') as f:
        json.dump(data, f)
    return pd.DataFrame(data)


def get_equity_token(ticker: str) -> dict:
    """
    Resolve an NSE equity ticker to its Angel One token dict.
    Falls back to the instruments file for stocks not in INDEX_TOKENS.

    Returns:
        {'token': '...', 'exchange': 'NSE', 'symbol': '...'}
    """
    ticker = ticker.upper()
    if ticker in INDEX_TOKENS:
        return INDEX_TOKENS[ticker]

    df  = _load_instruments()
    # NSE equity rows typically have symbol like 'RELIANCE-EQ'
    row = df[
        (df['exch_seg'] == 'NSE') &
        (df['symbol'].str.upper().isin([ticker, ticker + '-EQ']))
    ]
    if row.empty:
        raise ValueError(f"Ticker '{ticker}' not found in instruments master.")
    row = row.iloc[0]
    return {'token': str(row['token']), 'exchange': 'NSE', 'symbol': row['name']}


def find_option(underlying: str, strike: int, option_type: str,
                expiry_date: str = None) -> dict:
    """
    Find the Angel One trading symbol and token for an NSE F&O option.

    Args:
        underlying  : 'NIFTY', 'BANKNIFTY', 'RELIANCE', etc.
        strike      : strike price as integer (e.g. 22500)
        option_type : 'CE' or 'PE'
        expiry_date : 'YYYY-MM-DD' for a specific expiry,
                      or None to use the nearest available expiry.

    Returns:
        {tradingsymbol, symboltoken, expiry (YYYY-MM-DD), lot_size}
    """
    df         = _load_instruments()
    underlying = underlying.upper()

    mask = (
        (df['exch_seg'] == 'NFO') &
        (df['name'].str.upper() == underlying) &
        (df['symbol'].str.upper().str.endswith(option_type))
    )
    options = df[mask].copy()
    if options.empty:
        raise ValueError(f"No NFO options found for {underlying} {option_type}")

    # Normalise strike — Angel One stores it as a float string (e.g. '22500.0')
    options['strike_f'] = pd.to_numeric(options['strike'], errors='coerce')
    options = options[options['strike_f'] == float(strike)]
    if options.empty:
        raise ValueError(f"No {underlying} {strike} {option_type} found in instruments")

    options['expiry_dt'] = pd.to_datetime(options['expiry'], format='%d%b%Y', errors='coerce')
    options = options[options['expiry_dt'] >= pd.Timestamp.today().normalize()]
    options = options.sort_values('expiry_dt')

    if expiry_date:
        target  = pd.Timestamp(expiry_date)
        options = options[options['expiry_dt'] == target]
        if options.empty:
            raise ValueError(f"No {underlying} {strike} {option_type} expiring {expiry_date}")

    row = options.iloc[0]
    return {
        'tradingsymbol': str(row['symbol']),
        'symboltoken':   str(row['token']),
        'expiry':        row['expiry_dt'].strftime('%Y-%m-%d'),
        'lot_size':      int(row.get('lotsize', 1)),
    }
