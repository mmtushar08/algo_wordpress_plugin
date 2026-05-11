from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.supertrend import calculate_supertrend


def generate_equity_signals(data, rsi_period=14, overbought=70, oversold=30):
    """
    Multi-indicator confluence signal engine.

    Combines RSI, MACD, and Supertrend — a signal fires only when
    at least 2 of the 3 indicators agree, reducing false positives.

    Signal values:
        1  = BUY  (2 or 3 indicators bullish)
       -1  = SELL (2 or 3 indicators bearish)
        0  = WAIT (no clear consensus)

    Returns the full DataFrame with individual indicator columns and a
    final 'Signal' and 'Score' column for each bar.
    """
    df = data.copy()

    # RSI
    df['RSI'] = calculate_rsi(df['Close'], rsi_period)
    df['RSI_Signal'] = 0
    df.loc[df['RSI'] < oversold,   'RSI_Signal'] =  1
    df.loc[df['RSI'] > overbought, 'RSI_Signal'] = -1

    # MACD
    macd_df = calculate_macd(df['Close'])
    df['MACD']             = macd_df['MACD']
    df['MACD_Signal_Line'] = macd_df['Signal']
    df['MACD_Signal'] = 0
    df.loc[df['MACD'] > df['MACD_Signal_Line'], 'MACD_Signal'] =  1
    df.loc[df['MACD'] < df['MACD_Signal_Line'], 'MACD_Signal'] = -1

    # Supertrend
    st_df = calculate_supertrend(df)
    df['Supertrend'] = st_df['Supertrend']
    df['ST_Signal']  = st_df['ST_Direction']   # 1 bullish / -1 bearish

    # Confluence score: -3 to +3
    df['Score'] = df['RSI_Signal'] + df['MACD_Signal'] + df['ST_Signal']

    df['Signal'] = 0
    df.loc[df['Score'] >=  2, 'Signal'] =  1   # Strong BUY
    df.loc[df['Score'] <= -2, 'Signal'] = -1   # Strong SELL

    return df


def get_latest_signal(data, **kwargs):
    """
    Return a human-readable summary dict for the most recent bar.

    Example:
        {'signal': 1, 'score': 2, 'label': 'BUY', 'rsi': 28.4,
         'macd_bullish': True, 'st_bullish': True}
    """
    result = generate_equity_signals(data, **kwargs)
    last   = result.iloc[-1]

    label_map = {1: 'BUY', -1: 'SELL', 0: 'WAIT'}
    return {
        'signal':      int(last['Signal']),
        'score':       int(last['Score']),
        'label':       label_map[int(last['Signal'])],
        'rsi':         round(float(last['RSI']), 2),
        'macd_bullish': bool(last['MACD_Signal'] == 1),
        'st_bullish':   bool(last['ST_Signal']   == 1),
    }
