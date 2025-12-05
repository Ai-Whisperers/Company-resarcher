"""
LangChain model factory with resilience wrappers.

Provides a unified interface for creating LangChain chat models with:
- Multi-provider support (Anthropic, OpenAI, Gemini, Groq)
- Automatic fallback chains
- Circuit breaker protection
- Rate limiting integration
- Timeout handling

This replaces direct SDK usage with LangChain abstractions while
preserving our existing resilience patterns.

Usage:
    from src.infrastructure.ai.langchain_models import get_chat_model, get_model_factory

    # Simple usage - get model with fallbacks and resilience
    model = get_chat_model()
    response = await model.ainvoke([HumanMessage(content="Hello")])

    # Get specific provider
    factory = get_model_factory()
    claude = factory.get_anthropic(model="claude-sonnet-4-20250514")

    # Structured output
    structured = model.with_structured_output(MySchema)
    result = await structured.ainvoke([HumanMessage(content="...")])
"""

from typing import Optional, List, Literal, Any
from functools import lru_cache
import asyncio
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import BaseMessage
from src.core.config import get_settings
from src.core.logging import setup_logger
from .langsmith_setup import configure_langsmith

logger = setup_logger(__name__)

ProviderType = Literal["anthropic", "openai", "gemini", "groq", "ollama"]


