import pandas as pd
import logging
from typing import Dict, Any, List
from .quant_engine import QuantEngine

logger = logging.getLogger(__name__)


class AlphaFactorMiner:
    """
    Mines for alpha factors by testing various strategies on provided data.
    """

    def __init__(self):
        self.engine = QuantEngine()
        self.factors = [
            "SmaCross",
            # Future: Add "RSI", "BollingerBands", "MeanReversion"
        ]

    def mine_factors(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Test all defined factors on the data and return performance.
        """
        results = []

        for factor in self.factors:
            logger.info(f"Testing factor: {factor}")
            result = self.engine.run_backtest(data, strategy_name=factor)

            if "error" not in result:
                results.append(result)
            else:
                logger.warning(f"Factor {factor} failed: {result['error']}")

        # Sort by Sharpe Ratio descending
        results.sort(key=lambda x: x.get("Sharpe Ratio", 0), reverse=True)
        return results

    def analyze_company(self, company_name: str, data: pd.DataFrame) -> str:
        """
        Run alpha mining for a specific company and generate a summary string.
        """
        results = self.mine_factors(data)

        if not results:
            return "No alpha factors found or insufficient data."

        best_factor = results[0]
        summary = f"### Quantitative Analysis for {company_name}\n\n"
        summary += f"**Best Performing Strategy:** {best_factor['Strategy']}\n"
        summary += f"- **Return:** {best_factor['Return [%]']:.2f}%\n"
        summary += f"- **Sharpe Ratio:** {best_factor['Sharpe Ratio']:.2f}\n"
        summary += f"- **Max Drawdown:** {best_factor['Max Drawdown [%]']:.2f}%\n"
        summary += f"- **Win Rate:** {best_factor['Win Rate [%]']:.2f}%\n"

        return summary
