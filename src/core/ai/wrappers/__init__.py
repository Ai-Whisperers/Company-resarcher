"""
AI Client Wrappers.

Provides decorator pattern wrappers for AI clients:
- DelegatingAIClient: Base class for all wrappers
- RateLimitedClient: Adds rate limiting
- CachedClient: Adds response caching
- CostTrackedClient: Adds cost tracking
"""

from .base import DelegatingAIClient
from .rate_limited import RateLimitedClient
from .cached import CachedClient

__all__ = [
    "DelegatingAIClient",
    "RateLimitedClient",
    "CachedClient",
]
