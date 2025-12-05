"""
AI Client Manager.

Provides centralized AI client management with:
- Multi-provider fallback chain
- Circuit breaker protection
- Rate limiting integration
- Task-based client routing
"""

import asyncio
import logging
import threading
import time
from typing import Optional, List, Tuple

import tiktoken

from .base import BaseAIClient
from .clients import (
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    GroqClient,
    OllamaClient,
    MockAIClient,
)
from src.core.config import get_settings
from src.infrastructure.cache import get_ai_cache
from src.lib.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_registry,
)
from src.lib.resilience.rate_limiting import get_rate_limiter_manager, RateLimitConfig
from src.lib.resilience.rate_limit_tracker import get_rate_limit_tracker
from src.lib.tracking.cost_tracker import get_cost_tracker
from src.core.exceptions import AIRateLimitError
from src.core.logging.observability import ObservabilityContext

logger = logging.getLogger(__name__)


class AIClientManager:
    """
    Centralized AI client manager with fallback chain and circuit breakers.

    Features:
    - Automatic provider initialization from settings
    - Multi-provider fallback (tries all configured providers before mock)
    - Circuit breaker protection per provider
    - Rate limiting integration
    - Task-based routing (fast, smart, creative)
    - Response caching for low-temperature requests
    """

    def __init__(self):
        """Initialize the AI client manager."""
        self.settings = get_settings()
        self.primary_client: Optional[BaseAIClient] = None
        self.fallback_client: Optional[BaseAIClient] = None
        self.all_clients: List[BaseAIClient] = []
        self.mock_client = MockAIClient()
        self._circuit_registry = get_circuit_registry()
        self._rate_manager = get_rate_limiter_manager()
        self._cost_tracker = get_cost_tracker()
        self._rate_limit_tracker = get_rate_limit_tracker()
        self._tokenizer = None

        # Initialize tiktoken for accurate token counting
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not initialize tiktoken: {e}. Using estimation.")

        self._initialize_clients()

    def _get_api_key(self, key) -> Optional[str]:
        """Safely extract API key value from SecretStr."""
        if key is None:
            return None
        return key.get_secret_value()

    def _initialize_clients(self) -> None:
        """Initialize AI clients from settings."""
        primary = self.settings.ai.primary
        openai_key = self._get_api_key(self.settings.OPENAI_API_KEY)
        anthropic_key = self._get_api_key(self.settings.ANTHROPIC_API_KEY)
        gemini_key = self._get_api_key(self.settings.GEMINI_API_KEY)
        groq_key = self._get_api_key(self.settings.GROQ_API_KEY)

        # Initialize primary client
        self.primary_client = self._create_client(
            primary,
            {
                "openai": openai_key,
                "anthropic": anthropic_key,
                "gemini": gemini_key,
                "groq": groq_key,
            },
        )

        # Initialize fallback client
        fallback = self.settings.ai.fallback
        if fallback:
            self.fallback_client = self._create_client(
                fallback,
                {
                    "openai": openai_key,
                    "anthropic": anthropic_key,
                    "gemini": gemini_key,
                    "groq": groq_key,
                },
            )

        # Auto-detect fallback if not configured
        if not self.fallback_client:
            self.fallback_client = self._auto_detect_fallback(
                primary, openai_key, anthropic_key, gemini_key, groq_key
            )

        # Build complete fallback chain
        self._build_fallback_chain(
            primary, openai_key, anthropic_key, gemini_key, groq_key
        )

        logger.info(
            f"AI fallback chain: {[c.get_provider_name() for c in self.all_clients]}"
        )

    def _create_client(self, provider: str, keys: dict) -> Optional[BaseAIClient]:
        """Create a client for the specified provider."""
        if provider == "openai" and keys.get("openai"):
            return OpenAIClient(keys["openai"], self.settings.ai.openai.model)
        elif provider == "anthropic" and keys.get("anthropic"):
            return AnthropicClient(keys["anthropic"], self.settings.ai.anthropic.model)
        elif provider == "gemini" and keys.get("gemini"):
            return GeminiClient(keys["gemini"], self.settings.ai.gemini.model)
        elif provider == "groq" and keys.get("groq"):
            return GroqClient(keys["groq"], self.settings.ai.groq.model)
        elif provider == "ollama":
            return OllamaClient(self.settings.ai.ollama.model)
        return None

    def _auto_detect_fallback(
        self,
        primary: str,
        openai_key: Optional[str],
        anthropic_key: Optional[str],
        gemini_key: Optional[str],
        groq_key: Optional[str],
    ) -> Optional[BaseAIClient]:
        """Auto-detect fallback provider from available keys."""
        # Priority: OpenAI -> Gemini -> Anthropic -> Groq
        if openai_key and primary != "openai":
            return OpenAIClient(openai_key, self.settings.ai.openai.model)
        elif gemini_key and primary != "gemini":
            return GeminiClient(gemini_key, self.settings.ai.gemini.model)
        elif anthropic_key and primary != "anthropic":
            return AnthropicClient(anthropic_key, self.settings.ai.anthropic.model)
        elif groq_key and primary != "groq":
            return GroqClient(groq_key, self.settings.ai.groq.model)
        return None

    def _build_fallback_chain(
        self,
        primary: str,
        openai_key: Optional[str],
        anthropic_key: Optional[str],
        gemini_key: Optional[str],
        groq_key: Optional[str],
    ) -> None:
        """Build complete fallback chain with all available providers."""
        self.all_clients = []
        used_providers = set()

        # Add primary first
        if self.primary_client:
            self.all_clients.append(self.primary_client)
            used_providers.add(self.primary_client.get_provider_name())

        # Add fallback second
        if self.fallback_client:
            provider_name = self.fallback_client.get_provider_name()
            if provider_name not in used_providers:
                self.all_clients.append(self.fallback_client)
                used_providers.add(provider_name)

        # Add remaining providers in priority order
        # Priority: Gemini (fast, generous), Anthropic (smart), OpenAI, Groq
        if gemini_key and "gemini" not in used_providers:
            self.all_clients.append(
                GeminiClient(gemini_key, self.settings.ai.gemini.model)
            )
            used_providers.add("gemini")

        if anthropic_key and "anthropic" not in used_providers:
            self.all_clients.append(
                AnthropicClient(anthropic_key, self.settings.ai.anthropic.model)
            )
            used_providers.add("anthropic")

        if openai_key and "openai" not in used_providers:
            self.all_clients.append(
                OpenAIClient(openai_key, self.settings.ai.openai.model)
            )
            used_providers.add("openai")

        if groq_key and "groq" not in used_providers:
            self.all_clients.append(GroqClient(groq_key, self.settings.ai.groq.model))
            used_providers.add("groq")

    def _get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for a provider."""
        return self._circuit_registry.get_or_create(
            name=f"ai_{provider}",
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=2,
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or estimation."""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Rough estimation: ~4 characters per token
        return len(text) // 4

    def _get_model_name(self, client: BaseAIClient) -> str:
        """Get the model name for cost tracking."""
        if hasattr(client, "model"):
            return client.model
        # Infer from provider
        provider = client.get_provider_name().lower()
        if "openai" in provider:
            return self.settings.ai.openai.model
        elif "anthropic" in provider:
            return self.settings.ai.anthropic.model
        elif "gemini" in provider:
            return self.settings.ai.gemini.model
        elif "groq" in provider:
            return self.settings.ai.groq.model
        return "unknown"

    def get_client_for_task(self, task_type: str = "general") -> BaseAIClient:
        """
        Select the best AI client based on task type.

        Task Types:
        - "fast": Use Groq or fastest available (for simple queries)
        - "smart": Use Claude or GPT-4 (for complex reasoning)
        - "creative": Use Gemini or Claude (for brainstorming)
        - "general": Use primary configured client
        """
        groq_key = self._get_api_key(self.settings.GROQ_API_KEY)
        gemini_key = self._get_api_key(self.settings.GEMINI_API_KEY)
        anthropic_key = self._get_api_key(self.settings.ANTHROPIC_API_KEY)
        openai_key = self._get_api_key(self.settings.OPENAI_API_KEY)

        if task_type == "fast":
            if groq_key:
                return GroqClient(groq_key)
            if gemini_key:
                return GeminiClient(gemini_key)

        elif task_type == "smart":
            if anthropic_key:
                return AnthropicClient(anthropic_key, model="claude-sonnet-4-20250514")
            if openai_key:
                return OpenAIClient(openai_key, model="gpt-4-turbo-preview")

        # Default to primary
        if self.primary_client:
            return self.primary_client
        if self.fallback_client:
            return self.fallback_client

        return self.mock_client

    async def _generate_with_circuit_breaker(
        self,
        client: BaseAIClient,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: str,
        task_id: Optional[str] = None,
    ) -> str:
        """Generate response with circuit breaker, rate limit protection, and cost tracking."""
        provider = client.get_provider_name()
        breaker = self._get_circuit_breaker(provider)

        # Check circuit state
        if not breaker.can_execute():
            retry_after = breaker.time_until_retry()
            raise CircuitOpenError(provider, retry_after)

        # Apply rate limiting
        self._rate_manager.get_limiter(provider, RateLimitConfig(rate=1.0, burst=5))
        if not await self._rate_manager.acquire(provider, timeout=30.0):
            raise AIRateLimitError(f"Rate limit exceeded (local) for {provider}")

        # Count input tokens
        input_text = prompt
        if system:
            input_text = f"{system}\n\n{prompt}"
        input_tokens = self._count_tokens(input_text)

        try:
            await breaker.acquire()
            response = await client.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            breaker.record_success()

            # Count output tokens and track cost
            output_tokens = self._count_tokens(response)
            model_name = self._get_model_name(client)
            cost = self._cost_tracker.add(
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task_id=task_id,
            )
            logger.debug(
                f"API call tracked: {model_name} - {input_tokens} in / {output_tokens} out = ${cost:.6f}"
            )

            # Update rate limit tracker for dashboard visibility
            self._rate_limit_tracker.update(
                provider=provider,
                requests_limit=100,  # Approximate limit
                requests_remaining=95,  # Will be updated by actual API headers
                tokens_limit=100000,
                tokens_remaining=100000 - input_tokens - output_tokens,
            )

            return response

        except CircuitOpenError:
            raise
        except AIRateLimitError as e:
            logger.warning(f"Provider {provider} rate limited: {e}")
            breaker.record_failure(e)
            # Update rate limit tracker with rate limited status
            self._rate_limit_tracker.update(
                provider=provider,
                requests_remaining=0,
                reset_time="60s",
            )
            raise
        except Exception as e:
            breaker.record_failure(e)
            raise

    def _calculate_retry_wait_time(self, retry_round: int) -> float:
        """Calculate wait time before retrying all providers."""
        base_wait = 10.0 * (2**retry_round)

        # Check circuit breakers for minimum wait
        min_circuit_wait = 0.0
        for client in self.all_clients:
            provider = client.get_provider_name()
            breaker = self._get_circuit_breaker(provider)
            if not breaker.can_execute():
                retry_after = breaker.time_until_retry()
                min_circuit_wait = max(min_circuit_wait, retry_after)

        return min(max(base_wait, min_circuit_wait), 60.0)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
        use_fallback: bool = True,
        use_cache: bool = True,
        task_type: str = "general",
        retry_on_all_fail: bool = True,
        max_retry_rounds: int = 3,
        trace_context: Optional[ObservabilityContext] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Generate AI response with multi-provider fallback.

        Args:
            prompt: The prompt to send
            system: Optional system prompt
            temperature: Response temperature
            max_tokens: Maximum tokens in response
            response_format: "text" or "json"
            use_fallback: Whether to use fallback providers
            use_cache: Whether to use response cache
            task_type: Type of task for provider selection
            retry_on_all_fail: Whether to wait and retry if all fail
            max_retry_rounds: Maximum retry rounds
            trace_context: Optional observability context
            task_id: Optional task identifier for cost tracking

        Returns:
            Generated response text
        """
        start_time = time.time()

        # Check cache
        cache = get_ai_cache()
        if use_cache and temperature < 0.3:
            cached = cache.get(prompt, system, temperature, max_tokens)
            if cached:
                logger.debug("Using cached response")
                return cached

        response = None
        errors: List[Tuple[str, Exception]] = []
        successful_provider = None

        for retry_round in range(max_retry_rounds):
            if retry_round > 0:
                wait_time = self._calculate_retry_wait_time(retry_round)
                logger.info(
                    f"All providers failed in round {retry_round}. "
                    f"Waiting {wait_time:.1f}s before retry..."
                )
                await asyncio.sleep(wait_time)
                errors.clear()

            # Try all clients in fallback chain
            if use_fallback and self.all_clients:
                for client in self.all_clients:
                    provider = client.get_provider_name()
                    try:
                        response = await self._generate_with_circuit_breaker(
                            client,
                            prompt,
                            system,
                            temperature,
                            max_tokens,
                            response_format,
                            task_id,
                        )
                        if response:
                            logger.info(f"Successfully generated with {provider}")
                            successful_provider = provider
                            break
                    except CircuitOpenError as e:
                        logger.warning(f"Circuit open for {provider}, skipping")
                        errors.append((provider, e))
                    except Exception as e:
                        logger.warning(f"Provider {provider} failed: {e}")
                        errors.append((provider, e))
            else:
                # Try primary only
                client = self.get_client_for_task(task_type)
                try:
                    response = await self._generate_with_circuit_breaker(
                        client,
                        prompt,
                        system,
                        temperature,
                        max_tokens,
                        response_format,
                        task_id,
                    )
                    successful_provider = client.get_provider_name()
                except Exception as e:
                    errors.append((client.get_provider_name(), e))

            if response is not None:
                break

            if not retry_on_all_fail:
                break

        # Use mock as last resort
        if response is None:
            logger.warning(
                f"All {len(self.all_clients)} providers failed after "
                f"{max_retry_rounds} rounds, using mock"
            )
            response = await self.mock_client.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            successful_provider = "mock"

        # Cache response
        if use_cache and temperature < 0.3:
            cache.set(prompt, response, system, temperature, max_tokens)

        return response

    def get_provider_name(self) -> str:
        """Get the name of the current primary provider."""
        if self.primary_client:
            return f"Manager<{self.primary_client.get_provider_name()}>"
        return "Manager<None>"


# Singleton instance
_ai_manager: Optional[AIClientManager] = None
_ai_manager_lock = threading.Lock()


def get_ai_manager() -> AIClientManager:
    """Get the global AI client manager instance."""
    global _ai_manager
    if _ai_manager is None:
        with _ai_manager_lock:
            if _ai_manager is None:
                _ai_manager = AIClientManager()
    return _ai_manager
