"""
LiveEngine — main orchestrator for AlgoTrader India.

Flow every candle interval:
  1. Check market is open (09:15–15:30 IST, Mon–Fri)
  2. Fetch latest OHLCV candles from NSE / yfinance  (no broker account needed)
  3. Run multi-indicator confluence signal engine
  4. If signal changed since last check → send Telegram alert
  5. If auto_trade=True + signal is BUY/SELL → place CE/PE order (paper by default)

Run with:
    python run_live.py --tickers NIFTY BANKNIFTY --interval 15m
"""
import time
import logging
import signal as _signal
import sys
from datetime import datetime

import pytz

from data.live_feed import NSEFeed
from execution.order_manager import OrderManager
from signals.equity_signals import get_latest_signal
from signals.strike_selector import recommend_strike
from options.greeks import black_scholes_greeks
from alerts import telegram_bot
from utils.market_hours import is_market_open, next_candle_wait
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S IST',
)
logger = logging.getLogger(__name__)
IST    = pytz.timezone('Asia/Kolkata')

_INTERVAL_MINUTES = {
    '1m': 1, '3m': 3, '5m': 5, '10m': 10,
    '15m': 15, '30m': 30, '1h': 60, '1d': 1440,
}


class LiveEngine:
    """
    Continuously watches one or more NSE tickers, generates signals using
    the RSI + MACD + Supertrend confluence engine, and optionally places
    CE/PE orders via Angel One SmartAPI.
    """

    def __init__(self, auto_trade: bool = False):
        """
        Args:
            auto_trade : if True, places real/paper orders on every new signal.
                         Defaults to False — signals + Telegram only.
        """
        self.feed         = NSEFeed()
        self.order_mgr    = None
        self.auto_trade   = auto_trade
        self.last_signals = {}          # ticker → last signal label ('BUY'/'SELL'/'WAIT')
        self._running     = True

        # Graceful shutdown on Ctrl-C or SIGTERM
        _signal.signal(_signal.SIGINT,  self._handle_shutdown)
        _signal.signal(_signal.SIGTERM, self._handle_shutdown)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Initialise the NSE feed and order manager."""
        self.order_mgr = OrderManager(self.feed)
        mode = 'PAPER' if settings.PAPER_TRADING else '⚠️  LIVE'
        logger.info(f"LiveEngine started — mode={mode}  auto_trade={self.auto_trade}")
        telegram_bot._send(
            f"🚀 <b>AlgoTrader India started</b>\n"
            f"Mode      : {'PAPER' if settings.PAPER_TRADING else 'LIVE'}\n"
            f"AutoTrade : {self.auto_trade}\n"
            f"Time      : {datetime.now(IST).strftime('%d %b %Y  %H:%M IST')}"
        )

    def run(self, tickers=None, interval: str = '15m',
            iv: float = 0.15, days_to_expiry: int = 7,
            expiry: str = 'weekly'):
        """
        Main loop — runs until market close or KeyboardInterrupt.

        Args:
            tickers        : list of tickers to watch  (default: settings.DEFAULT_TICKER)
            interval       : candle size — '5m' | '15m' | '30m' | '1h' | '1d'
            iv             : implied volatility for Greeks (e.g. 0.15 = 15 %)
            days_to_expiry : DTE passed to Black-Scholes
            expiry         : 'weekly' or 'monthly' for strike recommendation
        """
        self.start()
        tickers          = tickers or [settings.DEFAULT_TICKER]
        interval_minutes = _INTERVAL_MINUTES.get(interval, 15)

        logger.info(f"Watching : {tickers}")
        logger.info(f"Interval : {interval}  ({interval_minutes} min candles)")

        while self._running:
            if not is_market_open():
                logger.info("Market closed — sleeping 5 min…")
                time.sleep(300)
                continue

            for ticker in tickers:
                if not self._running:
                    break
                try:
                    self._process(ticker, interval, iv, days_to_expiry, expiry)
                except Exception as exc:
                    logger.error(f"{ticker} processing error: {exc}")
                    telegram_bot.send_error(f"{ticker}: {exc}")

            wait_sec = next_candle_wait(interval_minutes)
            logger.info(f"Next candle in {wait_sec}s — sleeping…")
            time.sleep(wait_sec)

    # ── Per-ticker processing ─────────────────────────────────────────────────

    def _process(self, ticker: str, interval: str, iv: float,
                 days_to_expiry: int, expiry: str):
        try:
            data = self.feed.get_candles(ticker, interval=interval, days=59)
        except RuntimeError:
            # Intraday fetch failed — fall back to daily candles for signal
            logger.warning(f"  {ticker}: intraday fetch failed, falling back to 1d candles")
            data = self.feed.get_candles(ticker, interval='1d', days=180)
        sig  = get_latest_signal(data)
        spot = float(data['Close'].iloc[-1])

        logger.info(
            f"  {ticker:<12}  {sig['label']:<4}  "
            f"score={sig['score']:+d}/3  "
            f"RSI={sig['rsi']:.1f}  "
            f"spot=₹{spot:,.2f}"
        )

        # Only act when the signal direction changes
        prev_label = self.last_signals.get(ticker)
        if sig['label'] == prev_label:
            return

        self.last_signals[ticker] = sig['label']
        logger.info(f"  ↳ Signal changed: {prev_label} → {sig['label']}")

        rec    = recommend_strike(spot, sig['signal'], symbol=ticker, expiry=expiry)
        greeks = None
        if rec['action'] != 'WAIT':
            greeks = black_scholes_greeks(
                spot           = spot,
                strike         = rec['recommended_strike'],
                days_to_expiry = days_to_expiry,
                volatility     = iv,
                option_type    = rec['option_type'],
            )

        telegram_bot.send_signal(ticker, sig, rec, greeks)

        if self.auto_trade and sig['label'] in ('BUY', 'SELL') and rec['action'] != 'WAIT':
            self.order_mgr.place_options_order(
                ticker      = ticker,
                strike      = rec['recommended_strike'],
                option_type = rec['option_type'],
                expiry      = None,
                transaction = 'BUY',
                lots        = 1,
            )

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received — stopping…")
        self._running = False
        if self.auto_trade and self.order_mgr:
            logger.info("Squaring off all open positions…")
            self.order_mgr.square_off_all()
        telegram_bot._send("🛑 <b>AlgoTrader India stopped</b>")
        sys.exit(0)
