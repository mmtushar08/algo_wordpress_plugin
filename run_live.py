#!/usr/bin/env python3
"""
AlgoTrader India — Live Signal Engine entry point.

Prerequisites:
  1. pip install -r requirements.txt
  2. cp .env.example .env  and fill in your credentials
  3. python run_live.py                              # signal + Telegram alerts only
  4. python run_live.py --auto-trade                 # also place paper orders
  5. Set PAPER_TRADING=false in .env for live orders (after thorough testing!)

Examples:
  python run_live.py
  python run_live.py --tickers NIFTY BANKNIFTY
  python run_live.py --tickers RELIANCE TCS INFY --interval 1h
  python run_live.py --tickers NIFTY --interval 15m --auto-trade --expiry weekly
"""
import argparse
from engine.live_engine import LiveEngine


def main():
    parser = argparse.ArgumentParser(
        prog='run_live',
        description='AlgoTrader India — live NSE/BSE signal + options engine',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--tickers', nargs='+', default=None,
        help='Tickers to watch  e.g. NIFTY BANKNIFTY RELIANCE',
    )
    parser.add_argument(
        '--interval', default='15m',
        choices=['1m', '3m', '5m', '10m', '15m', '30m', '1h', '1d'],
        help='Candle interval',
    )
    parser.add_argument(
        '--iv', default=0.15, type=float,
        help='Implied volatility for Black-Scholes Greeks (e.g. 0.15 = 15%%)',
    )
    parser.add_argument(
        '--days-to-expiry', default=7, type=int,
        help='Days to expiry passed to Greeks calculator',
    )
    parser.add_argument(
        '--expiry', default='weekly', choices=['weekly', 'monthly'],
        help='Options expiry preference for strike recommendation',
    )
    parser.add_argument(
        '--auto-trade', action='store_true',
        help='Auto-place CE/PE orders on each new signal (paper by default)',
    )
    args = parser.parse_args()

    engine = LiveEngine(auto_trade=args.auto_trade)
    engine.run(
        tickers        = args.tickers,
        interval       = args.interval,
        iv             = args.iv,
        days_to_expiry = args.days_to_expiry,
        expiry         = args.expiry,
    )


if __name__ == '__main__':
    main()
