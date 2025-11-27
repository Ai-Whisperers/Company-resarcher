import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SmaCross(Strategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    Buy when fast SMA crosses above slow SMA.
    Sell when fast SMA crosses below slow SMA.
    """

    n1 = 10  # Fast SMA
    n2 = 20  # Slow SMA

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()


class QuantEngine:
    """
    Engine for running quantitative backtests using backtesting.py.
    """

    def __init__(self, cash: int = 10000, commission: float = 0.002):
        self.cash = cash
        self.commission = commission

    def run_backtest(
        self, data: pd.DataFrame, strategy_name: str = "SmaCross"
    ) -> Dict[str, Any]:
        """
        Run a backtest on the provided data.

        Args:
            data: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
                  and Datetime index.
            strategy_name: Name of the strategy to run (currently only 'SmaCross').

        Returns:
            Dictionary with performance metrics.
        """
        if data.empty:
            logger.warning("Empty data provided for backtest.")
            return {"error": "No data"}

        # Ensure column names match backtesting.py requirements
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_cols):
            logger.error(f"Data missing required columns: {required_cols}")
            return {"error": "Invalid data format"}

        try:
            strategy = SmaCross  # Default for now, can extend later

            bt = Backtest(
                data,
                strategy,
                cash=self.cash,
                commission=self.commission,
                exclusive_orders=True,
            )

            stats = bt.run()

            # Convert stats to dictionary
            result = {
                "Return [%]": stats["Return [%]"],
                "Buy & Hold Return [%]": stats["Buy & Hold Return [%]"],
                "Sharpe Ratio": stats["Sharpe Ratio"],
                "Max Drawdown [%]": stats["Max. Drawdown [%]"],
                "Win Rate [%]": stats["Win Rate [%]"],
                "Trades": stats["# Trades"],
                "Strategy": strategy_name,
            }

            logger.info(f"Backtest complete. Return: {result['Return [%]']:.2f}%")
            return result

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"error": str(e)}
