"""
Browser-related core functionality.

Provides:
- BrowserAgent: Browser automation agent
- BrowserConfig: Browser configuration
- BrowserPool: Browser instance pooling
"""

from .browser_agent import *
from .browser_config import *
from .browser_pool import *

__all__ = [
    "BrowserAgent",
    "BrowserConfig",
    "BrowserPool",
]
