"""
Modular Browser Tool - DEBT-001 Refactor

Splits browser functionality into focused components:
- BrowserManager: Playwright lifecycle management
- Navigator: Page navigation and waiting
- ContentExtractor: Content extraction and cleaning
- ModularBrowserTool: High-level interface composing all components
"""

from .manager import BrowserManager
from .navigator import Navigator
from .extractor import ContentExtractor
from .tool import ModularBrowserTool, FETCH_OVERALL_TIMEOUT

# Backwards compatibility alias (P1 fix)
BrowserTool = ModularBrowserTool

__all__ = [
    "BrowserManager",
    "Navigator",
    "ContentExtractor",
    "ModularBrowserTool",
    "BrowserTool",  # Alias for backwards compatibility
    "FETCH_OVERALL_TIMEOUT",
]
