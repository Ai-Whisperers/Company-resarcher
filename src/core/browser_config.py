"""
Browser Configuration Management (IMP-008).

Centralizes browser settings for consistent configuration across the codebase.
Inspired by crawl4ai's BrowserConfig pattern.

Usage:
    from src.core.browser_config import BrowserConfig, get_browser_config

    config = get_browser_config()

    # Access settings
    browser = await playwright.chromium.launch(headless=config.headless)
    page = await browser.new_page(
        viewport=config.viewport,
        user_agent=config.user_agent,
    )

    # Override for specific use case
    custom_config = BrowserConfig(headless=False, viewport={"width": 1920, "height": 1080})
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Any

from .logger import setup_logger

logger = setup_logger("browser_config")


# Default user agents for rotation
DEFAULT_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


@dataclass
class BrowserConfig:
    """
    Centralized browser configuration.

    All browser settings in one place for easy management
    and consistent behavior across the application.
    """

    # Browser type
    browser_type: str = "chromium"  # chromium, firefox, webkit

    # Display settings
    headless: bool = True
    viewport: Dict[str, int] = field(
        default_factory=lambda: {"width": 1280, "height": 720}
    )

    # User agent
    user_agent: str = DEFAULT_USER_AGENTS[0]
    rotate_user_agent: bool = False

    # Timeouts (in milliseconds for Playwright compatibility)
    page_timeout_ms: int = 30000  # 30 seconds
    navigation_timeout_ms: int = 30000  # 30 seconds
    fetch_timeout_seconds: int = 60  # Overall fetch timeout

    # Concurrency
    max_concurrent_pages: int = 5

    # Network settings
    ignore_https_errors: bool = False
    extra_http_headers: Dict[str, str] = field(default_factory=dict)

    # Proxy configuration
    proxy_server: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None

    # JavaScript settings
    javascript_enabled: bool = True
    bypass_csp: bool = False  # Bypass Content Security Policy

    # Storage and cookies
    accept_downloads: bool = False
    storage_state_path: Optional[str] = None

    # Anti-detection features
    disable_webrtc: bool = True  # Prevent WebRTC IP leak
    mock_geolocation: bool = False
    geolocation: Optional[Dict[str, float]] = None  # {"latitude": 0, "longitude": 0}

    # Resource blocking
    block_images: bool = False
    block_fonts: bool = False
    block_stylesheets: bool = False
    block_media: bool = False

    # Extra Chromium arguments
    extra_args: List[str] = field(default_factory=list)

    # HTML caching
    enable_html_cache: bool = True

    def __post_init__(self):
        """Validate and normalize configuration."""
        # Ensure viewport has required keys
        if "width" not in self.viewport or "height" not in self.viewport:
            self.viewport = {"width": 1280, "height": 720}

        # Add default anti-detection args for Chromium
        if self.browser_type == "chromium" and not self.extra_args:
            self.extra_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

    def get_launch_options(self) -> Dict[str, Any]:
        """Get options for playwright.chromium.launch()."""
        options = {
            "headless": self.headless,
        }

        if self.extra_args:
            options["args"] = self.extra_args

        if self.proxy_server:
            proxy = {"server": self.proxy_server}
            if self.proxy_username:
                proxy["username"] = self.proxy_username
            if self.proxy_password:
                proxy["password"] = self.proxy_password
            options["proxy"] = proxy

        return options

    def get_context_options(self) -> Dict[str, Any]:
        """Get options for browser.new_context()."""
        options = {
            "viewport": self.viewport,
            "user_agent": self.user_agent,
            "ignore_https_errors": self.ignore_https_errors,
            "java_script_enabled": self.javascript_enabled,
            "bypass_csp": self.bypass_csp,
            "accept_downloads": self.accept_downloads,
        }

        if self.extra_http_headers:
            options["extra_http_headers"] = self.extra_http_headers

        if self.geolocation:
            options["geolocation"] = self.geolocation

        if self.storage_state_path:
            options["storage_state"] = self.storage_state_path

        return options

    def get_page_options(self) -> Dict[str, Any]:
        """Get default navigation options for pages."""
        return {
            "timeout": self.navigation_timeout_ms,
            "wait_until": "domcontentloaded",
        }

    def get_blocked_resources(self) -> List[str]:
        """Get list of resource types to block."""
        blocked = []
        if self.block_images:
            blocked.append("image")
        if self.block_fonts:
            blocked.append("font")
        if self.block_stylesheets:
            blocked.append("stylesheet")
        if self.block_media:
            blocked.extend(["media", "video", "audio"])
        return blocked

    def get_next_user_agent(self) -> str:
        """Get next user agent for rotation."""
        if not self.rotate_user_agent:
            return self.user_agent

        import random
        return random.choice(DEFAULT_USER_AGENTS)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "browser_type": self.browser_type,
            "headless": self.headless,
            "viewport": self.viewport,
            "user_agent": self.user_agent[:50] + "...",  # Truncate for readability
            "page_timeout_ms": self.page_timeout_ms,
            "navigation_timeout_ms": self.navigation_timeout_ms,
            "fetch_timeout_seconds": self.fetch_timeout_seconds,
            "max_concurrent_pages": self.max_concurrent_pages,
            "javascript_enabled": self.javascript_enabled,
            "enable_html_cache": self.enable_html_cache,
            "has_proxy": self.proxy_server is not None,
        }


@lru_cache()
def get_browser_config() -> BrowserConfig:
    """
    Get cached browser configuration instance.

    Loads settings from environment variables.
    """
    config = BrowserConfig(
        headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
        page_timeout_ms=int(os.getenv("BROWSER_PAGE_TIMEOUT_MS", "30000")),
        navigation_timeout_ms=int(os.getenv("BROWSER_NAVIGATION_TIMEOUT_MS", "30000")),
        fetch_timeout_seconds=int(os.getenv("BROWSER_FETCH_TIMEOUT_SECONDS", "60")),
        max_concurrent_pages=int(os.getenv("BROWSER_MAX_CONCURRENT", "5")),
        enable_html_cache=os.getenv("ENABLE_HTML_CACHE", "true").lower() == "true",
        proxy_server=os.getenv("BROWSER_PROXY_SERVER"),
        proxy_username=os.getenv("BROWSER_PROXY_USERNAME"),
        proxy_password=os.getenv("BROWSER_PROXY_PASSWORD"),
        block_images=os.getenv("BROWSER_BLOCK_IMAGES", "false").lower() == "true",
        block_fonts=os.getenv("BROWSER_BLOCK_FONTS", "false").lower() == "true",
        rotate_user_agent=os.getenv("BROWSER_ROTATE_USER_AGENT", "false").lower() == "true",
    )

    # Custom user agent from environment
    custom_ua = os.getenv("BROWSER_USER_AGENT")
    if custom_ua:
        config.user_agent = custom_ua

    # Custom viewport from environment
    viewport_width = os.getenv("BROWSER_VIEWPORT_WIDTH")
    viewport_height = os.getenv("BROWSER_VIEWPORT_HEIGHT")
    if viewport_width and viewport_height:
        config.viewport = {
            "width": int(viewport_width),
            "height": int(viewport_height),
        }

    logger.debug(f"Browser config loaded: {config.to_dict()}")
    return config


def clear_browser_config():
    """Clear cached config (useful for testing)."""
    get_browser_config.cache_clear()


__all__ = [
    "BrowserConfig",
    "get_browser_config",
    "clear_browser_config",
    "DEFAULT_USER_AGENTS",
]
