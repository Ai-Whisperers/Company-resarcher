"""
Circuit Breaker pattern implementation for external service resilience.

Prevents cascading failures by detecting repeated failures and "opening" the circuit
to fail fast instead of waiting for timeouts. This protects the system from
overwhelming failing services and allows time for recovery.

States:
    CLOSED: Normal operation, requests pass through
    OPEN: Circuit tripped, requests fail immediately
    HALF_OPEN: Testing if service recovered, limited requests allowed

Example:
    breaker = CircuitBreaker(name="openai", failure_threshold=5, recovery_timeout=60)

    @breaker
    async def call_openai():
        return await openai_client.generate(...)

    # Or manual usage:
    async with breaker:
        result = await openai_client.generate(...)
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    TypeVar,
    ParamSpec,
    Optional,
    Any,
)
from functools import wraps

from .logger import setup_logger
from .exceptions import CompanyResearcherError

logger = setup_logger("circuit_breaker")

# Type variables for generic decorator
P = ParamSpec("P")
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(CompanyResearcherError):
    """Raised when circuit breaker is open and request is rejected."""

    def __init__(self, name: str, retry_after: float):
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is open. Retry after {retry_after:.1f}s",
            details={"circuit": name, "retry_after": retry_after},
        )


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Requests rejected due to open circuit
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    current_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        total = self.successful_requests + self.failed_requests
        if total == 0:
            return 0.0
        return (self.failed_requests / total) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for logging/API."""
        return {
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "rejected": self.rejected_requests,
            "failure_rate": f"{self.failure_rate:.1f}%",
            "state": self.current_state.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "state_changes": self.state_changes,
        }


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Args:
        name: Identifier for this circuit (e.g., "openai", "search")
        failure_threshold: Number of consecutive failures before opening
        recovery_timeout: Seconds to wait before attempting recovery (half-open)
        success_threshold: Consecutive successes needed to close from half-open
        excluded_exceptions: Exception types that don't count as failures

    Example:
        # As decorator
        breaker = CircuitBreaker("openai")

        @breaker
        async def call_api():
            ...

        # As context manager
        async with breaker:
            await call_api()

        # Manual control
        if breaker.can_execute():
            try:
                result = await call_api()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure(e)
                raise
    """

    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    excluded_exceptions: tuple[type[Exception], ...] = field(default_factory=tuple)

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[float] = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _stats: CircuitBreakerStats = field(default_factory=CircuitBreakerStats, init=False)

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        return self._stats

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state with logging."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats.current_state = new_state
            self._stats.state_changes += 1
            logger.info(
                f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
            )

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on current state."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time is not None:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._success_count = 0
                    return True
            return False

        # HALF_OPEN: allow limited requests to test recovery
        return True

    def can_execute(self) -> bool:
        """Check if a request can be executed (non-blocking check)."""
        return self._should_allow_request()

    def time_until_retry(self) -> float:
        """Seconds until circuit might allow requests again."""
        if self._state != CircuitState.OPEN:
            return 0.0

        if self._last_failure_time is None:
            return 0.0

        elapsed = time.monotonic() - self._last_failure_time
        remaining = self.recovery_timeout - elapsed
        return max(0.0, remaining)

    async def acquire(self) -> None:
        """Acquire permission to make a request. Raises CircuitOpenError if open."""
        async with self._lock:
            self._stats.total_requests += 1

            if not self._should_allow_request():
                self._stats.rejected_requests += 1
                retry_after = self.time_until_retry()
                raise CircuitOpenError(self.name, retry_after)

    def record_success(self) -> None:
        """Record a successful request."""
        self._stats.successful_requests += 1
        self._stats.last_success_time = time.monotonic()
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0
        self._failure_count = 0
        self._success_count += 1

        if self._state == CircuitState.HALF_OPEN:
            if self._success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                logger.info(f"Circuit '{self.name}' recovered after {self._success_count} successes")

    def record_failure(self, exception: Optional[Exception] = None) -> None:
        """Record a failed request."""
        # Check if this exception type should be excluded
        if exception and isinstance(exception, self.excluded_exceptions):
            logger.debug(f"Circuit '{self.name}' ignoring excluded exception: {type(exception).__name__}")
            return

        self._stats.failed_requests += 1
        self._stats.last_failure_time = time.monotonic()
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        self._success_count = 0

        if self._state == CircuitState.HALF_OPEN:
            # Single failure in half-open reopens the circuit
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"Circuit '{self.name}' reopened after failure in half-open state")

        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit '{self.name}' opened after {self._failure_count} failures"
                )

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._stats = CircuitBreakerStats()
        logger.info(f"Circuit '{self.name}' manually reset")

    async def __aenter__(self) -> "CircuitBreaker":
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure(exc_val)
        return False  # Don't suppress exceptions

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Use as decorator for async functions."""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async with self:
                return await func(*args, **kwargs)

        return wrapper


# =============================================================================
# Circuit Breaker Registry
# =============================================================================


class CircuitBreakerRegistry:
    """
    Central registry for managing multiple circuit breakers.

    Example:
        registry = get_circuit_registry()
        breaker = registry.get_or_create("openai", failure_threshold=5)
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        excluded_exceptions: tuple[type[Exception], ...] = (),
    ) -> CircuitBreaker:
        """Get existing breaker or create new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                excluded_exceptions=excluded_exceptions,
            )
            logger.debug(f"Created circuit breaker: {name}")
        return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get existing breaker or None."""
        return self._breakers.get(name)

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all breakers."""
        return {name: breaker.stats.to_dict() for name, breaker in self._breakers.items()}

    def get_open_circuits(self) -> list[str]:
        """Get names of all open circuits."""
        return [
            name
            for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# Global registry singleton
_registry: Optional[CircuitBreakerRegistry] = None
_registry_lock = asyncio.Lock()


def get_circuit_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _registry
    if _registry is None:
        _registry = CircuitBreakerRegistry()
    return _registry


# =============================================================================
# Convenience functions
# =============================================================================


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker from the global registry.

    Example:
        @circuit_breaker("openai")
        async def call_openai():
            ...
    """
    return get_circuit_registry().get_or_create(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitBreakerStats",
    "CircuitOpenError",
    "CircuitState",
    "circuit_breaker",
    "get_circuit_registry",
]
