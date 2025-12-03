"""
Memory Monitor for Adaptive Concurrency Control (IMP-002).

This module provides memory usage monitoring to prevent OOM crashes
by pausing new tasks when memory is high.

Usage:
    from src.core.managers.memory_monitor import MemoryMonitor, get_memory_monitor

    monitor = get_memory_monitor()

    # Check before heavy operations
    if monitor.is_memory_safe():
        # Proceed with operation
        pass

    # Wait for memory to become available
    await monitor.wait_for_memory(timeout=30.0)
"""

import asyncio
import os
import threading
import time
from functools import lru_cache
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from ..logging import setup_logger

logger = setup_logger("memory_monitor")


# Memory threshold configuration
MEMORY_HIGH_THRESHOLD = float(os.getenv("MEMORY_HIGH_THRESHOLD", "85"))  # Percent
MEMORY_CRITICAL_THRESHOLD = float(os.getenv("MEMORY_CRITICAL_THRESHOLD", "95"))  # Percent
MEMORY_CHECK_INTERVAL = float(os.getenv("MEMORY_CHECK_INTERVAL", "5"))  # Seconds


class MemoryMonitor:
    """
    Monitor system memory usage for adaptive concurrency control.

    Prevents OOM crashes by:
    - Tracking memory usage with caching to reduce overhead
    - Providing thresholds for high and critical memory states
    - Async waiting for memory to become available
    """

    def __init__(
        self,
        high_threshold: float = MEMORY_HIGH_THRESHOLD,
        critical_threshold: float = MEMORY_CRITICAL_THRESHOLD,
        check_interval: float = MEMORY_CHECK_INTERVAL,
    ):
        """
        Initialize the memory monitor.

        Args:
            high_threshold: Memory usage % above which to pause scaling up
            critical_threshold: Memory usage % above which to pause new tasks
            check_interval: Seconds between memory checks (to reduce overhead)
        """
        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold
        self.check_interval = check_interval
        self._last_check_time = 0.0
        self._last_memory_percent = 0.0
        self._lock = threading.Lock()

    def get_memory_usage(self) -> float:
        """
        Get current memory usage percentage (0-100).

        Caches result for check_interval seconds to avoid excessive calls.
        Returns 0.0 if psutil is not available.
        """
        if not PSUTIL_AVAILABLE:
            return 0.0

        current_time = time.time()
        with self._lock:
            if current_time - self._last_check_time >= self.check_interval:
                try:
                    self._last_memory_percent = psutil.virtual_memory().percent
                    self._last_check_time = current_time
                except Exception as e:
                    logger.debug(f"Failed to get memory usage: {e}")
            return self._last_memory_percent

    def is_memory_safe(self) -> bool:
        """Check if memory usage is below high threshold."""
        return self.get_memory_usage() < self.high_threshold

    def is_memory_high(self) -> bool:
        """Check if memory usage is above high threshold."""
        return self.get_memory_usage() >= self.high_threshold

    def is_memory_critical(self) -> bool:
        """Check if memory usage is at critical level."""
        return self.get_memory_usage() >= self.critical_threshold

    async def wait_for_memory(self, timeout: float = 60.0) -> bool:
        """
        Wait until memory usage drops below high threshold.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if memory became safe, False if timeout reached
        """
        if not PSUTIL_AVAILABLE:
            return True

        start_time = time.time()
        while not self.is_memory_safe():
            if time.time() - start_time > timeout:
                logger.warning(
                    f"Memory wait timeout ({timeout}s) - "
                    f"current usage: {self.get_memory_usage():.1f}%"
                )
                return False

            logger.debug(
                f"Memory high ({self.get_memory_usage():.1f}%), "
                f"waiting {self.check_interval}s..."
            )
            await asyncio.sleep(self.check_interval)

        return True

    def get_available_memory_mb(self) -> float:
        """Get available memory in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            return psutil.virtual_memory().available / (1024 * 1024)
        except Exception:
            return 0.0

    def get_total_memory_mb(self) -> float:
        """Get total memory in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            return psutil.virtual_memory().total / (1024 * 1024)
        except Exception:
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get memory monitor statistics."""
        return {
            "available": PSUTIL_AVAILABLE,
            "current_percent": self.get_memory_usage(),
            "available_mb": round(self.get_available_memory_mb(), 1),
            "total_mb": round(self.get_total_memory_mb(), 1),
            "high_threshold": self.high_threshold,
            "critical_threshold": self.critical_threshold,
            "is_safe": self.is_memory_safe(),
            "is_high": self.is_memory_high(),
            "is_critical": self.is_memory_critical(),
        }


@lru_cache()
def get_memory_monitor() -> MemoryMonitor:
    """Get cached MemoryMonitor instance."""
    return MemoryMonitor()


def clear_memory_monitor():
    """Clear cached monitor (useful for testing)."""
    get_memory_monitor.cache_clear()


__all__ = [
    "MemoryMonitor",
    "get_memory_monitor",
    "clear_memory_monitor",
    "PSUTIL_AVAILABLE",
    "MEMORY_HIGH_THRESHOLD",
    "MEMORY_CRITICAL_THRESHOLD",
]
