import unittest
import pandas as pd
from backtesting.strategies import simple_rsi_strategy

class TestStrategies(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.data = pd.DataFrame({
            'Close': [100, 102, 101, 105, 107, 110, 108, 106, 104, 103]
        })
    
    def test_rsi_strategy(self):
        signals = simple_rsi_strategy(self.data)
        self.assertEqual(signals[0], 1)  # Buy signal on the first day
        self.assertEqual(signals[9], -1)  # Sell signal on the last day

if __name__ == '__main__':
    unittest.main()
