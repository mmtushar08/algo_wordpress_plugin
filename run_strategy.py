from data.fetch_data import fetch_data
from backtesting.strategies import simple_rsi_strategy
from backtesting.metrics import compute_metrics


def main():
    ticker = 'AAPL'
    print(f"Fetching 6-month daily data for {ticker}…")
    data = fetch_data(ticker, period='6mo', interval='1d')

    result = simple_rsi_strategy(data)

    metrics = compute_metrics(result)
    print(f"\n{'═' * 40}")
    print(f"  {ticker} RSI Strategy — Backtest Results")
    print(f"{'═' * 40}")
    for key, val in metrics.items():
        print(f"  {key:<20} {val}")
    print(f"{'═' * 40}")

    print("\nRecent signals (last 10 rows):")
    print(result[['Close', 'RSI', 'Signal']].tail(10).to_string())


if __name__ == "__main__":
    main()
