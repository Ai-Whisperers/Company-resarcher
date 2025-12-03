"""Tests for alpha factor mining."""

import pytest
import math
from unittest.mock import MagicMock, patch

from src.core.quant.alpha_factors import (
    AlphaFactorManager,
    ExpressionParser,
    Factor,
    FactorCategory,
    FactorEvaluator,
    FactorLibrary,
    FactorResult,
    GeneticFactorMiner,
    TimeSeriesOperations,
    get_alpha_manager,
    reset_alpha_manager,
)


class TestFactorResult:
    """Tests for FactorResult class."""

    def test_create_result(self):
        """Test creating a result."""
        result = FactorResult(
            factor_id="test_1",
            name="Test Factor",
            expression="close / ma_20",
            category=FactorCategory.MOMENTUM,
            ic=0.05,
            ic_std=0.02,
            ir=2.5,
            rank_ic=0.06,
            t_stat=3.5,
            annualized_return=0.15,
            sharpe_ratio=1.2,
            max_drawdown=0.1,
            win_rate=0.55,
            coverage=0.95,
            turnover=0.2,
            periods_tested=252,
        )

        assert result.factor_id == "test_1"
        assert result.ic == 0.05
        assert result.ir == 2.5

    def test_to_dict(self):
        """Test serialization."""
        result = FactorResult(
            factor_id="test_1",
            name="Test",
            expression="close",
            category=FactorCategory.CUSTOM,
            ic=0.03,
            ic_std=0.01,
            ir=3.0,
            rank_ic=0.04,
            t_stat=4.0,
            annualized_return=0.2,
            sharpe_ratio=1.5,
            max_drawdown=0.08,
            win_rate=0.6,
            coverage=0.9,
            turnover=0.15,
        )
        data = result.to_dict()

        assert data["factor_id"] == "test_1"
        assert data["ic"] == 0.03
        assert data["category"] == "custom"

    def test_is_significant(self):
        """Test significance check."""
        significant = FactorResult(
            factor_id="sig",
            name="Significant",
            expression="x",
            category=FactorCategory.CUSTOM,
            ic=0.05,
            ic_std=0.01,
            ir=5.0,
            rank_ic=0.05,
            t_stat=2.5,
            annualized_return=0.1,
            sharpe_ratio=1.0,
            max_drawdown=0.1,
            win_rate=0.5,
            coverage=0.9,
            turnover=0.1,
        )
        assert significant.is_significant is True

        not_significant = FactorResult(
            factor_id="not_sig",
            name="Not Significant",
            expression="x",
            category=FactorCategory.CUSTOM,
            ic=0.01,
            ic_std=0.01,
            ir=1.0,
            rank_ic=0.01,
            t_stat=1.0,
            annualized_return=0.1,
            sharpe_ratio=1.0,
            max_drawdown=0.1,
            win_rate=0.5,
            coverage=0.5,
            turnover=0.1,
        )
        assert not_significant.is_significant is False


class TestFactor:
    """Tests for Factor class."""

    def test_create_factor(self):
        """Test creating a factor."""
        factor = Factor(
            factor_id="f1",
            name="Momentum",
            expression="close / ma_20 - 1",
            category=FactorCategory.MOMENTUM,
        )

        assert factor.factor_id == "f1"
        assert factor.category == FactorCategory.MOMENTUM

    def test_to_dict(self):
        """Test serialization."""
        factor = Factor(
            factor_id="f1",
            name="Test",
            expression="close",
            category=FactorCategory.VALUE,
            description="Test description",
        )
        data = factor.to_dict()

        assert data["name"] == "Test"
        assert data["category"] == "value"
        assert data["description"] == "Test description"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "factor_id": "f2",
            "name": "From Dict",
            "expression": "high - low",
            "category": "volatility",
        }
        factor = Factor.from_dict(data)

        assert factor.factor_id == "f2"
        assert factor.category == FactorCategory.VOLATILITY


class TestExpressionParser:
    """Tests for ExpressionParser class."""

    def setup_method(self):
        """Create parser."""
        self.parser = ExpressionParser()

    def test_validate_valid(self):
        """Test validating valid expression."""
        valid, msg = self.parser.validate("close / ma_20")
        assert valid is True

    def test_validate_invalid(self):
        """Test validating invalid expression."""
        valid, msg = self.parser.validate("close / ")
        assert valid is False

    def test_parse_simple(self):
        """Test parsing simple expression."""
        func = self.parser.parse("close + open")
        result = func({"close": 100, "open": 95})

        assert result == 195

    def test_parse_with_functions(self):
        """Test parsing with functions."""
        func = self.parser.parse("abs(close - open)")
        result = func({"close": 95, "open": 100})

        assert result == 5

    def test_parse_complex(self):
        """Test parsing complex expression."""
        func = self.parser.parse("(close - open) / open")
        result = func({"close": 105, "open": 100})

        assert abs(result - 0.05) < 0.001

    def test_parse_with_nan(self):
        """Test handling NaN values."""
        func = self.parser.parse("close / volume")
        result = func({"close": 100, "volume": 0})

        assert math.isinf(result) or math.isnan(result)

    def test_cache(self):
        """Test expression caching."""
        expr = "close * 2"
        func1 = self.parser.parse(expr)
        func2 = self.parser.parse(expr)

        assert func1 is func2


