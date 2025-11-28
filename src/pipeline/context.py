"""
RequestContext - The dependency carrier for pipeline execution.

This module eliminates global singletons by carrying all dependencies
through the pipeline via an explicit context object.

Benefits:
1. No more get_*() singleton calls
2. Easy testing - inject mocks via context
3. Request-scoped resources with automatic cleanup
4. Timeout budget tracking across stages
5. Cancellation support for long-running operations
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from ..core.config import Settings, get_settings
from ..core.logger import setup_logger

T = TypeVar("T")


# =============================================================================
# Protocols - Define contracts without importing implementations
# =============================================================================


@runtime_checkable
class AIClientProtocol(Protocol):
    """Protocol for AI client - allows any implementation."""

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str: ...

    async def generate_safe(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> Any: ...  # Result[str, AIError]

    def get_provider_name(self) -> str: ...


@runtime_checkable
class SearchToolProtocol(Protocol):
    """Protocol for search tool."""

    async def search(
        self, query: str, max_results: int = 5
    ) -> list[Dict[str, Any]]: ...

    async def search_safe(
        self, query: str, max_results: int = 5
    ) -> Any: ...  # Result[List[Dict], SearchError]


@runtime_checkable
class BrowserToolProtocol(Protocol):
    """Protocol for browser tool."""

    async def fetch_url(self, url: str) -> Any: ...
    async def fetch_multiple(self, urls: list[str]) -> list[Any]: ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache."""

    def get(
        self, prompt: str, system: str | None, temperature: float, max_tokens: int
    ) -> Optional[str]: ...

    def set(
        self,
        prompt: str,
        response: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ) -> None: ...


# =============================================================================
# TimeoutBudget - Track remaining time across stages
# =============================================================================


@dataclass
class TimeoutBudget:
    """
    Tracks remaining time budget for a request.

    As each stage executes, it consumes time from the budget.
    Stages can check remaining time and fail fast if exhausted.

    Example:
        budget = TimeoutBudget(total_seconds=300)

        # In stage:
        if not budget.has_time_remaining():
            return Err(StageError.timeout_exhausted())

        # Get remaining for sub-operation
        await some_operation(timeout=budget.remaining())
    """

    total_seconds: float
    start_time: float = field(default_factory=time.monotonic)

    def elapsed(self) -> float:
        """Seconds elapsed since budget started."""
        return time.monotonic() - self.start_time

    def remaining(self) -> float:
        """Seconds remaining in budget."""
        return max(0.0, self.total_seconds - self.elapsed())

    def has_time_remaining(self, min_required: float = 1.0) -> bool:
        """Check if at least min_required seconds remain."""
        return self.remaining() >= min_required

    def is_exhausted(self) -> bool:
        """Check if budget is fully consumed."""
        return self.remaining() <= 0

    def consume(self, seconds: float) -> "TimeoutBudget":
        """Create a sub-budget with reduced time."""
        return TimeoutBudget(
            total_seconds=min(seconds, self.remaining()),
            start_time=time.monotonic(),
        )

    def __repr__(self) -> str:
        return f"TimeoutBudget(remaining={self.remaining():.1f}s of {self.total_seconds}s)"


# =============================================================================
# CancellationToken - Cooperative cancellation
# =============================================================================


@dataclass
class CancellationToken:
    """
    Cooperative cancellation token for long-running operations.

    Stages should check this periodically and exit gracefully if cancelled.

    Example:
        # In stage:
        for item in items:
            if ctx.cancellation.is_cancelled:
                return Err(StageError.cancelled("User cancelled"))
            await process(item)

        # From outside:
        token.cancel("User requested cancellation")
    """

    _cancelled: bool = field(default=False, repr=False)
    _reason: Optional[str] = field(default=None, repr=False)
    _callbacks: list[Callable[[], None]] = field(default_factory=list, repr=False)

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    @property
    def reason(self) -> Optional[str]:
        """Get the cancellation reason if cancelled."""
        return self._reason

    def cancel(self, reason: str = "Cancelled") -> None:
        """Request cancellation."""
        if not self._cancelled:
            self._cancelled = True
            self._reason = reason
            for callback in self._callbacks:
                try:
                    callback()
                except Exception:
                    pass  # Don't let callback errors prevent cancellation

    def on_cancel(self, callback: Callable[[], None]) -> None:
        """Register a callback to run when cancelled."""
        if self._cancelled:
            callback()  # Already cancelled, run immediately
        else:
            self._callbacks.append(callback)

    def raise_if_cancelled(self) -> None:
        """Raise asyncio.CancelledError if cancelled."""
        if self._cancelled:
            raise asyncio.CancelledError(self._reason)


# =============================================================================
# BoundLogger - Logger with pre-bound context
# =============================================================================


