import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.quant_engine import QuantEngine


class TestQuantEngine(unittest.TestCase):

    def setUp(self):
        self.engine = QuantEngine()

        # Create mock OHLCV data
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {
            "Open": np.random.rand(100) * 100,
            "High": np.random.rand(100) * 100,
            "Low": np.random.rand(100) * 100,
            "Close": np.random.rand(100) * 100,
            "Volume": np.random.randint(1000, 10000, 100),
        }
        self.df = pd.DataFrame(data, index=dates)

        # Ensure High is highest and Low is lowest
        self.df["High"] = self.df[["Open", "Close"]].max(axis=1) + 1
        self.df["Low"] = self.df[["Open", "Close"]].min(axis=1) - 1

    def test_run_backtest(self):
        result = self.engine.run_backtest(self.df)

        self.assertNotIn("error", result)
        self.assertIn("Return [%]", result)
        self.assertIn("Sharpe Ratio", result)
        print(f"\nBacktest Result: {result}")


if __name__ == "__main__":
    unittest.main()
