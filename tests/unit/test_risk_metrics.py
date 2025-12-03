"""Tests for the risk metrics system."""

import pytest
import math

from src.core.quant.risk_metrics import (
    RiskCalculator,
    RiskMetrics,
    calculate_risk_metrics,
)


class TestRiskMetrics:
    """Tests for RiskMetrics class."""

    def test_create_metrics(self):
        """Test creating metrics."""
        metrics = RiskMetrics(
            total_return=0.15,
            sharpe_ratio=1.5,
            max_drawdown=0.10,
        )
        assert metrics.total_return == 0.15
        assert metrics.sharpe_ratio == 1.5

    def test_to_dict(self):
        """Test serialization."""
        metrics = RiskMetrics(
            total_return=0.20,
            annualized_return=0.25,
            sharpe_ratio=2.0,
        )
        data = metrics.to_dict()
        assert data["total_return"] == 0.2
        assert data["sharpe_ratio"] == 2.0

    def test_format_report(self):
        """Test report formatting."""
        metrics = RiskMetrics(
            total_return=0.15,
            annualized_return=0.20,
            volatility=0.01,
            annualized_volatility=0.16,
            sharpe_ratio=1.25,
            max_drawdown=0.08,
            trading_days=252,
        )
        report = metrics.format_report()
        assert "RISK METRICS REPORT" in report
        assert "Sharpe Ratio" in report
        assert "Max Drawdown" in report


class TestRiskCalculator:
    """Tests for RiskCalculator class."""

    def test_empty_returns(self):
        """Test handling empty returns."""
        calc = RiskCalculator()
        metrics = calc.calculate([])
        assert metrics.total_return == 0.0
        assert metrics.trading_days == 0

    def test_total_return(self):
        """Test total return calculation."""
        calc = RiskCalculator()
        # 10% return followed by -5% should give ~4.5%
        returns = [0.10, -0.05]
        metrics = calc.calculate(returns)
        expected = (1.10 * 0.95) - 1  # 0.045
        assert abs(metrics.total_return - expected) < 0.001

    def test_mean_return(self):
        """Test average return calculation."""
        calc = RiskCalculator()
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        metrics = calc.calculate(returns)
        expected_mean = 0.03
        assert abs(metrics.average_daily_return - expected_mean) < 0.001

    def test_volatility(self):
        """Test volatility calculation."""
        calc = RiskCalculator()
        # Returns with known std dev
        returns = [0.01, -0.01, 0.02, -0.02, 0.01]
        metrics = calc.calculate(returns)
        # Should have non-zero volatility
        assert metrics.volatility > 0
        assert metrics.annualized_volatility > metrics.volatility

    def test_sharpe_ratio_positive(self):
        """Test Sharpe ratio with positive returns."""
        calc = RiskCalculator(risk_free_rate=0.02)
        # Consistent positive returns
        returns = [0.001] * 252  # ~28% annualized
        metrics = calc.calculate(returns)
        # Should have positive Sharpe
        assert metrics.sharpe_ratio > 0

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        calc = RiskCalculator()
        returns = [0.0, 0.0, 0.0]
        metrics = calc.calculate(returns)
        assert metrics.sharpe_ratio == 0.0

    def test_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        calc = RiskCalculator()
        # Mix of positive and negative returns
        returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        metrics = calc.calculate(returns)
        # Sortino should be calculated
        assert metrics.sortino_ratio != 0.0 or metrics.downside_volatility == 0.0

    def test_max_drawdown(self):
        """Test max drawdown calculation."""
        calc = RiskCalculator()
        # Clear drawdown pattern: up, then down significantly
        returns = [0.10, 0.05, -0.20, -0.10, 0.05]
        metrics = calc.calculate(returns)
        # Should have significant drawdown
        assert metrics.max_drawdown > 0.20  # At least 20% drawdown

    def test_max_drawdown_from_prices(self):
        """Test drawdown from price series."""
        calc = RiskCalculator()
        # Price goes from 100 to 120 to 90 (25% drawdown from peak)
        prices = [100, 110, 120, 100, 90, 95]
        metrics = calc.calculate([], prices=prices)
        expected_dd = (120 - 90) / 120  # 0.25
        assert abs(metrics.max_drawdown - expected_dd) < 0.01

    def test_win_rate(self):
        """Test win rate calculation."""
        calc = RiskCalculator()
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]  # 3 wins, 2 losses
        metrics = calc.calculate(returns)
        assert abs(metrics.win_rate - 0.6) < 0.01

    def test_profit_factor(self):
        """Test profit factor calculation."""
        calc = RiskCalculator()
        returns = [0.10, -0.05]  # Profit: 0.10, Loss: 0.05
        metrics = calc.calculate(returns)
        expected = 0.10 / 0.05  # 2.0
        assert abs(metrics.profit_factor - expected) < 0.01

    def test_profit_factor_no_losses(self):
        """Test profit factor with no losses."""
        calc = RiskCalculator()
        returns = [0.01, 0.02, 0.03]
        metrics = calc.calculate(returns)
        assert metrics.profit_factor == float('inf')

    def test_beta_calculation(self):
        """Test beta calculation with benchmark."""
        calc = RiskCalculator()
        # Returns that move with benchmark
        returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        benchmark = [0.01, -0.005, 0.015, -0.01, 0.005]
        metrics = calc.calculate(returns, benchmark_returns=benchmark)
        # Beta should be positive (returns move with benchmark)
        assert metrics.beta is not None
        assert metrics.beta > 0

    def test_alpha_calculation(self):
        """Test alpha calculation with benchmark."""
        calc = RiskCalculator(risk_free_rate=0.02)
        # Returns that outperform benchmark
        returns = [0.02, 0.02, 0.02]  # Consistent 2% daily
        benchmark = [0.01, 0.01, 0.01]  # Consistent 1% daily
        metrics = calc.calculate(returns, benchmark_returns=benchmark)
        # Alpha should be positive (outperformance)
        assert metrics.alpha is not None

    def test_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        calc = RiskCalculator()
        returns = [0.001] * 200 + [-0.10, -0.05]  # Good returns then drawdown
        metrics = calc.calculate(returns)
        # Calmar ratio should exist
        assert metrics.calmar_ratio != 0.0 or metrics.max_drawdown == 0.0

    def test_drawdown_duration(self):
        """Test max drawdown duration tracking."""
        calc = RiskCalculator()
        # Extended drawdown period
        returns = [0.05] + [-0.02] * 10 + [0.10]  # 10 days of losses
        metrics = calc.calculate(returns)
        # Should track duration
        assert metrics.max_drawdown_duration >= 10

    def test_current_drawdown(self):
        """Test current drawdown at end of series."""
        calc = RiskCalculator()
        # End in a drawdown
        returns = [0.10, 0.05, -0.10, -0.05]
        metrics = calc.calculate(returns)
        # Should have current drawdown > 0
        assert metrics.current_drawdown > 0