class ModelFactory:
    """
    Factory for creating LangChain chat models with resilience wrappers.

    Handles provider initialization, fallback chains, and wraps models
    with circuit breakers, rate limiting, and timeouts.

    Usage:
        factory = get_model_factory()
        model = factory.get_model_with_fallbacks()

        # Or get specific provider
        claude = factory.get_anthropic()
    """

    def __init__(self):
        self.settings = get_settings()
        self._models: dict[str, BaseChatModel] = {}
        self._initialized_providers: set[str] = set()

        # Configure LangSmith tracing
        configure_langsmith(self.settings)

    def _check_api_key(self, provider: str) -> bool:
        """Check if API key is configured for a provider."""
        key_map = {
            "anthropic": self.settings.ANTHROPIC_API_KEY,
            "openai": self.settings.OPENAI_API_KEY,
            "gemini": self.settings.GEMINI_API_KEY,
            "groq": self.settings.GROQ_API_KEY,
            "ollama": True,  # Ollama doesn't need API key
        }
        key = key_map.get(provider)
        if key is True:
            return True
        return key is not None and len(key.get_secret_value()) > 0

    def get_anthropic(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get Anthropic Claude model.

        Args:
            model: Model name (claude-sonnet-4-20250514, claude-3-haiku, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            ChatAnthropic instance

        Raises:
            ValueError: If ANTHROPIC_API_KEY not configured
        """
        if not self._check_api_key("anthropic"):
            raise ValueError("ANTHROPIC_API_KEY not configured")

        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value(),
            **kwargs,
        )

    def get_openai(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get OpenAI model.

        Args:
            model: Model name (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            ChatOpenAI instance

        Raises:
            ValueError: If OPENAI_API_KEY not configured
        """
        if not self._check_api_key("openai"):
            raise ValueError("OPENAI_API_KEY not configured")

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.settings.OPENAI_API_KEY.get_secret_value(),
            **kwargs,
        )

    def get_gemini(
        self,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get Google Gemini model.

        Args:
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            **kwargs: Additional model parameters

        Returns:
            ChatGoogleGenerativeAI instance

        Raises:
            ValueError: If GEMINI_API_KEY not configured
        """
        if not self._check_api_key("gemini"):
            raise ValueError("GEMINI_API_KEY not configured")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=self.settings.GEMINI_API_KEY.get_secret_value(),
            **kwargs,
        )

    def get_groq(
        self,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get Groq model (fast inference for Llama models).

        Args:
            model: Model name (llama-3.1-70b-versatile, mixtral-8x7b-32768, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            ChatGroq instance

        Raises:
            ValueError: If GROQ_API_KEY not configured
        """
        if not self._check_api_key("groq"):
            raise ValueError("GROQ_API_KEY not configured")

        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.settings.GROQ_API_KEY.get_secret_value(),
            **kwargs,
        )

    def get_ollama(
        self,
        model: str = "llama3.1",
        temperature: float = 0.7,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get Ollama model (local LLM).

        Args:
            model: Model name (llama3.1, mistral, codellama, etc.)
            temperature: Sampling temperature
            **kwargs: Additional model parameters

        Returns:
            ChatOllama instance
        """
        from langchain_ollama import ChatOllama

        base_url = (
            getattr(self.settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434"
        )

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            **kwargs,
        )

    def get_available_providers(self) -> List[ProviderType]:
        """
        Get list of providers with valid API keys configured.

        Returns:
            List of available provider names
        """
        providers: List[ProviderType] = []

        if self._check_api_key("anthropic"):
            providers.append("anthropic")
        if self._check_api_key("openai"):
            providers.append("openai")
        if self._check_api_key("gemini"):
            providers.append("gemini")
        if self._check_api_key("groq"):
            providers.append("groq")

        return providers

    def get_model_with_fallbacks(
        self,
        primary: Optional[ProviderType] = None,
        fallbacks: Optional[List[ProviderType]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        with_resilience: bool = True,
        **kwargs,
    ) -> Runnable:
        """
        Get a model with automatic fallback chain.

        Creates a primary model with fallbacks that automatically switch
        on failure. Optionally wraps with circuit breaker, rate limiting,
        and timeout protection.

        Args:
            primary: Primary provider (auto-detected if None)
            fallbacks: Fallback providers (auto-detected if None)
            temperature: Sampling temperature for all models
            max_tokens: Max tokens for all models
            with_resilience: Whether to add circuit breaker/rate limiting
            **kwargs: Additional parameters passed to model constructors

        Returns:
            Runnable with fallback chain and optional resilience wrappers

        Raises:
            ValueError: If no AI providers are configured
        """
        # Provider factory map
        provider_map = {
            "anthropic": self.get_anthropic,
            "openai": self.get_openai,
            "gemini": self.get_gemini,
            "groq": self.get_groq,
            "ollama": self.get_ollama,
        }

        # Get available providers
        available = self.get_available_providers()

        if not available:
            raise ValueError(
                "No AI providers configured. Set at least one of: "
                "ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY"
            )

        # Determine primary provider
        if primary is None:
            # Use settings preference or first available
            preferred = getattr(self.settings.ai, "primary", "anthropic")
            if preferred in available:
                primary = preferred
            else:
                primary = available[0]
        elif primary not in available:
            logger.warning(
                f"Primary provider {primary} not available, using {available[0]}"
            )
            primary = available[0]

        # Build fallback list
        if fallbacks is None:
            fallbacks = [p for p in available if p != primary]

        # Model creation kwargs
        model_kwargs = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Create primary model
        try:
            primary_model = provider_map[primary](**model_kwargs)
            logger.debug(f"Created primary model: {primary}")
        except Exception as e:
            logger.error(f"Failed to create primary model {primary}: {e}")
            # Try first fallback
            for fb in fallbacks:
                try:
                    primary_model = provider_map[fb](**model_kwargs)
                    primary = fb
                    fallbacks = [p for p in fallbacks if p != fb]
                    logger.info(f"Using fallback {fb} as primary")
                    break
                except Exception:
                    continue
            else:
                raise ValueError(f"Failed to create any AI model: {e}")

        # Create fallback models
        fallback_models = []
        for fb in fallbacks:
            try:
                fallback_models.append(provider_map[fb](**model_kwargs))
                logger.debug(f"Created fallback model: {fb}")
            except Exception as e:
                logger.debug(f"Skipping unavailable fallback {fb}: {e}")

        # Build chain with fallbacks
        if fallback_models:
            model = primary_model.with_fallbacks(fallback_models)
            logger.info(
                f"Created model chain: {primary} -> {[f for f in fallbacks if f in available]}"
            )
        else:
            model = primary_model
            logger.info(f"Created single model: {primary} (no fallbacks available)")

        # Wrap with resilience layers
        if with_resilience:
            model = self._wrap_with_resilience(model, primary)

        return model

    def _wrap_with_resilience(
        self,
        model: Runnable,
        provider: str,
    ) -> Runnable:
        """
        Wrap model with circuit breaker, rate limiting, and timeout.

        Uses our existing resilience infrastructure to protect LangChain models.

        Args:
            model: The LangChain model to wrap
            provider: Provider name for circuit breaker identification

        Returns:
            Model wrapped with resilience layers
        """
        from .resilience_wrappers import (
            CircuitBreakerRunnable,
            RateLimitedRunnable,
            TimeoutRunnable,
        )

        # Apply circuit breaker
        model = CircuitBreakerRunnable(
            runnable=model,
            name=f"langchain_{provider}",
            failure_threshold=5,
            recovery_timeout=60,
        )

        # Apply rate limiting
        model = RateLimitedRunnable(
            runnable=model,
            provider=provider,
        )

        # Apply timeout
        timeout_seconds = getattr(self.settings.ai, "timeout_seconds", 120)
        model = TimeoutRunnable(
            runnable=model,
            timeout_seconds=timeout_seconds,
        )

        return model

    def get_model_for_task(
        self,
        task_type: Literal["fast", "smart", "creative", "cheap"] = "smart",
        **kwargs,
    ) -> Runnable:
        """
        Get optimal model for a specific task type.

        Args:
            task_type: Type of task
                - "fast": Low latency (Groq, Gemini Flash)
                - "smart": Best quality (Claude, GPT-4)
                - "creative": High temperature creative tasks
                - "cheap": Cost-effective (Groq, Gemini)
            **kwargs: Additional model parameters

        Returns:
            Configured model for the task type
        """
        available = self.get_available_providers()

        if task_type == "fast":
            # Prioritize low latency
            priority = ["groq", "gemini", "openai", "anthropic"]
            kwargs.setdefault("temperature", 0.3)
        elif task_type == "smart":
            # Prioritize quality
            priority = ["anthropic", "openai", "gemini", "groq"]
            kwargs.setdefault("temperature", 0.5)
        elif task_type == "creative":
            # High temperature for creativity
            priority = ["anthropic", "openai", "gemini", "groq"]
            kwargs.setdefault("temperature", 0.9)
        elif task_type == "cheap":
            # Prioritize cost
            priority = ["groq", "gemini", "ollama", "openai", "anthropic"]
            kwargs.setdefault("temperature", 0.5)
        else:
            priority = ["anthropic", "openai", "gemini", "groq"]

        # Find first available in priority order
        primary = None
        for p in priority:
            if p in available:
                primary = p
                break

        if primary is None:
            primary = available[0] if available else None

        return self.get_model_with_fallbacks(primary=primary, **kwargs)


# Module-level factory instance
_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """
    Get the global model factory instance.

    Creates factory on first call, reuses same instance thereafter.

    Returns:
        ModelFactory instance
    """
    global _factory
    if _factory is None:
        _factory = ModelFactory()
    return _factory


def reset_model_factory() -> None:
    """Reset the model factory (useful for testing)."""
    global _factory
    _factory = None


def get_chat_model(
    primary: Optional[ProviderType] = None,
    task_type: Optional[Literal["fast", "smart", "creative", "cheap"]] = None,
    **kwargs,
) -> Runnable:
    """
    Convenience function to get a chat model with fallbacks.

    Args:
        primary: Primary provider (optional)
        task_type: Task type for automatic model selection (optional)
        **kwargs: Additional model parameters

    Returns:
        Configured chat model with fallbacks and resilience

    Examples:
        # Default model with fallbacks
        model = get_chat_model()

        # Specific provider
        model = get_chat_model(primary="openai")

        # Task-optimized
        model = get_chat_model(task_type="fast")
    """
    factory = get_model_factory()

    if task_type:
        return factory.get_model_for_task(task_type=task_type, **kwargs)

    return factory.get_model_with_fallbacks(primary=primary, **kwargs)
