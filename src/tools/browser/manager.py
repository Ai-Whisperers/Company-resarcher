"""
Browser Manager - Playwright Lifecycle Management

Handles:
- Browser initialization and cleanup
- Context and page management
- Resource pooling and reuse
"""

import asyncio
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from ...core.logger import setup_logger

logger = setup_logger("browser_manager")


@dataclass
class BrowserConfig:
    """Configuration for browser manager."""

    headless: bool = True
    timeout_ms: int = 30000
    max_concurrent_pages: int = 5
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    ignore_https_errors: bool = False
    proxy: Optional[Dict[str, str]] = None

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """Create config from environment variables."""
        return cls(
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            timeout_ms=int(os.getenv("BROWSER_PAGE_TIMEOUT_MS", "30000")),
            max_concurrent_pages=int(os.getenv("BROWSER_MAX_CONCURRENT", "5")),
            user_agent=os.getenv("BROWSER_USER_AGENT"),
            viewport_width=int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920")),
            viewport_height=int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080")),
            ignore_https_errors=os.getenv("BROWSER_IGNORE_HTTPS_ERRORS", "false").lower() == "true",
        )


class BrowserManager:
    """
    Manages Playwright browser lifecycle.

    Responsibilities:
    - Initialize/shutdown Playwright and browser
    - Create and manage browser contexts
    - Handle page creation with proper cleanup
    - Provide async context manager interface
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig.from_env()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._init_lock = asyncio.Lock()
        self._page_semaphore = asyncio.Semaphore(self.config.max_concurrent_pages)
        self._is_started = False

    @property
    def is_started(self) -> bool:
        """Check if browser is initialized."""
        return self._is_started and self._browser is not None

    async def __aenter__(self) -> "BrowserManager":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.stop()

    async def start(self) -> None:
        """Initialize Playwright and browser."""
        if self._is_started:
            return

        async with self._init_lock:
            if self._is_started:
                return

            try:
                self._playwright = await async_playwright().start()

                launch_options: Dict[str, Any] = {
                    "headless": self.config.headless,
                }

                if self.config.proxy:
                    launch_options["proxy"] = self.config.proxy

                self._browser = await self._playwright.chromium.launch(**launch_options)

                # Create default context
                context_options: Dict[str, Any] = {
                    "viewport": {
                        "width": self.config.viewport_width,
                        "height": self.config.viewport_height,
                    },
                    "ignore_https_errors": self.config.ignore_https_errors,
                }

                if self.config.user_agent:
                    context_options["user_agent"] = self.config.user_agent

                self._context = await self._browser.new_context(**context_options)

                self._is_started = True
                logger.info("Browser manager started successfully")

            except Exception as e:
                logger.error(f"Failed to start browser: {e}")
                await self.stop()
                raise

    async def stop(self) -> None:
        """Shutdown browser and Playwright."""
        try:
            if self._context:
                await self._context.close()
                self._context = None

            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._is_started = False
            logger.info("Browser manager stopped")

        except Exception as e:
            logger.error(f"Error during browser shutdown: {e}")
            raise

    async def get_page(self) -> Page:
        """
        Get a new page from the browser context.

        Uses semaphore to limit concurrent pages.
        Caller is responsible for closing the page.
        """
        if not self._is_started:
            await self.start()

        await self._page_semaphore.acquire()

        try:
            page = await self._context.new_page()
            page.set_default_timeout(self.config.timeout_ms)
            return page
        except Exception:
            self._page_semaphore.release()
            raise

    async def release_page(self, page: Page) -> None:
        """Release a page and return semaphore permit."""
        try:
            if page and not page.is_closed():
                await page.close()
        except Exception as e:
            logger.warning(f"Error closing page: {e}")
        finally:
            self._page_semaphore.release()

    async def new_context(self, **options) -> BrowserContext:
        """Create a new browser context with custom options."""
        if not self._is_started:
            await self.start()

        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "ignore_https_errors": self.config.ignore_https_errors,
            **options,
        }

        if self.config.user_agent and "user_agent" not in options:
            context_options["user_agent"] = self.config.user_agent

        return await self._browser.new_context(**context_options)
