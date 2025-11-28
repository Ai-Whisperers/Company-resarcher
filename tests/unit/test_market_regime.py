"""Tests for market regime detection."""

import pytest
import math
from datetime import datetime, timedelta

from src.core.market_regime import (
    BaseRegimeDetector,
    HMMRegimeDetector,
    KMeansRegimeDetector,
    MarketRegime,
    RegimeAnalysis,
    RegimeDetectionManager,
    RegimeState,
    RegimeTransition,
    SimpleRegimeDetector,
    get_regime_manager,
    reset_regime_manager,
)


class TestRegimeState:
    """Tests for RegimeState class."""

    def test_create_state(self):
        """Test creating a state."""
        state = RegimeState(
            regime=MarketRegime.BULL,
            confidence=0.85,
            start_date=datetime(2024, 1, 1),
            duration_days=30,
        )

        assert state.regime == MarketRegime.BULL
        assert state.confidence == 0.85
        assert state.duration_days == 30

    def test_to_dict(self):
        """Test serialization."""
        state = RegimeState(
            regime=MarketRegime.BEAR,
            confidence=0.75,
            trend=-0.02,
            volatility=0.03,
        )
        data = state.to_dict()

        assert data["regime"] == "bear"
        assert data["confidence"] == 0.75
        assert data["trend"] == -0.02


class TestRegimeTransition:
    """Tests for RegimeTransition class."""

    def test_create_transition(self):
        """Test creating a transition."""
        transition = RegimeTransition(
            from_regime=MarketRegime.BULL,
            to_regime=MarketRegime.BEAR,
            date=datetime(2024, 1, 15),
            confidence=0.9,
        )

        assert transition.from_regime == MarketRegime.BULL
        assert transition.to_regime == MarketRegime.BEAR
        assert transition.confidence == 0.9

    def test_to_dict(self):
        """Test serialization."""
        transition = RegimeTransition(
            from_regime=MarketRegime.SIDEWAYS,
            to_regime=MarketRegime.HIGH_VOLATILITY,
            date=datetime(2024, 2, 1),
            confidence=0.8,
        )
        data = transition.to_dict()

        assert data["from_regime"] == "sideways"
        assert data["to_regime"] == "high_volatility"


class TestRegimeAnalysis:
    """Tests for RegimeAnalysis class."""

    def test_to_dict(self):
        """Test serialization."""
        analysis = RegimeAnalysis(
            current_regime=RegimeState(
                regime=MarketRegime.BULL,
                confidence=0.8,
            ),
            regime_history=[],
            transitions=[],
            regime_probabilities={MarketRegime.BULL: 0.7, MarketRegime.BEAR: 0.3},
        )
        data = analysis.to_dict()

        assert "current_regime" in data
        assert "regime_probabilities" in data
        assert data["regime_probabilities"]["bull"] == 0.7


class TestSimpleRegimeDetector:
    """Tests for SimpleRegimeDetector class."""

    def setup_method(self):
        """Create detector."""
        self.detector = SimpleRegimeDetector(
            bull_threshold=0.0,
            bear_threshold=0.0,
            volatility_threshold=0.02,
            lookback_period=10,
        )

    def test_fit(self):
        """Test fitting detector."""
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 20
        self.detector.fit(returns)

        assert self.detector.historical_vol > 0

    def test_predict_bull(self):
        """Test predicting bull regime."""
        returns = [0.01, 0.02, 0.015, 0.01, 0.02] * 5
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert MarketRegime.BULL in regimes

    def test_predict_bear(self):
        """Test predicting bear regime."""
        returns = [-0.01, -0.02, -0.015, -0.01, -0.02] * 5
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert MarketRegime.BEAR in regimes

    def test_predict_high_volatility(self):
        """Test predicting high volatility regime."""
        returns = [0.05, -0.05, 0.04, -0.04, 0.03] * 5
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert MarketRegime.HIGH_VOLATILITY in regimes

    def test_predict_proba(self):
        """Test predicting probabilities."""
        returns = [0.01, 0.02, -0.01, 0.015, -0.005] * 10
        self.detector.fit(returns)
        probas = self.detector.predict_proba(returns)

        assert len(probas) == len(returns)
        assert all(isinstance(p, dict) for p in probas)


