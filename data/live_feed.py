"""
Angel One SmartAPI live data feed.

Provides authenticated candle data and LTP for NSE/BSE instruments.
Uses REST polling (getCandleData) which works on any plan; WebSocket
streaming can be layered on top using SmartWebSocketV2 if needed.
"""
import logging
import pandas as pd
import pyotp
from datetime import datetime, timedelta

from SmartApi import SmartConnect

from config import settings
from data.instrument_lookup import INDEX_TOKENS, get_equity_token

logger = logging.getLogger(__name__)

# Map our short interval strings → Angel One API interval names
INTERVAL_MAP = {
    '1m':  'ONE_MINUTE',
    '3m':  'THREE_MINUTE',
    '5m':  'FIVE_MINUTE',
    '10m': 'TEN_MINUTE',
    '15m': 'FIFTEEN_MINUTE',
    '30m': 'THIRTY_MINUTE',
    '1h':  'ONE_HOUR',
    '1d':  'ONE_DAY',
}


class AngelOneFeed:
    """Thin wrapper around SmartConnect for data fetching."""

    def __init__(self):
        self.obj       = None   # SmartConnect instance
        self.auth_data = None

    # ── Authentication ────────────────────────────────────────────────────────

    def authenticate(self):
        """
        Login to Angel One using API key + client credentials + TOTP.
        TOTP is generated automatically from the TOTP secret in settings.
        """
        totp = pyotp.TOTP(settings.ANGEL_TOTP_TOKEN).now()
        self.obj = SmartConnect(api_key=settings.ANGEL_API_KEY)

        self.auth_data = self.obj.generateSession(
            settings.ANGEL_CLIENT_ID,
            settings.ANGEL_PASSWORD,
            totp,
        )
        if not self.auth_data.get('status'):
            raise ConnectionError(
                f"Angel One authentication failed: {self.auth_data.get('message')}"
            )
        logger.info("Angel One authenticated successfully")
        return self.auth_data

    def _ensure_auth(self):
        if self.obj is None:
            self.authenticate()

    # ── Market data ───────────────────────────────────────────────────────────

    def get_candles(self, ticker: str, interval: str = '15m', days: int = 60) -> pd.DataFrame:
        """
        Fetch OHLCV candles for an NSE equity, index, or F&O contract.

        Args:
            ticker   : 'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', etc.
            interval : '1m' | '5m' | '15m' | '30m' | '1h' | '1d'
            days     : how many calendar days of history to request

        Returns:
            DataFrame indexed by datetime with columns Open/High/Low/Close/Volume
        """
        self._ensure_auth()
        ticker     = ticker.upper()
        instrument = INDEX_TOKENS.get(ticker) or get_equity_token(ticker)

        to_dt   = datetime.now()
        from_dt = to_dt - timedelta(days=days)

        params = {
            'exchange':    instrument['exchange'],
            'symboltoken': instrument['token'],
            'interval':    INTERVAL_MAP.get(interval, 'ONE_DAY'),
            'fromdate':    from_dt.strftime('%Y-%m-%d %H:%M'),
            'todate':      to_dt.strftime('%Y-%m-%d %H:%M'),
        }

        resp = self.obj.getCandleData(params)
        if not resp.get('status'):
            raise RuntimeError(f"getCandleData error: {resp.get('message')}")

        raw = resp['data']
        if not raw:
            raise RuntimeError(f"No candle data returned for {ticker}")

        df = pd.DataFrame(raw, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
        return df.astype(float)

    def get_ltp(self, ticker: str) -> float:
        """Return the last traded price for a ticker."""
        self._ensure_auth()
        ticker     = ticker.upper()
        instrument = INDEX_TOKENS.get(ticker) or get_equity_token(ticker)

        resp = self.obj.ltpData(
            instrument['exchange'],
            instrument['symbol'],
            instrument['token'],
        )
        if not resp.get('status'):
            raise RuntimeError(f"ltpData error for {ticker}: {resp.get('message')}")
        return float(resp['data']['ltp'])
