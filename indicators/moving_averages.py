def calculate_sma(data, window=20):
    return data.rolling(window=window).mean()


def calculate_ema(data, span=20):
    return data.ewm(span=span, adjust=False).mean()
