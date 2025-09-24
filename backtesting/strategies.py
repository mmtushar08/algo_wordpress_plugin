from indicators.rsi import calculate_rsi

def simple_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30):
    rsi = calculate_rsi(data['Close'], rsi_period)
    signals = pd.Series(index=data.index)
    
    signals[rsi < oversold] = 1  # Buy signal
    signals[rsi > overbought] = -1  # Sell signal
    
    return signals