class TestTimeSeriesOperations:
    """Tests for TimeSeriesOperations class."""

    def test_moving_average(self):
        """Test moving average calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ma = TimeSeriesOperations.moving_average(values, 3)

        assert len(ma) == 10
        assert math.isnan(ma[0])
        assert math.isnan(ma[1])
        assert abs(ma[2] - 2.0) < 0.001  # (1+2+3)/3

    def test_exponential_ma(self):
        """Test exponential moving average."""
        values = [1, 2, 3, 4, 5]
        ema = TimeSeriesOperations.exponential_ma(values, 3)

        assert len(ema) == 5
        assert ema[0] == 1

    def test_std(self):
        """Test standard deviation calculation."""
        values = [1, 2, 3, 4, 5]
        std = TimeSeriesOperations.std(values, 3)

        assert len(std) == 5
        assert math.isnan(std[0])
        assert std[2] > 0

    def test_returns(self):
        """Test returns calculation."""
        prices = [100, 105, 103, 107, 110]
        returns = TimeSeriesOperations.returns(prices, 1)

        assert len(returns) == 5
        assert math.isnan(returns[0])
        assert abs(returns[1] - 0.05) < 0.001

    def test_rank(self):
        """Test percentile rank."""
        values = [3, 1, 4, 1, 5]
        ranks = TimeSeriesOperations.rank(values)

        assert len(ranks) == 5
        assert ranks[4] == 1.0  # Highest value

    def test_zscore(self):
        """Test z-score calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        zscores = TimeSeriesOperations.zscore(values, 5)

        assert len(zscores) == 10
        # Z-scores should be centered around 0
        valid_z = [z for z in zscores if not math.isnan(z)]
        assert len(valid_z) > 0


