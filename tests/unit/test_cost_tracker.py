"""Tests for the cost tracking system."""

import pytest
from src.core.tracking.cost_tracker import (
    CostTracker,
    ModelPricing,
    MODEL_PRICING,
    get_cost_tracker,
    reset_cost_tracker,
)


class TestModelPricing:
    """Tests for model pricing data."""

    def test_known_models_have_pricing(self):
        """Test that common models have pricing defined."""
        known_models = [
            "gpt-4-turbo-preview",
            "gpt-4o",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "gemini-1.5-pro-latest",
            "llama-3.1-8b-instant",
        ]
        for model in known_models:
            assert model in MODEL_PRICING, f"Missing pricing for {model}"

    def test_ollama_models_are_free(self):
        """Test that Ollama models are priced at $0."""
        ollama_models = ["llama3", "llama3.1:8b", "mistral"]
        for model in ollama_models:
            pricing = MODEL_PRICING.get(model)
            if pricing:
                assert pricing.input_price == 0.0
                assert pricing.output_price == 0.0


class TestCostTracker:
    """Tests for CostTracker class."""

    def setup_method(self):
        """Reset tracker before each test."""
        reset_cost_tracker()

    def test_init_default_budget(self):
        """Test default budget limit."""
        tracker = CostTracker()
        assert tracker.budget_limit == 10.0  # Default from env

    def test_init_custom_budget(self):
        """Test custom budget limit."""
        tracker = CostTracker(budget_limit=5.0)
        assert tracker.budget_limit == 5.0

    def test_calculate_cost(self):
        """Test cost calculation."""
        tracker = CostTracker()
        # GPT-4 Turbo: $10/1M input, $30/1M output
        cost = tracker.calculate_cost(
            model="gpt-4-turbo-preview",
            input_tokens=1000,
            output_tokens=500,
        )
        # Expected: (1000/1M * 10) + (500/1M * 30) = 0.01 + 0.015 = 0.025
        assert abs(cost - 0.025) < 0.0001

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model uses default pricing."""
        tracker = CostTracker()
        cost = tracker.calculate_cost(
            model="unknown-model",
            input_tokens=1000,
            output_tokens=1000,
        )
        # Default: $1/1M input, $2/1M output
        # Expected: (1000/1M * 1) + (1000/1M * 2) = 0.003
        assert abs(cost - 0.003) < 0.0001

    def test_add_tracks_cost(self):
        """Test that add() tracks costs correctly."""
        tracker = CostTracker(budget_limit=100.0)
        cost1 = tracker.add("gpt-4-turbo-preview", 1000, 500)
        cost2 = tracker.add("gpt-4-turbo-preview", 2000, 1000)

        assert tracker.total_cost == cost1 + cost2
        assert len(tracker.get_usage_log()) == 2

    def test_remaining_budget(self):
        """Test remaining budget calculation."""
        tracker = CostTracker(budget_limit=1.0)
        tracker.add("gpt-4-turbo-preview", 10000, 5000)  # ~$0.25
        assert tracker.remaining_budget < 1.0
        assert tracker.remaining_budget > 0

    def test_budget_exceeded(self):
        """Test budget exceeded detection."""
        tracker = CostTracker(budget_limit=0.01)
        tracker.add("gpt-4-turbo-preview", 10000, 10000)  # ~$0.40
        assert tracker.budget_exceeded is True

    def test_budget_callback(self):
        """Test budget exceeded callback."""
        callback_called = []

        def on_budget_exceeded(total, limit):
            callback_called.append((total, limit))

        tracker = CostTracker(budget_limit=0.01)
        tracker.set_budget_callback(on_budget_exceeded)
        tracker.add("gpt-4-turbo-preview", 10000, 10000)

        assert len(callback_called) == 1
        assert callback_called[0][1] == 0.01

    def test_get_summary(self):
        """Test summary generation."""
        tracker = CostTracker()
        tracker.add("gpt-4-turbo-preview", 1000, 500)
        tracker.add("claude-3-opus-20240229", 2000, 1000)

        summary = tracker.get_summary()
        assert summary.calls_count == 2
        assert summary.total_input_tokens == 3000
        assert summary.total_output_tokens == 1500
        assert "gpt-4-turbo-preview" in summary.by_model
        assert "claude-3-opus-20240229" in summary.by_model

    def test_reset(self):
        """Test tracker reset."""
        tracker = CostTracker()
        tracker.add("gpt-4-turbo-preview", 1000, 500)
        tracker.reset()

        assert tracker.total_cost == 0.0
        assert len(tracker.get_usage_log()) == 0

    def test_format_summary(self):
        """Test formatted summary output."""
        tracker = CostTracker(budget_limit=10.0)
        tracker.add("gpt-4-turbo-preview", 1000, 500)

        summary_str = tracker.format_summary()
        assert "COST SUMMARY" in summary_str
        assert "$10.00" in summary_str  # Budget limit
        assert "gpt-4-turbo-preview" in summary_str


class TestGlobalCostTracker:
    """Tests for global cost tracker functions."""

    def setup_method(self):
        """Reset tracker before each test."""
        reset_cost_tracker()

    def test_get_cost_tracker_singleton(self):
        """Test that get_cost_tracker returns singleton."""
        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()
        assert tracker1 is tracker2

    def test_reset_cost_tracker(self):
        """Test that reset clears the singleton."""
        tracker1 = get_cost_tracker()
        tracker1.add("gpt-4o", 1000, 500)
        reset_cost_tracker()
        tracker2 = get_cost_tracker()
        assert tracker2.total_cost == 0.0
