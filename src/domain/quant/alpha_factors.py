"""Alpha Factor Mining for financial analysis.

This module provides tools for discovering and evaluating alpha factors
(predictive signals) for financial strategies.

Inspired by microsoft/qlib alpha factor mining.
"""

import hashlib
import logging
import math
import random
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.infrastructure.security.safe_eval import SafeExpressionEvaluator, SafeEvalError

logger = logging.getLogger(__name__)


class FactorCategory(str, Enum):
    """Categories of alpha factors."""

    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VALUE = "value"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    CUSTOM = "custom"


@dataclass
class FactorResult:
    """Result of factor evaluation."""

    factor_id: str
    name: str
    expression: str
    category: FactorCategory

    # Performance metrics
    ic: float  # Information Coefficient
    ic_std: float  # IC standard deviation
    ir: float  # Information Ratio (IC / IC_std)
    rank_ic: float  # Rank IC (Spearman)
    t_stat: float  # T-statistic for IC

    # Return metrics
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float

    # Coverage
    coverage: float  # % of periods with valid factor values
    turnover: float  # Factor turnover

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    periods_tested: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "expression": self.expression,
            "category": self.category.value,
            "ic": self.ic,
            "ic_std": self.ic_std,
            "ir": self.ir,
            "rank_ic": self.rank_ic,
            "t_stat": self.t_stat,
            "annualized_return": self.annualized_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "coverage": self.coverage,
            "turnover": self.turnover,
            "periods_tested": self.periods_tested,
            "created_at": self.created_at.isoformat(),
        }

    @property
    def is_significant(self) -> bool:
        """Check if factor is statistically significant."""
        return abs(self.t_stat) > 2.0 and self.coverage > 0.8


