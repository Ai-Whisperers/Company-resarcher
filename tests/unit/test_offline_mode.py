"""Tests for offline mode support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.persistence.offline_mode import (
    BaseEmbeddingProvider,
    BaseLLMProvider,
    EmbeddingProvider,
    GenerationResult,
    MockEmbeddingProvider,
    MockProvider,
    OfflineConfig,
    OfflineManager,
    OfflineProvider,
    OllamaProvider,
    SentenceTransformersProvider,
    get_offline_manager,
    is_offline_available,
    reset_offline_manager,
)


class TestOfflineConfig:
    """Tests for OfflineConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = OfflineConfig()

        assert config.enabled is False
        assert config.llm_provider == OfflineProvider.OLLAMA
        assert config.llm_model == "llama3"
        assert config.embedding_provider == EmbeddingProvider.SENTENCE_TRANSFORMERS

    def test_custom_config(self):
        """Test custom configuration."""
        config = OfflineConfig(
            enabled=True,
            llm_provider=OfflineProvider.LLAMA_CPP,
            llm_model="mistral",
            temperature=0.5,
        )

        assert config.enabled is True
        assert config.llm_provider == OfflineProvider.LLAMA_CPP
        assert config.llm_model == "mistral"
        assert config.temperature == 0.5

    def test_to_dict(self):
        """Test serialization."""
        config = OfflineConfig(enabled=True, temperature=0.8)
        data = config.to_dict()

        assert data["enabled"] is True
        assert data["temperature"] == 0.8
        assert data["llm_provider"] == "ollama"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "enabled": True,
            "llm_provider": "mock",
            "llm_model": "test-model",
        }
        config = OfflineConfig.from_dict(data)

        assert config.enabled is True
        assert config.llm_provider == OfflineProvider.MOCK
        assert config.llm_model == "test-model"


class TestGenerationResult:
    """Tests for GenerationResult class."""

    def test_create_result(self):
        """Test creating a result."""
        result = GenerationResult(
            text="Generated response",
            model="llama3",
            provider="ollama",
            prompt_tokens=10,
            completion_tokens=20,
        )

        assert result.text == "Generated response"
        assert result.total_tokens == 30

    def test_to_dict(self):
        """Test serialization."""
        result = GenerationResult(
            text="Response",
            model="model",
            provider="provider",
            latency_ms=150.5,
        )
        data = result.to_dict()

        assert data["text"] == "Response"
        assert data["latency_ms"] == 150.5


class TestMockProvider:
    """Tests for MockProvider class."""

    def setup_method(self):
        """Create provider."""
        self.provider = MockProvider()

    def test_is_available(self):
        """Test availability check."""
        assert self.provider.is_available() is True

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test generation."""
        result = await self.provider.generate("Test prompt")

        assert result.text is not None
        assert "Mock response" in result.text
        assert result.provider == "mock"

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        """Test generation with system prompt."""
        result = await self.provider.generate(
            "Test prompt",
            system="You are helpful",
        )

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        chunks = []
        async for chunk in self.provider.generate_stream("Test prompt"):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert "Mock response" in full_text


class TestOllamaProvider:
    """Tests for OllamaProvider class."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OllamaProvider(model="mistral", base_url="http://localhost:11434")

        assert provider.model == "mistral"
        assert provider.base_url == "http://localhost:11434"

    def test_is_available_offline(self):
        """Test availability when Ollama not running."""
        provider = OllamaProvider(base_url="http://localhost:99999")

        # Should return False when Ollama is not available
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_mock(self):
        """Test generation with mocked response."""
        provider = OllamaProvider()

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"response": "Test response", "done": true}'
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = await provider.generate("Test prompt")

            assert result.text == "Test response"


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider class."""

    def setup_method(self):
        """Create provider."""
        self.provider = MockEmbeddingProvider(dimension=128)

    def test_dimension(self):
        """Test dimension property."""
        assert self.provider.dimension == 128

    def test_embed_single(self):
        """Test embedding single text."""
        embeddings = self.provider.embed(["Hello world"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 128

    def test_embed_multiple(self):
        """Test embedding multiple texts."""
        texts = ["Text one", "Text two", "Text three"]
        embeddings = self.provider.embed(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 128

    def test_embed_query(self):
        """Test embedding query."""
        embedding = self.provider.embed_query("Query text")

        assert len(embedding) == 128

    def test_deterministic(self):
        """Test embeddings are deterministic."""
        emb1 = self.provider.embed(["Test"])[0]
        emb2 = self.provider.embed(["Test"])[0]

        assert emb1 == emb2

    def test_different_texts_different_embeddings(self):
        """Test different texts get different embeddings."""
        emb1 = self.provider.embed(["Text A"])[0]
        emb2 = self.provider.embed(["Text B"])[0]

        assert emb1 != emb2


class TestSentenceTransformersProvider:
    """Tests for SentenceTransformersProvider class."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = SentenceTransformersProvider(model_name="test-model")

        assert provider.model_name == "test-model"

    def test_fallback_to_mock(self):
        """Test fallback to mock when library not available."""
        provider = SentenceTransformersProvider()

        # Should fall back to mock if sentence-transformers not installed
        # This will use mock or real depending on environment
        embedding = provider.embed_query("Test")
        assert len(embedding) > 0


