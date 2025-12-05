import json
import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Optional
import google.generativeai as genai
from anthropic import (
    AsyncAnthropic,
    APIError,
    RateLimitError as AnthropicRateLimitError,
)
from openai import (
    AsyncOpenAI,
    APIError as OpenAIAPIError,
    RateLimitError as OpenAIRateLimitError,
)
from google.api_core import exceptions as google_exceptions

from src.core.config import get_settings
from src.core.exceptions import (
    AIProviderError,
    AIRateLimitError,
)
from src.core.logging import setup_logger
from src.core.result import Result, Ok, Err, AIError
from src.lib.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_registry,
)
from src.lib.resilience.retry_strategy import (
    RetryStrategy,
    RetryPolicy,
)
from src.infrastructure.cache import get_ai_cache
from src.lib.resilience.rate_limiting import rate_limiter_manager, RateLimitConfig
from src.core.logging.observability import get_langfuse, ObservabilityContext

logger = setup_logger("ai_client")

# Default retry configuration for AI providers
AI_RETRY_STRATEGY = RetryStrategy(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    policies=[
        RetryPolicy(
            exception_types=(AIRateLimitError,),
            max_attempts=5,
            base_delay=5.0,
            max_delay=60.0,
            respect_retry_after=True,
        ),
    ],
)

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
            return Err(
                AIError.rate_limited(
                    f"Rate limit exceeded for {self.get_provider_name()}"
                )
            )
        except AIProviderError as e:
            return Err(
                AIError(
                    code=AIError.MODEL_ERROR,
                    message=str(e),
                    details={"provider": self.get_provider_name()},
                    recoverable=True,
                )
            )
        except asyncio.TimeoutError:
            return Err(
                AIError.timeout(f"Request to {self.get_provider_name()} timed out")
            )
        except Exception as e:
            return Err(
                AIError.connection_error(f"{self.get_provider_name()}: {str(e)}")
            )

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
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

            # Track token usage for cost tracking
            if hasattr(response, "usage") and response.usage:
                from src.infrastructure.tracking.cost_tracker import get_cost_tracker

                try:
                    cost_tracker = get_cost_tracker()
                    cost_tracker.add(
                        model=self.model,
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                    )
                except Exception as cost_err:
                    logger.debug(f"Cost tracking error (non-fatal): {cost_err}")

            # Track rate limits from response headers (if available)
            try:
                from src.lib.resilience.rate_limit_tracker import (
                    get_rate_limit_tracker,
                )

                rate_tracker = get_rate_limit_tracker()
                # Try to extract rate limit headers from raw response
                raw_response = getattr(response, "_response", None)
                if raw_response and hasattr(raw_response, "headers"):
                    rate_tracker.update_from_headers(
                        "anthropic", dict(raw_response.headers)
                    )
            except Exception:
                pass  # Non-fatal if rate limit tracking fails

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
    def __init__(self, api_key: str, model: str = "gpt-4o"):
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

            # Track token usage for cost tracking
            if hasattr(response, "usage") and response.usage:
                from src.infrastructure.tracking.cost_tracker import get_cost_tracker

                try:
                    cost_tracker = get_cost_tracker()
                    cost_tracker.add(
                        model=self.model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                    )
                except Exception as cost_err:
                    logger.debug(f"Cost tracking error (non-fatal): {cost_err}")

            # Track rate limits from response headers (if available)
            try:
                from src.infrastructure.resilience.rate_limit_tracker import get_rate_limit_tracker

                rate_tracker = get_rate_limit_tracker()
                # Try to extract rate limit headers from raw response
                raw_response = getattr(response, "_response", None)
                if raw_response and hasattr(raw_response, "headers"):
                    rate_tracker.update_from_headers(
                        "openai", dict(raw_response.headers)
                    )
            except Exception:
                pass  # Non-fatal if rate limit tracking fails

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
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
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

            # Track token usage for cost tracking (Gemini uses usage_metadata)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                from src.infrastructure.tracking.cost_tracker import get_cost_tracker

                try:
                    cost_tracker = get_cost_tracker()
                    cost_tracker.add(
                        model="gemini-2.0-flash",  # Use known model name for pricing
                        input_tokens=response.usage_metadata.prompt_token_count or 0,
                        output_tokens=response.usage_metadata.candidates_token_count
                        or 0,
                    )
                except Exception as cost_err:
                    logger.debug(f"Cost tracking error (non-fatal): {cost_err}")

            return response.text
        except google_exceptions.ResourceExhausted as e:
            # Gemini rate limit error (BUG-047)
            raise AIRateLimitError("gemini") from e
        except Exception as e:
            # Check for rate limit errors in message (BUG-047)
            error_str = str(e).lower()
            if any(
                p in error_str
                for p in [
                    "rate limit",
                    "ratelimit",
                    "429",
                    "quota",
                    "resource exhausted",
                ]
            ):
                raise AIRateLimitError("gemini") from e
            raise AIProviderError(str(e), "gemini") from e

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

            # Track token usage for cost tracking (Groq uses same format as OpenAI)
            if hasattr(response, "usage") and response.usage:
                from src.infrastructure.tracking.cost_tracker import get_cost_tracker

                try:
                    cost_tracker = get_cost_tracker()
                    cost_tracker.add(
                        model=self.model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                    )
                except Exception as cost_err:
                    logger.debug(f"Cost tracking error (non-fatal): {cost_err}")

            # Track rate limits from response headers (if available)
            try:
                from src.infrastructure.resilience.rate_limit_tracker import get_rate_limit_tracker

                rate_tracker = get_rate_limit_tracker()
                # Try to extract rate limit headers from raw response
                raw_response = getattr(response, "_response", None)
                if raw_response and hasattr(raw_response, "headers"):
                    rate_tracker.update_from_headers("groq", dict(raw_response.headers))
            except Exception:
                pass  # Non-fatal if rate limit tracking fails

            return response.choices[0].message.content
        except Exception as e:
            # Check for rate limit errors (BUG-047)
            error_str = str(e).lower()
            if any(
                p in error_str
                for p in [
                    "rate limit",
                    "ratelimit",
                    "429",
                    "quota",
                    "too many requests",
                ]
            ):
                raise AIRateLimitError("groq") from e
            raise AIProviderError(str(e), "groq") from e

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
            logger.warning(
                f"Ollama AsyncClient not available, using sync client with model: {model}"
            )

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
    """
    Mock AI client that returns template-compatible placeholder data.

    When all real AI providers fail, this returns structured data that
    templates can render properly instead of blank fields everywhere.
    """

    # Template-compatible mock responses for each research type
    MOCK_RESPONSES = {
        "market": {
            "tam": "⚠️ Data unavailable - AI providers rate limited",
            "sam": "Data unavailable",
            "som": "Data unavailable",
            "cagr": "Data unavailable",
            "forecast_summary": "AI analysis unavailable. Please retry when AI providers are available.",
            "growth_drivers": [
                "⚠️ AI analysis unavailable - all providers rate limited",
                "Retry in a few minutes or configure additional AI providers",
            ],
            "market_challenges": [
                "⚠️ Could not analyze market challenges - AI unavailable",
            ],
            "market_size": "Data unavailable",
            "market_trends": ["AI analysis required for trend identification"],
            "is_mock": True,
        },
        "financial": {
            "revenue": "⚠️ Data unavailable - AI analysis required",
            "revenue_growth": "N/A",
            "profitability": "N/A",
            "funding_history": ["⚠️ AI providers unavailable for financial analysis"],
            "stock_performance": "Data unavailable",
            "financial_highlights": [
                "AI analysis unavailable - retry when providers are available"
            ],
            "is_mock": True,
        },
        "competitor": {
            "direct_competitors": [
                {
                    "name": "⚠️ Competitor Analysis Unavailable",
                    "website": "N/A",
                    "description": "AI providers are rate limited. Retry in a few minutes.",
                    "strength": "N/A",
                }
            ],
            "indirect_competitors": [
                {"name": "Data unavailable", "description": "AI analysis required"}
            ],
            "emerging_threats": [
                "⚠️ AI analysis unavailable - retry when providers are available"
            ],
            "competitive_advantages": ["Data requires AI analysis"],
            "is_mock": True,
        },
        "brand": {
            "usp": "⚠️ AI analysis unavailable - all providers rate limited",
            "value_proposition": "Data unavailable - retry when AI is available",
            "brand_archetype": "N/A",
            "archetype_description": "AI analysis required",
            "positioning_statement": "⚠️ Could not generate - AI providers unavailable",
            "brand_strengths": ["AI analysis unavailable"],
            "brand_values": ["Data requires AI analysis"],
            "is_mock": True,
        },
        "sales": {
            "executive_summary": "⚠️ **AI Analysis Unavailable**\n\nAll configured AI providers are currently rate-limited. Sales strategy analysis could not be performed. Please retry in a few minutes or configure additional AI providers.",
            "priorities": [
                "⚠️ AI analysis unavailable - retry when providers are available",
            ],
            "pain_points": [
                "Could not identify pain points - AI providers rate limited",
            ],
            "recommended_solutions": [
                {
                    "product": "Analysis Unavailable",
                    "rationale": "AI providers are rate limited",
                    "pitch_angle": "Retry when AI is available",
                }
            ],
            "sales_channels": ["Data requires AI analysis"],
            "pricing_insights": "AI analysis unavailable",
            "is_mock": True,
        },
    }

    # Default fallback for unknown research types
    DEFAULT_MOCK = {
        "summary": "⚠️ AI analysis unavailable - all providers rate limited",
        "key_findings": ["Data unavailable - retry when AI providers are available"],
        "recommendations": [
            "Wait a few minutes and retry",
            "Configure additional AI providers in .env",
            "Check API key quotas and rate limits",
        ],
        "is_mock": True,
    }

    def _detect_research_type(self, prompt: str) -> str:
        """Detect research type from prompt content."""
        prompt_lower = prompt.lower()
        if "market" in prompt_lower and (
            "size" in prompt_lower or "growth" in prompt_lower or "tam" in prompt_lower
        ):
            return "market"
        elif (
            "financial" in prompt_lower
            or "revenue" in prompt_lower
            or "funding" in prompt_lower
        ):
            return "financial"
        elif "competitor" in prompt_lower or "competitive" in prompt_lower:
            return "competitor"
        elif (
            "brand" in prompt_lower
            or "positioning" in prompt_lower
            or "usp" in prompt_lower
        ):
            return "brand"
        elif (
            "sales" in prompt_lower
            or "pricing" in prompt_lower
            or "distribution" in prompt_lower
        ):
            return "sales"
        return "default"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        logger.warning(
            "Generating MOCK response - all AI providers unavailable (BUG-047)"
        )

        if response_format == "json":
            # Detect research type and return appropriate mock data
            research_type = self._detect_research_type(prompt)
            mock_data = self.MOCK_RESPONSES.get(research_type, self.DEFAULT_MOCK)
            return json.dumps(mock_data)

        # Return a clear indicator that this is a fallback response
        return (
            "**⚠️ AI Analysis Unavailable**\n\n"
            "All configured AI providers are currently rate-limited or unavailable. "
            "This section could not be analyzed.\n\n"
            "**Recommendations:**\n"
            "- Wait a few minutes and try again\n"
            "- Configure additional AI providers (Gemini, Anthropic, etc.) in .env\n"
            "- Check your API key quotas and rate limits\n"
        )

    def get_provider_name(self) -> str:
        return "mock"