@dataclass
class Factor:
    """Represents an alpha factor."""

    factor_id: str
    name: str
    expression: str
    category: FactorCategory = FactorCategory.CUSTOM
    description: str = ""

    # Evaluation results
    result: Optional[FactorResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "expression": self.expression,
            "category": self.category.value,
            "description": self.description,
            "result": self.result.to_dict() if self.result else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Factor":
        """Deserialize from dictionary."""
        return cls(
            factor_id=data["factor_id"],
            name=data["name"],
            expression=data["expression"],
            category=FactorCategory(data.get("category", "custom")),
            description=data.get("description", ""),
        )


class ExpressionParser:
    """Parse and evaluate factor expressions safely using AST parsing.

    This class uses SafeExpressionEvaluator to prevent code injection attacks
    while still supporting mathematical expressions for alpha factor calculations.
    """

    FUNCTIONS = {
        'abs': abs,
        'log': math.log,
        'exp': math.exp,
        'sqrt': math.sqrt,
        'sign': lambda x: 1 if x > 0 else (-1 if x < 0 else 0),
        'max': max,
        'min': min,
    }

    def __init__(self):
        """Initialize parser with safe expression evaluator."""
        self._cache: Dict[str, Callable] = {}
        self._evaluator = SafeExpressionEvaluator(
            additional_functions=self.FUNCTIONS
        )

    def parse(self, expression: str) -> Callable:
        """Parse expression into callable function."""
        if expression in self._cache:
            return self._cache[expression]

        func = self._compile(expression)
        self._cache[expression] = func
        return func

    def _compile(self, expression: str) -> Callable:
        """Compile expression to function using safe evaluation."""
        safe_expr = self._sanitize(expression)
        evaluator = self._evaluator

        def evaluate(data: Dict[str, float]) -> float:
            try:
                return evaluator.evaluate(safe_expr, data)
            except SafeEvalError:
                return float('nan')
            except Exception:
                return float('nan')

        return evaluate

    def _sanitize(self, expression: str) -> str:
        """Sanitize expression for safe evaluation."""
        expression = re.sub(r'[^\w\s+\-*/^().,]', '', expression)
        expression = expression.replace('^', '**')
        return expression

    def validate(self, expression: str) -> Tuple[bool, str]:
        """Validate expression syntax using safe evaluator."""
        try:
            safe_expr = self._sanitize(expression)
            return self._evaluator.validate(safe_expr)
        except Exception as e:
            return False, f"Validation error: {e}"


class TimeSeriesOperations:
    """Time series operations for factor calculation."""

    @staticmethod
    def moving_average(values: List[float], window: int) -> List[float]:
        """Calculate moving average."""
        if len(values) < window:
            return [float('nan')] * len(values)

        result = [float('nan')] * (window - 1)
        for i in range(window - 1, len(values)):
            window_values = values[i - window + 1:i + 1]
            valid = [v for v in window_values if not math.isnan(v)]
            if valid:
                result.append(sum(valid) / len(valid))
            else:
                result.append(float('nan'))

        return result

    @staticmethod
    def exponential_ma(values: List[float], span: int) -> List[float]:
        """Calculate exponential moving average."""
        if not values:
            return []

        alpha = 2.0 / (span + 1)
        result = [values[0]]

        for i in range(1, len(values)):
            if math.isnan(values[i]):
                result.append(result[-1])
            else:
                result.append(alpha * values[i] + (1 - alpha) * result[-1])

        return result

    @staticmethod
    def std(values: List[float], window: int) -> List[float]:
        """Calculate rolling standard deviation."""
        if len(values) < window:
            return [float('nan')] * len(values)

        result = [float('nan')] * (window - 1)
        for i in range(window - 1, len(values)):
            window_values = values[i - window + 1:i + 1]
            valid = [v for v in window_values if not math.isnan(v)]
            if len(valid) >= 2:
                mean = sum(valid) / len(valid)
                variance = sum((v - mean) ** 2 for v in valid) / len(valid)
                result.append(math.sqrt(variance))
            else:
                result.append(float('nan'))

        return result

    @staticmethod
    def returns(prices: List[float], periods: int = 1) -> List[float]:
        """Calculate returns."""
        result = [float('nan')] * periods

        for i in range(periods, len(prices)):
            if prices[i - periods] != 0 and not math.isnan(prices[i - periods]):
                result.append((prices[i] - prices[i - periods]) / prices[i - periods])
            else:
                result.append(float('nan'))

        return result

    @staticmethod
    def rank(values: List[float]) -> List[float]:
        """Calculate percentile rank."""
        valid_indices = [(i, v) for i, v in enumerate(values) if not math.isnan(v)]
        sorted_indices = sorted(valid_indices, key=lambda x: x[1])

        result = [float('nan')] * len(values)
        n = len(sorted_indices)

        for rank, (idx, _) in enumerate(sorted_indices):
            result[idx] = (rank + 1) / n

        return result

    @staticmethod
    def zscore(values: List[float], window: int) -> List[float]:
        """Calculate rolling z-score."""
        ma = TimeSeriesOperations.moving_average(values, window)
        std_values = TimeSeriesOperations.std(values, window)

        result = []
        for i, (v, m, s) in enumerate(zip(values, ma, std_values)):
            if math.isnan(v) or math.isnan(m) or math.isnan(s) or s == 0:
                result.append(float('nan'))
            else:
                result.append((v - m) / s)

        return result


class FactorEvaluator:
    """Evaluate alpha factors."""

    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize evaluator."""
        self.risk_free_rate = risk_free_rate

    def calculate_ic(
        self,
        factor_values: List[float],
        forward_returns: List[float],
    ) -> float:
        """Calculate Information Coefficient (Pearson correlation)."""
        pairs = [
            (f, r) for f, r in zip(factor_values, forward_returns)
            if not math.isnan(f) and not math.isnan(r)
        ]

        if len(pairs) < 3:
            return float('nan')

        factors, returns = zip(*pairs)
        return self._pearson_correlation(list(factors), list(returns))

    def calculate_rank_ic(
        self,
        factor_values: List[float],
        forward_returns: List[float],
    ) -> float:
        """Calculate Rank IC (Spearman correlation)."""
        pairs = [
            (f, r) for f, r in zip(factor_values, forward_returns)
            if not math.isnan(f) and not math.isnan(r)
        ]

        if len(pairs) < 3:
            return float('nan')

        factors, returns = zip(*pairs)
        factor_ranks = TimeSeriesOperations.rank(list(factors))
        return_ranks = TimeSeriesOperations.rank(list(returns))

        return self._pearson_correlation(factor_ranks, return_ranks)

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n < 3:
            return float('nan')

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)

        if std_x == 0 or std_y == 0:
            return float('nan')

        return cov / (std_x * std_y)

    def calculate_sharpe(
        self,
        returns: List[float],
        periods_per_year: int = 252,
    ) -> float:
        """Calculate Sharpe ratio."""
        valid_returns = [r for r in returns if not math.isnan(r)]

        if len(valid_returns) < 2:
            return float('nan')

        mean_return = sum(valid_returns) / len(valid_returns)
        std_return = math.sqrt(
            sum((r - mean_return) ** 2 for r in valid_returns) / len(valid_returns)
        )

        if std_return == 0:
            return float('nan')

        annualized_return = mean_return * periods_per_year
        annualized_std = std_return * math.sqrt(periods_per_year)

        return (annualized_return - self.risk_free_rate) / annualized_std

    def calculate_max_drawdown(self, cumulative_returns: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not cumulative_returns:
            return 0.0

        peak = cumulative_returns[0]
        max_dd = 0.0

        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak != 0 else 0
            max_dd = max(max_dd, drawdown)

        return max_dd

    def evaluate_factor(
        self,
        factor: Factor,
        price_data: Dict[str, List[float]],
        forward_periods: int = 1,
    ) -> FactorResult:
        """Evaluate a factor on price data."""
        parser = ExpressionParser()
        func = parser.parse(factor.expression)

        n_periods = len(next(iter(price_data.values())))

        factor_values = []
        for i in range(n_periods):
            data_point = {k: v[i] for k, v in price_data.items()}
            factor_values.append(func(data_point))

        if "close" in price_data:
            forward_returns = TimeSeriesOperations.returns(
                price_data["close"], forward_periods
            )
            forward_returns = forward_returns[forward_periods:] + [float('nan')] * forward_periods
        else:
            forward_returns = [float('nan')] * n_periods

        ic_values = []
        window_size = 20

        for i in range(window_size, n_periods - forward_periods):
            window_factors = factor_values[i - window_size:i]
            window_returns = forward_returns[i - window_size:i]
            ic = self.calculate_ic(window_factors, window_returns)
            if not math.isnan(ic):
                ic_values.append(ic)

        if ic_values:
            mean_ic = sum(ic_values) / len(ic_values)
            ic_std = math.sqrt(sum((ic - mean_ic) ** 2 for ic in ic_values) / len(ic_values))
            ir = mean_ic / ic_std if ic_std > 0 else float('nan')
            t_stat = mean_ic * math.sqrt(len(ic_values)) / ic_std if ic_std > 0 else float('nan')
        else:
            mean_ic = float('nan')
            ic_std = float('nan')
            ir = float('nan')
            t_stat = float('nan')

        rank_ic = self.calculate_rank_ic(factor_values, forward_returns)

        valid_count = sum(1 for v in factor_values if not math.isnan(v))
        coverage = valid_count / n_periods if n_periods > 0 else 0.0

        factor_returns = self._calculate_factor_returns(
            factor_values, forward_returns, n_periods
        )

        cumulative_returns = []
        cum = 1.0
        for r in factor_returns:
            if not math.isnan(r):
                cum *= (1 + r)
            cumulative_returns.append(cum)

        valid_factor_returns = [r for r in factor_returns if not math.isnan(r)]
        annualized_return = (
            sum(valid_factor_returns) / len(valid_factor_returns) * 252
            if valid_factor_returns else float('nan')
        )

        sharpe = self.calculate_sharpe(factor_returns)
        max_dd = self.calculate_max_drawdown(cumulative_returns)

        win_count = sum(1 for r in valid_factor_returns if r > 0)
        win_rate = win_count / len(valid_factor_returns) if valid_factor_returns else 0.0

        turnover = self._calculate_turnover(factor_values)

        return FactorResult(
            factor_id=factor.factor_id,
            name=factor.name,
            expression=factor.expression,
            category=factor.category,
            ic=mean_ic,
            ic_std=ic_std,
            ir=ir,
            rank_ic=rank_ic,
            t_stat=t_stat,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            coverage=coverage,
            turnover=turnover,
            periods_tested=n_periods,
        )

    def _calculate_factor_returns(
        self,
        factor_values: List[float],
        forward_returns: List[float],
        n_periods: int,
    ) -> List[float]:
        """Calculate returns from factor signals."""
        returns = []

        for i in range(n_periods):
            if math.isnan(factor_values[i]) or math.isnan(forward_returns[i]):
                returns.append(float('nan'))
            else:
                signal = 1 if factor_values[i] > 0 else -1
                returns.append(signal * forward_returns[i])

        return returns

    def _calculate_turnover(self, factor_values: List[float]) -> float:
        """Calculate factor turnover."""
        changes = 0
        prev_signal = None

        for v in factor_values:
            if math.isnan(v):
                continue

            signal = 1 if v > 0 else -1
            if prev_signal is not None and signal != prev_signal:
                changes += 1
            prev_signal = signal

        valid_count = sum(1 for v in factor_values if not math.isnan(v))
        return changes / valid_count if valid_count > 1 else 0.0


class GeneticFactorMiner:
    """Mine alpha factors using genetic programming."""

    OPERATORS = ['+', '-', '*', '/']
    FEATURES = ['open', 'high', 'low', 'close', 'volume']
    FUNCTIONS = ['abs', 'log', 'sqrt', 'sign']
    WINDOWS = [5, 10, 20, 50]

    def __init__(
        self,
        population_size: int = 100,
        generations: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
    ):
        """Initialize genetic miner."""
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.evaluator = FactorEvaluator()

    def generate_random_expression(self, depth: int = 3) -> str:
        """Generate random factor expression."""
        if depth <= 1 or random.random() < 0.3:
            feature = random.choice(self.FEATURES)
            if random.random() < 0.3:
                func = random.choice(self.FUNCTIONS)
                return f"{func}({feature})"
            return feature

        op = random.choice(self.OPERATORS)
        left = self.generate_random_expression(depth - 1)
        right = self.generate_random_expression(depth - 1)

        if random.random() < 0.2:
            func = random.choice(self.FUNCTIONS)
            return f"{func}(({left}) {op} ({right}))"

        return f"(({left}) {op} ({right}))"

    def mutate(self, expression: str) -> str:
        """Mutate an expression."""
        if random.random() < 0.5:
            for feature in self.FEATURES:
                if feature in expression:
                    new_feature = random.choice(self.FEATURES)
                    expression = expression.replace(feature, new_feature, 1)
                    break

        if random.random() < 0.3:
            for op in self.OPERATORS:
                if op in expression:
                    new_op = random.choice(self.OPERATORS)
                    expression = expression.replace(op, new_op, 1)
                    break

        return expression

    def crossover(self, expr1: str, expr2: str) -> Tuple[str, str]:
        """Crossover two expressions."""
        parts1 = re.split(r'(\+|\-|\*|/)', expr1)
        parts2 = re.split(r'(\+|\-|\*|/)', expr2)

        if len(parts1) > 1 and len(parts2) > 1:
            idx1 = random.randint(0, len(parts1) - 1)
            idx2 = random.randint(0, len(parts2) - 1)

            new_parts1 = parts1[:idx1] + parts2[idx2:]
            new_parts2 = parts2[:idx2] + parts1[idx1:]

            return ''.join(new_parts1), ''.join(new_parts2)

        return expr1, expr2

    def mine(
        self,
        price_data: Dict[str, List[float]],
        target_metric: str = "ir",
    ) -> List[Factor]:
        """Mine alpha factors using genetic algorithm."""
        population = [
            self.generate_random_expression()
            for _ in range(self.population_size)
        ]

        best_factors = []

        for gen in range(self.generations):
            scored = []

            for expr in population:
                factor = Factor(
                    factor_id=hashlib.md5(expr.encode()).hexdigest()[:8],
                    name=f"GA_Factor_{gen}",
                    expression=expr,
                )

                try:
                    result = self.evaluator.evaluate_factor(factor, price_data)
                    score = getattr(result, target_metric, float('nan'))
                    if not math.isnan(score):
                        factor.result = result
                        scored.append((expr, score))
                except Exception:
                    continue

            if not scored:
                population = [
                    self.generate_random_expression()
                    for _ in range(self.population_size)
                ]
                continue

            scored.sort(key=lambda x: x[1], reverse=True)

            for expr, score in scored[:5]:
                factor = Factor(
                    factor_id=hashlib.md5(expr.encode()).hexdigest()[:8],
                    name=f"GA_Factor_Gen{gen}",
                    expression=expr,
                )
                factor.result = self.evaluator.evaluate_factor(factor, price_data)
                best_factors.append(factor)

            elite_count = int(self.population_size * 0.1)
            new_population = [expr for expr, _ in scored[:elite_count]]

            while len(new_population) < self.population_size:
                if random.random() < self.crossover_rate and len(scored) >= 2:
                    idx1, idx2 = random.sample(range(min(20, len(scored))), 2)
                    child1, child2 = self.crossover(scored[idx1][0], scored[idx2][0])
                    new_population.extend([child1, child2])
                else:
                    parent_idx = random.randint(0, min(20, len(scored)) - 1)
                    child = self.mutate(scored[parent_idx][0])
                    new_population.append(child)

            population = new_population[:self.population_size]

        best_factors.sort(
            key=lambda f: getattr(f.result, target_metric, float('-inf'))
            if f.result else float('-inf'),
            reverse=True
        )

        return best_factors[:10]


class FactorLibrary:
    """Library of pre-built alpha factors."""

    MOMENTUM_FACTORS = [
        Factor(
            factor_id="mom_1m",
            name="1-Month Momentum",
            expression="close / close_20d_ago - 1",
            category=FactorCategory.MOMENTUM,
            description="Price change over 20 trading days",
        ),
        Factor(
            factor_id="mom_3m",
            name="3-Month Momentum",
            expression="close / close_60d_ago - 1",
            category=FactorCategory.MOMENTUM,
            description="Price change over 60 trading days",
        ),
        Factor(
            factor_id="rsi",
            name="RSI",
            expression="gains_14d / (gains_14d + losses_14d)",
            category=FactorCategory.MOMENTUM,
            description="Relative Strength Index",
        ),
    ]

    MEAN_REVERSION_FACTORS = [
        Factor(
            factor_id="mean_rev_20d",
            name="20-Day Mean Reversion",
            expression="close / ma_20d - 1",
            category=FactorCategory.MEAN_REVERSION,
            description="Price distance from 20-day moving average",
        ),
        Factor(
            factor_id="bb_position",
            name="Bollinger Band Position",
            expression="(close - ma_20d) / (2 * std_20d)",
            category=FactorCategory.MEAN_REVERSION,
            description="Position within Bollinger Bands",
        ),
    ]

    VOLATILITY_FACTORS = [
        Factor(
            factor_id="vol_20d",
            name="20-Day Volatility",
            expression="std_20d / ma_20d",
            category=FactorCategory.VOLATILITY,
            description="Rolling 20-day volatility",
        ),
        Factor(
            factor_id="atr",
            name="Average True Range",
            expression="(high - low) / close",
            category=FactorCategory.VOLATILITY,
            description="True range relative to price",
        ),
    ]

    VOLUME_FACTORS = [
        Factor(
            factor_id="vol_surge",
            name="Volume Surge",
            expression="volume / volume_ma_20d",
            category=FactorCategory.VOLUME,
            description="Volume relative to 20-day average",
        ),
        Factor(
            factor_id="obv_trend",
            name="OBV Trend",
            expression="obv / obv_ma_20d - 1",
            category=FactorCategory.VOLUME,
            description="On-Balance Volume trend",
        ),
    ]

    @classmethod
    def get_all(cls) -> List[Factor]:
        """Get all pre-built factors."""
        return (
            cls.MOMENTUM_FACTORS +
            cls.MEAN_REVERSION_FACTORS +
            cls.VOLATILITY_FACTORS +
            cls.VOLUME_FACTORS
        )

    @classmethod
    def get_by_category(cls, category: FactorCategory) -> List[Factor]:
        """Get factors by category."""
        all_factors = cls.get_all()
        return [f for f in all_factors if f.category == category]


class AlphaFactorManager:
    """Manager for alpha factor operations."""

    def __init__(self):
        """Initialize manager."""
        self.factors: Dict[str, Factor] = {}
        self.evaluator = FactorEvaluator()
        self.parser = ExpressionParser()
        self._lock = threading.Lock()

    def add_factor(
        self,
        name: str,
        expression: str,
        category: FactorCategory = FactorCategory.CUSTOM,
        description: str = "",
    ) -> Factor:
        """Add a new factor."""
        valid, msg = self.parser.validate(expression)
        if not valid:
            raise ValueError(f"Invalid expression: {msg}")

        factor_id = hashlib.md5(f"{name}:{expression}".encode()).hexdigest()[:8]

        factor = Factor(
            factor_id=factor_id,
            name=name,
            expression=expression,
            category=category,
            description=description,
        )

        with self._lock:
            self.factors[factor_id] = factor

        return factor

    def get_factor(self, factor_id: str) -> Optional[Factor]:
        """Get factor by ID."""
        return self.factors.get(factor_id)

    def list_factors(
        self,
        category: Optional[FactorCategory] = None,
    ) -> List[Factor]:
        """List all factors."""
        factors = list(self.factors.values())

        if category:
            factors = [f for f in factors if f.category == category]

        return factors

    def evaluate(
        self,
        factor_id: str,
        price_data: Dict[str, List[float]],
    ) -> FactorResult:
        """Evaluate a factor."""
        factor = self.get_factor(factor_id)
        if factor is None:
            raise ValueError(f"Factor not found: {factor_id}")

        result = self.evaluator.evaluate_factor(factor, price_data)
        factor.result = result
        return result

    def evaluate_all(
        self,
        price_data: Dict[str, List[float]],
    ) -> List[FactorResult]:
        """Evaluate all factors."""
        results = []

        for factor in self.factors.values():
            try:
                result = self.evaluator.evaluate_factor(factor, price_data)
                factor.result = result
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to evaluate factor {factor.name}: {e}")

        return results

    def rank_factors(
        self,
        price_data: Dict[str, List[float]],
        metric: str = "ir",
    ) -> List[Tuple[Factor, float]]:
        """Rank factors by metric."""
        self.evaluate_all(price_data)

        ranked = []
        for factor in self.factors.values():
            if factor.result:
                score = getattr(factor.result, metric, float('nan'))
                if not math.isnan(score):
                    ranked.append((factor, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def mine_factors(
        self,
        price_data: Dict[str, List[float]],
        generations: int = 50,
    ) -> List[Factor]:
        """Mine new factors using genetic programming."""
        miner = GeneticFactorMiner(generations=generations)
        new_factors = miner.mine(price_data)

        for factor in new_factors:
            with self._lock:
                self.factors[factor.factor_id] = factor

        return new_factors

    def remove_factor(self, factor_id: str) -> bool:
        """Remove a factor."""
        with self._lock:
            if factor_id in self.factors:
                del self.factors[factor_id]
                return True
            return False

    def load_library(self) -> None:
        """Load pre-built factors from library."""
        for factor in FactorLibrary.get_all():
            with self._lock:
                self.factors[factor.factor_id] = factor

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about factors."""
        factors = list(self.factors.values())
        evaluated = [f for f in factors if f.result is not None]

        stats = {
            "total_factors": len(factors),
            "evaluated_factors": len(evaluated),
            "by_category": {},
        }

        for category in FactorCategory:
            cat_factors = [f for f in factors if f.category == category]
            stats["by_category"][category.value] = len(cat_factors)

        if evaluated:
            significant = [
                f for f in evaluated
                if f.result and f.result.is_significant
            ]
            stats["significant_factors"] = len(significant)

            avg_ic = sum(
                f.result.ic for f in evaluated
                if f.result and not math.isnan(f.result.ic)
            ) / len(evaluated)
            stats["average_ic"] = avg_ic

        return stats


_alpha_manager: Optional[AlphaFactorManager] = None
_alpha_lock = threading.Lock()


def get_alpha_manager() -> AlphaFactorManager:
    """Get singleton alpha factor manager."""
    global _alpha_manager

    with _alpha_lock:
        if _alpha_manager is None:
            _alpha_manager = AlphaFactorManager()
        return _alpha_manager


def reset_alpha_manager() -> None:
    """Reset singleton alpha factor manager."""
    global _alpha_manager

    with _alpha_lock:
        _alpha_manager = None
