"""
Unit tests for AI client module.

Tests the AI client abstraction, including:
- MockAIClient behavior
- Client provider names
- Response format handling
- Error handling and exceptions
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

# Import the modules under test
from src.core.ai.ai_client import (
    BaseAIClient,
    MockAIClient,
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    GroqClient,
    OllamaClient,
    AIClientManager,
)
from src.core.exceptions.base import (
    AIProviderError,
    AIRateLimitError,
)


# =============================================================================
# MockAIClient Tests
# =============================================================================


class TestMockAIClient:
    """Tests for MockAIClient."""

    @pytest.fixture
    def mock_client(self):
        """Provide a MockAIClient instance."""
        return MockAIClient()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_returns_text_response(self, mock_client):
        """Verify generate returns text response by default."""
        result = await mock_client.generate("test prompt")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_returns_json_when_requested(self, mock_client):
        """Verify generate returns JSON when response_format is json."""
        result = await mock_client.generate("test prompt", response_format="json")

        assert result is not None
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "mock_key" in parsed

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_accepts_system_prompt(self, mock_client):
        """Verify generate accepts system prompt parameter."""
        result = await mock_client.generate(
            "test prompt",
            system="You are a helpful assistant"
        )

        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_accepts_temperature(self, mock_client):
        """Verify generate accepts temperature parameter."""
        result = await mock_client.generate(
            "test prompt",
            temperature=0.5
        )

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_accepts_max_tokens(self, mock_client):
        """Verify generate accepts max_tokens parameter."""
        result = await mock_client.generate(
            "test prompt",
            max_tokens=1000
        )

        assert result is not None

    @pytest.mark.unit
    def test_get_provider_name_returns_mock(self, mock_client):
        """Verify provider name is 'mock'."""
        assert mock_client.get_provider_name() == "mock"


# =============================================================================
# OpenAIClient Tests
# =============================================================================


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    @pytest.fixture
    def mock_openai(self):
        """Mock the OpenAI client."""
        with patch("src.core.ai_client.AsyncOpenAI") as mock:
            # Create mock response structure
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"

            mock.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )
            yield mock

    @pytest.mark.unit
    def test_get_provider_name_returns_openai(self, mock_openai):
        """Verify provider name is 'openai'."""
        client = OpenAIClient(api_key="test-key")
        assert client.get_provider_name() == "openai"

    @pytest.mark.unit
    def test_initializes_with_api_key(self, mock_openai):
        """Verify client initializes with API key."""
        client = OpenAIClient(api_key="test-key")
        assert client.model == "gpt-4-turbo-preview"

    @pytest.mark.unit
    def test_initializes_with_custom_model(self, mock_openai):
        """Verify client initializes with custom model."""
        client = OpenAIClient(api_key="test-key", model="gpt-4")
        assert client.model == "gpt-4"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_calls_openai_api(self, mock_openai):
        """Verify generate calls OpenAI API correctly."""
        client = OpenAIClient(api_key="test-key")
        result = await client.generate("test prompt")

        assert result == "Test response"
        mock_openai.return_value.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_with_system_prompt(self, mock_openai):
        """Verify system prompt is included in messages."""
        client = OpenAIClient(api_key="test-key")
        await client.generate("test prompt", system="System instructions")

        call_args = mock_openai.return_value.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System instructions"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_json_format(self, mock_openai):
        """Verify JSON response format is requested correctly."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_openai.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        client = OpenAIClient(api_key="test-key")
        result = await client.generate("test prompt", response_format="json")

        call_args = mock_openai.return_value.chat.completions.create.call_args
        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_raises_rate_limit_error(self, mock_openai):
        """Verify rate limit errors are wrapped correctly."""
        from openai import RateLimitError as OpenAIRateLimitError

        mock_openai.return_value.chat.completions.create = AsyncMock(
            side_effect=OpenAIRateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body={}
            )
        )

        client = OpenAIClient(api_key="test-key")

        with pytest.raises(AIRateLimitError):
            await client.generate("test prompt")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_raises_provider_error_on_api_error(self, mock_openai):
        """Verify API errors are wrapped as AIProviderError."""
        from openai import APIError as OpenAIAPIError

        mock_openai.return_value.chat.completions.create = AsyncMock(
            side_effect=OpenAIAPIError(
                message="API Error",
                request=MagicMock(),
                body={}
            )
        )

        client = OpenAIClient(api_key="test-key")

        with pytest.raises(AIProviderError):
            await client.generate("test prompt")


# =============================================================================
# AnthropicClient Tests
# =============================================================================


