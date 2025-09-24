import pandas as pd
from data.fetch_data import fetch_data
from backtesting.strategies import simple_rsi_strategy

def main():
    # Fetch historical data
    data = fetch_data('AAPL', period='3mo', interval='1d')
    print("Data fetched:\n", data.head())

    # Run RSI strategy
    result = simple_rsi_strategy(data)
    print("\nStrategy signals:\n", result[['Close', 'RSI', 'Signal']].tail(10))

if __name__ == "__main__":
    main()
