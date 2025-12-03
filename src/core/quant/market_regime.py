"""Market Regime Detection for financial analysis.

This module provides tools for detecting and classifying market regimes
(Bull, Bear, Sideways, High Volatility) to adapt trading strategies.

Inspired by microsoft/qlib regime detection concepts.
"""

import logging
import math
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Types of market regimes."""

    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    RECOVERY = "recovery"
    CRASH = "crash"
    UNKNOWN = "unknown"


@dataclass
class RegimeState:
    """Current regime state with confidence."""

    regime: MarketRegime
    confidence: float
    start_date: Optional[datetime] = None
    duration_days: int = 0

    # Regime characteristics
    trend: float = 0.0  # Positive = uptrend, Negative = downtrend
    volatility: float = 0.0
    momentum: float = 0.0

    # Additional features
    features: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "duration_days": self.duration_days,
            "trend": self.trend,
            "volatility": self.volatility,
            "momentum": self.momentum,
            "features": self.features,
        }


@dataclass
class RegimeTransition:
    """Represents a regime transition."""

    from_regime: MarketRegime
    to_regime: MarketRegime
    date: datetime
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "from_regime": self.from_regime.value,
            "to_regime": self.to_regime.value,
            "date": self.date.isoformat(),
            "confidence": self.confidence,
        }


@dataclass
class RegimeAnalysis:
    """Complete regime analysis result."""

    current_regime: RegimeState
    regime_history: List[RegimeState]
    transitions: List[RegimeTransition]
    regime_probabilities: Dict[MarketRegime, float]

    # Performance by regime
    returns_by_regime: Dict[MarketRegime, float] = field(default_factory=dict)
    volatility_by_regime: Dict[MarketRegime, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "current_regime": self.current_regime.to_dict(),
            "regime_history": [r.to_dict() for r in self.regime_history],
            "transitions": [t.to_dict() for t in self.transitions],
            "regime_probabilities": {
                k.value: v for k, v in self.regime_probabilities.items()
            },
            "returns_by_regime": {
                k.value: v for k, v in self.returns_by_regime.items()
            },
            "volatility_by_regime": {
                k.value: v for k, v in self.volatility_by_regime.items()
            },
        }


class BaseRegimeDetector(ABC):
    """Abstract base class for regime detectors."""

    @abstractmethod
    def fit(self, returns: List[float], **kwargs) -> None:
        """Fit the detector to historical data."""
        pass

    @abstractmethod
    def predict(self, returns: List[float]) -> List[MarketRegime]:
        """Predict regime for each period."""
        pass

    @abstractmethod
    def predict_proba(self, returns: List[float]) -> List[Dict[MarketRegime, float]]:
        """Predict regime probabilities."""
        pass


class SimpleRegimeDetector(BaseRegimeDetector):
    """Simple rule-based regime detector."""

    def __init__(
        self,
        bull_threshold: float = 0.0,
        bear_threshold: float = 0.0,
        volatility_threshold: float = 0.02,
        lookback_period: int = 20,
    ):
        """Initialize detector."""
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
        self.volatility_threshold = volatility_threshold
        self.lookback_period = lookback_period
        self.historical_vol: float = 0.0

    def fit(self, returns: List[float], **kwargs) -> None:
        """Fit to historical data."""
        valid_returns = [r for r in returns if not math.isnan(r)]
        if valid_returns:
            mean = sum(valid_returns) / len(valid_returns)
            variance = sum((r - mean) ** 2 for r in valid_returns) / len(valid_returns)
            self.historical_vol = math.sqrt(variance)

    def predict(self, returns: List[float]) -> List[MarketRegime]:
        """Predict regimes."""
        regimes = []

        for i in range(len(returns)):
            start_idx = max(0, i - self.lookback_period + 1)
            window = returns[start_idx:i + 1]
            valid_window = [r for r in window if not math.isnan(r)]

            if not valid_window:
                regimes.append(MarketRegime.UNKNOWN)
                continue

            mean_return = sum(valid_window) / len(valid_window)
            if len(valid_window) >= 2:
                variance = sum((r - mean_return) ** 2 for r in valid_window) / len(valid_window)
                volatility = math.sqrt(variance)
            else:
                volatility = 0.0

            cumulative_return = sum(valid_window)

            if volatility > self.volatility_threshold:
                regimes.append(MarketRegime.HIGH_VOLATILITY)
            elif cumulative_return > self.bull_threshold:
                regimes.append(MarketRegime.BULL)
            elif cumulative_return < self.bear_threshold:
                regimes.append(MarketRegime.BEAR)
            else:
                regimes.append(MarketRegime.SIDEWAYS)

        return regimes

    def predict_proba(self, returns: List[float]) -> List[Dict[MarketRegime, float]]:
        """Predict regime probabilities."""
        regimes = self.predict(returns)
        probas = []

        for regime in regimes:
            proba = {r: 0.1 for r in MarketRegime}
            proba[regime] = 0.7
            probas.append(proba)

        return probas


class HMMRegimeDetector(BaseRegimeDetector):
    """Hidden Markov Model based regime detector."""

    def __init__(
        self,
        n_regimes: int = 3,
        n_iterations: int = 100,
        convergence_threshold: float = 1e-4,
    ):
        """Initialize HMM detector."""
        self.n_regimes = n_regimes
        self.n_iterations = n_iterations
        self.convergence_threshold = convergence_threshold

        self.means: List[float] = []
        self.variances: List[float] = []
        self.transition_matrix: List[List[float]] = []
        self.initial_probs: List[float] = []
        self._fitted = False

    def fit(self, returns: List[float], **kwargs) -> None:
        """Fit HMM to historical returns."""
        valid_returns = [r for r in returns if not math.isnan(r)]

        if len(valid_returns) < self.n_regimes * 10:
            logger.warning("Insufficient data for HMM fitting")
            self._initialize_defaults(valid_returns)
            return

        self._initialize_parameters(valid_returns)
        self._em_algorithm(valid_returns)
        self._fitted = True

    def _initialize_defaults(self, returns: List[float]) -> None:
        """Initialize with default parameters."""
        if returns:
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        else:
            mean = 0.0
            variance = 0.01

        self.means = [mean - 0.01, mean, mean + 0.01][:self.n_regimes]
        self.variances = [variance] * self.n_regimes

        uniform = 1.0 / self.n_regimes
        self.initial_probs = [uniform] * self.n_regimes
        self.transition_matrix = [
            [uniform] * self.n_regimes for _ in range(self.n_regimes)
        ]
        self._fitted = True

    def _initialize_parameters(self, returns: List[float]) -> None:
        """Initialize HMM parameters using k-means-style initialization."""
        sorted_returns = sorted(returns)
        n = len(sorted_returns)

        quantiles = []
        for i in range(self.n_regimes):
            idx = int((i + 0.5) * n / self.n_regimes)
            quantiles.append(sorted_returns[min(idx, n - 1)])

        self.means = quantiles

        overall_variance = sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns)
        self.variances = [overall_variance] * self.n_regimes

        uniform = 1.0 / self.n_regimes
        self.initial_probs = [uniform] * self.n_regimes

        self.transition_matrix = []
        for i in range(self.n_regimes):
            row = []
            for j in range(self.n_regimes):
                if i == j:
                    row.append(0.9)
                else:
                    row.append(0.1 / (self.n_regimes - 1))
            self.transition_matrix.append(row)

    def _em_algorithm(self, returns: List[float]) -> None:
        """Run EM algorithm for HMM fitting."""
        prev_log_likelihood = float('-inf')

        for iteration in range(self.n_iterations):
            forward, scaling = self._forward(returns)
            backward = self._backward(returns, scaling)

            gamma = self._compute_gamma(forward, backward, scaling)
            xi = self._compute_xi(forward, backward, returns, scaling)

            self._update_parameters(returns, gamma, xi)

            log_likelihood = sum(math.log(s) if s > 0 else float('-inf') for s in scaling)

            if abs(log_likelihood - prev_log_likelihood) < self.convergence_threshold:
                break

            prev_log_likelihood = log_likelihood

    def _gaussian_pdf(self, x: float, mean: float, variance: float) -> float:
        """Calculate Gaussian probability density."""
        if variance <= 0:
            return 1e-10

        coef = 1.0 / math.sqrt(2 * math.pi * variance)
        exp_term = math.exp(-0.5 * (x - mean) ** 2 / variance)
        return max(coef * exp_term, 1e-10)

    def _forward(self, returns: List[float]) -> Tuple[List[List[float]], List[float]]:
        """Forward pass of HMM."""
        T = len(returns)
        alpha = [[0.0] * self.n_regimes for _ in range(T)]
        scaling = [0.0] * T

        for i in range(self.n_regimes):
            alpha[0][i] = self.initial_probs[i] * self._gaussian_pdf(
                returns[0], self.means[i], self.variances[i]
            )
            scaling[0] += alpha[0][i]

        if scaling[0] > 0:
            for i in range(self.n_regimes):
                alpha[0][i] /= scaling[0]

        for t in range(1, T):
            for j in range(self.n_regimes):
                for i in range(self.n_regimes):
                    alpha[t][j] += alpha[t-1][i] * self.transition_matrix[i][j]
                alpha[t][j] *= self._gaussian_pdf(
                    returns[t], self.means[j], self.variances[j]
                )
                scaling[t] += alpha[t][j]

            if scaling[t] > 0:
                for j in range(self.n_regimes):
                    alpha[t][j] /= scaling[t]

        return alpha, scaling

    def _backward(
        self,
        returns: List[float],
        scaling: List[float],
    ) -> List[List[float]]:
        """Backward pass of HMM."""
        T = len(returns)
        beta = [[0.0] * self.n_regimes for _ in range(T)]

        for i in range(self.n_regimes):
            beta[T-1][i] = 1.0

        for t in range(T - 2, -1, -1):
            for i in range(self.n_regimes):
                for j in range(self.n_regimes):
                    beta[t][i] += (
                        self.transition_matrix[i][j] *
                        self._gaussian_pdf(returns[t+1], self.means[j], self.variances[j]) *
                        beta[t+1][j]
                    )
                if scaling[t+1] > 0:
                    beta[t][i] /= scaling[t+1]

        return beta

    def _compute_gamma(
        self,
        alpha: List[List[float]],
        beta: List[List[float]],
        scaling: List[float],
    ) -> List[List[float]]:
        """Compute state probabilities."""
        T = len(alpha)
        gamma = [[0.0] * self.n_regimes for _ in range(T)]

        for t in range(T):
            total = sum(alpha[t][i] * beta[t][i] for i in range(self.n_regimes))
            if total > 0:
                for i in range(self.n_regimes):
                    gamma[t][i] = alpha[t][i] * beta[t][i] / total

        return gamma

    def _compute_xi(
        self,
        alpha: List[List[float]],
        beta: List[List[float]],
        returns: List[float],
        scaling: List[float],
    ) -> List[List[List[float]]]:
        """Compute transition probabilities."""
        T = len(returns)
        xi = [
            [[0.0] * self.n_regimes for _ in range(self.n_regimes)]
            for _ in range(T - 1)
        ]

        for t in range(T - 1):
            total = 0.0
            for i in range(self.n_regimes):
                for j in range(self.n_regimes):
                    xi[t][i][j] = (
                        alpha[t][i] *
                        self.transition_matrix[i][j] *
                        self._gaussian_pdf(returns[t+1], self.means[j], self.variances[j]) *
                        beta[t+1][j]
                    )
                    total += xi[t][i][j]

            if total > 0:
                for i in range(self.n_regimes):
                    for j in range(self.n_regimes):
                        xi[t][i][j] /= total

        return xi

    def _update_parameters(
        self,
        returns: List[float],
        gamma: List[List[float]],
        xi: List[List[List[float]]],
    ) -> None:
        """Update HMM parameters."""
        T = len(returns)

        self.initial_probs = gamma[0][:]

        for i in range(self.n_regimes):
            gamma_sum = sum(gamma[t][i] for t in range(T - 1))
            if gamma_sum > 0:
                for j in range(self.n_regimes):
                    xi_sum = sum(xi[t][i][j] for t in range(T - 1))
                    self.transition_matrix[i][j] = xi_sum / gamma_sum

        for i in range(self.n_regimes):
            gamma_sum = sum(gamma[t][i] for t in range(T))
            if gamma_sum > 0:
                weighted_sum = sum(gamma[t][i] * returns[t] for t in range(T))
                self.means[i] = weighted_sum / gamma_sum

                variance_sum = sum(
                    gamma[t][i] * (returns[t] - self.means[i]) ** 2
                    for t in range(T)
                )
                self.variances[i] = max(variance_sum / gamma_sum, 1e-6)

    def predict(self, returns: List[float]) -> List[MarketRegime]:
        """Predict most likely regime sequence using Viterbi."""
        if not self._fitted:
            self._initialize_defaults(returns)

        T = len(returns)
        if T == 0:
            return []

        viterbi = [[0.0] * self.n_regimes for _ in range(T)]
        backpointer = [[0] * self.n_regimes for _ in range(T)]

        for i in range(self.n_regimes):
            prob = self._gaussian_pdf(returns[0], self.means[i], self.variances[i])
            viterbi[0][i] = math.log(max(self.initial_probs[i], 1e-10)) + math.log(max(prob, 1e-10))

        for t in range(1, T):
            for j in range(self.n_regimes):
                best_score = float('-inf')
                best_state = 0

                for i in range(self.n_regimes):
                    trans_prob = self.transition_matrix[i][j]
                    score = viterbi[t-1][i] + math.log(max(trans_prob, 1e-10))

                    if score > best_score:
                        best_score = score
                        best_state = i

                emit_prob = self._gaussian_pdf(returns[t], self.means[j], self.variances[j])
                viterbi[t][j] = best_score + math.log(max(emit_prob, 1e-10))
                backpointer[t][j] = best_state

        state_sequence = [0] * T
        state_sequence[T-1] = max(range(self.n_regimes), key=lambda i: viterbi[T-1][i])

        for t in range(T - 2, -1, -1):
            state_sequence[t] = backpointer[t + 1][state_sequence[t + 1]]

        return self._map_states_to_regimes(state_sequence, returns)

    def _map_states_to_regimes(
        self,
        states: List[int],
        returns: List[float],
    ) -> List[MarketRegime]:
        """Map HMM states to market regimes."""
        sorted_indices = sorted(range(self.n_regimes), key=lambda i: self.means[i])

        regime_map = {}
        if self.n_regimes >= 3:
            regime_map[sorted_indices[0]] = MarketRegime.BEAR
            regime_map[sorted_indices[-1]] = MarketRegime.BULL

            for i in sorted_indices[1:-1]:
                if self.variances[i] > sum(self.variances) / len(self.variances):
                    regime_map[i] = MarketRegime.HIGH_VOLATILITY
                else:
                    regime_map[i] = MarketRegime.SIDEWAYS
        else:
            for i, idx in enumerate(sorted_indices):
                if i == 0:
                    regime_map[idx] = MarketRegime.BEAR
                elif i == len(sorted_indices) - 1:
                    regime_map[idx] = MarketRegime.BULL
                else:
                    regime_map[idx] = MarketRegime.SIDEWAYS

        return [regime_map.get(s, MarketRegime.UNKNOWN) for s in states]

    def predict_proba(self, returns: List[float]) -> List[Dict[MarketRegime, float]]:
        """Predict regime probabilities."""
        if not self._fitted:
            self._initialize_defaults(returns)

        forward, scaling = self._forward(returns)
        backward = self._backward(returns, scaling)
        gamma = self._compute_gamma(forward, backward, scaling)

        states = self.predict(returns)
        sorted_indices = sorted(range(self.n_regimes), key=lambda i: self.means[i])

        probas = []
        for t in range(len(returns)):
            proba = {regime: 0.0 for regime in MarketRegime}

            for i in range(self.n_regimes):
                if i == sorted_indices[0]:
                    proba[MarketRegime.BEAR] += gamma[t][i]
                elif i == sorted_indices[-1]:
                    proba[MarketRegime.BULL] += gamma[t][i]
                else:
                    if self.variances[i] > sum(self.variances) / len(self.variances):
                        proba[MarketRegime.HIGH_VOLATILITY] += gamma[t][i]
                    else:
                        proba[MarketRegime.SIDEWAYS] += gamma[t][i]

            probas.append(proba)

        return probas


class KMeansRegimeDetector(BaseRegimeDetector):
    """K-Means clustering based regime detector."""

    def __init__(
        self,
        n_regimes: int = 4,
        n_iterations: int = 100,
        features: List[str] = None,
    ):
        """Initialize detector."""
        self.n_regimes = n_regimes
        self.n_iterations = n_iterations
        self.features = features or ["returns", "volatility", "momentum"]
        self.centroids: List[List[float]] = []
        self._fitted = False

    def fit(self, returns: List[float], **kwargs) -> None:
        """Fit K-Means to features derived from returns."""
        feature_matrix = self._extract_features(returns)

        if len(feature_matrix) < self.n_regimes:
            self._fitted = False
            return

        self.centroids = self._kmeans(feature_matrix)
        self._fitted = True

    def _extract_features(self, returns: List[float]) -> List[List[float]]:
        """Extract features from returns."""
        features = []
        window = 20

        for i in range(window, len(returns)):
            window_returns = returns[i - window:i]
            valid = [r for r in window_returns if not math.isnan(r)]

            if not valid:
                continue

            mean_return = sum(valid) / len(valid)
            variance = sum((r - mean_return) ** 2 for r in valid) / len(valid)
            volatility = math.sqrt(variance)

            cumulative = sum(valid)

            features.append([mean_return, volatility, cumulative])

        return features

    def _kmeans(self, data: List[List[float]]) -> List[List[float]]:
        """Run K-Means clustering."""
        import random

        indices = random.sample(range(len(data)), min(self.n_regimes, len(data)))
        centroids = [data[i][:] for i in indices]

        for _ in range(self.n_iterations):
            clusters = [[] for _ in range(self.n_regimes)]

            for point in data:
                distances = [
                    sum((a - b) ** 2 for a, b in zip(point, c))
                    for c in centroids
                ]
                cluster_idx = distances.index(min(distances))
                clusters[cluster_idx].append(point)

            new_centroids = []
            for i, cluster in enumerate(clusters):
                if cluster:
                    n_features = len(data[0])
                    new_centroid = [
                        sum(p[j] for p in cluster) / len(cluster)
                        for j in range(n_features)
                    ]
                    new_centroids.append(new_centroid)
                else:
                    new_centroids.append(centroids[i])

            if new_centroids == centroids:
                break

            centroids = new_centroids

        return centroids

    def predict(self, returns: List[float]) -> List[MarketRegime]:
        """Predict regimes using K-Means."""
        if not self._fitted or not self.centroids:
            return [MarketRegime.UNKNOWN] * len(returns)

        features = self._extract_features(returns)
        regimes = [MarketRegime.UNKNOWN] * 20

        sorted_centroids = sorted(
            range(len(self.centroids)),
            key=lambda i: self.centroids[i][0] if self.centroids[i] else 0
        )

        for point in features:
            distances = [
                sum((a - b) ** 2 for a, b in zip(point, c))
                for c in self.centroids
            ]
            cluster_idx = distances.index(min(distances))

            rank = sorted_centroids.index(cluster_idx)
            if rank == 0:
                regimes.append(MarketRegime.BEAR)
            elif rank == len(sorted_centroids) - 1:
                regimes.append(MarketRegime.BULL)
            elif self.centroids[cluster_idx][1] > 0.02:
                regimes.append(MarketRegime.HIGH_VOLATILITY)
            else:
                regimes.append(MarketRegime.SIDEWAYS)

        return regimes[:len(returns)]

    def predict_proba(self, returns: List[float]) -> List[Dict[MarketRegime, float]]:
        """Predict regime probabilities using distance-based softmax."""
        regimes = self.predict(returns)

        return [
            {r: 0.7 if r == regime else 0.1 for r in MarketRegime}
            for regime in regimes
        ]


class RegimeDetectionManager:
    """Manager for regime detection operations."""

    def __init__(
        self,
        detector_type: str = "hmm",
        n_regimes: int = 3,
    ):
        """Initialize manager."""
        self.detector_type = detector_type
        self.n_regimes = n_regimes
        self.detector = self._create_detector()
        self._lock = threading.Lock()

        self.current_regime: Optional[RegimeState] = None
        self.regime_history: List[RegimeState] = []
        self.transitions: List[RegimeTransition] = []

    def _create_detector(self) -> BaseRegimeDetector:
        """Create regime detector."""
        if self.detector_type == "hmm":
            return HMMRegimeDetector(n_regimes=self.n_regimes)
        elif self.detector_type == "kmeans":
            return KMeansRegimeDetector(n_regimes=self.n_regimes)
        else:
            return SimpleRegimeDetector()

    def fit(self, returns: List[float]) -> None:
        """Fit detector to historical returns."""
        with self._lock:
            self.detector.fit(returns)

    def detect(
        self,
        returns: List[float],
        dates: Optional[List[datetime]] = None,
    ) -> RegimeAnalysis:
        """Detect regimes and return analysis."""
        with self._lock:
            regimes = self.detector.predict(returns)
            probas = self.detector.predict_proba(returns)

            if not dates:
                dates = [
                    datetime.utcnow()
                    for _ in range(len(returns))
                ]

            self.regime_history = []
            self.transitions = []

            current_regime = None
            current_start = None
            current_confidence = 0.0

            for i, (regime, proba, date) in enumerate(zip(regimes, probas, dates)):
                confidence = proba.get(regime, 0.5)

                if regime != current_regime:
                    if current_regime is not None:
                        duration = (date - current_start).days if current_start else 0
                        state = RegimeState(
                            regime=current_regime,
                            confidence=current_confidence,
                            start_date=current_start,
                            duration_days=duration,
                        )
                        self.regime_history.append(state)

                        transition = RegimeTransition(
                            from_regime=current_regime,
                            to_regime=regime,
                            date=date,
                            confidence=confidence,
                        )
                        self.transitions.append(transition)

                    current_regime = regime
                    current_start = date
                    current_confidence = confidence
                else:
                    current_confidence = (current_confidence + confidence) / 2

            if current_regime is not None:
                duration = (dates[-1] - current_start).days if current_start else 0
                state = RegimeState(
                    regime=current_regime,
                    confidence=current_confidence,
                    start_date=current_start,
                    duration_days=duration,
                )
                self.regime_history.append(state)
                self.current_regime = state

            regime_probs = {regime: 0.0 for regime in MarketRegime}
            if probas:
                for proba in probas[-20:]:
                    for regime, p in proba.items():
                        regime_probs[regime] += p
                total = sum(regime_probs.values())
                if total > 0:
                    regime_probs = {k: v / total for k, v in regime_probs.items()}

            returns_by_regime = self._calculate_returns_by_regime(returns, regimes)
            volatility_by_regime = self._calculate_volatility_by_regime(returns, regimes)

            return RegimeAnalysis(
                current_regime=self.current_regime or RegimeState(
                    regime=MarketRegime.UNKNOWN,
                    confidence=0.0,
                ),
                regime_history=self.regime_history,
                transitions=self.transitions,
                regime_probabilities=regime_probs,
                returns_by_regime=returns_by_regime,
                volatility_by_regime=volatility_by_regime,
            )

    def _calculate_returns_by_regime(
        self,
        returns: List[float],
        regimes: List[MarketRegime],
    ) -> Dict[MarketRegime, float]:
        """Calculate average returns by regime."""
        regime_returns: Dict[MarketRegime, List[float]] = {
            regime: [] for regime in MarketRegime
        }

        for ret, regime in zip(returns, regimes):
            if not math.isnan(ret):
                regime_returns[regime].append(ret)

        result = {}
        for regime, rets in regime_returns.items():
            if rets:
                result[regime] = sum(rets) / len(rets)
            else:
                result[regime] = 0.0

        return result

    def _calculate_volatility_by_regime(
        self,
        returns: List[float],
        regimes: List[MarketRegime],
    ) -> Dict[MarketRegime, float]:
        """Calculate volatility by regime."""
        regime_returns: Dict[MarketRegime, List[float]] = {
            regime: [] for regime in MarketRegime
        }

        for ret, regime in zip(returns, regimes):
            if not math.isnan(ret):
                regime_returns[regime].append(ret)

        result = {}
        for regime, rets in regime_returns.items():
            if len(rets) >= 2:
                mean = sum(rets) / len(rets)
                variance = sum((r - mean) ** 2 for r in rets) / len(rets)
                result[regime] = math.sqrt(variance)
            else:
                result[regime] = 0.0

        return result

    def get_current_regime(self) -> Optional[RegimeState]:
        """Get current regime state."""
        return self.current_regime

    def get_regime_probabilities(
        self,
        returns: List[float],
    ) -> Dict[MarketRegime, float]:
        """Get current regime probabilities."""
        probas = self.detector.predict_proba(returns)

        if not probas:
            return {regime: 0.0 for regime in MarketRegime}

        last_probas = probas[-1]
        total = sum(last_probas.values())

        if total > 0:
            return {k: v / total for k, v in last_probas.items()}

        return last_probas

    def get_statistics(self) -> Dict[str, Any]:
        """Get regime detection statistics."""
        stats = {
            "detector_type": self.detector_type,
            "n_regimes": self.n_regimes,
            "total_transitions": len(self.transitions),
            "regime_distribution": {},
        }

        if self.regime_history:
            regime_counts: Dict[MarketRegime, int] = {}
            for state in self.regime_history:
                regime_counts[state.regime] = regime_counts.get(state.regime, 0) + 1

            total = sum(regime_counts.values())
            stats["regime_distribution"] = {
                k.value: v / total for k, v in regime_counts.items()
            }

        if self.current_regime:
            stats["current_regime"] = self.current_regime.regime.value
            stats["current_confidence"] = self.current_regime.confidence

        return stats


_regime_manager: Optional[RegimeDetectionManager] = None
_regime_lock = threading.Lock()


def get_regime_manager(
    detector_type: str = "hmm",
    n_regimes: int = 3,
) -> RegimeDetectionManager:
    """Get singleton regime detection manager."""
    global _regime_manager

    with _regime_lock:
        if _regime_manager is None:
            _regime_manager = RegimeDetectionManager(detector_type, n_regimes)
        return _regime_manager


def reset_regime_manager() -> None:
    """Reset singleton regime detection manager."""
    global _regime_manager

    with _regime_lock:
        _regime_manager = None
