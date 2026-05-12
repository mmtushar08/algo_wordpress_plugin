"""
Order manager for AlgoTrader India.

Paper trading works out of the box — no broker account needed.

For live order placement, plug in any Indian broker SDK:
  • Zerodha  → pip install kiteconnect  (₹2,000/mo API fee)
  • Upstox   → pip install upstox-python-sdk  (free with Upstox account)
  • Fyers    → pip install fyers-apiv3  (free with Fyers account)
  • ICICI    → pip install breeze-connect  (free with ICICI Direct account)

Set PAPER_TRADING=false in .env only after verifying signals for several
days in paper mode.
"""
import logging
from signals.strike_selector import LOT_SIZES
from config import settings
from alerts import telegram_bot

logger = logging.getLogger(__name__)


class OrderManager:

    def __init__(self, nse_feed):
        """
        Args:
            nse_feed : NSEFeed instance (used for LTP-based cost estimation)
        """
        self.feed          = nse_feed
        self.paper_mode    = settings.PAPER_TRADING
        self.daily_pnl     = 0.0
        self._paper_orders = []

    # ── Risk guards ───────────────────────────────────────────────────────────

    def _check_risk(self, estimated_cost: float):
        if (-self.daily_pnl) >= settings.MAX_DAILY_LOSS:
            raise RuntimeError(
                f"Daily loss limit reached: ₹{-self.daily_pnl:,.0f} "
                f"≥ ₹{settings.MAX_DAILY_LOSS:,.0f}. No more trades today."
            )
        if estimated_cost > settings.MAX_POSITION_SIZE:
            raise RuntimeError(
                f"Trade cost ₹{estimated_cost:,.0f} exceeds "
                f"max position size ₹{settings.MAX_POSITION_SIZE:,.0f}."
            )

    # ── Order placement ───────────────────────────────────────────────────────

    def place_options_order(self, ticker: str, strike: int, option_type: str,
                            expiry: str = None, transaction: str = 'BUY',
                            lots: int = 1) -> str:
        """
        Place (or simulate) a CE/PE options order.

        Args:
            ticker      : underlying — 'NIFTY', 'BANKNIFTY', 'RELIANCE', …
            strike      : strike price (e.g. 24500)
            option_type : 'CE' or 'PE'
            expiry      : descriptive string for logging (e.g. '29-May-2025')
            transaction : 'BUY' or 'SELL'
            lots        : number of lots (1 lot = 1 × lot_size)

        Returns:
            order_id string ('PAPER-XXXX' in paper mode)
        """
        lot_size  = LOT_SIZES.get(ticker.upper(), LOT_SIZES['default'])
        quantity  = lot_size * lots
        symbol    = f"{ticker.upper()}{strike}{option_type}"

        # Estimate cost: option premium ≈ 1–3% of spot × quantity
        try:
            spot           = self.feed.get_ltp(ticker)
            premium_est    = spot * 0.015          # rough 1.5% of spot
            estimated_cost = premium_est * quantity
        except Exception:
            estimated_cost = 0.0                   # skip cost check if LTP fails

        self._check_risk(estimated_cost)

        order_record = {
            'tradingsymbol':   symbol,
            'transactiontype': transaction,
            'quantity':        quantity,
            'strike':          strike,
            'option_type':     option_type,
            'expiry':          expiry or 'nearest',
        }

        if self.paper_mode:
            order_id = f"PAPER-{len(self._paper_orders) + 1:04d}"
            self._paper_orders.append({'order_id': order_id, **order_record})
            logger.info(
                f"[PAPER] {transaction} {quantity}× {symbol}  →  {order_id}"
            )
        else:
            # ── Live broker integration ──────────────────────────────────────
            # Replace this block with your broker's SDK call, e.g.:
            #
            #   from kiteconnect import KiteConnect
            #   kite = KiteConnect(api_key=settings.BROKER_API_KEY)
            #   kite.set_access_token(settings.BROKER_ACCESS_TOKEN)
            #   resp     = kite.place_order(...)
            #   order_id = resp['order_id']
            #
            raise NotImplementedError(
                "Live order placement requires a broker SDK.\n"
                "Options: Zerodha Kite, Upstox, Fyers, ICICI Breeze.\n"
                "Set PAPER_TRADING=true in .env to use paper mode."
            )

        telegram_bot.send_order_placed(ticker, order_id, order_record)
        return order_id

    # ── Position management ───────────────────────────────────────────────────

    def get_positions(self) -> list:
        """Return open positions (paper log in paper mode)."""
        return self._paper_orders if self.paper_mode else []

    def square_off_all(self):
        """Clear all paper positions (live square-off requires broker SDK)."""
        count = len(self._paper_orders)
        self._paper_orders.clear()
        self.daily_pnl = 0.0
        logger.info(f"[PAPER] Squared off {count} position(s)")
