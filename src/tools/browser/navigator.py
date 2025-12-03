"""
Navigator - Page Navigation and Waiting

Handles:
- URL navigation with error handling
- Wait for selectors and network idle
- Scrolling and interaction
- URL validation
"""

import asyncio
from typing import Optional, Literal
from dataclasses import dataclass

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from ...core.logging import setup_logger
from ...core.validation import URLValidator, URLValidationError

logger = setup_logger("browser_navigator")


WaitUntil = Literal["load", "domcontentloaded", "networkidle", "commit"]


@dataclass
class NavigationResult:
    """Result of a navigation attempt."""

    success: bool
    url: str
    final_url: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    redirected: bool = False


class Navigator:
    """
    Handles page navigation and waiting.

    Responsibilities:
    - Navigate to URLs with configurable wait conditions
    - Wait for selectors and network states
    - Handle redirects and errors
    - Provide scrolling capabilities
    """

    def __init__(
        self,
        default_timeout_ms: int = 30000,
        default_wait_until: WaitUntil = "domcontentloaded",
    ):
        self.default_timeout_ms = default_timeout_ms
        self.default_wait_until = default_wait_until

    async def goto(
        self,
        page: Page,
        url: str,
        wait_until: Optional[WaitUntil] = None,
        timeout_ms: Optional[int] = None,
        validate_url: bool = True,
    ) -> NavigationResult:
        """
        Navigate to a URL.

        Args:
            page: Playwright page instance
            url: URL to navigate to
            wait_until: When to consider navigation complete
            timeout_ms: Navigation timeout
            validate_url: Whether to validate URL for security

        Returns:
            NavigationResult with status information
        """
        # Validate URL
        if validate_url:
            try:
                URLValidator.validate_url(url)
            except URLValidationError as e:
                logger.warning(f"URL validation failed for {url}: {e}")
                return NavigationResult(
                    success=False,
                    url=url,
                    final_url=url,
                    error=f"URL blocked for security: {e}",
                )

        try:
            response = await page.goto(
                url,
                wait_until=wait_until or self.default_wait_until,
                timeout=timeout_ms or self.default_timeout_ms,
            )

            final_url = page.url
            status_code = response.status if response else None

            return NavigationResult(
                success=True,
                url=url,
                final_url=final_url,
                status_code=status_code,
                redirected=final_url != url,
            )

        except PlaywrightTimeout:
            logger.warning(f"Navigation timeout for {url}")
            return NavigationResult(
                success=False,
                url=url,
                final_url=page.url,
                error="Navigation timeout",
            )

        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            return NavigationResult(
                success=False,
                url=url,
                final_url=url,
                error=str(e),
            )

    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout_ms: int = 5000,
        state: Literal["attached", "detached", "visible", "hidden"] = "visible",
    ) -> bool:
        """
        Wait for a selector to appear on the page.

        Args:
            page: Playwright page instance
            selector: CSS selector to wait for
            timeout_ms: Wait timeout
            state: State to wait for

        Returns:
            True if selector found, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout_ms, state=state)
            return True
        except PlaywrightTimeout:
            logger.debug(f"Timeout waiting for selector '{selector}'")
            return False
        except Exception as e:
            logger.warning(f"Error waiting for selector '{selector}': {e}")
            return False

    async def wait_for_load_state(
        self,
        page: Page,
        state: Literal["load", "domcontentloaded", "networkidle"] = "networkidle",
        timeout_ms: Optional[int] = None,
    ) -> bool:
        """
        Wait for page to reach a specific load state.

        Args:
            page: Playwright page instance
            state: Load state to wait for
            timeout_ms: Wait timeout

        Returns:
            True if state reached, False on timeout
        """
        try:
            await page.wait_for_load_state(
                state,
                timeout=timeout_ms or self.default_timeout_ms,
            )
            return True
        except PlaywrightTimeout:
            logger.debug(f"Timeout waiting for load state '{state}'")
            return False
        except Exception as e:
            logger.warning(f"Error waiting for load state '{state}': {e}")
            return False

    async def scroll_to_bottom(
        self,
        page: Page,
        step_px: int = 500,
        delay_ms: int = 100,
        max_scrolls: int = 50,
    ) -> int:
        """
        Scroll to the bottom of the page gradually.

        Useful for triggering lazy-loaded content.

        Args:
            page: Playwright page instance
            step_px: Pixels to scroll per step
            delay_ms: Delay between scrolls
            max_scrolls: Maximum scroll iterations

        Returns:
            Number of scrolls performed
        """
        scrolls = 0
        previous_height = 0

        for _ in range(max_scrolls):
            current_height = await page.evaluate("document.body.scrollHeight")

            if current_height == previous_height:
                break

            await page.evaluate(f"window.scrollBy(0, {step_px})")
            await asyncio.sleep(delay_ms / 1000)

            previous_height = current_height
            scrolls += 1

        return scrolls

    async def scroll_into_view(self, page: Page, selector: str) -> bool:
        """
        Scroll an element into view.

        Args:
            page: Playwright page instance
            selector: CSS selector of element to scroll into view

        Returns:
            True if successful, False otherwise
        """
        try:
            element = await page.query_selector(selector)
            if element:
                await element.scroll_into_view_if_needed()
                return True
            return False
        except Exception as e:
            logger.warning(f"Error scrolling '{selector}' into view: {e}")
            return False

    async def execute_js(self, page: Page, script: str) -> Optional[str]:
        """
        Execute JavaScript on the page.

        Args:
            page: Playwright page instance
            script: JavaScript code to execute

        Returns:
            Result of script execution or None on error
        """
        try:
            result = await page.evaluate(script)
            return result
        except Exception as e:
            logger.warning(f"Error executing JavaScript: {e}")
            return None
