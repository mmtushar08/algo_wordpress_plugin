import pandas as pd
from indicators.rsi import calculate_rsi


def simple_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30):
    df = data.copy()
    df['RSI'] = calculate_rsi(df['Close'], rsi_period)
    df['Signal'] = 0
    df.loc[df['RSI'] < oversold, 'Signal'] = 1
    df.loc[df['RSI'] > overbought, 'Signal'] = -1
    return df
