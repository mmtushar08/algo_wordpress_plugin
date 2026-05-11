import unittest
import pandas as pd
import numpy as np

from backtesting.strategies import simple_rsi_strategy
from backtesting.metrics import compute_metrics


def _make_prices(n=60, seed=42):
    np.random.seed(seed)
    prices = [100.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + np.random.uniform(-0.02, 0.02)))
    return pd.DataFrame({'Close': prices})


def _declining_prices(n=60):
    return pd.DataFrame({'Close': [100.0 - i * 1.5 for i in range(n)]})


def _rising_prices(n=60):
    return pd.DataFrame({'Close': [100.0 + i * 1.5 for i in range(n)]})


class TestRSIStrategy(unittest.TestCase):

    def setUp(self):
        self.data = _make_prices()

    def test_returns_dataframe(self):
        result = simple_rsi_strategy(self.data)
        self.assertIsInstance(result, pd.DataFrame)

    def test_output_has_required_columns(self):
        result = simple_rsi_strategy(self.data)
        for col in ('Close', 'RSI', 'Signal'):
            self.assertIn(col, result.columns)

    def test_signal_values_are_valid(self):
        result = simple_rsi_strategy(self.data)
        self.assertTrue(set(result['Signal'].unique()).issubset({-1, 0, 1}))

    def test_buy_signal_generated_for_declining_prices(self):
        result = simple_rsi_strategy(_declining_prices())
        self.assertIn(1, result['Signal'].values, "Expected at least one buy signal on declining prices")

    def test_sell_signal_generated_for_rising_prices(self):
        result = simple_rsi_strategy(_rising_prices())
        self.assertIn(-1, result['Signal'].values, "Expected at least one sell signal on rising prices")

    def test_custom_thresholds(self):
        result = simple_rsi_strategy(self.data, overbought=60, oversold=40)
        self.assertTrue(set(result['Signal'].unique()).issubset({-1, 0, 1}))


class TestMetrics(unittest.TestCase):

    def setUp(self):
        data = _make_prices(n=100)
        self.result = simple_rsi_strategy(data)

    def test_returns_all_expected_keys(self):
        metrics = compute_metrics(self.result)
        expected = {'Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Total Trades', 'Win Rate', 'Final Equity'}
        self.assertEqual(expected, set(metrics.keys()))

    def test_final_equity_positive(self):
        metrics = compute_metrics(self.result, initial_capital=10000)
        equity = float(metrics['Final Equity'].replace('$', '').replace(',', ''))
        self.assertGreater(equity, 0)

    def test_custom_capital(self):
        metrics = compute_metrics(self.result, initial_capital=50000)
        self.assertIn('$', metrics['Final Equity'])


if __name__ == '__main__':
    unittest.main()