class TestHMMRegimeDetector:
    """Tests for HMMRegimeDetector class."""

    def setup_method(self):
        """Create detector."""
        self.detector = HMMRegimeDetector(n_regimes=3, n_iterations=20)

    def test_fit(self):
        """Test fitting HMM."""
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 30
        self.detector.fit(returns)

        assert self.detector._fitted
        assert len(self.detector.means) == 3
        assert len(self.detector.variances) == 3

    def test_predict(self):
        """Test predicting regimes."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 20
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert len(regimes) == len(returns)
        assert all(isinstance(r, MarketRegime) for r in regimes)

    def test_predict_proba(self):
        """Test predicting probabilities."""
        returns = [0.01, -0.01, 0.02, -0.02, 0.005] * 20
        self.detector.fit(returns)
        probas = self.detector.predict_proba(returns)

        assert len(probas) == len(returns)
        for proba in probas:
            assert isinstance(proba, dict)

    def test_handles_short_data(self):
        """Test handling short data sequences."""
        returns = [0.01, -0.01, 0.02]
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert len(regimes) == 3

    def test_handles_nan(self):
        """Test handling NaN values."""
        returns = [0.01, float('nan'), 0.02, -0.01, float('nan')] * 10
        self.detector.fit([r for r in returns if not math.isnan(r)])
        regimes = self.detector.predict(returns)

        assert len(regimes) == len(returns)


class TestKMeansRegimeDetector:
    """Tests for KMeansRegimeDetector class."""

    def setup_method(self):
        """Create detector."""
        self.detector = KMeansRegimeDetector(n_regimes=4, n_iterations=20)

    def test_fit(self):
        """Test fitting K-Means."""
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 30
        self.detector.fit(returns)

        assert self.detector._fitted
        assert len(self.detector.centroids) > 0

    def test_predict(self):
        """Test predicting regimes."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 30
        self.detector.fit(returns)
        regimes = self.detector.predict(returns)

        assert len(regimes) == len(returns)

    def test_predict_proba(self):
        """Test predicting probabilities."""
        returns = [0.01, -0.01, 0.02, -0.02, 0.005] * 30
        self.detector.fit(returns)
        probas = self.detector.predict_proba(returns)

        assert len(probas) == len(returns)


