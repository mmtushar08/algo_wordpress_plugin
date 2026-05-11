import pandas as pd


def calculate_bollinger_bands(data, window=20, num_std=2):
    """Return DataFrame with SMA, upper band, and lower band."""
    sma = data.rolling(window=window).mean()
    std = data.rolling(window=window).std()
    return pd.DataFrame({
        'SMA':   sma,
        'Upper': sma + std * num_std,
        'Lower': sma - std * num_std,
    }, index=data.index)
