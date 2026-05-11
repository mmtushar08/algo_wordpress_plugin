# AlgoTrader India

> Open-source buy/sell signal engine for NSE/BSE equities and F&O — built for Indian retail traders.

## Why AlgoTrader India?

| | AlgoTrader India | TradingView Pro | Zerodha Streak | Paid Signal Groups |
|---|---|---|---|---|
| Cost | Free & open source | ₹1,500/mo | ₹500/mo | ₹2,000–10,000/mo |
| Customizable | Full Python control | Limited Pine Script | No | No |
| Options strike recommendation | Yes | Manual | Manual | Varies |
| Backtesting metrics | Sharpe, drawdown, win rate | Yes | Yes | No |
| Transparent logic | Read the code | No black box | No | No |
| Works offline | Yes | No | No | No |

## What It Does

1. **Equity Signals** — Multi-indicator confluence (RSI + MACD + Supertrend) for any NSE/BSE stock or index
2. **Options Recommendation** — Automatically suggests CE/PE and the right strike price based on the signal
3. **Backtesting** — Measure Sharpe ratio, max drawdown, win rate, and final equity curve

## Quick Start

```bash
pip install -r requirements.txt

# Signal + options recommendation for RELIANCE
python cli.py --ticker RELIANCE --options

# Backtest BANKNIFTY with Supertrend strategy
python cli.py --ticker BANKNIFTY --strategy supertrend --period 3mo

# Custom RSI settings for TCS
python cli.py --ticker TCS --rsi-period 21 --oversold 25 --overbought 75 --options

# NIFTY with monthly expiry options
python cli.py --ticker NIFTY --options --expiry monthly

# Simple run with defaults (RELIANCE, 6mo, RSI)
python run_strategy.py
```

## Supported Instruments

| Instrument | Symbol to use | Strike Interval | Lot Size |
|---|---|---|---|
| NIFTY 50 | `NIFTY` | 50 pts | 75 |
| Bank NIFTY | `BANKNIFTY` | 100 pts | 15 |
| Fin NIFTY | `FINNIFTY` | 50 pts | 40 |
| MidCap NIFTY | `MIDCPNIFTY` | 25 pts | 75 |
| NSE Stocks | `RELIANCE`, `TCS`, `INFY` | 50 pts (varies) | Stock-specific |

NSE stock symbols are automatically suffixed with `.NS`. BSE stocks: add `.BO` manually.

## Indicators

| Indicator | Module | Best Used For |
|---|---|---|
| RSI (14) | `indicators/rsi.py` | Overbought/oversold reversal |
| MACD (12/26/9) | `indicators/macd.py` | Trend + momentum crossover |
| Supertrend (10, 3) | `indicators/supertrend.py` | Trend direction (most popular in India) |
| Bollinger Bands (20) | `indicators/bollinger.py` | Volatility and breakout |
| SMA / EMA | `indicators/moving_averages.py` | Trend confirmation |
| VWAP | `indicators/vwap.py` | Intraday fair value |

## Strategies

| Strategy | Module | Logic |
|---|---|---|
| RSI | `backtesting/strategies.py` | Buy RSI < 30, Sell RSI > 70 |
| MACD Crossover | `strategies/macd_strategy.py` | MACD line crosses signal line |
| Supertrend + EMA | `strategies/supertrend_strategy.py` | ST bullish + EMA9 > EMA21 (swing trading) |
| Confluence | `signals/equity_signals.py` | 2-of-3 agreement: RSI + MACD + Supertrend |

## Options Module

Pass `--options` to get a strike recommendation alongside the signal:

```
Signal Score:        +2 / 3  (BULLISH)
Option Type:         CE  (Call)
ATM Strike:          22500
Recommended Strike:  22550 CE  (weekly)
Reasoning:           RSI oversold + Supertrend bullish.
                     1 OTM strike for leverage with defined risk.
```

The options module uses Black-Scholes to show theoretical price and Greeks (delta, gamma, theta, vega) so you know the risk before entering.

## Project Structure

```
algo_wordpress_plugin/
├── run_strategy.py              # Quick-run demo
├── cli.py                       # Full CLI interface
├── requirements.txt
│
├── data/
│   ├── fetch_data.py            # Generic Yahoo Finance fetcher
│   └── fetch_equity.py          # NSE/BSE-aware fetcher (auto .NS suffix)
│
├── indicators/
│   ├── rsi.py
│   ├── macd.py
│   ├── bollinger.py
│   ├── moving_averages.py
│   ├── supertrend.py            # ATR-based trend indicator
│   └── vwap.py                  # Volume weighted average price
│
├── signals/
│   ├── equity_signals.py        # Multi-indicator confluence engine
│   └── strike_selector.py       # CE/PE + strike price recommendation
│
├── options/
│   └── greeks.py                # Black-Scholes delta/gamma/theta/vega
│
├── backtesting/
│   ├── strategies.py            # RSI strategy
│   └── metrics.py               # Sharpe, drawdown, win rate
│
├── strategies/
│   ├── macd_strategy.py
│   └── supertrend_strategy.py
│
└── tests/
    └── test_strategies.py
```

## Roadmap

- [ ] Live signal alerts via Telegram bot
- [ ] Options chain analysis (OI, PCR, IV skew)
- [ ] Paper trading mode with P&L tracking
- [ ] Zerodha Kite Connect / Angel One SmartAPI integration
- [ ] F&O scanner — screen all 200 NSE F&O stocks at once
- [ ] Streamlit dashboard with live charts

## Disclaimer

This tool is for **educational and research purposes only**. It does not constitute financial advice. Always conduct your own research before trading. Options trading involves substantial risk of loss and may not be suitable for all investors.
