import json
import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Optional
import google.generativeai as genai
from anthropic import AsyncAnthropic, APIError, RateLimitError as AnthropicRateLimitError
from openai import (
    AsyncOpenAI,
    APIError as OpenAIAPIError,
    RateLimitError as OpenAIRateLimitError,
)
from google.api_core import exceptions as google_exceptions

from ..core.config import get_settings
from ..core.exceptions import (
    AIProviderError,
    AIRateLimitError,
    AIResponseError,
    AITimeoutError,
)
from ..core.logger import setup_logger
from ..core.result import Result, Ok, Err, AIError
from .cache import get_ai_cache

logger = setup_logger("ai_client")

# =============================================================================
# Base AI Client
# =============================================================================


class BaseAIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        pass

    async def generate_safe(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> Result[str, AIError]:
        """
        Generate response with explicit error handling via Result type.

        Returns Ok(response) on success, Err(AIError) on failure.
        This is the recommended method for new code.
        """
        try:
            response = await self.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            return Ok(response)
        except AIRateLimitError:
            return Err(AIError.rate_limited(f"Rate limit exceeded for {self.get_provider_name()}"))
        except AIProviderError as e:
            return Err(AIError(
                code=AIError.MODEL_ERROR,
                message=str(e),
                details={"provider": self.get_provider_name()},
                recoverable=True,
            ))
        except asyncio.TimeoutError:
            return Err(AIError.timeout(f"Request to {self.get_provider_name()} timed out"))
        except Exception as e:
            return Err(AIError.connection_error(f"{self.get_provider_name()}: {str(e)}"))

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Anthropic client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = await self.client.messages.create(**kwargs)
            return response.content[0].text

        except AnthropicRateLimitError as e:
            raise AIRateLimitError("anthropic") from e
        except APIError as e:
            raise AIProviderError(str(e), "anthropic") from e
        except Exception as e:
            raise AIProviderError(str(e), "anthropic") from e

    def get_provider_name(self) -> str:
        return "anthropic"


# =============================================================================
# OpenAI Client
# =============================================================================


class OpenAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except OpenAIRateLimitError as e:
            raise AIRateLimitError("openai") from e
        except OpenAIAPIError as e:
            raise AIProviderError(str(e), "openai") from e
        except Exception as e:
            raise AIProviderError(str(e), "openai") from e

    def get_provider_name(self) -> str:
        return "openai"


# =============================================================================
# Gemini Client
# =============================================================================


class GeminiClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro-latest"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"Initialized Gemini client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type=(
                    "application/json" if response_format == "json" else "text/plain"
                ),
            )
            full_prompt = f"System: {system}\n\nUser: {prompt}" if system else prompt
            response = await self.model.generate_content_async(
                full_prompt, generation_config=generation_config
            )
            return response.text
        except Exception as e:
            raise AIProviderError(str(e), "gemini")

    def get_provider_name(self) -> str:
        return "gemini"


# =============================================================================
# Groq Client
# =============================================================================


class GroqClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        from groq import AsyncGroq

        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise AIProviderError(str(e), "groq")

    def get_provider_name(self) -> str:
        return "groq"


# =============================================================================
# Ollama Client
# =============================================================================


class OllamaClient(BaseAIClient):
    """
    Ollama client using the async API for better performance.
    Falls back to sync client via to_thread if async client unavailable.
    """

    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self._async_client = None
        self._sync_client = None

        # Try to use async client for better performance
        try:
            from ollama import AsyncClient
            self._async_client = AsyncClient()
            logger.info(f"Initialized Ollama async client with model: {model}")
        except ImportError:
            # Fall back to sync client
            import ollama
            self._sync_client = ollama
            logger.warning(f"Ollama AsyncClient not available, using sync client with model: {model}")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            options = {"temperature": temperature, "num_predict": max_tokens}

            if self._async_client:
                # Use native async client for better performance
                response = await self._async_client.chat(
                    model=self.model,
                    messages=messages,
                    options=options,
                )
            else:
                # Fall back to sync client in thread pool
                # Note: This blocks a thread pool thread, use sparingly under high load
                response = await asyncio.to_thread(
                    self._sync_client.chat,
                    model=self.model,
                    messages=messages,
                    options=options,
                )

            return response["message"]["content"]
        except Exception as e:
            raise AIProviderError(str(e), "ollama") from e

    def get_provider_name(self) -> str:
        return "ollama"


