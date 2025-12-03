"""
Tests for the Langfuse observability integration.

Tests cover:
- Graceful degradation when Langfuse is not configured
- ObservabilityContext functionality
- Span and generation tracking
- Integration with AI client
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.core.logging.observability import (
    get_langfuse,
    reset_langfuse,
    ObservabilityContext,
    SpanContext,
    GenerationContext,
    trace_ai_call,
    trace_operation,
)


class TestLangfuseInitialization:
    """Test Langfuse client initialization."""

    def setup_method(self):
        """Reset Langfuse client before each test."""
        reset_langfuse()

    def test_get_langfuse_returns_none_without_keys(self):
        """Should return None when Langfuse keys are not configured."""
        with patch("src.core.observability.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                LANGFUSE_PUBLIC_KEY=None,
                LANGFUSE_SECRET_KEY=None,
                LANGFUSE_HOST="https://cloud.langfuse.com",
                LANGFUSE_ENABLED=True,
            )
            reset_langfuse()
            client = get_langfuse()
            assert client is None

    def test_get_langfuse_returns_none_when_disabled(self):
        """Should return None when LANGFUSE_ENABLED is False."""
        with patch("src.core.observability.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                LANGFUSE_PUBLIC_KEY="pk-test",
                LANGFUSE_SECRET_KEY="sk-test",
                LANGFUSE_HOST="https://cloud.langfuse.com",
                LANGFUSE_ENABLED=False,
            )
            reset_langfuse()
            client = get_langfuse()
            assert client is None


class TestObservabilityContext:
    """Test ObservabilityContext functionality."""

    def setup_method(self):
        """Reset Langfuse client before each test."""
        reset_langfuse()

    def test_context_works_without_langfuse(self):
        """Context should work gracefully when Langfuse is not configured."""
        with patch("src.core.observability.get_langfuse", return_value=None):
            with ObservabilityContext(
                company_name="Test Company",
                research_type="test",
                metadata={"key": "value"},
            ) as ctx:
                assert ctx.company_name == "Test Company"
                assert ctx.research_type == "test"
                assert ctx.trace is None
                assert ctx.langfuse is None

    def test_span_returns_dummy_without_langfuse(self):
        """Span should return DummySpan when Langfuse is not configured."""
        with patch("src.core.observability.get_langfuse", return_value=None):
            with ObservabilityContext("Test Company") as ctx:
                span = ctx.span("test_span", input_data={"query": "test"})
                assert isinstance(span, SpanContext)
                # Should not raise when ending
                span.end(output={"result": "ok"})

    def test_generation_returns_dummy_without_langfuse(self):
        """Generation should return DummyGeneration when Langfuse is not configured."""
        with patch("src.core.observability.get_langfuse", return_value=None):
            with ObservabilityContext("Test Company") as ctx:
                gen = ctx.generation(
                    name="test_gen",
                    model="gpt-4",
                    input_prompt="Hello",
                )
                assert isinstance(gen, GenerationContext)
                # Should not raise when ending
                gen.end(
                    output="World",
                    usage={"input_tokens": 10, "output_tokens": 5},
                )


class TestSpanContext:
    """Test SpanContext functionality."""

    def test_span_context_as_context_manager(self):
        """SpanContext should work as a context manager."""
        span = SpanContext(None, "test_span")
        with span:
            pass  # Should not raise

    def test_span_context_end_without_langfuse(self):
        """SpanContext.end should not raise without Langfuse."""
        span = SpanContext(None, "test_span")
        span.end(output={"result": "ok"}, metadata={"key": "value"})


class TestGenerationContext:
    """Test GenerationContext functionality."""

    def test_generation_context_end_without_langfuse(self):
        """GenerationContext.end should not raise without Langfuse."""
        gen = GenerationContext(None, "test_gen", "gpt-4")
        gen.end(
            output="Hello World",
            usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            metadata={"success": True},
        )


class TestTraceAICallDecorator:
    """Test trace_ai_call decorator."""

    @pytest.mark.asyncio
    async def test_decorator_works_without_context(self):
        """Decorator should work when no trace context is provided."""

        class MockClient:
            model = "test-model"

            @trace_ai_call
            async def generate(self, prompt: str) -> str:
                return f"Response to: {prompt}"

        client = MockClient()
        result = await client.generate("Hello")
        assert result == "Response to: Hello"

    @pytest.mark.asyncio
    async def test_decorator_with_context(self):
        """Decorator should work with trace context."""
        with patch("src.core.observability.get_langfuse", return_value=None):

            class MockClient:
                model = "test-model"

                @trace_ai_call
                async def generate(self, prompt: str, **kwargs) -> str:
                    return f"Response to: {prompt}"

            client = MockClient()
            with ObservabilityContext("Test Company") as ctx:
                result = await client.generate("Hello", _trace_context=ctx)
                assert result == "Response to: Hello"

    @pytest.mark.asyncio
    async def test_decorator_handles_exceptions(self):
        """Decorator should handle exceptions gracefully."""

        class MockClient:
            model = "test-model"

            @trace_ai_call
            async def generate(self, prompt: str) -> str:
                raise ValueError("Test error")

        client = MockClient()
        with pytest.raises(ValueError, match="Test error"):
            await client.generate("Hello")


class TestTraceOperation:
    """Test trace_operation async context manager."""

    @pytest.mark.asyncio
    async def test_trace_operation_without_langfuse(self):
        """trace_operation should work when Langfuse is not configured."""
        with patch("src.core.observability.get_langfuse", return_value=None):
            async with trace_operation("test_op", company="Test") as trace:
                assert trace is None  # No trace when Langfuse disabled

    @pytest.mark.asyncio
    async def test_trace_operation_yields_trace(self):
        """trace_operation should yield trace object when Langfuse is configured."""
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace

        with patch("src.core.observability.get_langfuse", return_value=mock_langfuse):
            async with trace_operation("test_op", company="Test") as trace:
                assert trace == mock_trace

            # Verify flush was called
            mock_langfuse.flush.assert_called()


class TestIntegration:
    """Integration tests for observability."""

    def test_import_from_ai_client(self):
        """Should be able to import observability from ai_client."""
        from src.core.ai.ai_client import get_langfuse, ObservabilityContext

        assert get_langfuse is not None
        assert ObservabilityContext is not None

    def test_import_from_comprehensive_research(self):
        """Should be able to import ObservabilityContext in research pipeline."""
        from src.pipeline.comprehensive_research import ObservabilityContext

        assert ObservabilityContext is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
