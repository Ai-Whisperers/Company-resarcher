"""
Resilience patterns for handling failures gracefully.

Provides:
- CircuitBreaker: Prevent cascading failures
- RetryStrategy: Retry failed operations with backoff
- AdaptiveTimeoutManager: Dynamic timeout adjustment
- TimeoutBudget: Budget-based timeout management
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerStats, CircuitBreakerRegistry
from .retry_strategy import RetryStrategy
from .adaptive_timeout import AdaptiveTimeoutManager
from .timeout_budget import TimeoutBudget
from .rate_limiting import *

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerStats",
    "CircuitBreakerRegistry",
    "RetryStrategy",
    "AdaptiveTimeoutManager",
    "TimeoutBudget",
    "RateLimiter",
]
