import numpy as np


def compute_metrics(df, initial_capital=10000):
    """Compute backtesting performance metrics from a strategy result DataFrame."""
    df = df.copy()
    df['Position'] = df['Signal'].shift(1).fillna(0)
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Position'] * df['Returns']
    df['Cumulative'] = (1 + df['Strategy_Returns']).cumprod()
    df['Equity'] = initial_capital * df['Cumulative']

    total_return = df['Cumulative'].iloc[-1] - 1

    daily = df['Strategy_Returns'].dropna()
    sharpe = (daily.mean() / daily.std() * np.sqrt(252)) if daily.std() > 0 else 0.0

    rolling_max = df['Equity'].cummax()
    drawdown = (df['Equity'] - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    trades = df[df['Signal'] != 0]
    num_trades = len(trades)

    buy_wins = ((df['Signal'] == 1) & (df['Returns'] > 0)).sum()
    sell_wins = ((df['Signal'] == -1) & (df['Returns'] < 0)).sum()
    win_rate = (buy_wins + sell_wins) / num_trades if num_trades > 0 else 0.0

    return {
        'Total Return':  f"{total_return:.2%}",
        'Sharpe Ratio':  f"{sharpe:.2f}",
        'Max Drawdown':  f"{max_drawdown:.2%}",
        'Total Trades':  num_trades,
        'Win Rate':      f"{win_rate:.2%}",
        'Final Equity':  f"${df['Equity'].iloc[-1]:,.2f}",
    }