class TestOfflineManager:
    """Tests for OfflineManager class."""

    def setup_method(self):
        """Create manager with mock config."""
        self.config = OfflineConfig(
            enabled=True,
            llm_provider=OfflineProvider.MOCK,
            embedding_provider=EmbeddingProvider.MOCK,
        )
        self.manager = OfflineManager(self.config)

    def test_is_available(self):
        """Test availability check."""
        assert self.manager.is_available() is True

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test generation."""
        result = await self.manager.generate("Test prompt")

        assert isinstance(result, GenerationResult)
        assert result.text is not None

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        """Test generation with system prompt."""
        result = await self.manager.generate(
            "Test prompt",
            system="You are an assistant",
        )

        assert result.text is not None

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        chunks = []
        async for chunk in self.manager.generate_stream("Test prompt"):
            chunks.append(chunk)

        assert len(chunks) > 0

    def test_embed(self):
        """Test embedding generation."""
        embeddings = self.manager.embed(["Text 1", "Text 2"])

        assert len(embeddings) == 2

    def test_embed_query(self):
        """Test query embedding."""
        embedding = self.manager.embed_query("Query text")

        assert len(embedding) > 0

    def test_embedding_dimension(self):
        """Test embedding dimension property."""
        dim = self.manager.embedding_dimension

        assert dim > 0

    def test_get_status(self):
        """Test getting status."""
        status = self.manager.get_status()

        assert "enabled" in status
        assert "llm_provider" in status
        assert "llm_available" in status
        assert "embedding_dimension" in status

    @pytest.mark.asyncio
    async def test_custom_parameters(self):
        """Test custom generation parameters."""
        result = await self.manager.generate(
            "Test",
            temperature=0.5,
            max_tokens=100,
        )

        assert result.text is not None


class TestOfflineManagerProviderSelection:
    """Tests for provider selection."""

    def test_ollama_provider(self):
        """Test Ollama provider selection."""
        config = OfflineConfig(llm_provider=OfflineProvider.OLLAMA)
        manager = OfflineManager(config)

        provider = manager._get_llm_provider()
        assert isinstance(provider, OllamaProvider)

    def test_mock_provider(self):
        """Test mock provider selection."""
        config = OfflineConfig(llm_provider=OfflineProvider.MOCK)
        manager = OfflineManager(config)

        provider = manager._get_llm_provider()
        assert isinstance(provider, MockProvider)

    def test_mock_embedding_provider(self):
        """Test mock embedding provider selection."""
        config = OfflineConfig(embedding_provider=EmbeddingProvider.MOCK)
        manager = OfflineManager(config)

        provider = manager._get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_offline_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_offline_manager()

    def test_get_offline_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_offline_manager()
        m2 = get_offline_manager()
        assert m1 is m2

    def test_get_offline_manager_with_config(self):
        """Test getting manager with config."""
        config = OfflineConfig(enabled=True)
        manager = get_offline_manager(config)

        assert manager.config.enabled is True

    def test_reset_offline_manager(self):
        """Test resetting singleton."""
        m1 = get_offline_manager()
        reset_offline_manager()
        m2 = get_offline_manager()
        assert m1 is not m2

    def test_is_offline_available(self):
        """Test convenience availability check."""
        # With mock provider, should be available
        config = OfflineConfig(llm_provider=OfflineProvider.MOCK)
        reset_offline_manager()
        get_offline_manager(config)

        assert is_offline_available() is True


class TestProviderEnums:
    """Tests for provider enums."""

    def test_offline_providers(self):
        """Test all offline providers."""
        providers = [
            OfflineProvider.OLLAMA,
            OfflineProvider.LLAMA_CPP,
            OfflineProvider.TRANSFORMERS,
            OfflineProvider.MOCK,
        ]
        assert len(providers) == len(OfflineProvider)

    def test_embedding_providers(self):
        """Test all embedding providers."""
        providers = [
            EmbeddingProvider.SENTENCE_TRANSFORMERS,
            EmbeddingProvider.OLLAMA,
            EmbeddingProvider.HUGGINGFACE,
            EmbeddingProvider.MOCK,
        ]
        assert len(providers) == len(EmbeddingProvider)

    def test_provider_values(self):
        """Test provider string values."""
        assert OfflineProvider.OLLAMA.value == "ollama"
        assert EmbeddingProvider.SENTENCE_TRANSFORMERS.value == "sentence_transformers"
