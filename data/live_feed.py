"""
NSE India live data feed — no broker account or demat required.

Live LTP + options chain  →  NSE India web API  (free, no login)
Historical OHLCV candles  →  yfinance            (free, no login)

Usage:
    feed = NSEFeed()
    ltp  = feed.get_ltp('NIFTY')          # live last traded price
    data = feed.get_candles('NIFTY', '1d', days=90)   # OHLCV DataFrame
    oc   = feed.get_option_chain('NIFTY') # full options chain dict
"""
import time
import logging

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# yfinance symbols for major NSE instruments
YF_SYMBOLS = {
    'NIFTY':      '^NSEI',
    'BANKNIFTY':  '^NSEBANK',
    'FINNIFTY':   'NIFTY_FIN_SERVICE.NS',
    'MIDCPNIFTY': '^NSEMDCP50',
    'SENSEX':     '^BSESN',
}

# Display names used by NSE allIndices API
NSE_INDEX_NAMES = {
    'NIFTY':      'NIFTY 50',
    'BANKNIFTY':  'NIFTY BANK',
    'FINNIFTY':   'NIFTY FIN SERVICE',
    'MIDCPNIFTY': 'NIFTY MIDCAP SELECT',
}

NSE_BASE = 'https://www.nseindia.com'
NSE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept':          'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer':         'https://www.nseindia.com/',
    'Connection':      'keep-alive',
}


class NSEFeed:
    """
    Live NSE data feed — no broker account or demat required.

    Live prices and options chain come from NSE's web API.
    Historical OHLCV candles are fetched via yfinance.
    """

    def __init__(self):
        self.session       = requests.Session()
        self.session.headers.update(NSE_HEADERS)
        self._ready        = False

    # ── Session management ────────────────────────────────────────────────────

    def _init_session(self):
        """Visit NSE homepage once to collect cookies needed for API calls."""
        if self._ready:
            return
        try:
            self.session.get(NSE_BASE, timeout=10)
            time.sleep(0.5)
            self._ready = True
            logger.info('NSE session ready')
        except Exception as exc:
            logger.warning(f'NSE session init warning: {exc}')

    # ── Live price ────────────────────────────────────────────────────────────

    def get_ltp(self, ticker: str) -> float:
        """
        Last traded price for a major NSE index or any equity.

        Args:
            ticker : 'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', …

        Returns:
            LTP as float (INR)
        """
        self._init_session()
        ticker = ticker.upper()
        return (
            self._index_ltp(ticker)
            if ticker in NSE_INDEX_NAMES
            else self._equity_ltp(ticker)
        )

    def _index_ltp(self, ticker: str) -> float:
        resp = self.session.get(f'{NSE_BASE}/api/allIndices', timeout=10)
        resp.raise_for_status()
        name = NSE_INDEX_NAMES[ticker]
        for item in resp.json()['data']:
            if item['index'] == name:
                return float(item['last'])
        raise ValueError(f"Index '{ticker}' not found in NSE response")

    def _equity_ltp(self, ticker: str) -> float:
        resp = self.session.get(
            f'{NSE_BASE}/api/quote-equity?symbol={ticker}', timeout=10
        )
        resp.raise_for_status()
        return float(resp.json()['priceInfo']['lastPrice'])

    # ── Historical candles ────────────────────────────────────────────────────

    def get_candles(self, ticker: str, interval: str = '1d',
                    days: int = 90) -> pd.DataFrame:
        """
        OHLCV candles via yfinance — works for both indices and equities.

        Args:
            ticker   : 'NIFTY', 'BANKNIFTY', 'RELIANCE', etc.
            interval : '1d' | '1h' | '15m' | '5m'
            days     : calendar days of history to fetch

        Returns:
            DataFrame with Open / High / Low / Close / Volume columns
        """
        ticker = ticker.upper()
        symbol = YF_SYMBOLS.get(ticker, ticker + '.NS')

        to_dt   = datetime.now()
        from_dt = to_dt - timedelta(days=days)

        raw = yf.download(
            symbol,
            start    = from_dt.strftime('%Y-%m-%d'),
            end      = to_dt.strftime('%Y-%m-%d'),
            interval = interval,
            progress = False,
            auto_adjust = True,
        )
        if raw.empty:
            raise RuntimeError(
                f"No data for '{ticker}' ({symbol}). "
                "Check internet connection and ticker symbol."
            )
        # Flatten MultiIndex produced by newer yfinance versions
        if hasattr(raw.columns, 'levels'):
            raw.columns = raw.columns.get_level_values(0)

        return raw[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

    # ── Options chain ─────────────────────────────────────────────────────────

    def get_option_chain(self, symbol: str = 'NIFTY') -> dict:
        """
        Full live options chain from NSE (OI, IV, bid/ask, LTP per strike).

        Args:
            symbol : 'NIFTY', 'BANKNIFTY', 'FINNIFTY', or any F&O equity

        Returns:
            NSE 'records' dict — keys: data (list of strikes), expiryDates,
            strikePrices, underlyingValue, timestamp
        """
        self._init_session()
        symbol = symbol.upper()
        base   = 'option-chain-indices' if symbol in NSE_INDEX_NAMES else 'option-chain-equities'
        resp   = self.session.get(
            f'{NSE_BASE}/api/{base}?symbol={symbol}', timeout=15
        )
        resp.raise_for_status()
        return resp.json()['records']
