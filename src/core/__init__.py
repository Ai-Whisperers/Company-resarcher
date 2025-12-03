"""
Core module for Company Researcher.

Provides centralized access to:
- Configuration (get_settings, Settings)
- AI clients (get_ai_manager, BaseAIClient)
- HTTP client (get_http_client)
- Rate limiting (get_rate_limiter_manager)
- Caching (get_cache, get_ai_cache)
- Logging (setup_logger)
- Exceptions (CompanyResearcherError and subclasses)
- Types and Models
- Resilience patterns (CircuitBreaker, RetryStrategy)
"""

# Configuration - from config subdirectory
from .config import (
    get_settings,
    Settings,
    Profile,
)

# AI Clients - from ai subdirectory
from .ai import (
    BaseAIClient,
    AIClientManager,
    get_ai_manager,
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    GroqClient,
    OllamaClient,
    MockAIClient,
)

# HTTP Client - from network subdirectory
from .network.http_client import (
    get_http_client,
    HTTPClient,
    HTTPClientConfig,
)

# Rate Limiting - from resilience subdirectory
from .resilience.rate_limiting import (
    get_rate_limiter_manager,
    RateLimiterManager,
    RateLimitConfig,
)

# Caching - from cache subdirectory
from .cache import get_ai_cache

# Logging - from logging subdirectory
from .logging import setup_logger, get_logger

# Exceptions - from exceptions subdirectory
from .exceptions import (
    CompanyResearcherError,
    AIError,
    AIProviderError,
    AIRateLimitError,
    NetworkError,
    SearchError,
    PipelineError,
    ValidationError,
)

# Resilience patterns - from resilience subdirectory
from .resilience import CircuitBreaker, RetryStrategy

__all__ = [
    # Config
    "get_settings",
    "Settings",
    "Profile",
    # AI
    "BaseAIClient",
    "AIClientManager",
    "get_ai_manager",
    "OpenAIClient",
    "AnthropicClient",
    "GeminiClient",
    "GroqClient",
    "OllamaClient",
    "MockAIClient",
    # HTTP
    "get_http_client",
    "HTTPClient",
    "HTTPClientConfig",
    # Rate Limiting
    "get_rate_limiter_manager",
    "RateLimiterManager",
    "RateLimitConfig",
    # Cache
    "get_ai_cache",
    # Logging
    "setup_logger",
    "get_logger",
    # Exceptions
    "CompanyResearcherError",
    "AIError",
    "AIProviderError",
    "AIRateLimitError",
    "NetworkError",
    "SearchError",
    "PipelineError",
    "ValidationError",
    # Resilience
    "CircuitBreaker",
    "RetryStrategy",
]
