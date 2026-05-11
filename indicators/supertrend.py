import pandas as pd


def calculate_supertrend(data, atr_period=10, multiplier=3.0):
    """
    Supertrend indicator — ATR-based trend follower widely used in Indian markets.

    Returns a DataFrame with:
        Supertrend  : the trailing stop line
        ST_Direction: 1 = bullish (price above line), -1 = bearish
    """
    df = data.copy()

    # True Range
    prev_close = df['Close'].shift(1)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - prev_close).abs(),
        (df['Low']  - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(span=atr_period, adjust=False).mean()

    hl_mid = (df['High'] + df['Low']) / 2
    upper_band = hl_mid + multiplier * atr
    lower_band = hl_mid - multiplier * atr

    n = len(df)
    supertrend = [0.0] * n
    direction  = [1]   * n          # 1 = bullish, -1 = bearish

    for i in range(1, n):
        close      = df['Close'].iloc[i]
        prev_close = df['Close'].iloc[i - 1]

        # Bands only tighten, never widen, to avoid whipsaws
        ub = upper_band.iloc[i]
        lb = lower_band.iloc[i]
        final_upper = ub if ub < upper_band.iloc[i-1] or prev_close > upper_band.iloc[i-1] else upper_band.iloc[i-1]
        final_lower = lb if lb > lower_band.iloc[i-1] or prev_close < lower_band.iloc[i-1] else lower_band.iloc[i-1]

        prev_st  = supertrend[i - 1]
        prev_dir = direction[i - 1]

        if prev_st == upper_band.iloc[i - 1]:       # was bearish
            if close <= final_upper:
                supertrend[i] = final_upper
                direction[i]  = -1
            else:
                supertrend[i] = final_lower
                direction[i]  = 1
        else:                                        # was bullish
            if close >= final_lower:
                supertrend[i] = final_lower
                direction[i]  = 1
            else:
                supertrend[i] = final_upper
                direction[i]  = -1

    result = pd.DataFrame({
        'Supertrend':   supertrend,
        'ST_Direction': direction,
    }, index=df.index)

    return result
