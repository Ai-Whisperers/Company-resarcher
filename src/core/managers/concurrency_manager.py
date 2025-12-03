"""
Dynamic Concurrency Control Manager (ENH-003).

This module provides adaptive concurrency management based on:
- System load and response times
- Rate limit headers from API responses
- Error rates and backpressure signals

Usage:
    from src.core.managers.concurrency_manager import get_concurrency_manager

    manager = get_concurrency_manager()
    async with manager.acquire("search"):
        # Perform rate-limited operation
        result = await search_api.query(...)

    # Report rate limit info from response headers
    manager.report_rate_limit("search", remaining=50, limit=100, reset_at=time.time() + 60)
"""

import asyncio
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

from ..logging import setup_logger
from .memory_monitor import get_memory_monitor, MemoryMonitor, PSUTIL_AVAILABLE

logger = setup_logger("concurrency_manager")

# Memory-aware concurrency settings
ENABLE_MEMORY_AWARE = os.getenv("ENABLE_MEMORY_AWARE_CONCURRENCY", "true").lower() == "true"
MEMORY_WAIT_TIMEOUT = float(os.getenv("MEMORY_WAIT_TIMEOUT", "30"))


class ConcurrencyStrategy(str, Enum):
    """Concurrency adjustment strategies."""

    FIXED = "fixed"  # Never adjust (use initial value)
    ADAPTIVE = "adaptive"  # Adjust based on rate limits and errors
    AGGRESSIVE = "aggressive"  # More aggressive scaling up


@dataclass
class ProviderState:
    """Track concurrency state for a single provider/resource."""

    name: str
    current_limit: int
    min_limit: int = 1
    max_limit: int = 20
    semaphore: asyncio.Semaphore = field(default=None, repr=False)

    # Rate limit tracking
    rate_limit_remaining: Optional[int] = None
    rate_limit_total: Optional[int] = None
    rate_limit_reset_at: Optional[float] = None

    # Performance tracking
    recent_latencies: list = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0
    last_adjustment: float = field(default_factory=time.time)

    # Lock for thread-safe operations
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.current_limit)

    @property
    def error_rate(self) -> float:
        """Calculate recent error rate."""
        total = self.error_count + self.success_count
        if total == 0:
            return 0.0
        return self.error_count / total

    @property
    def avg_latency(self) -> float:
        """Calculate average recent latency."""
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)

    def record_latency(self, latency: float) -> None:
        """Record a request latency."""
        with self._lock:
            self.recent_latencies.append(latency)
            # Keep only last 100 latencies
            if len(self.recent_latencies) > 100:
                self.recent_latencies = self.recent_latencies[-100:]

    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            self.success_count += 1

    def record_error(self) -> None:
        """Record a failed request."""
        with self._lock:
            self.error_count += 1

    def reset_counters(self) -> None:
        """Reset error and success counters."""
        with self._lock:
            self.error_count = 0
            self.success_count = 0
            self.recent_latencies = []


