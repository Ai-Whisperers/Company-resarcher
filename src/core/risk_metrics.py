"""
Risk metrics for financial analysis.

Provides standard risk measures for evaluating investment strategies.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from .logger import setup_logger

logger = setup_logger("risk_metrics")


@dataclass
class RiskMetrics:
    """Container for calculated risk metrics."""

    # Return metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    average_daily_return: float = 0.0

    # Volatility metrics
    volatility: float = 0.0
    annualized_volatility: float = 0.0
    downside_volatility: float = 0.0

    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Drawdown metrics
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0  # In days
    current_drawdown: float = 0.0

    # Other metrics
    beta: Optional[float] = None
    alpha: Optional[float] = None
    win_rate: float = 0.0
    profit_factor: float = 0.0

    # Time period
    trading_days: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_return": round(self.total_return, 4),
            "annualized_return": round(self.annualized_return, 4),
            "average_daily_return": round(self.average_daily_return, 6),
            "volatility": round(self.volatility, 4),
            "annualized_volatility": round(self.annualized_volatility, 4),
            "downside_volatility": round(self.downside_volatility, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "sortino_ratio": round(self.sortino_ratio, 4),
            "calmar_ratio": round(self.calmar_ratio, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "max_drawdown_duration": self.max_drawdown_duration,
            "current_drawdown": round(self.current_drawdown, 4),
            "beta": round(self.beta, 4) if self.beta is not None else None,
            "alpha": round(self.alpha, 4) if self.alpha is not None else None,
            "win_rate": round(self.win_rate, 4),
            "profit_factor": round(self.profit_factor, 4),
            "trading_days": self.trading_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }

    def format_report(self) -> str:
        """Format as a readable report."""
        lines = [
            "=" * 50,
            "RISK METRICS REPORT",
            "=" * 50,
            "",
            "RETURNS",
            f"  Total Return:        {self.total_return:>10.2%}",
            f"  Annualized Return:   {self.annualized_return:>10.2%}",
            f"  Avg Daily Return:    {self.average_daily_return:>10.4%}",
            "",
            "VOLATILITY",
            f"  Daily Volatility:    {self.volatility:>10.2%}",
            f"  Annual Volatility:   {self.annualized_volatility:>10.2%}",
            f"  Downside Volatility: {self.downside_volatility:>10.2%}",
            "",
            "RISK-ADJUSTED RETURNS",
            f"  Sharpe Ratio:        {self.sharpe_ratio:>10.2f}",
            f"  Sortino Ratio:       {self.sortino_ratio:>10.2f}",
            f"  Calmar Ratio:        {self.calmar_ratio:>10.2f}",
            "",
            "DRAWDOWN",
            f"  Max Drawdown:        {self.max_drawdown:>10.2%}",
            f"  Max DD Duration:     {self.max_drawdown_duration:>10d} days",
            f"  Current Drawdown:    {self.current_drawdown:>10.2%}",
            "",
            "OTHER METRICS",
            f"  Win Rate:            {self.win_rate:>10.2%}",
            f"  Profit Factor:       {self.profit_factor:>10.2f}",
        ]

        if self.beta is not None:
            lines.append(f"  Beta:                {self.beta:>10.2f}")
        if self.alpha is not None:
            lines.append(f"  Alpha:               {self.alpha:>10.2%}")

        lines.extend([
            "",
            f"Period: {self.trading_days} trading days",
            "=" * 50,
        ])

        return "\n".join(lines)


class RiskCalculator:
    """
    Calculates risk metrics from returns data.

    Supports daily returns series and optional benchmark comparison.
    """

    TRADING_DAYS_PER_YEAR = 252

    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize the calculator.

        Args:
            risk_free_rate: Annual risk-free rate (e.g., 0.05 for 5%).
        """
        self.risk_free_rate = risk_free_rate
        self._daily_rf_rate = risk_free_rate / self.TRADING_DAYS_PER_YEAR

    def calculate(
        self,
        returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
        prices: Optional[List[float]] = None,
    ) -> RiskMetrics:
        """
        Calculate all risk metrics from returns.

        Args:
            returns: List of daily returns (e.g., [0.01, -0.02, 0.015]).
            benchmark_returns: Optional benchmark returns for beta/alpha.
            prices: Optional price series (for drawdown if not using returns).

        Returns:
            RiskMetrics with all calculated values.
        """
        if not returns:
            return RiskMetrics()

        metrics = RiskMetrics(trading_days=len(returns))

        # Calculate return metrics
        metrics.total_return = self._calculate_total_return(returns)
        metrics.average_daily_return = self._calculate_mean(returns)
        metrics.annualized_return = self._annualize_return(metrics.average_daily_return)

        # Calculate volatility metrics
        metrics.volatility = self._calculate_std(returns)
        metrics.annualized_volatility = self._annualize_volatility(metrics.volatility)
        metrics.downside_volatility = self._calculate_downside_volatility(returns)

        # Calculate risk-adjusted returns
        metrics.sharpe_ratio = self._calculate_sharpe(
            metrics.annualized_return,
            metrics.annualized_volatility,
        )
        metrics.sortino_ratio = self._calculate_sortino(
            metrics.annualized_return,
            metrics.downside_volatility,
        )

        # Calculate drawdown metrics
        if prices:
            dd_metrics = self._calculate_drawdown_from_prices(prices)
        else:
            dd_metrics = self._calculate_drawdown_from_returns(returns)

        metrics.max_drawdown = dd_metrics[0]
        metrics.max_drawdown_duration = dd_metrics[1]
        metrics.current_drawdown = dd_metrics[2]

        # Calmar ratio
        metrics.calmar_ratio = self._calculate_calmar(
            metrics.annualized_return,
            metrics.max_drawdown,
        )

        # Win rate and profit factor
        metrics.win_rate = self._calculate_win_rate(returns)
        metrics.profit_factor = self._calculate_profit_factor(returns)

        # Beta and Alpha (if benchmark provided)
        if benchmark_returns and len(benchmark_returns) == len(returns):
            metrics.beta = self._calculate_beta(returns, benchmark_returns)
            metrics.alpha = self._calculate_alpha(
                returns,
                benchmark_returns,
                metrics.beta,
            )

        return metrics

    def _calculate_total_return(self, returns: List[float]) -> float:
        """Calculate cumulative return."""
        cumulative = 1.0
        for r in returns:
            cumulative *= (1 + r)
        return cumulative - 1

    def _calculate_mean(self, values: List[float]) -> float:
        """Calculate mean."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = self._calculate_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _annualize_return(self, daily_return: float) -> float:
        """Annualize daily return."""
        return (1 + daily_return) ** self.TRADING_DAYS_PER_YEAR - 1

    def _annualize_volatility(self, daily_vol: float) -> float:
        """Annualize daily volatility."""
        return daily_vol * math.sqrt(self.TRADING_DAYS_PER_YEAR)

    def _calculate_downside_volatility(self, returns: List[float]) -> float:
        """Calculate downside volatility (only negative returns)."""
        negative_returns = [r for r in returns if r < self._daily_rf_rate]
        if len(negative_returns) < 2:
            return 0.0

        mean = self._daily_rf_rate
        variance = sum((r - mean) ** 2 for r in negative_returns) / len(negative_returns)
        return math.sqrt(variance) * math.sqrt(self.TRADING_DAYS_PER_YEAR)

    def _calculate_sharpe(
        self,
        annualized_return: float,
        annualized_volatility: float,
    ) -> float:
        """Calculate Sharpe ratio."""
        if annualized_volatility == 0:
            return 0.0
        return (annualized_return - self.risk_free_rate) / annualized_volatility

    def _calculate_sortino(
        self,
        annualized_return: float,
        downside_volatility: float,
    ) -> float:
        """Calculate Sortino ratio."""
        if downside_volatility == 0:
            return 0.0
        return (annualized_return - self.risk_free_rate) / downside_volatility

    def _calculate_calmar(
        self,
        annualized_return: float,
        max_drawdown: float,
    ) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / abs(max_drawdown)

    def _calculate_drawdown_from_returns(
        self,
        returns: List[float],
    ) -> Tuple[float, int, float]:
        """Calculate drawdown metrics from returns."""
        # Convert returns to price series
        prices = [1.0]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        return self._calculate_drawdown_from_prices(prices)

    def _calculate_drawdown_from_prices(
        self,
        prices: List[float],
    ) -> Tuple[float, int, float]:
        """Calculate drawdown metrics from price series."""
        if not prices:
            return 0.0, 0, 0.0

        peak = prices[0]
        max_drawdown = 0.0
        current_drawdown = 0.0
        max_duration = 0
        current_duration = 0
        in_drawdown = False

        for price in prices:
            if price > peak:
                peak = price
                if in_drawdown:
                    max_duration = max(max_duration, current_duration)
                    current_duration = 0
                    in_drawdown = False
            else:
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)
                current_drawdown = drawdown
                in_drawdown = True
                current_duration += 1

        if in_drawdown:
            max_duration = max(max_duration, current_duration)

        return max_drawdown, max_duration, current_drawdown

    def _calculate_win_rate(self, returns: List[float]) -> float:
        """Calculate win rate (percentage of positive returns)."""
        if not returns:
            return 0.0
        wins = sum(1 for r in returns if r > 0)
        return wins / len(returns)

    def _calculate_profit_factor(self, returns: List[float]) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    def _calculate_beta(
        self,
        returns: List[float],
        benchmark_returns: List[float],
    ) -> float:
        """Calculate beta (covariance / variance of benchmark)."""
        if len(returns) < 2:
            return 0.0

        mean_r = self._calculate_mean(returns)
        mean_b = self._calculate_mean(benchmark_returns)

        covariance = sum(
            (r - mean_r) * (b - mean_b)
            for r, b in zip(returns, benchmark_returns)
        ) / (len(returns) - 1)

        variance_b = sum(
            (b - mean_b) ** 2 for b in benchmark_returns
        ) / (len(benchmark_returns) - 1)

        if variance_b == 0:
            return 0.0
        return covariance / variance_b

    def _calculate_alpha(
        self,
        returns: List[float],
        benchmark_returns: List[float],
        beta: float,
    ) -> float:
        """Calculate alpha (Jensen's alpha)."""
        avg_return = self._calculate_mean(returns)
        avg_benchmark = self._calculate_mean(benchmark_returns)

        # Annualize
        annual_return = self._annualize_return(avg_return)
        annual_benchmark = self._annualize_return(avg_benchmark)

        # Alpha = Rp - [Rf + Beta * (Rm - Rf)]
        return annual_return - (self.risk_free_rate + beta * (annual_benchmark - self.risk_free_rate))


# Convenience function
def calculate_risk_metrics(
    returns: List[float],
    benchmark_returns: Optional[List[float]] = None,
    risk_free_rate: float = 0.0,
) -> RiskMetrics:
    """
    Calculate risk metrics from returns.

    Args:
        returns: List of daily returns.
        benchmark_returns: Optional benchmark returns.
        risk_free_rate: Annual risk-free rate.

    Returns:
        RiskMetrics with calculated values.
    """
    calculator = RiskCalculator(risk_free_rate)
    return calculator.calculate(returns, benchmark_returns)
