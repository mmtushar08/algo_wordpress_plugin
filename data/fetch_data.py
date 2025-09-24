import yfinance as yf

def fetch_data(ticker='AAPL', period='1mo', interval='1d'):
    """
    Fetch historical market data from Yahoo Finance.
    
    Args:
        ticker (str): Stock ticker symbol.
        period (str): How much historical data to fetch (e.g., '1mo', '6mo', '1y').
        interval (str): Data interval (e.g., '1d', '1h').
    
    Returns:
        pandas.DataFrame: Historical OHLCV data.
    """
    data = yf.download(ticker, period=period, interval=interval)
    return data
