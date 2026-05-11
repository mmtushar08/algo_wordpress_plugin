import pandas as pd


def calculate_macd(data, fast=12, slow=26, signal=9):
    """Return DataFrame with MACD line, signal line, and histogram."""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        'MACD':      macd_line,
        'Signal':    signal_line,
        'Histogram': macd_line - signal_line,
    }, index=data.index)
