import json
from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx
import google.generativeai as genai
from anthropic import Anthropic, APIError, RateLimitError as AnthropicRateLimitError
from openai import (
    OpenAI,
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

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = Anthropic(api_key=api_key)
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

            response = self.client.messages.create(**kwargs)
            return response.content[0].text

        except AnthropicRateLimitError as e:
            raise AIRateLimitError("anthropic")
        except APIError as e:
            raise AIProviderError(str(e), "anthropic")
        except Exception as e:
            raise AIProviderError(str(e), "anthropic")

    def get_provider_name(self) -> str:
        return "anthropic"


# =============================================================================
# OpenAI Client
# =============================================================================


class OpenAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
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

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except OpenAIRateLimitError:
            raise AIRateLimitError("openai")
        except OpenAIAPIError as e:
            raise AIProviderError(str(e), "openai")
        except Exception as e:
            raise AIProviderError(str(e), "openai")

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
    def __init__(self, model: str = "llama3.1:8b"):
        import ollama

        self.client = ollama
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

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature, "num_predict": max_tokens},
            )
            return response["message"]["content"]
        except Exception as e:
            raise AIProviderError(str(e), "ollama")

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

    def _initialize_clients(self):
        # Initialize Primary
        primary = self.settings.ai.primary
        if primary == "openai" and self.settings.OPENAI_API_KEY:
            self.primary_client = OpenAIClient(
                self.settings.OPENAI_API_KEY, self.settings.ai.openai.model
            )
        elif primary == "anthropic" and self.settings.ANTHROPIC_API_KEY:
            self.primary_client = AnthropicClient(
                self.settings.ANTHROPIC_API_KEY, self.settings.ai.anthropic.model
            )
        elif primary == "gemini" and self.settings.GEMINI_API_KEY:
            self.primary_client = GeminiClient(
                self.settings.GEMINI_API_KEY, self.settings.ai.gemini.model
            )
        elif primary == "groq" and self.settings.GROQ_API_KEY:
            self.primary_client = GroqClient(
                self.settings.GROQ_API_KEY, self.settings.ai.groq.model
            )
        elif primary == "ollama":
            self.primary_client = OllamaClient(self.settings.ai.ollama.model)

        # Initialize Fallback
        fallback = self.settings.ai.fallback
        if fallback == "openai" and self.settings.OPENAI_API_KEY:
            self.fallback_client = OpenAIClient(
                self.settings.OPENAI_API_KEY, self.settings.ai.openai.model
            )
        elif fallback == "anthropic" and self.settings.ANTHROPIC_API_KEY:
            self.fallback_client = AnthropicClient(
                self.settings.ANTHROPIC_API_KEY, self.settings.ai.anthropic.model
            )
        elif fallback == "groq" and self.settings.GROQ_API_KEY:
            self.fallback_client = GroqClient(
                self.settings.GROQ_API_KEY, self.settings.ai.groq.model
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

        if task_type == "fast":
            # Prefer Groq -> Gemini -> OpenAI 3.5 -> Local
            if self.settings.GROQ_API_KEY:
                return GroqClient(self.settings.GROQ_API_KEY)
            if self.settings.GEMINI_API_KEY:
                return GeminiClient(self.settings.GEMINI_API_KEY)

        elif task_type == "smart":
            # Prefer Anthropic Opus -> GPT-4 -> Gemini Pro
            if self.settings.ANTHROPIC_API_KEY:
                return AnthropicClient(
                    self.settings.ANTHROPIC_API_KEY, model="claude-3-opus-20240229"
                )
            if self.settings.OPENAI_API_KEY:
                return OpenAIClient(
                    self.settings.OPENAI_API_KEY, model="gpt-4-turbo-preview"
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


_ai_manager = None


def get_ai_manager() -> AIClientManager:
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIClientManager()
    return _ai_manager
