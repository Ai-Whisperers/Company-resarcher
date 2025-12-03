"""
Unit tests for Smart AI Router module.

Tests the intelligent routing logic that selects models based on task complexity.
Includes tests for:
- Complexity estimation
- Model selection
- Statistics tracking
- Cost optimization
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import time

from src.core.ai.routing.smart_router import SmartAIRouter, COUNTER_RESET_INTERVAL
from src.core.ai.ai_client import MockAIClient, BaseAIClient


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_cheap_client():
    """Create a mock cheap/fast client."""
    client = MagicMock(spec=BaseAIClient)
    client.get_provider_name.return_value = "cheap-model"
    client.generate = AsyncMock(return_value="Cheap response")
    return client


@pytest.fixture
def mock_expensive_client():
    """Create a mock expensive/smart client."""
    client = MagicMock(spec=BaseAIClient)
    client.get_provider_name.return_value = "expensive-model"
    client.generate = AsyncMock(return_value="Expensive response")
    return client


@pytest.fixture
def router(mock_cheap_client, mock_expensive_client):
    """Create a SmartAIRouter with mock clients."""
    return SmartAIRouter(
        cheap_client=mock_cheap_client,
        expensive_client=mock_expensive_client
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestSmartAIRouterInitialization:
    """Tests for SmartAIRouter initialization."""

    @pytest.mark.unit
    def test_initializes_with_provided_clients(self, mock_cheap_client, mock_expensive_client):
        """Verify router initializes with provided clients."""
        router = SmartAIRouter(
            cheap_client=mock_cheap_client,
            expensive_client=mock_expensive_client
        )

        assert router.cheap == mock_cheap_client
        assert router.expensive == mock_expensive_client

    @pytest.mark.unit
    def test_initializes_with_api_key(self):
        """Verify router initializes with API key."""
        with patch("src.core.smart_router.OpenAIClient") as mock_openai:
            mock_openai.return_value = MagicMock()

            router = SmartAIRouter(api_key="test-key")

            assert router.cheap is not None
            assert router.expensive is not None

    @pytest.mark.unit
    def test_raises_without_clients_or_key(self):
        """Verify router raises error without clients or API key."""
        with pytest.raises(ValueError, match="Must provide clients or API key"):
            SmartAIRouter()

    @pytest.mark.unit
    def test_initializes_counters_to_zero(self, router):
        """Verify request counters start at zero."""
        assert router.cheap_requests == 0
        assert router.expensive_requests == 0

    @pytest.mark.unit
    def test_get_provider_name_shows_both_models(self, router):
        """Verify provider name shows both model names."""
        name = router.get_provider_name()

        assert "SmartRouter" in name
        assert "cheap" in name
        assert "expensive" in name


# =============================================================================
# Complexity Estimation Tests
# =============================================================================


class TestComplexityEstimation:
    """Tests for task complexity estimation."""

    @pytest.mark.unit
    def test_simple_keyword_returns_simple(self, router):
        """Verify simple keywords result in 'simple' complexity."""
        simple_prompts = [
            "summarize this text",
            "list the main points",
            "extract the data",
            "find the company name",
            "search for results",
            "get the information",
        ]

        for prompt in simple_prompts:
            result = router._estimate_complexity(prompt)
            assert result == "simple", f"Expected 'simple' for: {prompt}"

    @pytest.mark.unit
    def test_complex_keyword_returns_complex(self, router):
        """Verify complex keywords result in 'complex' complexity."""
        complex_prompts = [
            "analyze this business strategy",
            "critique the approach",
            "evaluate the performance",
            "compare these competitors",
            "synthesize the findings",
            "strategic recommendations needed",
            "provide an in-depth assessment",
        ]

        for prompt in complex_prompts:
            result = router._estimate_complexity(prompt)
            assert result == "complex", f"Expected 'complex' for: {prompt}"

    @pytest.mark.unit
    def test_long_prompt_considered_complex(self, router):
        """Verify very long prompts are considered complex."""
        long_prompt = "x" * 3500  # > 3000 characters

        result = router._estimate_complexity(long_prompt)

        assert result == "complex"

    @pytest.mark.unit
    def test_system_prompt_affects_complexity(self, router):
        """Verify system prompt is considered in complexity."""
        prompt = "do this task"
        system = "you must analyze and evaluate carefully"

        result = router._estimate_complexity(prompt, system)

        assert result == "complex"

    @pytest.mark.unit
    def test_mixed_keywords_uses_scoring(self, router):
        """Verify mixed keywords use scoring to decide."""
        # More complex than simple keywords
        prompt = "analyze, critique, and evaluate this data"

        result = router._estimate_complexity(prompt)

        assert result == "complex"

    @pytest.mark.unit
    def test_no_keywords_defaults_to_simple(self, router):
        """Verify prompts without keywords default to simple."""
        prompt = "hello world"

        result = router._estimate_complexity(prompt)

        assert result == "simple"

    @pytest.mark.unit
    def test_case_insensitive_matching(self, router):
        """Verify keyword matching is case-insensitive."""
        prompts = [
            "ANALYZE this",
            "Summarize this",
            "sUmMaRiZe this",
        ]

        results = [router._estimate_complexity(p) for p in prompts]

        assert results[0] == "complex"  # ANALYZE
        assert results[1] == "simple"   # Summarize
        assert results[2] == "simple"   # sUmMaRiZe


# =============================================================================
# Request Routing Tests
# =============================================================================


class TestRequestRouting:
    """Tests for request routing to appropriate models."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_simple_task_uses_cheap_model(self, router, mock_cheap_client):
        """Verify simple tasks route to cheap model."""
        result = await router.generate("summarize this text")

        mock_cheap_client.generate.assert_called_once()
        assert result == "Cheap response"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_complex_task_uses_expensive_model(self, router, mock_expensive_client):
        """Verify complex tasks route to expensive model."""
        result = await router.generate("analyze and critique this strategy")

        mock_expensive_client.generate.assert_called_once()
        assert result == "Expensive response"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_force_cheap_model(self, router, mock_cheap_client, mock_expensive_client):
        """Verify force_model='cheap' uses cheap model regardless of complexity."""
        complex_prompt = "analyze and critique this strategy"

        result = await router.generate(complex_prompt, force_model="cheap")

        mock_cheap_client.generate.assert_called_once()
        mock_expensive_client.generate.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_force_expensive_model(self, router, mock_cheap_client, mock_expensive_client):
        """Verify force_model='expensive' uses expensive model regardless of complexity."""
        simple_prompt = "summarize this"

        result = await router.generate(simple_prompt, force_model="expensive")

        mock_expensive_client.generate.assert_called_once()
        mock_cheap_client.generate.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_parameters_passed_to_model(self, router, mock_cheap_client):
        """Verify all parameters are passed to selected model."""
        await router.generate(
            prompt="summarize this",
            system="Be concise",
            temperature=0.5,
            max_tokens=1000,
            response_format="json",
        )

        mock_cheap_client.generate.assert_called_once_with(
            "summarize this",
            "Be concise",
            0.5,
            1000,
            "json"
        )


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for routing statistics."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cheap_requests_incremented(self, router):
        """Verify cheap request counter increments."""
        assert router.cheap_requests == 0

        await router.generate("summarize this")

        assert router.cheap_requests == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_expensive_requests_incremented(self, router):
        """Verify expensive request counter increments."""
        assert router.expensive_requests == 0

        await router.generate("analyze this strategy")

        assert router.expensive_requests == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_stats_returns_correct_counts(self, router):
        """Verify get_stats returns correct request counts."""
        # Make some requests
        await router.generate("summarize")      # cheap
        await router.generate("summarize")      # cheap
        await router.generate("analyze")        # expensive

        stats = router.get_stats()

        assert stats["cheap_requests"] == 2
        assert stats["expensive_requests"] == 1
        assert stats["total_requests"] == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_stats_calculates_percentages(self, router):
        """Verify get_stats calculates correct percentages."""
        # Make 3 cheap, 1 expensive = 75% cheap
        await router.generate("summarize")
        await router.generate("list")
        await router.generate("extract")
        await router.generate("analyze deeply")

        stats = router.get_stats()

        assert stats["cheap_percentage"] == 75.0
        assert stats["estimated_cost_savings_percent"] > 70  # 75 * 0.97 ≈ 72.75

    @pytest.mark.unit
    def test_get_stats_with_no_requests(self, router):
        """Verify get_stats handles zero requests."""
        stats = router.get_stats()

        assert stats["total_requests"] == 0
        assert stats["cheap_percentage"] == 0
        assert stats["estimated_cost_savings_percent"] == 0


