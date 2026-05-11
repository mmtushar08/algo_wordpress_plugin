"""
Order manager for AlgoTrader India.

Wraps Angel One order placement with:
  - Paper trading mode (default ON — no real money until you flip PAPER_TRADING=false)
  - Daily loss limit guard
  - Per-trade position size cap
  - Telegram confirmation on every order

Always start with PAPER_TRADING=true in .env and verify signals for several
days before switching to live mode.
"""
import logging
from data.instrument_lookup import find_option
from config import settings
from alerts import telegram_bot

logger = logging.getLogger(__name__)


class OrderManager:

    def __init__(self, angel_feed):
        """
        Args:
            angel_feed : authenticated AngelOneFeed instance
        """
        self.feed       = angel_feed
        self.paper_mode = settings.PAPER_TRADING
        self.daily_pnl  = 0.0          # running P&L for today (losses are negative)
        self._paper_orders = []        # in-memory log for paper trades

    # ── Risk guards ───────────────────────────────────────────────────────────

    def _check_risk(self, estimated_cost: float):
        if (-self.daily_pnl) >= settings.MAX_DAILY_LOSS:
            raise RuntimeError(
                f"Daily loss limit hit: ₹{-self.daily_pnl:,.0f} "
                f"≥ ₹{settings.MAX_DAILY_LOSS:,.0f} — no more trades today."
            )
        if estimated_cost > settings.MAX_POSITION_SIZE:
            raise RuntimeError(
                f"Position size ₹{estimated_cost:,.0f} exceeds "
                f"max allowed ₹{settings.MAX_POSITION_SIZE:,.0f}."
            )

    # ── Order placement ───────────────────────────────────────────────────────

    def place_options_order(self, ticker: str, strike: int, option_type: str,
                            expiry: str = None, transaction: str = 'BUY',
                            lots: int = 1) -> str:
        """
        Place (or simulate) a CE/PE order.

        Args:
            ticker      : underlying — 'NIFTY', 'BANKNIFTY', 'RELIANCE', …
            strike      : strike price integer (e.g. 22500)
            option_type : 'CE' or 'PE'
            expiry      : 'YYYY-MM-DD', or None for nearest expiry
            transaction : 'BUY' or 'SELL'
            lots        : number of lots (1 lot = 1 × lot_size contracts)

        Returns:
            order_id string (real ID on live; 'PAPER-XXXX' on paper)
        """
        instrument = find_option(ticker, strike, option_type, expiry_date=expiry)
        quantity   = instrument['lot_size'] * lots

        # Estimate cost using LTP
        ltp_resp = self.feed.obj.ltpData(
            'NFO',
            instrument['tradingsymbol'],
            instrument['symboltoken'],
        )
        ltp            = float(ltp_resp['data']['ltp'])
        estimated_cost = ltp * quantity

        self._check_risk(estimated_cost)

        order_params = {
            'variety':         'NORMAL',
            'tradingsymbol':   instrument['tradingsymbol'],
            'symboltoken':     instrument['symboltoken'],
            'transactiontype': transaction,
            'exchange':        'NFO',
            'ordertype':       'MARKET',
            'producttype':     'INTRADAY',
            'duration':        'DAY',
            'price':           '0',
            'squareoff':       '0',
            'stoploss':        '0',
            'quantity':        str(quantity),
        }

        if self.paper_mode:
            order_id = f"PAPER-{len(self._paper_orders) + 1:04d}"
            self._paper_orders.append({'order_id': order_id, **order_params,
                                       'ltp': ltp, 'cost': estimated_cost})
            logger.info(f"[PAPER] {transaction} {quantity} × {instrument['tradingsymbol']} "
                        f"@ ₹{ltp:.2f}  (order {order_id})")
        else:
            resp = self.feed.obj.placeOrder(order_params)
            if not resp.get('status'):
                raise RuntimeError(f"placeOrder failed: {resp.get('message')}")
            order_id = resp['data']['orderid']
            logger.info(f"[LIVE] Order placed: {order_id}")

        telegram_bot.send_order_placed(ticker, order_id, order_params)
        return order_id

    # ── Position management ───────────────────────────────────────────────────

    def get_positions(self) -> list:
        """Return current open positions (paper log or live API)."""
        if self.paper_mode:
            return self._paper_orders
        resp = self.feed.obj.position()
        return resp.get('data') or []

    def square_off_all(self):
        """
        Emergency square-off — close every open position immediately.
        In paper mode this just clears the in-memory log.
        """
        if self.paper_mode:
            count = len(self._paper_orders)
            self._paper_orders.clear()
            logger.info(f"[PAPER] Squared off {count} position(s)")
            return

        positions = self.get_positions()
        for pos in positions:
            net_qty = int(pos.get('netqty', 0))
            if net_qty == 0:
                continue
            side = 'SELL' if net_qty > 0 else 'BUY'
            try:
                self.feed.obj.placeOrder({
                    'variety':         'NORMAL',
                    'tradingsymbol':   pos['tradingsymbol'],
                    'symboltoken':     pos['symboltoken'],
                    'transactiontype': side,
                    'exchange':        pos['exchange'],
                    'ordertype':       'MARKET',
                    'producttype':     'INTRADAY',
                    'duration':        'DAY',
                    'price':           '0',
                    'squareoff':       '0',
                    'stoploss':        '0',
                    'quantity':        str(abs(net_qty)),
                })
                logger.info(f"Squared off {pos['tradingsymbol']} ({side} {abs(net_qty)})")
            except Exception as exc:
                logger.error(f"Square-off failed for {pos['tradingsymbol']}: {exc}")
                telegram_bot.send_error(f"Square-off failed: {pos['tradingsymbol']} — {exc}")
