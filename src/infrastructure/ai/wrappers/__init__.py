"""
AI Client Wrappers.

Provides decorator pattern wrappers for AI clients:
- DelegatingAIClient: Base class for all wrappers
- RateLimitedAIClient: Adds rate limiting
- CachedAIClient: Adds response caching
- CostTrackedAIClient: Adds cost tracking
"""

from .base import DelegatingAIClient
from .rate_limited import RateLimitedAIClient
from .cached import CachedAIClient
from .cost_tracked import CostTrackedAIClient

__all__ = [
    "DelegatingAIClient",
    "RateLimitedAIClient",
    "CachedAIClient",
    "CostTrackedAIClient",
]