class TestConvenienceFunction:
    """Tests for calculate_risk_metrics function."""

    def test_basic_calculation(self):
        """Test basic calculation."""
        returns = [0.01, -0.005, 0.02, -0.01, 0.015]
        metrics = calculate_risk_metrics(returns)

        assert metrics.trading_days == 5
        assert metrics.total_return != 0
        assert metrics.sharpe_ratio is not None

    def test_with_benchmark(self):
        """Test calculation with benchmark."""
        returns = [0.02, 0.01, 0.03]
        benchmark = [0.01, 0.005, 0.015]

        metrics = calculate_risk_metrics(
            returns,
            benchmark_returns=benchmark,
        )

        assert metrics.beta is not None
        assert metrics.alpha is not None

    def test_with_risk_free_rate(self):
        """Test calculation with risk-free rate."""
        returns = [0.01] * 10

        metrics_no_rf = calculate_risk_metrics(returns, risk_free_rate=0.0)
        metrics_with_rf = calculate_risk_metrics(returns, risk_free_rate=0.05)

        # Sharpe should be lower with risk-free rate
        assert metrics_with_rf.sharpe_ratio < metrics_no_rf.sharpe_ratio


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_return(self):
        """Test with single return."""
        calc = RiskCalculator()
        metrics = calc.calculate([0.05])

        assert metrics.total_return == 0.05
        assert metrics.volatility == 0.0  # Can't calculate with single point

    def test_all_zero_returns(self):
        """Test with all zero returns."""
        calc = RiskCalculator()
        metrics = calc.calculate([0.0, 0.0, 0.0])

        assert metrics.total_return == 0.0
        assert metrics.volatility == 0.0
        assert metrics.sharpe_ratio == 0.0

    def test_all_positive_returns(self):
        """Test with all positive returns."""
        calc = RiskCalculator()
        metrics = calc.calculate([0.01, 0.02, 0.01, 0.03, 0.02])

        assert metrics.win_rate == 1.0
        assert metrics.max_drawdown == 0.0
        assert metrics.profit_factor == float('inf')

    def test_all_negative_returns(self):
        """Test with all negative returns."""
        calc = RiskCalculator()
        metrics = calc.calculate([-0.01, -0.02, -0.01])

        assert metrics.win_rate == 0.0
        assert metrics.total_return < 0
        assert metrics.profit_factor == 0.0

    def test_large_returns(self):
        """Test with large returns (no overflow)."""
        calc = RiskCalculator()
        # 100% gains and 50% losses
        returns = [1.0, -0.5, 0.5, -0.3]
        metrics = calc.calculate(returns)

        assert math.isfinite(metrics.total_return)
        assert math.isfinite(metrics.sharpe_ratio)