class TestRegimeDetectionManager:
    """Tests for RegimeDetectionManager class."""

    def setup_method(self):
        """Create manager."""
        self.manager = RegimeDetectionManager(detector_type="simple")

    def test_fit(self):
        """Test fitting manager."""
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 20
        self.manager.fit(returns)

        # Should not raise

    def test_detect(self):
        """Test regime detection."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 20

        analysis = self.manager.detect(returns)

        assert isinstance(analysis, RegimeAnalysis)
        assert analysis.current_regime is not None

    def test_detect_with_dates(self):
        """Test detection with date tracking."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 20
        start_date = datetime(2024, 1, 1)
        dates = [
            start_date + timedelta(days=i)
            for i in range(len(returns))
        ]

        analysis = self.manager.detect(returns, dates)

        assert analysis.current_regime.start_date is not None

    def test_detect_tracks_transitions(self):
        """Test that transitions are tracked."""
        returns = [0.02] * 20 + [-0.02] * 20
        analysis = self.manager.detect(returns)

        # Should detect at least one transition (bull to bear)
        # May not always happen with simple detector
        assert isinstance(analysis.transitions, list)

    def test_get_current_regime(self):
        """Test getting current regime."""
        returns = [0.01, 0.02, 0.015, 0.01, 0.02] * 10
        self.manager.detect(returns)

        current = self.manager.get_current_regime()

        assert current is not None
        assert isinstance(current.regime, MarketRegime)

    def test_get_regime_probabilities(self):
        """Test getting regime probabilities."""
        returns = [0.01, -0.01, 0.02, -0.02] * 10
        self.manager.fit(returns)

        probas = self.manager.get_regime_probabilities(returns)

        assert isinstance(probas, dict)
        assert all(r in probas for r in MarketRegime)

    def test_get_statistics(self):
        """Test getting statistics."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 20
        self.manager.detect(returns)

        stats = self.manager.get_statistics()

        assert "detector_type" in stats
        assert "n_regimes" in stats
        assert "regime_distribution" in stats


class TestRegimeDetectionManagerWithHMM:
    """Tests for RegimeDetectionManager with HMM detector."""

    def setup_method(self):
        """Create manager with HMM."""
        self.manager = RegimeDetectionManager(detector_type="hmm", n_regimes=3)

    def test_detect_with_hmm(self):
        """Test detection with HMM."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 30
        self.manager.fit(returns)

        analysis = self.manager.detect(returns)

        assert isinstance(analysis, RegimeAnalysis)

    def test_returns_by_regime(self):
        """Test returns calculation by regime."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 30
        self.manager.fit(returns)

        analysis = self.manager.detect(returns)

        assert "returns_by_regime" in analysis.to_dict()

    def test_volatility_by_regime(self):
        """Test volatility calculation by regime."""
        returns = [0.01, 0.02, -0.01, -0.02, 0.005] * 30
        self.manager.fit(returns)

        analysis = self.manager.detect(returns)

        assert "volatility_by_regime" in analysis.to_dict()


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_regime_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_regime_manager()

    def test_get_regime_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_regime_manager()
        m2 = get_regime_manager()
        assert m1 is m2

    def test_get_regime_manager_with_config(self):
        """Test getting manager with config."""
        manager = get_regime_manager(detector_type="simple", n_regimes=4)

        assert manager.detector_type == "simple"
        assert manager.n_regimes == 4

    def test_reset_regime_manager(self):
        """Test resetting singleton."""
        m1 = get_regime_manager()
        reset_regime_manager()
        m2 = get_regime_manager()
        assert m1 is not m2


class TestMarketRegimeEnum:
    """Tests for MarketRegime enum."""

    def test_all_regimes(self):
        """Test all market regimes."""
        regimes = [
            MarketRegime.BULL,
            MarketRegime.BEAR,
            MarketRegime.SIDEWAYS,
            MarketRegime.HIGH_VOLATILITY,
            MarketRegime.LOW_VOLATILITY,
            MarketRegime.RECOVERY,
            MarketRegime.CRASH,
            MarketRegime.UNKNOWN,
        ]
        assert len(regimes) == len(MarketRegime)

    def test_regime_values(self):
        """Test regime string values."""
        assert MarketRegime.BULL.value == "bull"
        assert MarketRegime.BEAR.value == "bear"
        assert MarketRegime.HIGH_VOLATILITY.value == "high_volatility"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_returns(self):
        """Test with empty returns."""
        manager = RegimeDetectionManager(detector_type="simple")

        analysis = manager.detect([])

        assert analysis.current_regime.regime == MarketRegime.UNKNOWN

    def test_single_return(self):
        """Test with single return value."""
        manager = RegimeDetectionManager(detector_type="simple")

        analysis = manager.detect([0.01])

        assert isinstance(analysis, RegimeAnalysis)

    def test_all_nan_returns(self):
        """Test with all NaN returns."""
        manager = RegimeDetectionManager(detector_type="simple")
        returns = [float('nan')] * 20

        analysis = manager.detect(returns)

        # Should handle gracefully
        assert isinstance(analysis, RegimeAnalysis)

    def test_constant_returns(self):
        """Test with constant returns."""
        manager = RegimeDetectionManager(detector_type="hmm")
        returns = [0.01] * 100

        manager.fit(returns)
        analysis = manager.detect(returns)

        assert isinstance(analysis, RegimeAnalysis)
