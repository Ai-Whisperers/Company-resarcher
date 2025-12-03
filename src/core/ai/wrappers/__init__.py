"""
AI Client Wrappers.

Provides decorator pattern wrappers for AI clients:
- DelegatingAIClient: Base class for all wrappers
- RateLimitedClient: Adds rate limiting
- CachedClient: Adds response caching
- CostTrackedAIClient: Adds cost tracking
"""

from .base import DelegatingAIClient
from .rate_limited import RateLimitedClient
from .cached import CachedClient
from .cost_tracked import CostTrackedAIClient

__all__ = [
    "DelegatingAIClient",
    "RateLimitedClient",
    "CachedClient",
    "CostTrackedAIClient",
]