class TestAnthropicClient:
    """Tests for AnthropicClient."""

    @pytest.fixture
    def mock_anthropic(self):
        """Mock the Anthropic client."""
        with patch("src.core.ai_client.AsyncAnthropic") as mock:
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Test response"

            mock.return_value.messages.create = AsyncMock(
                return_value=mock_response
            )
            yield mock

    @pytest.mark.unit
    def test_get_provider_name_returns_anthropic(self, mock_anthropic):
        """Verify provider name is 'anthropic'."""
        client = AnthropicClient(api_key="test-key")
        assert client.get_provider_name() == "anthropic"

    @pytest.mark.unit
    def test_initializes_with_default_model(self, mock_anthropic):
        """Verify client initializes with default model."""
        client = AnthropicClient(api_key="test-key")
        assert "claude" in client.model

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_calls_anthropic_api(self, mock_anthropic):
        """Verify generate calls Anthropic API correctly."""
        client = AnthropicClient(api_key="test-key")
        result = await client.generate("test prompt")

        assert result == "Test response"
        mock_anthropic.return_value.messages.create.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_with_system_prompt(self, mock_anthropic):
        """Verify system prompt is passed to API."""
        client = AnthropicClient(api_key="test-key")
        await client.generate("test prompt", system="System instructions")

        call_args = mock_anthropic.return_value.messages.create.call_args
        assert call_args.kwargs["system"] == "System instructions"


# =============================================================================
# AIClientManager Tests
# =============================================================================


class TestAIClientManager:
    """Tests for AIClientManager."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.core.ai_client.get_settings") as mock:
            settings = MagicMock()
            settings.OPENAI_API_KEY = None
            settings.ANTHROPIC_API_KEY = None
            settings.GEMINI_API_KEY = None
            settings.GROQ_API_KEY = None
            settings.ai.primary = "openai"
            settings.ai.fallback = "anthropic"
            settings.ai.openai.model = "gpt-4"
            settings.ai.anthropic.model = "claude-3"
            settings.ai.gemini.model = "gemini-pro"
            settings.ai.groq.model = "llama3"
            settings.ai.ollama.model = "llama3"
            mock.return_value = settings
            yield settings

    @pytest.mark.unit
    def test_manager_initializes_with_mock_fallback(self, mock_settings):
        """Verify manager falls back to mock when no API keys."""
        manager = AIClientManager()

        assert manager.primary_client is None
        assert manager.fallback_client is None
        assert manager.mock_client is not None

    @pytest.mark.unit
    def test_get_client_for_task_returns_mock_without_keys(self, mock_settings):
        """Verify get_client_for_task returns mock without API keys."""
        manager = AIClientManager()
        client = manager.get_client_for_task("general")

        assert client.get_provider_name() == "mock"

    @pytest.mark.unit
    def test_get_client_for_task_with_openai_key(self, mock_settings):
        """Verify get_client_for_task returns OpenAI with API key."""
        mock_settings.OPENAI_API_KEY = "test-key"

        with patch("src.core.ai_client.AsyncOpenAI"):
            manager = AIClientManager()

            assert manager.primary_client is not None
            assert manager.primary_client.get_provider_name() == "openai"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_uses_mock_without_api_keys(self, mock_settings):
        """Verify generate uses mock when no API keys configured."""
        manager = AIClientManager()

        result = await manager.generate("test prompt")

        assert result is not None
        assert "mock" in result.lower() or len(result) > 0

    @pytest.mark.unit
    def test_get_provider_name_shows_manager_status(self, mock_settings):
        """Verify provider name shows manager status."""
        manager = AIClientManager()
        name = manager.get_provider_name()

        assert "Manager" in name


# =============================================================================
# BaseAIClient Abstract Tests
# =============================================================================


class TestBaseAIClient:
    """Tests for BaseAIClient abstract class."""

    @pytest.mark.unit
    def test_cannot_instantiate_base_class(self):
        """Verify BaseAIClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAIClient()

    @pytest.mark.unit
    def test_subclass_must_implement_generate(self):
        """Verify subclass must implement generate method."""

        class IncompleteClient(BaseAIClient):
            def get_provider_name(self):
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteClient()

    @pytest.mark.unit
    def test_subclass_must_implement_get_provider_name(self):
        """Verify subclass must implement get_provider_name method."""

        class IncompleteClient(BaseAIClient):
            async def generate(self, prompt, **kwargs):
                return "test"

        with pytest.raises(TypeError):
            IncompleteClient()


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_prompt_handled(self):
        """Verify empty prompt is handled gracefully."""
        client = MockAIClient()
        result = await client.generate("")

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_very_long_prompt_handled(self):
        """Verify very long prompt is handled."""
        client = MockAIClient()
        long_prompt = "x" * 100000
        result = await client.generate(long_prompt)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_special_characters_in_prompt(self):
        """Verify special characters in prompt are handled."""
        client = MockAIClient()
        special_prompt = "Test with special chars: <>&\"'{}[]|\\`~!@#$%^*()"
        result = await client.generate(special_prompt)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unicode_in_prompt(self):
        """Verify unicode characters in prompt are handled."""
        client = MockAIClient()
        unicode_prompt = "Test with unicode: 你好世界 مرحبا العالم 🌍🚀"
        result = await client.generate(unicode_prompt)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_zero_temperature(self):
        """Verify zero temperature is handled."""
        client = MockAIClient()
        result = await client.generate("test", temperature=0.0)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_high_temperature(self):
        """Verify high temperature is handled."""
        client = MockAIClient()
        result = await client.generate("test", temperature=2.0)

        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_small_max_tokens(self):
        """Verify small max_tokens is handled."""
        client = MockAIClient()
        result = await client.generate("test", max_tokens=1)

        assert result is not None