# =============================================================================
# Counter Reset Tests
# =============================================================================


class TestCounterReset:
    """Tests for periodic counter reset functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_counters_reset_after_interval(self, router):
        """Verify counters reset after configured interval."""
        # Make some requests
        await router.generate("summarize")
        await router.generate("analyze")

        assert router.cheap_requests == 1
        assert router.expensive_requests == 1

        # Simulate time passing beyond reset interval
        router._counter_reset_time = time.time() - (COUNTER_RESET_INTERVAL + 1)

        # Next request should trigger reset
        await router.generate("summarize")

        # Counters should have been reset, then incremented
        assert router.cheap_requests == 1
        assert router.expensive_requests == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_counters_not_reset_before_interval(self, router):
        """Verify counters don't reset before interval."""
        await router.generate("summarize")
        await router.generate("analyze")

        # Don't change time - should not reset
        await router.generate("summarize")

        assert router.cheap_requests == 2
        assert router.expensive_requests == 1


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_prompt_handled(self, router):
        """Verify empty prompt is handled."""
        result = await router.generate("")

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_none_system_handled(self, router):
        """Verify None system prompt is handled."""
        result = await router.generate("test", system=None)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_model_error_propagates(self, router, mock_cheap_client):
        """Verify errors from underlying model propagate."""
        mock_cheap_client.generate.side_effect = Exception("Model error")

        with pytest.raises(Exception, match="Model error"):
            await router.generate("summarize")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_whitespace_prompt_handled(self, router):
        """Verify whitespace-only prompt is handled."""
        result = await router.generate("   ")

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unicode_in_complexity_estimation(self, router):
        """Verify unicode characters don't break complexity estimation."""
        prompt = "analyze 分析 this تحليل data"

        result = router._estimate_complexity(prompt)

        # Should detect "analyze" keyword
        assert result == "complex"


# =============================================================================
# Ollama Hybrid Mode Tests
# =============================================================================


class TestOllamaHybridMode:
    """Tests for Ollama hybrid mode (local + cloud)."""

    @pytest.mark.unit
    def test_ollama_hybrid_initialization(self):
        """Verify Ollama hybrid mode initializes correctly."""
        with patch("src.core.smart_router.OllamaClient") as mock_ollama, \
             patch("src.core.smart_router.OpenAIClient") as mock_openai:

            mock_ollama.return_value = MagicMock()
            mock_openai.return_value = MagicMock()

            router = SmartAIRouter(api_key="test-key", use_ollama=True)

            mock_ollama.assert_called_once()
            mock_openai.assert_called_once()
