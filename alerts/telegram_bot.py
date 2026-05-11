"""
Telegram alert sender for AlgoTrader India.

Uses the Telegram Bot API directly via requests — no heavy async library needed.
Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file.

How to set up:
  1. Message @BotFather on Telegram → /newbot → copy the token
  2. Message @userinfobot on Telegram → copy your chat_id
  3. Add both to .env
"""
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)


def _send(text: str):
    """Post a message to the configured Telegram chat (HTML formatting)."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — printing to console instead")
        print(text)
        return

    url     = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id':    settings.TELEGRAM_CHAT_ID,
        'text':       text,
        'parse_mode': 'HTML',
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        logger.error(f"Telegram send failed: {exc}")


def send_signal(ticker: str, sig_info: dict,
                options_rec: dict = None, greeks: dict = None):
    """
    Send a formatted signal alert.

    Args:
        ticker      : instrument name
        sig_info    : dict from get_latest_signal()
        options_rec : dict from recommend_strike() — optional
        greeks      : dict from black_scholes_greeks() — optional
    """
    icon = {'BUY': '🟢 BUY', 'SELL': '🔴 SELL', 'WAIT': '🟡 WAIT'}[sig_info['label']]

    lines = [
        f"<b>{icon} — {ticker}</b>",
        f"Consensus  : {sig_info['score']:+d} / 3",
        f"RSI        : {sig_info['rsi']}",
        f"MACD       : {'Bullish ▲' if sig_info['macd_bullish'] else 'Bearish ▼'}",
        f"Supertrend : {'Bullish ▲' if sig_info['st_bullish']   else 'Bearish ▼'}",
    ]

    if options_rec and options_rec.get('action') != 'WAIT':
        lines += [
            '',
            '<b>Options Trade</b>',
            f"Action  : {options_rec['action']} "
            f"{options_rec['recommended_strike']:,} {options_rec['option_type']}",
            f"ATM     : {options_rec['atm_strike']:,}",
            f"Expiry  : {options_rec['expiry']}",
            f"Lot sz  : {options_rec['lot_size']}",
        ]
        if greeks:
            lines += [
                '',
                f"Th. Price : ₹{greeks['price']:,.2f}",
                f"Delta     : {greeks['delta']}",
                f"Theta/day : ₹{greeks['theta']}",
                f"Vega/1%IV : ₹{greeks['vega']}",
            ]

    _send('\n'.join(lines))


def send_order_placed(ticker: str, order_id: str, details: dict):
    """Confirm a placed (or simulated) order."""
    mode = '[PAPER]' if settings.PAPER_TRADING else '[LIVE]'
    text = (
        f"✅ <b>Order Placed {mode}</b>\n"
        f"Ticker  : {ticker}\n"
        f"Symbol  : {details.get('tradingsymbol')}\n"
        f"Side    : {details.get('transactiontype')}  "
        f"{details.get('quantity')} qty\n"
        f"OrderID : {order_id}"
    )
    _send(text)


def send_error(message: str):
    """Send an error/warning notification."""
    _send(f"⚠️ <b>AlgoTrader Error</b>\n{message}")


def send_daily_summary(date_str: str, results: list):
    """
    Send end-of-day P&L summary.

    Args:
        results : list of dicts with keys ticker, signal, pnl
    """
    lines = [f"<b>Daily Summary — {date_str}</b>", '']
    total = 0.0
    for r in results:
        pnl   = r.get('pnl', 0)
        total += pnl
        icon  = '✅' if pnl >= 0 else '❌'
        lines.append(f"{icon} {r['ticker']:12} {r['signal']:4}  ₹{pnl:+,.0f}")
    lines += ['', f"<b>Total P&L : ₹{total:+,.0f}</b>"]
    _send('\n'.join(lines))