class BoundLogger:
    """
    Logger with pre-bound context fields.

    All log messages automatically include request_id and stage name.

    Example:
        logger = BoundLogger(request_id="req-123", stage="search")
        logger.info("Found results", count=42)
        # Output: [req-123] [search] Found results count=42
    """

    def __init__(
        self,
        request_id: str,
        stage: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self._logger = setup_logger("pipeline")
        self._request_id = request_id
        self._stage = stage
        self._extra = extra or {}

    def _format(self, message: str, **kwargs: Any) -> str:
        """Format message with context."""
        prefix = f"[{self._request_id}]"
        if self._stage:
            prefix += f" [{self._stage}]"

        extras = {**self._extra, **kwargs}
        if extras:
            extra_str = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{prefix} {message} {extra_str}"
        return f"{prefix} {message}"

    def with_stage(self, stage: str) -> "BoundLogger":
        """Create new logger bound to a stage."""
        return BoundLogger(self._request_id, stage, self._extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(self._format(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(self._format(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(self._format(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(self._format(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.exception(self._format(message, **kwargs))


# =============================================================================
# RequestContext - The main context object
# =============================================================================


@dataclass
class RequestContext:
    """
    Carries all dependencies through the pipeline.

    This replaces all global singletons. Every stage receives this context
    and uses it to access services. No more get_*() calls anywhere.

    Attributes:
        request_id: Unique identifier for this request (for tracing)
        ai_client: AI client for LLM operations
        search_tool: Search tool for web searches
        browser_tool: Browser tool for fetching URLs
        cache: Cache for AI responses
        timeout_budget: Remaining time for the request
        cancellation: Token for cooperative cancellation
        settings: Application settings
        logger: Pre-bound logger with request context
        metadata: Additional request metadata

    Example:
        ctx = create_context(request_id="req-123")

        # In a stage:
        result = await ctx.ai_client.generate_safe(prompt)
        ctx.logger.info("Generated response", tokens=len(result))

        # Check cancellation:
        if ctx.cancellation.is_cancelled:
            return Err(StageError.cancelled())

        # Check timeout:
        if not ctx.timeout_budget.has_time_remaining():
            return Err(StageError.timeout())
    """

    # Identity
    request_id: str

    # Services (injected, not imported)
    ai_client: AIClientProtocol
    search_tool: SearchToolProtocol
    browser_tool: BrowserToolProtocol
    cache: CacheProtocol

    # Control flow
    timeout_budget: TimeoutBudget
    cancellation: CancellationToken

    # Configuration
    settings: Settings

    # Observability
    logger: BoundLogger

    # Extensibility
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_stage(self, stage_name: str) -> "RequestContext":
        """
        Create a new context bound to a specific stage.

        The new context shares all services but has a stage-specific logger.
        """
        return RequestContext(
            request_id=self.request_id,
            ai_client=self.ai_client,
            search_tool=self.search_tool,
            browser_tool=self.browser_tool,
            cache=self.cache,
            timeout_budget=self.timeout_budget,
            cancellation=self.cancellation,
            settings=self.settings,
            logger=self.logger.with_stage(stage_name),
            metadata=self.metadata,
        )

    def check_can_continue(self) -> Optional[str]:
        """
        Check if execution can continue.

        Returns None if OK, or an error reason if should stop.
        """
        if self.cancellation.is_cancelled:
            return f"Cancelled: {self.cancellation.reason}"
        if self.timeout_budget.is_exhausted():
            return "Timeout budget exhausted"
        return None


# =============================================================================
# Context Factory
# =============================================================================


def create_context(
    request_id: Optional[str] = None,
    timeout_seconds: float = 300.0,
    ai_client: Optional[AIClientProtocol] = None,
    search_tool: Optional[SearchToolProtocol] = None,
    browser_tool: Optional[BrowserToolProtocol] = None,
    cache: Optional[CacheProtocol] = None,
    settings: Optional[Settings] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> RequestContext:
    """
    Create a RequestContext with default or provided services.

    This is the main entry point for creating contexts. It resolves
    services from the DI container if not explicitly provided.

    Args:
        request_id: Unique request ID (generated if not provided)
        timeout_seconds: Total timeout budget for the request
        ai_client: AI client (resolved from container if not provided)
        search_tool: Search tool (resolved from container if not provided)
        browser_tool: Browser tool (resolved from container if not provided)
        cache: Cache (resolved from container if not provided)
        settings: Settings (resolved from container if not provided)
        metadata: Additional metadata to attach

    Returns:
        Fully initialized RequestContext

    Example:
        # Production - uses real services from container
        ctx = create_context(request_id="req-123")

        # Testing - inject mocks
        ctx = create_context(
            ai_client=mock_ai,
            search_tool=mock_search,
        )
    """
    # Generate request ID if not provided
    if request_id is None:
        request_id = f"req-{uuid.uuid4().hex[:12]}"

    # Resolve services from container if not provided
    # Import here to avoid circular imports
    from ..core.container import get_container
    from ..core.ai_client import AIClientManager
    from ..core.cache import AICache
    from ..tools.search import SearchTool
    from ..tools.browser import BrowserTool

    container = get_container()

    resolved_ai = ai_client or container.resolve(AIClientManager)
    resolved_search = search_tool or container.resolve(SearchTool)
    resolved_browser = browser_tool or container.resolve(BrowserTool)
    resolved_cache = cache or container.resolve(AICache)
    resolved_settings = settings or get_settings()

    return RequestContext(
        request_id=request_id,
        ai_client=resolved_ai,
        search_tool=resolved_search,
        browser_tool=resolved_browser,
        cache=resolved_cache,
        timeout_budget=TimeoutBudget(total_seconds=timeout_seconds),
        cancellation=CancellationToken(),
        settings=resolved_settings,
        logger=BoundLogger(request_id),
        metadata=metadata or {},
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Protocols
    "AIClientProtocol",
    "SearchToolProtocol",
    "BrowserToolProtocol",
    "CacheProtocol",
    # Control flow
    "TimeoutBudget",
    "CancellationToken",
    # Logging
    "BoundLogger",
    # Context
    "RequestContext",
    "create_context",
]
