"""
Browser Pool with Health Checks (PERF-019).

Manages a pool of browser contexts with health monitoring,
automatic recovery, and load balancing.
"""

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
from contextlib import asynccontextmanager

from .logger import setup_logger

logger = setup_logger("browser_pool")


class ContextHealth(Enum):
    """Health status of a browser context."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Working but with issues
    UNHEALTHY = "unhealthy"  # Should be replaced
    DEAD = "dead"  # Completely broken


@dataclass
class ContextStats:
    """Statistics for a browser context."""
    pages_loaded: int = 0
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    consecutive_failures: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    total_load_time: float = 0.0

    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        if total == 0:
            return 1.0
        return self.successes / total

    @property
    def avg_load_time(self) -> float:
        if self.successes == 0:
            return 0.0
        return self.total_load_time / self.successes

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


@dataclass
class PoolConfig:
    """Configuration for browser pool."""
    min_contexts: int = 1
    max_contexts: int = 5
    max_pages_per_context: int = 50  # Recycle after this many pages
    max_context_age_seconds: int = 600  # Recycle after 10 minutes
    health_check_interval: int = 30  # Check health every 30 seconds
    consecutive_failure_threshold: int = 3  # Mark unhealthy after 3 failures
    auto_recover: bool = True


class BrowserContextWrapper:
    """
    Wrapper around a browser context with health tracking.
    """

    def __init__(
        self,
        context: Any,  # playwright.async_api.BrowserContext
        context_id: str,
        pool: "BrowserPool",
    ):
        self.context = context
        self.context_id = context_id
        self.pool = pool
        self.stats = ContextStats()
        self.health = ContextHealth.HEALTHY
        self._lock = asyncio.Lock()
        self._in_use = False

    async def get_page(self) -> Any:
        """Get a page from this context."""
        try:
            page = await self.context.new_page()
            self.stats.pages_loaded += 1
            return page
        except Exception as e:
            logger.warning(f"Failed to create page in context {self.context_id}: {e}")
            self.health = ContextHealth.UNHEALTHY
            raise

    async def close_page(self, page: Any) -> None:
        """Close a page."""
        try:
            if page and not page.is_closed():
                await page.close()
        except Exception as e:
            logger.debug(f"Error closing page: {e}")

    def record_success(self, load_time: float = 0.0) -> None:
        """Record a successful operation."""
        self.stats.successes += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success = time.time()
        self.stats.total_load_time += load_time

        if self.health == ContextHealth.DEGRADED:
            self.health = ContextHealth.HEALTHY

    def record_failure(self, is_timeout: bool = False) -> None:
        """Record a failed operation."""
        self.stats.failures += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure = time.time()

        if is_timeout:
            self.stats.timeouts += 1

        # Update health based on failures
        if self.stats.consecutive_failures >= self.pool.config.consecutive_failure_threshold:
            self.health = ContextHealth.UNHEALTHY
        elif self.stats.consecutive_failures >= 2:
            self.health = ContextHealth.DEGRADED

    def should_recycle(self) -> bool:
        """Check if context should be recycled."""
        config = self.pool.config

        # Too many pages loaded
        if self.stats.pages_loaded >= config.max_pages_per_context:
            return True

        # Too old
        if self.stats.age_seconds >= config.max_context_age_seconds:
            return True

        # Unhealthy
        if self.health == ContextHealth.UNHEALTHY:
            return True

        return False

    async def check_health(self) -> ContextHealth:
        """Perform health check on context."""
        try:
            # Try to access context properties
            if self.context.pages is None:
                self.health = ContextHealth.DEAD
                return self.health

            # Check if we can create a test page
            async with asyncio.timeout(5):
                test_page = await self.context.new_page()
                await test_page.close()

            # Context is responsive
            if self.health == ContextHealth.DEGRADED:
                self.health = ContextHealth.HEALTHY

            return self.health

        except asyncio.TimeoutError:
            self.health = ContextHealth.DEGRADED
            return self.health
        except Exception as e:
            logger.debug(f"Health check failed for {self.context_id}: {e}")
            self.health = ContextHealth.DEAD
            return self.health

    async def close(self) -> None:
        """Close this context."""
        try:
            await self.context.close()
        except Exception as e:
            logger.debug(f"Error closing context {self.context_id}: {e}")


class BrowserPool:
    """
    Pool of browser contexts with health management.

    Features:
    - Automatic context creation/recycling
    - Health monitoring with automatic recovery
    - Load balancing across contexts
    - Graceful degradation under load

    Usage:
        pool = BrowserPool(browser)
        await pool.start()

        async with pool.get_context() as ctx:
            page = await ctx.get_page()
            await page.goto(url)
            ctx.record_success(elapsed)

        await pool.stop()
    """

    def __init__(
        self,
        browser: Any,  # playwright.async_api.Browser
        config: Optional[PoolConfig] = None,
    ):
        self.browser = browser
        self.config = config or PoolConfig()
        self._contexts: Dict[str, BrowserContextWrapper] = {}
        self._context_counter = 0
        self._lock = asyncio.Lock()
        self._running = False
        self._health_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the browser pool."""
        async with self._lock:
            if self._running:
                return

            # Create initial contexts
            for _ in range(self.config.min_contexts):
                await self._create_context()

            self._running = True

            # Start health check task
            if self.config.auto_recover:
                self._health_task = asyncio.create_task(self._health_check_loop())

            logger.info(
                f"Browser pool started with {len(self._contexts)} contexts "
                f"(min={self.config.min_contexts}, max={self.config.max_contexts})"
            )

    async def stop(self) -> None:
        """Stop the browser pool."""
        async with self._lock:
            self._running = False

            # Cancel health check
            if self._health_task:
                self._health_task.cancel()
                try:
                    await self._health_task
                except asyncio.CancelledError:
                    pass

            # Close all contexts
            for wrapper in list(self._contexts.values()):
                await wrapper.close()

            self._contexts.clear()
            logger.info("Browser pool stopped")

    async def _create_context(self) -> BrowserContextWrapper:
        """Create a new browser context."""
        self._context_counter += 1
        context_id = f"ctx_{self._context_counter}"

        try:
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                java_script_enabled=True,
            )

            wrapper = BrowserContextWrapper(context, context_id, self)
            self._contexts[context_id] = wrapper

            logger.debug(f"Created browser context {context_id}")
            return wrapper

        except Exception as e:
            logger.error(f"Failed to create browser context: {e}")
            raise

    async def _remove_context(self, context_id: str) -> None:
        """Remove and close a context."""
        if context_id in self._contexts:
            wrapper = self._contexts.pop(context_id)
            await wrapper.close()
            logger.debug(f"Removed browser context {context_id}")

    @asynccontextmanager
    async def get_context(self):
        """
        Get a healthy browser context from the pool.

        Usage:
            async with pool.get_context() as ctx:
                page = await ctx.get_page()
                # ... use page ...
                ctx.record_success()
        """
        async with self._lock:
            # Find best available context
            wrapper = await self._select_context()

            if wrapper is None:
                # Create new context if under max
                if len(self._contexts) < self.config.max_contexts:
                    wrapper = await self._create_context()
                else:
                    # Wait for a context to become available
                    raise RuntimeError("No browser contexts available")

            wrapper._in_use = True

        try:
            yield wrapper
        finally:
            wrapper._in_use = False

            # Check if context should be recycled after use
            if wrapper.should_recycle():
                asyncio.create_task(self._recycle_context(wrapper.context_id))

    async def _select_context(self) -> Optional[BrowserContextWrapper]:
        """Select the best available context."""
        candidates = []

        for wrapper in self._contexts.values():
            if wrapper._in_use:
                continue
            if wrapper.health == ContextHealth.DEAD:
                continue
            if wrapper.should_recycle():
                continue

            candidates.append(wrapper)

        if not candidates:
            return None

        # Sort by health (healthy first), then by usage (least used first)
        candidates.sort(key=lambda w: (
            w.health != ContextHealth.HEALTHY,
            w.stats.pages_loaded,
        ))

        return candidates[0]

    async def _recycle_context(self, context_id: str) -> None:
        """Recycle a context by replacing it with a new one."""
        async with self._lock:
            await self._remove_context(context_id)

            # Create replacement if we're under min
            if len(self._contexts) < self.config.min_contexts:
                await self._create_context()

        logger.debug(f"Recycled context {context_id}")

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                async with self._lock:
                    for context_id, wrapper in list(self._contexts.items()):
                        if wrapper._in_use:
                            continue

                        health = await wrapper.check_health()

                        if health == ContextHealth.DEAD:
                            logger.warning(f"Context {context_id} is dead, recycling")
                            await self._recycle_context(context_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        contexts_stats = {}
        total_successes = 0
        total_failures = 0

        for ctx_id, wrapper in self._contexts.items():
            contexts_stats[ctx_id] = {
                "health": wrapper.health.value,
                "pages_loaded": wrapper.stats.pages_loaded,
                "success_rate": wrapper.stats.success_rate,
                "age_seconds": wrapper.stats.age_seconds,
                "in_use": wrapper._in_use,
            }
            total_successes += wrapper.stats.successes
            total_failures += wrapper.stats.failures

        return {
            "total_contexts": len(self._contexts),
            "healthy_contexts": sum(1 for w in self._contexts.values() if w.health == ContextHealth.HEALTHY),
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 1.0,
            "contexts": contexts_stats,
        }

    def get_health_summary(self) -> Dict[str, int]:
        """Get summary of context health states."""
        summary = {health.value: 0 for health in ContextHealth}
        for wrapper in self._contexts.values():
            summary[wrapper.health.value] += 1
        return summary


# Global browser pool instance
_browser_pool: Optional[BrowserPool] = None
_pool_lock = threading.Lock()


async def get_browser_pool(browser: Any) -> BrowserPool:
    """Get or create global browser pool."""
    global _browser_pool
    if _browser_pool is None:
        with _pool_lock:
            if _browser_pool is None:
                _browser_pool = BrowserPool(browser)
                await _browser_pool.start()
    return _browser_pool


async def reset_browser_pool() -> None:
    """Reset the global browser pool."""
    global _browser_pool
    with _pool_lock:
        if _browser_pool is not None:
            await _browser_pool.stop()
            _browser_pool = None


__all__ = [
    "BrowserPool",
    "BrowserContextWrapper",
    "PoolConfig",
    "ContextHealth",
    "ContextStats",
    "get_browser_pool",
    "reset_browser_pool",
]
