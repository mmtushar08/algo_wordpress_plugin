def calculate_vwap(data):
    """
    Volume Weighted Average Price (VWAP).

    Designed for intraday data (interval='15m', '1h', etc.).
    On daily data it gives a cumulative session VWAP — useful as a
    trend benchmark but resets meaning at session boundaries.

    Returns a pandas Series aligned to data.index.
    """
    df = data.copy()
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    cum_tpv       = (typical_price * df['Volume']).cumsum()
    cum_vol       = df['Volume'].cumsum()
    return cum_tpv / cum_vol
