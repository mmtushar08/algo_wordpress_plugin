#!/usr/bin/env python3
"""
AlgoTrader CLI — backtest RSI or MACD strategies from the command line.

Usage examples:
    python cli.py --ticker TSLA --period 1y --strategy rsi
    python cli.py --ticker MSFT --strategy macd --capital 50000
    python cli.py --ticker AAPL --rsi-period 21 --oversold 25 --overbought 75
"""
import argparse

from data.fetch_data import fetch_data
from backtesting.strategies import simple_rsi_strategy
from backtesting.metrics import compute_metrics
from strategies.macd_strategy import macd_crossover_strategy


STRATEGIES = {
    'rsi':  simple_rsi_strategy,
    'macd': macd_crossover_strategy,
}


def print_report(ticker, strategy_name, metrics, result):
    width = 52
    print(f"\n{'═' * width}")
    print(f"  {ticker}  ·  {strategy_name.upper()} Strategy  ·  Backtest Report")
    print(f"{'═' * width}")
    for key, val in metrics.items():
        print(f"  {key:<20} {val}")
    print(f"{'═' * width}")
    print("\nRecent signals (last 10 rows):")
    cols = [c for c in ['Close', 'RSI', 'MACD', 'MACD_Signal', 'Signal'] if c in result.columns]
    print(result[cols].tail(10).to_string())
    print()


def main():
    parser = argparse.ArgumentParser(
        prog='algotrader',
        description='AlgoTrader — modular algorithmic trading backtester',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--ticker',     default='AAPL',  help='Stock ticker symbol')
    parser.add_argument('--period',     default='6mo',   help='Historical data window (1mo, 3mo, 6mo, 1y, 2y)')
    parser.add_argument('--interval',   default='1d',    help='Bar interval (1d, 1h, 15m)')
    parser.add_argument('--strategy',   default='rsi',   choices=STRATEGIES.keys(), help='Trading strategy')
    parser.add_argument('--capital',    default=10000,   type=float, help='Starting capital in USD')
    parser.add_argument('--rsi-period', default=14,      type=int,   help='RSI look-back period')
    parser.add_argument('--overbought', default=70.0,    type=float, help='RSI overbought threshold')
    parser.add_argument('--oversold',   default=30.0,    type=float, help='RSI oversold threshold')

    args = parser.parse_args()

    print(f"Fetching {args.period} of {args.ticker} ({args.interval} bars)…")
    data = fetch_data(args.ticker, period=args.period, interval=args.interval)

    strategy_fn = STRATEGIES[args.strategy]

    if args.strategy == 'rsi':
        result = strategy_fn(
            data,
            rsi_period=args.rsi_period,
            overbought=args.overbought,
            oversold=args.oversold,
        )
    else:
        result = strategy_fn(data)

    metrics = compute_metrics(result, initial_capital=args.capital)
    print_report(args.ticker, args.strategy, metrics, result)


if __name__ == '__main__':
    main()