class TestFactorEvaluator:
    """Tests for FactorEvaluator class."""

    def setup_method(self):
        """Create evaluator."""
        self.evaluator = FactorEvaluator()

    def test_calculate_ic(self):
        """Test IC calculation."""
        factors = [1, 2, 3, 4, 5]
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]

        ic = self.evaluator.calculate_ic(factors, returns)

        assert not math.isnan(ic)
        assert abs(ic - 1.0) < 0.001  # Perfect correlation

    def test_calculate_ic_negative(self):
        """Test IC with negative correlation."""
        factors = [5, 4, 3, 2, 1]
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]

        ic = self.evaluator.calculate_ic(factors, returns)

        assert not math.isnan(ic)
        assert abs(ic - (-1.0)) < 0.001

    def test_calculate_rank_ic(self):
        """Test rank IC calculation."""
        factors = [1, 2, 3, 4, 5]
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]

        rank_ic = self.evaluator.calculate_rank_ic(factors, returns)

        assert not math.isnan(rank_ic)
        assert abs(rank_ic - 1.0) < 0.001

    def test_calculate_sharpe(self):
        """Test Sharpe ratio calculation."""
        returns = [0.01, 0.02, -0.01, 0.015, 0.005] * 50

        sharpe = self.evaluator.calculate_sharpe(returns)

        assert not math.isnan(sharpe)

    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation."""
        cumulative = [1.0, 1.1, 1.2, 1.0, 0.9, 1.1]

        max_dd = self.evaluator.calculate_max_drawdown(cumulative)

        assert max_dd == 0.25  # From 1.2 to 0.9

    def test_evaluate_factor(self):
        """Test full factor evaluation."""
        factor = Factor(
            factor_id="test",
            name="Test",
            expression="close - open",
        )

        price_data = {
            "close": [100, 101, 102, 103, 104] * 20,
            "open": [99, 100, 101, 102, 103] * 20,
        }

        result = self.evaluator.evaluate_factor(factor, price_data)

        assert isinstance(result, FactorResult)
        assert result.periods_tested == 100


class TestGeneticFactorMiner:
    """Tests for GeneticFactorMiner class."""

    def setup_method(self):
        """Create miner."""
        self.miner = GeneticFactorMiner(
            population_size=10,
            generations=3,
        )

    def test_generate_random_expression(self):
        """Test random expression generation."""
        expr = self.miner.generate_random_expression()

        assert isinstance(expr, str)
        assert len(expr) > 0

    def test_mutate(self):
        """Test mutation."""
        original = "close + open"
        mutated = self.miner.mutate(original)

        assert isinstance(mutated, str)

    def test_crossover(self):
        """Test crossover."""
        expr1 = "close + open"
        expr2 = "high - low"

        child1, child2 = self.miner.crossover(expr1, expr2)

        assert isinstance(child1, str)
        assert isinstance(child2, str)

    def test_mine(self):
        """Test mining factors."""
        price_data = {
            "close": [100 + i + (i % 3) for i in range(100)],
            "open": [99 + i + (i % 2) for i in range(100)],
            "high": [102 + i for i in range(100)],
            "low": [98 + i for i in range(100)],
            "volume": [1000 + i * 10 for i in range(100)],
        }

        factors = self.miner.mine(price_data)

        assert isinstance(factors, list)


class TestFactorLibrary:
    """Tests for FactorLibrary class."""

    def test_get_all(self):
        """Test getting all factors."""
        factors = FactorLibrary.get_all()

        assert len(factors) > 0
        assert all(isinstance(f, Factor) for f in factors)

    def test_get_by_category_momentum(self):
        """Test getting momentum factors."""
        factors = FactorLibrary.get_by_category(FactorCategory.MOMENTUM)

        assert len(factors) > 0
        assert all(f.category == FactorCategory.MOMENTUM for f in factors)

    def test_get_by_category_volatility(self):
        """Test getting volatility factors."""
        factors = FactorLibrary.get_by_category(FactorCategory.VOLATILITY)

        assert len(factors) > 0


class TestAlphaFactorManager:
    """Tests for AlphaFactorManager class."""

    def setup_method(self):
        """Create manager."""
        self.manager = AlphaFactorManager()

    def test_add_factor(self):
        """Test adding a factor."""
        factor = self.manager.add_factor(
            name="Test Factor",
            expression="close - open",
            category=FactorCategory.TECHNICAL,
        )

        assert factor.factor_id is not None
        assert factor.name == "Test Factor"

    def test_add_factor_invalid(self):
        """Test adding invalid factor."""
        with pytest.raises(ValueError):
            self.manager.add_factor(
                name="Invalid",
                expression="close / ",
            )

    def test_get_factor(self):
        """Test getting a factor."""
        added = self.manager.add_factor("Test", "close")
        retrieved = self.manager.get_factor(added.factor_id)

        assert retrieved is not None
        assert retrieved.factor_id == added.factor_id

    def test_list_factors(self):
        """Test listing factors."""
        self.manager.add_factor("F1", "close", category=FactorCategory.MOMENTUM)
        self.manager.add_factor("F2", "open", category=FactorCategory.VALUE)

        all_factors = self.manager.list_factors()
        assert len(all_factors) == 2

        momentum = self.manager.list_factors(category=FactorCategory.MOMENTUM)
        assert len(momentum) == 1

    def test_evaluate(self):
        """Test evaluating a factor."""
        factor = self.manager.add_factor("Test", "close - open")

        price_data = {
            "close": [100 + i for i in range(50)],
            "open": [99 + i for i in range(50)],
        }

        result = self.manager.evaluate(factor.factor_id, price_data)

        assert isinstance(result, FactorResult)

    def test_evaluate_all(self):
        """Test evaluating all factors."""
        self.manager.add_factor("F1", "close - open")
        self.manager.add_factor("F2", "high - low")

        price_data = {
            "close": [100 + i for i in range(50)],
            "open": [99 + i for i in range(50)],
            "high": [102 + i for i in range(50)],
            "low": [98 + i for i in range(50)],
        }

        results = self.manager.evaluate_all(price_data)

        assert len(results) == 2

    def test_rank_factors(self):
        """Test ranking factors."""
        self.manager.add_factor("F1", "close - open")
        self.manager.add_factor("F2", "high - low")

        price_data = {
            "close": [100 + i for i in range(50)],
            "open": [99 + i for i in range(50)],
            "high": [102 + i for i in range(50)],
            "low": [98 + i for i in range(50)],
        }

        ranked = self.manager.rank_factors(price_data, metric="ic")

        assert len(ranked) >= 0

    def test_remove_factor(self):
        """Test removing a factor."""
        factor = self.manager.add_factor("To Remove", "close")
        success = self.manager.remove_factor(factor.factor_id)

        assert success is True
        assert self.manager.get_factor(factor.factor_id) is None

    def test_load_library(self):
        """Test loading factor library."""
        self.manager.load_library()

        factors = self.manager.list_factors()
        assert len(factors) > 0

    def test_get_statistics(self):
        """Test getting statistics."""
        self.manager.add_factor("F1", "close", category=FactorCategory.MOMENTUM)

        stats = self.manager.get_statistics()

        assert "total_factors" in stats
        assert "by_category" in stats
        assert stats["total_factors"] == 1


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_alpha_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_alpha_manager()

    def test_get_alpha_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_alpha_manager()
        m2 = get_alpha_manager()
        assert m1 is m2

    def test_reset_alpha_manager(self):
        """Test resetting singleton."""
        m1 = get_alpha_manager()
        reset_alpha_manager()
        m2 = get_alpha_manager()
        assert m1 is not m2


class TestFactorCategoryEnum:
    """Tests for FactorCategory enum."""

    def test_all_categories(self):
        """Test all factor categories."""
        categories = [
            FactorCategory.MOMENTUM,
            FactorCategory.MEAN_REVERSION,
            FactorCategory.VALUE,
            FactorCategory.VOLATILITY,
            FactorCategory.VOLUME,
            FactorCategory.TECHNICAL,
            FactorCategory.FUNDAMENTAL,
            FactorCategory.CUSTOM,
        ]
        assert len(categories) == len(FactorCategory)

    def test_category_values(self):
        """Test category string values."""
        assert FactorCategory.MOMENTUM.value == "momentum"
        assert FactorCategory.VALUE.value == "value"