class ConcurrencyManager:
    """
    Manages concurrency across multiple providers with adaptive scaling.

    Features:
    - Per-provider semaphores for rate limiting
    - Dynamic adjustment based on rate limit headers
    - Backpressure handling on errors
    - Configurable min/max limits per provider
    - Memory-aware concurrency control (IMP-002)
    """

    # Default limits per provider type
    DEFAULT_LIMITS = {
        "search": {"initial": 5, "min": 1, "max": 10},
        "browser": {"initial": 3, "min": 1, "max": 5},
        "ai": {"initial": 2, "min": 1, "max": 5},
        "default": {"initial": 5, "min": 1, "max": 20},
    }

    def __init__(
        self,
        strategy: ConcurrencyStrategy = ConcurrencyStrategy.ADAPTIVE,
        adjustment_interval: float = 30.0,
        enable_memory_aware: bool = ENABLE_MEMORY_AWARE,
        memory_wait_timeout: float = MEMORY_WAIT_TIMEOUT,
    ):
        """
        Initialize the concurrency manager.

        Args:
            strategy: How to adjust concurrency (fixed, adaptive, aggressive)
            adjustment_interval: Minimum seconds between adjustments
            enable_memory_aware: Whether to check memory before acquiring slots
            memory_wait_timeout: Seconds to wait for memory to become available
        """
        self.strategy = strategy
        self.adjustment_interval = adjustment_interval
        self.enable_memory_aware = enable_memory_aware and PSUTIL_AVAILABLE
        self.memory_wait_timeout = memory_wait_timeout
        self.providers: Dict[str, ProviderState] = {}
        self._lock = threading.Lock()
        self._memory_monitor: Optional[MemoryMonitor] = None

    @property
    def memory_monitor(self) -> MemoryMonitor:
        """Lazy-load memory monitor."""
        if self._memory_monitor is None:
            self._memory_monitor = get_memory_monitor()
        return self._memory_monitor

    def _get_or_create_provider(self, name: str) -> ProviderState:
        """Get or create provider state."""
        with self._lock:
            if name not in self.providers:
                # Determine limits based on provider type
                limits = self.DEFAULT_LIMITS.get(name, self.DEFAULT_LIMITS["default"])
                self.providers[name] = ProviderState(
                    name=name,
                    current_limit=limits["initial"],
                    min_limit=limits["min"],
                    max_limit=limits["max"],
                )
                logger.debug(
                    f"Created concurrency state for '{name}' with limit {limits['initial']}"
                )
            return self.providers[name]

    @asynccontextmanager
    async def acquire(self, provider: str = "default"):
        """
        Acquire a concurrency slot for the given provider.

        If memory-aware mode is enabled, waits for memory to be available
        before acquiring the slot (prevents OOM during high load).

        Usage:
            async with manager.acquire("search"):
                result = await search_api.query(...)
        """
        state = self._get_or_create_provider(provider)
        start_time = time.time()

        # Memory-aware: wait for memory if high
        if self.enable_memory_aware:
            if self.memory_monitor.is_memory_critical():
                logger.warning(
                    f"Memory critical ({self.memory_monitor.get_memory_usage():.1f}%), "
                    f"waiting before acquiring '{provider}' slot"
                )
                memory_available = await self.memory_monitor.wait_for_memory(
                    timeout=self.memory_wait_timeout
                )
                if not memory_available:
                    logger.warning(
                        f"Memory still high after {self.memory_wait_timeout}s wait, "
                        f"proceeding anyway for '{provider}'"
                    )
            elif self.memory_monitor.is_memory_high():
                # Memory is high but not critical - reduce concurrency proactively
                self._maybe_reduce_for_memory(state)

        try:
            async with state.semaphore:
                yield state
                # Record success after yield completes without error
                latency = time.time() - start_time
                state.record_latency(latency)
                state.record_success()
        except Exception:
            state.record_error()
            self._maybe_adjust_down(state)
            raise

    def _maybe_reduce_for_memory(self, state: ProviderState) -> None:
        """Proactively reduce concurrency when memory is high."""
        if self.strategy == ConcurrencyStrategy.FIXED:
            return

        # Only adjust if enough time has passed
        if time.time() - state.last_adjustment < self.adjustment_interval:
            return

        # Reduce if memory is high and we're above minimum
        if state.current_limit > state.min_limit:
            self._decrease_limit(state, reason="high memory usage")

    def report_rate_limit(
        self,
        provider: str,
        remaining: int,
        limit: int,
        reset_at: Optional[float] = None,
    ) -> None:
        """
        Report rate limit information from API response headers.

        Args:
            provider: Provider name
            remaining: Remaining requests in current window
            limit: Total requests allowed in window
            reset_at: Unix timestamp when limit resets
        """
        state = self._get_or_create_provider(provider)

        with state._lock:
            state.rate_limit_remaining = remaining
            state.rate_limit_total = limit
            state.rate_limit_reset_at = reset_at

        # Adjust concurrency based on remaining quota
        if self.strategy != ConcurrencyStrategy.FIXED:
            self._adjust_for_rate_limit(state)

    def _adjust_for_rate_limit(self, state: ProviderState) -> None:
        """Adjust concurrency based on rate limit remaining."""
        if state.rate_limit_remaining is None or state.rate_limit_total is None:
            return

        remaining_ratio = state.rate_limit_remaining / state.rate_limit_total

        # If less than 20% remaining, reduce concurrency
        if remaining_ratio < 0.2:
            self._decrease_limit(state, reason="low rate limit remaining")
        # If more than 80% remaining and not at max, consider increasing
        elif remaining_ratio > 0.8 and state.error_rate < 0.05:
            self._increase_limit(state, reason="high rate limit remaining")

    def _maybe_adjust_down(self, state: ProviderState) -> None:
        """Consider reducing concurrency after an error."""
        if self.strategy == ConcurrencyStrategy.FIXED:
            return

        # Only adjust if enough time has passed
        if time.time() - state.last_adjustment < self.adjustment_interval:
            return

        # If error rate is high, reduce concurrency
        if state.error_rate > 0.1:
            self._decrease_limit(state, reason="high error rate")

    def _increase_limit(self, state: ProviderState, reason: str = "") -> None:
        """Increase concurrency limit."""
        with state._lock:
            if state.current_limit < state.max_limit:
                old_limit = state.current_limit
                state.current_limit = min(state.current_limit + 1, state.max_limit)
                state.last_adjustment = time.time()

                # Create new semaphore with increased limit
                state.semaphore = asyncio.Semaphore(state.current_limit)

                logger.info(
                    f"Increased {state.name} concurrency: {old_limit} -> {state.current_limit} ({reason})"
                )

    def _decrease_limit(self, state: ProviderState, reason: str = "") -> None:
        """Decrease concurrency limit."""
        with state._lock:
            if state.current_limit > state.min_limit:
                old_limit = state.current_limit
                state.current_limit = max(state.current_limit - 1, state.min_limit)
                state.last_adjustment = time.time()

                # Create new semaphore with decreased limit
                state.semaphore = asyncio.Semaphore(state.current_limit)

                logger.info(
                    f"Decreased {state.name} concurrency: {old_limit} -> {state.current_limit} ({reason})"
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers including memory status."""
        stats = {
            "strategy": self.strategy.value,
            "memory_aware_enabled": self.enable_memory_aware,
            "providers": {
                name: {
                    "current_limit": state.current_limit,
                    "min_limit": state.min_limit,
                    "max_limit": state.max_limit,
                    "error_rate": round(state.error_rate, 3),
                    "avg_latency": round(state.avg_latency, 3),
                    "rate_limit_remaining": state.rate_limit_remaining,
                    "rate_limit_total": state.rate_limit_total,
                }
                for name, state in self.providers.items()
            },
        }

        # Include memory stats if memory-aware mode is enabled
        if self.enable_memory_aware:
            stats["memory"] = self.memory_monitor.get_stats()

        return stats

    def set_limit(self, provider: str, limit: int) -> None:
        """Manually set concurrency limit for a provider."""
        state = self._get_or_create_provider(provider)
        with state._lock:
            limit = max(state.min_limit, min(limit, state.max_limit))
            state.current_limit = limit
            state.semaphore = asyncio.Semaphore(limit)
            logger.info(f"Manually set {provider} concurrency to {limit}")

    def reset_provider(self, provider: str) -> None:
        """Reset a provider's state and counters."""
        if provider in self.providers:
            state = self.providers[provider]
            state.reset_counters()
            logger.debug(f"Reset counters for {provider}")


@lru_cache()
def get_concurrency_manager() -> ConcurrencyManager:
    """Get cached ConcurrencyManager instance."""
    strategy_env = os.getenv("CONCURRENCY_STRATEGY", "adaptive").lower()
    try:
        strategy = ConcurrencyStrategy(strategy_env)
    except ValueError:
        strategy = ConcurrencyStrategy.ADAPTIVE

    interval = float(os.getenv("CONCURRENCY_ADJUSTMENT_INTERVAL", "30"))

    return ConcurrencyManager(strategy=strategy, adjustment_interval=interval)


def clear_concurrency_manager():
    """Clear cached manager (useful for testing)."""
    get_concurrency_manager.cache_clear()


__all__ = [
    "ConcurrencyManager",
    "ConcurrencyStrategy",
    "ProviderState",
    "get_concurrency_manager",
    "clear_concurrency_manager",
]
