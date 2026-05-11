from indicators.macd import calculate_macd


def macd_crossover_strategy(data):
    """
    Generate buy/sell signals based on MACD line crossing the signal line.
    Buy  (1)  when MACD crosses above the signal line.
    Sell (-1) when MACD crosses below the signal line.
    """
    df = data.copy()
    macd_df = calculate_macd(df['Close'])
    df['MACD'] = macd_df['MACD']
    df['MACD_Signal'] = macd_df['Signal']
    df['Signal'] = 0
    df.loc[df['MACD'] > df['MACD_Signal'], 'Signal'] = 1
    df.loc[df['MACD'] < df['MACD_Signal'], 'Signal'] = -1
    return df
