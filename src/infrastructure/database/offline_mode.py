"""
Offline Mode support for running without internet.

Provides infrastructure for using local LLMs (Ollama, LlamaCpp) and
local embeddings when running in offline/air-gapped environments.
"""

import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

from src.infrastructure.logging import setup_logger

logger = setup_logger("offline_mode")


class OfflineProvider(str, Enum):
    """Available offline LLM providers."""

    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    TRANSFORMERS = "transformers"
    MOCK = "mock"  # For testing


class EmbeddingProvider(str, Enum):
    """Available offline embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    MOCK = "mock"


@dataclass
class OfflineConfig:
    """Configuration for offline mode."""

    # Mode settings
    enabled: bool = False
    fallback_to_online: bool = False

    # LLM settings
    llm_provider: OfflineProvider = OfflineProvider.OLLAMA
    llm_model: str = "llama3"
    llm_base_url: str = "http://localhost:11434"

    # LlamaCpp specific
    llama_cpp_model_path: Optional[str] = None
    llama_cpp_n_ctx: int = 4096
    llama_cpp_n_gpu_layers: int = -1

    # Embedding settings
    embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS
    embedding_model: str = "all-MiniLM-L6-v2"

    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9

    # Caching
    cache_responses: bool = True
    cache_embeddings: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "fallback_to_online": self.fallback_to_online,
            "llm_provider": self.llm_provider.value,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "embedding_provider": self.embedding_provider.value,
            "embedding_model": self.embedding_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OfflineConfig":
        """Create from dictionary."""
        if "llm_provider" in data:
            data["llm_provider"] = OfflineProvider(data["llm_provider"])
        if "embedding_provider" in data:
            data["embedding_provider"] = EmbeddingProvider(data["embedding_provider"])
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class GenerationResult:
    """Result from LLM generation."""

    text: str
    model: str
    provider: str

    # Token counts
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Timing
    latency_ms: float = 0.0

    # Additional info
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "finish_reason": self.finish_reason,
        }


class BaseLLMProvider(ABC):
    """Base class for offline LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> GenerationResult:
        """Generate a response."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local inference."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialize Ollama provider.

        Args:
            model: Model name.
            base_url: Ollama server URL.
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        if self._available is not None:
            return self._available

        try:
            import urllib.request
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                self._available = response.status == 200
        except Exception:
            self._available = False

        return self._available

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> GenerationResult:
        """Generate using Ollama API."""
        import json
        import time
        import urllib.request

        start_time = time.time()

        # Build request
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            data["system"] = system

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())

            latency = (time.time() - start_time) * 1000

            return GenerationResult(
                text=result.get("response", ""),
                model=self.model,
                provider="ollama",
                prompt_tokens=result.get("prompt_eval_count", 0),
                completion_tokens=result.get("eval_count", 0),
                total_tokens=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                latency_ms=latency,
                finish_reason="stop",
            )

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return GenerationResult(
                text="",
                model=self.model,
                provider="ollama",
                metadata={"error": str(e)},
            )

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream generation from Ollama."""
        import json
        import urllib.request

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            data["system"] = system

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                for line in response:
                    if line:
                        chunk = json.loads(line.decode())
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break

        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield ""


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""

    def __init__(self, model: str = "mock-model"):
        self.model = model

    def is_available(self) -> bool:
        return True

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> GenerationResult:
        """Return mock response."""
        response = f"Mock response to: {prompt[:50]}..."
        return GenerationResult(
            text=response,
            model=self.model,
            provider="mock",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(response.split()),
            total_tokens=len(prompt.split()) + len(response.split()),
            latency_ms=10.0,
            finish_reason="stop",
        )

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream mock response."""
        response = f"Mock response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.01)


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider for testing."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings."""
        import hashlib

        embeddings = []
        for text in texts:
            # Generate deterministic embedding based on text hash
            hash_bytes = hashlib.sha256(text.encode()).digest()
            embedding = []
            for i in range(self._dimension):
                byte_idx = i % len(hash_bytes)
                embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate mock query embedding."""
        return self.embed([text])[0]


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """Sentence Transformers embedding provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize provider.

        Args:
            model_name: HuggingFace model name.
        """
        self.model_name = model_name
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not installed, using mock")
                self._model = MockEmbeddingProvider()
                self._dimension = 384

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension or 384

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings."""
        self._load_model()

        if isinstance(self._model, MockEmbeddingProvider):
            return self._model.embed(texts)

        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generate query embedding."""
        return self.embed([text])[0]


class OfflineManager:
    """
    Manages offline mode operations.

    Provides a unified interface for local LLM and embedding operations.
    """

    def __init__(self, config: Optional[OfflineConfig] = None):
        """
        Initialize the offline manager.

        Args:
            config: Offline configuration.
        """
        self.config = config or OfflineConfig()
        self._llm_provider: Optional[BaseLLMProvider] = None
        self._embedding_provider: Optional[BaseEmbeddingProvider] = None
        self._lock = threading.Lock()

    def _get_llm_provider(self) -> BaseLLMProvider:
        """Get or create LLM provider."""
        if self._llm_provider is None:
            if self.config.llm_provider == OfflineProvider.OLLAMA:
                self._llm_provider = OllamaProvider(
                    model=self.config.llm_model,
                    base_url=self.config.llm_base_url,
                )
            elif self.config.llm_provider == OfflineProvider.MOCK:
                self._llm_provider = MockProvider(self.config.llm_model)
            else:
                # Default to mock if provider not implemented
                logger.warning(f"Provider {self.config.llm_provider} not implemented, using mock")
                self._llm_provider = MockProvider()

        return self._llm_provider

    def _get_embedding_provider(self) -> BaseEmbeddingProvider:
        """Get or create embedding provider."""
        if self._embedding_provider is None:
            if self.config.embedding_provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
                self._embedding_provider = SentenceTransformersProvider(
                    model_name=self.config.embedding_model,
                )
            elif self.config.embedding_provider == EmbeddingProvider.MOCK:
                self._embedding_provider = MockEmbeddingProvider()
            else:
                logger.warning(f"Embedding provider {self.config.embedding_provider} not implemented")
                self._embedding_provider = MockEmbeddingProvider()

        return self._embedding_provider

    def is_available(self) -> bool:
        """Check if offline mode is available."""
        provider = self._get_llm_provider()
        return provider.is_available()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """
        Generate a response using local LLM.

        Args:
            prompt: User prompt.
            system: System prompt.
            **kwargs: Additional generation parameters.

        Returns:
            GenerationResult.
        """
        provider = self._get_llm_provider()

        return await provider.generate(
            prompt=prompt,
            system=system,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            **kwargs,
        )

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a response using local LLM.

        Args:
            prompt: User prompt.
            system: System prompt.
            **kwargs: Additional generation parameters.

        Yields:
            Response text chunks.
        """
        provider = self._get_llm_provider()

        async for chunk in provider.generate_stream(
            prompt=prompt,
            system=system,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            **kwargs,
        ):
            yield chunk

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        provider = self._get_embedding_provider()
        return provider.embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            text: Query text.

        Returns:
            Embedding vector.
        """
        provider = self._get_embedding_provider()
        return provider.embed_query(text)

    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension."""
        provider = self._get_embedding_provider()
        return provider.dimension

    def get_status(self) -> Dict[str, Any]:
        """Get offline mode status."""
        llm_provider = self._get_llm_provider()

        return {
            "enabled": self.config.enabled,
            "llm_provider": self.config.llm_provider.value,
            "llm_model": self.config.llm_model,
            "llm_available": llm_provider.is_available(),
            "embedding_provider": self.config.embedding_provider.value,
            "embedding_model": self.config.embedding_model,
            "embedding_dimension": self.embedding_dimension,
        }


# Global instance
_manager: Optional[OfflineManager] = None
_global_lock = threading.Lock()


def get_offline_manager(config: Optional[OfflineConfig] = None) -> OfflineManager:
    """Get or create the global offline manager."""
    global _manager
    with _global_lock:
        if _manager is None:
            _manager = OfflineManager(config)
        return _manager


def reset_offline_manager() -> None:
    """Reset the global manager (for testing)."""
    global _manager
    with _global_lock:
        _manager = None


def is_offline_available() -> bool:
    """Quick check if offline mode is available."""
    manager = get_offline_manager()
    return manager.is_available()
