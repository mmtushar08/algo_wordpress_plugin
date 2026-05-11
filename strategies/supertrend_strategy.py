from indicators.supertrend import calculate_supertrend
from indicators.moving_averages import calculate_ema


def supertrend_ema_strategy(data, ema_fast=9, ema_slow=21,
                             st_period=10, st_multiplier=3.0):
    """
    Supertrend + EMA crossover strategy — widely used by Indian swing traders.

    Entry rules:
        BUY  (1)  : Supertrend bullish  AND  EMA9 > EMA21
        SELL (-1) : Supertrend bearish  AND  EMA9 < EMA21
        WAIT (0)  : Mixed signals

    Works well on daily charts for NIFTY, BANKNIFTY, and trending F&O stocks.
    """
    df = data.copy()

    st_df = calculate_supertrend(df, atr_period=st_period, multiplier=st_multiplier)
    df['Supertrend']   = st_df['Supertrend']
    df['ST_Direction'] = st_df['ST_Direction']

    df['EMA_Fast'] = calculate_ema(df['Close'], span=ema_fast)
    df['EMA_Slow'] = calculate_ema(df['Close'], span=ema_slow)

    df['Signal'] = 0
    bullish = (df['ST_Direction'] == 1)  & (df['EMA_Fast'] > df['EMA_Slow'])
    bearish = (df['ST_Direction'] == -1) & (df['EMA_Fast'] < df['EMA_Slow'])
    df.loc[bullish, 'Signal'] =  1
    df.loc[bearish, 'Signal'] = -1

    return df