# =============================================================================
# Mock Client
# =============================================================================


class MockAIClient(BaseAIClient):
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        logger.info("Generating MOCK response")
        if response_format == "json":
            return json.dumps(
                {"mock_key": "mock_value", "note": "This is a mock response"}
            )
        return "This is a mock response from the AI client."

    def get_provider_name(self) -> str:
        return "mock"


# =============================================================================
# AI Client Manager
# =============================================================================


class AIClientManager:
    def __init__(self):
        self.settings = get_settings()
        self.primary_client: Optional[BaseAIClient] = None
        self.fallback_client: Optional[BaseAIClient] = None
        self.mock_client = MockAIClient()
        self._initialize_clients()

    def _get_api_key(self, key) -> str | None:
        """Safely extract API key value from SecretStr."""
        if key is None:
            return None
        return key.get_secret_value()

    def _initialize_clients(self):
        # Initialize Primary
        primary = self.settings.ai.primary
        openai_key = self._get_api_key(self.settings.OPENAI_API_KEY)
        anthropic_key = self._get_api_key(self.settings.ANTHROPIC_API_KEY)
        gemini_key = self._get_api_key(self.settings.GEMINI_API_KEY)
        groq_key = self._get_api_key(self.settings.GROQ_API_KEY)

        if primary == "openai" and openai_key:
            self.primary_client = OpenAIClient(
                openai_key, self.settings.ai.openai.model
            )
        elif primary == "anthropic" and anthropic_key:
            self.primary_client = AnthropicClient(
                anthropic_key, self.settings.ai.anthropic.model
            )
        elif primary == "gemini" and gemini_key:
            self.primary_client = GeminiClient(
                gemini_key, self.settings.ai.gemini.model
            )
        elif primary == "groq" and groq_key:
            self.primary_client = GroqClient(
                groq_key, self.settings.ai.groq.model
            )
        elif primary == "ollama":
            self.primary_client = OllamaClient(self.settings.ai.ollama.model)

        # Initialize Fallback
        fallback = self.settings.ai.fallback
        if fallback == "openai" and openai_key:
            self.fallback_client = OpenAIClient(
                openai_key, self.settings.ai.openai.model
            )
        elif fallback == "anthropic" and anthropic_key:
            self.fallback_client = AnthropicClient(
                anthropic_key, self.settings.ai.anthropic.model
            )
        elif fallback == "groq" and groq_key:
            self.fallback_client = GroqClient(
                groq_key, self.settings.ai.groq.model
            )

    def get_client_for_task(self, task_type: str = "general") -> BaseAIClient:
        """
        Select the best AI client based on the task type.

        Task Types:
        - "fast": Use Groq or fastest available (for simple queries, extraction)
        - "smart": Use Claude Opus/GPT-4 (for complex reasoning, synthesis)
        - "creative": Use Gemini or Claude (for brainstorming)
        - "general": Use primary configured client
        """
        # If specific provider is configured as primary, prefer it
        # But if we have multiple keys, we can route intelligently

        groq_key = self._get_api_key(self.settings.GROQ_API_KEY)
        gemini_key = self._get_api_key(self.settings.GEMINI_API_KEY)
        anthropic_key = self._get_api_key(self.settings.ANTHROPIC_API_KEY)
        openai_key = self._get_api_key(self.settings.OPENAI_API_KEY)

        if task_type == "fast":
            # Prefer Groq -> Gemini -> OpenAI 3.5 -> Local
            if groq_key:
                return GroqClient(groq_key)
            if gemini_key:
                return GeminiClient(gemini_key)

        elif task_type == "smart":
            # Prefer Anthropic Opus -> GPT-4 -> Gemini Pro
            if anthropic_key:
                return AnthropicClient(
                    anthropic_key, model="claude-3-opus-20240229"
                )
            if openai_key:
                return OpenAIClient(
                    openai_key, model="gpt-4-turbo-preview"
                )

        # Default to primary
        if self.primary_client:
            return self.primary_client

        # Fallback
        if self.fallback_client:
            return self.fallback_client

        return self.mock_client

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        use_fallback: bool = True,
        use_cache: bool = True,
        task_type: str = "general",
    ) -> str:
        cache = get_ai_cache()
        if use_cache and temperature < 0.3:
            cached = cache.get(prompt, system, temperature, max_tokens)
            if cached:
                logger.debug("Using cached response")
                return cached

        response = None

        # Select client based on task
        client = self.get_client_for_task(task_type)

        try:
            response = await client.generate(
                prompt, system, temperature, max_tokens, response_format
            )
        except Exception as e:
            logger.warning(
                f"Selected provider {client.get_provider_name()} failed: {e}"
            )
            if use_fallback and self.fallback_client and client != self.fallback_client:
                try:
                    logger.info("Attempting fallback...")
                    response = await self.fallback_client.generate(
                        prompt, system, temperature, max_tokens, response_format
                    )
                except Exception as e2:
                    logger.warning(f"Fallback provider failed: {e2}")

        # Use Mock
        if response is None:
            logger.warning("All providers failed, using mock")
            response = await self.mock_client.generate(
                prompt, system, temperature, max_tokens, response_format
            )

        if use_cache and temperature < 0.3:
            cache.set(prompt, response, system, temperature, max_tokens)

        return response

    async def generate_safe(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        use_fallback: bool = True,
        use_cache: bool = True,
        task_type: str = "general",
    ) -> Result[str, AIError]:
        """
        Generate response with explicit error handling via Result type.

        Returns Ok(response) on success, Err(AIError) on failure.
        This is the recommended method for new code - eliminates need for try/except.

        Example:
            result = await manager.generate_safe("Hello")
            if result.is_ok:
                print(result.unwrap())
            else:
                print(f"Error: {result.unwrap_err()}")

            # Or with chaining:
            response = result.unwrap_or("default response")
        """
        cache = get_ai_cache()
        if use_cache and temperature < 0.3:
            cached = cache.get(prompt, system, temperature, max_tokens)
            if cached:
                logger.debug("Using cached response")
                return Ok(cached)

        # Select client based on task
        client = self.get_client_for_task(task_type)
        errors: list[AIError] = []

        # Try primary client
        result = await client.generate_safe(
            prompt, system, temperature, max_tokens, response_format
        )

        if result.is_ok:
            response = result.unwrap()
            if use_cache and temperature < 0.3:
                cache.set(prompt, response, system, temperature, max_tokens)
            return Ok(response)

        # Collect error from primary
        errors.append(result.unwrap_err())
        logger.warning(f"Selected provider {client.get_provider_name()} failed: {result.unwrap_err()}")

        # Try fallback if enabled
        if use_fallback and self.fallback_client and client != self.fallback_client:
            logger.info("Attempting fallback...")
            fallback_result = await self.fallback_client.generate_safe(
                prompt, system, temperature, max_tokens, response_format
            )

            if fallback_result.is_ok:
                response = fallback_result.unwrap()
                if use_cache and temperature < 0.3:
                    cache.set(prompt, response, system, temperature, max_tokens)
                return Ok(response)

            errors.append(fallback_result.unwrap_err())
            logger.warning(f"Fallback provider failed: {fallback_result.unwrap_err()}")

        # Use mock as last resort
        logger.warning("All providers failed, using mock")
        mock_result = await self.mock_client.generate_safe(
            prompt, system, temperature, max_tokens, response_format
        )

        if mock_result.is_ok:
            return mock_result

        # All failed - return combined error
        return Err(AIError(
            code=AIError.MODEL_ERROR,
            message="All AI providers failed",
            details={"errors": [str(e) for e in errors]},
            recoverable=False,
        ))

    def get_provider_name(self) -> str:
        if self.primary_client:
            return f"Manager<{self.primary_client.get_provider_name()}>"
        return "Manager<None>"


_ai_manager: Optional[AIClientManager] = None
_ai_manager_lock = threading.Lock()


def get_ai_manager() -> AIClientManager:
    """Thread-safe singleton access for AIClientManager."""
    global _ai_manager
    if _ai_manager is None:
        with _ai_manager_lock:
            # Double-checked locking pattern
            if _ai_manager is None:
                _ai_manager = AIClientManager()
    return _ai_manager
