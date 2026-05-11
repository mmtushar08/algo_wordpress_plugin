#!/usr/bin/env python3
"""
AlgoTrader India CLI

Examples:
    python cli.py --ticker RELIANCE --options
    python cli.py --ticker NIFTY --strategy supertrend --options --expiry weekly
    python cli.py --ticker BANKNIFTY --strategy confluence --options --iv 0.18
    python cli.py --ticker TCS --strategy rsi --rsi-period 21 --period 1y
    python cli.py --ticker INFY --strategy macd --period 3mo
"""
import argparse

from data.fetch_equity import fetch_equity
from backtesting.strategies import simple_rsi_strategy
from backtesting.metrics import compute_metrics
from strategies.macd_strategy import macd_crossover_strategy
from strategies.supertrend_strategy import supertrend_ema_strategy
from signals.equity_signals import generate_equity_signals, get_latest_signal
from signals.strike_selector import recommend_strike
from options.greeks import black_scholes_greeks

STRATEGIES = {
    'rsi':        simple_rsi_strategy,
    'macd':       macd_crossover_strategy,
    'supertrend': supertrend_ema_strategy,
    'confluence': generate_equity_signals,
}


def _divider(width=56):
    return '═' * width


def print_backtest_report(ticker, strategy_name, metrics):
    w = 56
    print(f"\n{_divider(w)}")
    print(f"  {ticker}  ·  {strategy_name.upper()}  ·  Backtest Report")
    print(f"{_divider(w)}")
    for key, val in metrics.items():
        print(f"  {key:<22} {val}")
    print(_divider(w))


def print_signal_report(ticker, sig_info):
    label_icon = {'BUY': '[BUY]', 'SELL': '[SELL]', 'WAIT': '[WAIT]'}
    icon  = label_icon[sig_info['label']]
    score = sig_info['score']
    print(f"\n{'─' * 56}")
    print(f"  Latest Signal  :  {icon}  (consensus score {score:+d} / 3)")
    print(f"  RSI            :  {sig_info['rsi']}")
    print(f"  MACD           :  {'Bullish' if sig_info['macd_bullish'] else 'Bearish'}")
    print(f"  Supertrend     :  {'Bullish' if sig_info['st_bullish']   else 'Bearish'}")
    print(f"{'─' * 56}")


def print_options_report(rec, greeks):
    print(f"\n  Options Recommendation")
    print(f"{'─' * 56}")
    if rec['action'] == 'WAIT':
        print(f"  Action         :  WAIT — no directional consensus")
        print(f"  ATM Strike     :  {rec['atm_strike']:,.0f}")
    else:
        print(f"  Action         :  {rec['action']} {rec['recommended_strike']:,.0f} {rec['option_type']}")
        print(f"  ATM Strike     :  {rec['atm_strike']:,.0f}")
        print(f"  Expiry         :  {rec['expiry']}")
        print(f"  Lot Size       :  {rec['lot_size']}")
        if greeks:
            print(f"\n  Black-Scholes Greeks")
            print(f"  {'─' * 30}")
            print(f"  Theoretical Price :  ₹{greeks['price']:,.2f}")
            print(f"  Delta             :  {greeks['delta']}")
            print(f"  Gamma             :  {greeks['gamma']}")
            print(f"  Theta (per day)   :  ₹{greeks['theta']}")
            print(f"  Vega  (per 1% IV) :  ₹{greeks['vega']}")
    print(f"\n  Reasoning: {rec['reasoning']}")
    print(f"{'─' * 56}")


def main():
    parser = argparse.ArgumentParser(
        prog='algotrader',
        description='AlgoTrader India — NSE/BSE signal engine with options recommendation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--ticker',          default='RELIANCE',    help='NSE/BSE ticker or index (NIFTY, BANKNIFTY, RELIANCE…)')
    parser.add_argument('--period',          default='6mo',         help='Data window: 1mo 3mo 6mo 1y 2y')
    parser.add_argument('--interval',        default='1d',          help='Bar size: 1d 1h 15m 5m')
    parser.add_argument('--strategy',        default='confluence',  choices=STRATEGIES.keys(),
                        help='Signal strategy to use')
    parser.add_argument('--capital',         default=100000,        type=float, help='Starting capital (INR)')
    parser.add_argument('--rsi-period',      default=14,            type=int)
    parser.add_argument('--overbought',      default=70.0,          type=float)
    parser.add_argument('--oversold',        default=30.0,          type=float)
    parser.add_argument('--options',         action='store_true',   help='Show CE/PE strike recommendation')
    parser.add_argument('--expiry',          default='weekly',      choices=['weekly', 'monthly'])
    parser.add_argument('--iv',              default=0.15,          type=float, help='Implied volatility for Greeks (e.g. 0.15 = 15%%)')
    parser.add_argument('--days-to-expiry',  default=7,             type=int,   help='Days to expiry for Greeks')

    args = parser.parse_args()

    print(f"\nFetching {args.period} of {args.ticker} ({args.interval} bars)…")
    data = fetch_equity(args.ticker, period=args.period, interval=args.interval)

    # Run chosen strategy
    strategy_fn = STRATEGIES[args.strategy]
    if args.strategy == 'rsi':
        result = strategy_fn(data, rsi_period=args.rsi_period,
                             overbought=args.overbought, oversold=args.oversold)
    elif args.strategy == 'confluence':
        result = strategy_fn(data, rsi_period=args.rsi_period,
                             overbought=args.overbought, oversold=args.oversold)
    else:
        result = strategy_fn(data)

    # Backtest metrics
    metrics = compute_metrics(result, initial_capital=args.capital)
    print_backtest_report(args.ticker, args.strategy, metrics)

    # Latest signal summary (confluence always available)
    sig_info = get_latest_signal(data, rsi_period=args.rsi_period,
                                 overbought=args.overbought, oversold=args.oversold)
    print_signal_report(args.ticker, sig_info)

    # Options recommendation
    if args.options:
        spot = float(data['Close'].iloc[-1])
        rec  = recommend_strike(spot, sig_info['signal'],
                                symbol=args.ticker, expiry=args.expiry)
        greeks = None
        if rec['action'] != 'WAIT':
            greeks = black_scholes_greeks(
                spot            = spot,
                strike          = rec['recommended_strike'],
                days_to_expiry  = args.days_to_expiry,
                volatility      = args.iv,
                option_type     = rec['option_type'],
            )
        print_options_report(rec, greeks)

    print()


if __name__ == '__main__':
    main()