class AIClientManager:
    def __init__(self):
        self.settings = get_settings()
        self.primary_client: Optional[BaseAIClient] = None
        self.fallback_client: Optional[BaseAIClient] = None
        self.all_clients: list[BaseAIClient] = (
            []
        )  # All available clients for multi-fallback
        self.mock_client = MockAIClient()
        self._circuit_registry = get_circuit_registry()
        self._retry_strategy = AI_RETRY_STRATEGY
        # self._rate_limiter = get_ai_rate_limiter()  # Replaced by rate_limiter_manager
        self._initialize_clients()

    def _get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for a provider."""
        return self._circuit_registry.get_or_create(
            name=f"ai_{provider}",
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=2,
        )

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
            self.primary_client = GroqClient(groq_key, self.settings.ai.groq.model)
        elif primary == "ollama":
            self.primary_client = OllamaClient(self.settings.ai.ollama.model)

        # Initialize Fallback (BUG-047: improved fallback chain)
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
            self.fallback_client = GroqClient(groq_key, self.settings.ai.groq.model)
        elif fallback == "gemini" and gemini_key:
            self.fallback_client = GeminiClient(
                gemini_key, self.settings.ai.gemini.model
            )

        # Auto-detect additional fallback if no explicit fallback configured
        # This helps prevent mock responses when multiple providers are available
        if not self.fallback_client:
            # Try providers in order: OpenAI -> Gemini -> Anthropic -> Groq
            if openai_key and primary != "openai":
                self.fallback_client = OpenAIClient(
                    openai_key, self.settings.ai.openai.model
                )
            elif gemini_key and primary != "gemini":
                self.fallback_client = GeminiClient(
                    gemini_key, self.settings.ai.gemini.model
                )
            elif anthropic_key and primary != "anthropic":
                self.fallback_client = AnthropicClient(
                    anthropic_key, self.settings.ai.anthropic.model
                )
            elif groq_key and primary != "groq":
                self.fallback_client = GroqClient(groq_key, self.settings.ai.groq.model)

        # Build complete fallback chain with ALL available providers
        # This ensures we try every configured provider before using mock
        self.all_clients = []
        used_providers = set()

        # Add primary first
        if self.primary_client:
            self.all_clients.append(self.primary_client)
            used_providers.add(self.primary_client.get_provider_name())

        # Add fallback second
        if (
            self.fallback_client
            and self.fallback_client.get_provider_name() not in used_providers
        ):
            self.all_clients.append(self.fallback_client)
            used_providers.add(self.fallback_client.get_provider_name())

        # Add all other available providers
        # Priority order: Gemini (fast, generous limits), Anthropic (smart), OpenAI, Groq
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

        logger.info(
            f"AI fallback chain: {[c.get_provider_name() for c in self.all_clients]}"
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
            # Prefer Anthropic Sonnet (best accuracy) -> GPT-4 -> Gemini Pro
            if anthropic_key:
                return AnthropicClient(anthropic_key, model="claude-sonnet-4-20250514")
            if openai_key:
                return OpenAIClient(openai_key, model="gpt-4-turbo-preview")

        # Default to primary
        if self.primary_client:
            return self.primary_client

        # Fallback
        if self.fallback_client:
            return self.fallback_client

        return self.mock_client

    async def _generate_with_circuit_breaker(
        self,
        client: BaseAIClient,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:
        """Generate response using a client with circuit breaker and rate limit protection."""
        provider = client.get_provider_name()
        breaker = self._get_circuit_breaker(provider)

        # Check circuit state before attempting
        if not breaker.can_execute():
            retry_after = breaker.time_until_retry()
            raise CircuitOpenError(provider, retry_after)

        # PERF-016: Proactive rate limiting - wait if approaching limit
        # Configure limiter if not exists (default 60 RPM = 1 RPS for safety, burst 5)
        # In a real scenario, we should load this from config per provider
        rate_limiter_manager.get_limiter(provider, RateLimitConfig(rate=1.0, burst=5))

        if not await rate_limiter_manager.acquire(provider, timeout=30.0):
            raise AIRateLimitError(f"Rate limit exceeded (local) for {provider}")

        try:
            await breaker.acquire()
            response = await client.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            breaker.record_success()
            # PERF-016: Record successful request for rate tracking
            # rate_limiter_manager.acquire already consumed the token
            return response
        except CircuitOpenError:
            raise
        except AIRateLimitError as e:
            # PERF-016: Record rate limit for adaptive waiting
            # rate_limiter_manager doesn't support adaptive updates yet, just log
            logger.warning(f"Provider {provider} rate limited: {e}")
            breaker.record_failure(e)
            raise
        except Exception as e:
            breaker.record_failure(e)
            raise

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
        retry_on_all_fail: bool = True,
        max_retry_rounds: int = 3,
        trace_context: Optional[ObservabilityContext] = None,
    ) -> str:
        """
        Generate AI response with multi-provider fallback and retry logic.

        P1 Fix: Added retry_on_all_fail parameter to wait and retry when all
        providers are rate-limited instead of immediately returning mock data.

        Args:
            prompt: The prompt to send
            system: Optional system prompt
            temperature: Response temperature
            max_tokens: Maximum tokens in response
            response_format: "text" or "json"
            use_fallback: Whether to use fallback providers
            use_cache: Whether to use response cache
            task_type: Type of task for provider selection
            retry_on_all_fail: Whether to wait and retry if all providers fail
            max_retry_rounds: Maximum number of retry rounds (each round tries all providers)
            trace_context: Optional observability context for Langfuse tracing
        """
        import time

        start_time = time.time()

        cache = get_ai_cache()
        if use_cache and temperature < 0.3:
            cached = cache.get(prompt, system, temperature, max_tokens)
            if cached:
                logger.debug("Using cached response")
                return cached

        response = None
        errors: list[tuple[str, Exception]] = []
        successful_provider = None

        # Create Langfuse generation tracking if context provided
        generation = None
        if trace_context and hasattr(trace_context, "generation"):
            generation = trace_context.generation(
                name="ai_generate",
                model=self.get_provider_name(),
                input_prompt=prompt[:2000],  # Truncate for storage
                metadata={
                    "task_type": task_type,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                },
            )

        for retry_round in range(max_retry_rounds):
            if retry_round > 0:
                # P1 Fix: Calculate wait time based on circuit breaker states
                wait_time = self._calculate_retry_wait_time(retry_round)
                logger.info(
                    f"All providers failed in round {retry_round}. "
                    f"Waiting {wait_time:.1f}s before retry round {retry_round + 1}..."
                )
                await asyncio.sleep(wait_time)
                errors.clear()

            # Try ALL available clients in the fallback chain with circuit breaker
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
                        )
                        if response:
                            logger.info(f"Successfully generated with {provider}")
                            successful_provider = provider
                            break
                    except CircuitOpenError as e:
                        logger.warning(
                            f"Circuit open for {provider}, skipping (retry in {e.retry_after:.1f}s)"
                        )
                        errors.append((provider, e))
                        continue
                    except Exception as e:
                        logger.warning(f"Provider {provider} failed: {e}")
                        errors.append((provider, e))
                        continue
            else:
                # Fallback disabled or no clients - try primary only
                client = self.get_client_for_task(task_type)
                try:
                    response = await self._generate_with_circuit_breaker(
                        client, prompt, system, temperature, max_tokens, response_format
                    )
                    successful_provider = client.get_provider_name()
                except Exception as e:
                    logger.warning(f"Provider {client.get_provider_name()} failed: {e}")
                    errors.append((client.get_provider_name(), e))

            # If we got a response, break out of retry loop
            if response is not None:
                break

            # Check if we should retry
            if not retry_on_all_fail:
                break

        # Use Mock only if ALL providers failed after all retry rounds
        if response is None:
            open_circuits = self._circuit_registry.get_open_circuits()
            logger.warning(
                f"All {len(self.all_clients)} providers failed after {max_retry_rounds} rounds, using mock. "
                f"Open circuits: {open_circuits}"
            )
            response = await self.mock_client.generate(
                prompt, system, temperature, max_tokens, response_format
            )
            successful_provider = "mock"

        # Record generation in Langfuse
        if generation:
            duration_ms = int((time.time() - start_time) * 1000)
            generation.end(
                output=response[:2000] if response else None,
                metadata={
                    "duration_ms": duration_ms,
                    "provider_used": successful_provider,
                    "retry_rounds": retry_round + 1 if retry_round > 0 else 0,
                    "errors_count": len(errors),
                },
            )

        if use_cache and temperature < 0.3:
            cache.set(prompt, response, system, temperature, max_tokens)

        return response

    def _calculate_retry_wait_time(self, retry_round: int) -> float:
        """
        P1 Fix: Calculate how long to wait before retrying all providers.

        Uses exponential backoff based on retry round, but also considers
        circuit breaker retry_after times to avoid wasted attempts.
        """
        # Base exponential backoff: 10s, 20s, 40s, etc.
        base_wait = 10.0 * (2**retry_round)

        # Check circuit breakers for minimum wait time
        min_circuit_wait = 0.0
        for client in self.all_clients:
            provider = client.get_provider_name()
            breaker = self._get_circuit_breaker(provider)
            if not breaker.can_execute():
                retry_after = breaker.time_until_retry()
                min_circuit_wait = max(min_circuit_wait, retry_after)

        # Use the longer of base backoff or circuit breaker wait time
        # But cap at 60 seconds to avoid excessive waits
        wait_time = min(max(base_wait, min_circuit_wait), 60.0)

        return wait_time

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
        logger.warning(
            f"Selected provider {client.get_provider_name()} failed: {result.unwrap_err()}"
        )

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
        return Err(
            AIError(
                code=AIError.MODEL_ERROR,
                message="All AI providers failed",
                details={"errors": [str(e) for e in errors]},
                recoverable=False,
            )
        )

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
