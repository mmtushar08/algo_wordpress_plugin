import yfinance as yf

NSE_SUFFIX = '.NS'
BSE_SUFFIX = '.BO'

# yfinance symbols for major Indian indices
NSE_INDICES = {
    'NIFTY':      '^NSEI',
    'BANKNIFTY':  '^NSEBANK',
    'FINNIFTY':   'NIFTY_FIN_SERVICE.NS',
    'MIDCPNIFTY': '^NSEMDCP50',
    'SENSEX':     '^BSESN',
}


def nse_symbol(ticker):
    """Resolve a plain NSE ticker to the correct yfinance symbol."""
    ticker = ticker.upper().strip()
    if ticker in NSE_INDICES:
        return NSE_INDICES[ticker]
    if not ticker.endswith(('.NS', '.BO')):
        return ticker + NSE_SUFFIX
    return ticker


def fetch_equity(ticker, period='6mo', interval='1d'):
    """
    Fetch NSE/BSE equity or index OHLCV data from Yahoo Finance.

    Auto-appends .NS for plain NSE stock symbols.
    Supports index aliases: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX.

    Args:
        ticker   : e.g. 'RELIANCE', 'TCS', 'NIFTY', 'BANKNIFTY'
        period   : '1mo', '3mo', '6mo', '1y', '2y'
        interval : '1d', '1h', '15m', '5m'

    Returns:
        pandas.DataFrame with OHLCV columns
    """
    symbol = nse_symbol(ticker)
    data = yf.download(symbol, period=period, interval=interval,
                       progress=False, auto_adjust=True)
    if data.empty:
        raise ValueError(
            f"No data returned for '{symbol}'. "
            "Check the ticker symbol and try again."
        )
    # Flatten MultiIndex columns produced by yfinance >= 0.2
    if isinstance(data.columns, type(data.columns)) and hasattr(data.columns, 'levels'):
        data.columns = data.columns.get_level_values(0)
    return data
