"""
Exception hierarchy for Company Researcher.

This module defines a structured exception hierarchy for better error handling
and differentiation across the application.

Hierarchy:
    CompanyResearcherError (base)
    ├── AIError
    │   ├── AIProviderError
    │   ├── AIRateLimitError
    │   ├── AITimeoutError
    │   └── AIResponseError
    ├── NetworkError
    │   ├── ConnectionError
    │   ├── TimeoutError
    │   └── RateLimitError
    ├── ValidationError
    │   ├── ConfigValidationError
    │   └── InputValidationError
    ├── SearchError
    │   ├── SearchProviderError
    │   └── NoResultsError
    └── PipelineError
        ├── StageError
        └── OrchestratorError
"""

from typing import Optional, Any


# =============================================================================
# Base Exception
# =============================================================================


class CompanyResearcherError(Exception):
    """Base exception for all Company Researcher errors.

    All custom exceptions should inherit from this class to enable
    catching all application-specific errors with a single handler.

    Attributes:
        message: Human-readable error description
        details: Optional structured data about the error
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for structured logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# AI Exceptions
# =============================================================================


class AIError(CompanyResearcherError):
    """Base exception for AI-related errors."""

    def __init__(self, message: str, provider: Optional[str] = None, **kwargs):
        self.provider = provider
        details = {"provider": provider} if provider else {}
        details.update(kwargs)
        super().__init__(message, details)


class AIProviderError(AIError):
    """Error related to specific AI provider."""

    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}", provider, error_code=error_code)


class AIRateLimitError(AIError):
    """Rate limit exceeded for AI provider."""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        msg = f"[{provider}] Rate limit exceeded"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg, provider, retry_after=retry_after)


class AITimeoutError(AIError):
    """Request to AI provider timed out."""

    def __init__(self, provider: str, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"[{provider}] Request timed out after {timeout_seconds}s",
            provider,
            timeout_seconds=timeout_seconds,
        )


class AIResponseError(AIError):
    """Invalid or unexpected response from AI provider."""

    def __init__(self, provider: str, reason: str):
        self.reason = reason
        super().__init__(f"[{provider}] Invalid response: {reason}", provider, reason=reason)


class AIModelNotFoundError(AIError):
    """Requested AI model is not available."""

    def __init__(self, provider: str, model: str):
        self.model = model
        super().__init__(f"[{provider}] Model not found: {model}", provider, model=model)


# =============================================================================
# Network Exceptions
# =============================================================================


class NetworkError(CompanyResearcherError):
    """Base exception for network-related errors."""

    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        self.url = url
        details = {"url": url} if url else {}
        details.update(kwargs)
        super().__init__(message, details)


class ConnectionFailedError(NetworkError):
    """Failed to establish connection."""

    def __init__(self, url: str, reason: Optional[str] = None):
        self.reason = reason
        msg = f"Failed to connect to {url}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, url, reason=reason)


class NetworkTimeoutError(NetworkError):
    """Network request timed out."""

    def __init__(self, url: str, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Request to {url} timed out after {timeout_seconds}s",
            url,
            timeout_seconds=timeout_seconds,
        )


class HTTPError(NetworkError):
    """HTTP request returned error status code."""

    def __init__(self, url: str, status_code: int, reason: Optional[str] = None):
        self.status_code = status_code
        self.reason = reason
        msg = f"HTTP {status_code} from {url}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, url, status_code=status_code, reason=reason)


class RateLimitedError(NetworkError):
    """Request was rate limited."""

    def __init__(self, url: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        msg = f"Rate limited by {url}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg, url, retry_after=retry_after)


# =============================================================================
# Validation Exceptions
# =============================================================================


class ValidationError(CompanyResearcherError):
    """Base exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        self.field = field
        details = {"field": field} if field else {}
        details.update(kwargs)
        super().__init__(message, details)


class ConfigValidationError(ValidationError):
    """Configuration validation failed."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        self.config_key = config_key
        super().__init__(message, field=config_key, config_key=config_key)


class InputValidationError(ValidationError):
    """User input validation failed."""

    def __init__(self, message: str, field: str, value: Any = None):
        self.value = value
        super().__init__(message, field=field, invalid_value=repr(value) if value else None)


class SchemaValidationError(ValidationError):
    """Data does not match expected schema."""

    def __init__(self, message: str, schema_name: Optional[str] = None, errors: Optional[list] = None):
        self.schema_name = schema_name
        self.errors = errors or []
        super().__init__(message, schema_name=schema_name, validation_errors=errors)


# =============================================================================
# Search Exceptions
# =============================================================================


class SearchError(CompanyResearcherError):
    """Base exception for search-related errors."""

    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        self.query = query
        details = {"query": query} if query else {}
        details.update(kwargs)
        super().__init__(message, details)


class SearchProviderError(SearchError):
    """Error from a search provider."""

    def __init__(self, message: str, provider: str, query: Optional[str] = None):
        self.provider = provider
        super().__init__(f"[{provider}] {message}", query, provider=provider)


class NoResultsError(SearchError):
    """Search returned no results."""

    def __init__(self, query: str, providers_tried: Optional[list[str]] = None):
        self.providers_tried = providers_tried or []
        msg = f"No results found for query: {query}"
        if providers_tried:
            msg += f" (tried: {', '.join(providers_tried)})"
        super().__init__(msg, query, providers_tried=providers_tried)


class SearchQuotaExceededError(SearchError):
    """Search quota has been exceeded."""

    def __init__(self, provider: str, query: Optional[str] = None):
        self.provider = provider
        super().__init__(f"[{provider}] Search quota exceeded", query, provider=provider)


# =============================================================================
# Pipeline Exceptions
# =============================================================================


class PipelineError(CompanyResearcherError):
    """Base exception for pipeline/orchestration errors."""

    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        self.stage = stage
        details = {"stage": stage} if stage else {}
        details.update(kwargs)
        super().__init__(message, details)


class StageError(PipelineError):
    """Error during pipeline stage execution."""

    def __init__(self, stage: str, message: str, cause: Optional[Exception] = None):
        self.cause = cause
        details = {}
        if cause:
            details["cause_type"] = type(cause).__name__
            details["cause_message"] = str(cause)
        super().__init__(f"Stage '{stage}' failed: {message}", stage, **details)


class OrchestratorError(PipelineError):
    """Error in pipeline orchestration."""

    def __init__(self, message: str, failed_stages: Optional[list[str]] = None):
        self.failed_stages = failed_stages or []
        super().__init__(message, failed_stages=failed_stages)


class PipelineTimeoutError(PipelineError):
    """Pipeline execution timed out."""

    def __init__(self, timeout_seconds: int, stage: Optional[str] = None):
        self.timeout_seconds = timeout_seconds
        msg = f"Pipeline timed out after {timeout_seconds}s"
        if stage:
            msg += f" (at stage: {stage})"
        super().__init__(msg, stage, timeout_seconds=timeout_seconds)


class TimeoutBudgetExhaustedError(PipelineError):
    """Timeout budget has been exhausted."""

    def __init__(self, budget_seconds: float, consumed_seconds: float, stage: Optional[str] = None):
        self.budget_seconds = budget_seconds
        self.consumed_seconds = consumed_seconds
        msg = f"Timeout budget exhausted ({consumed_seconds:.1f}s/{budget_seconds:.1f}s)"
        if stage:
            msg += f" at stage: {stage}"
        super().__init__(msg, stage, budget_seconds=budget_seconds, consumed_seconds=consumed_seconds)


# =============================================================================
# Tool Exceptions
# =============================================================================


class ToolError(CompanyResearcherError):
    """Base exception for tool-related errors."""

    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        self.tool_name = tool_name
        details = {"tool_name": tool_name} if tool_name else {}
        details.update(kwargs)
        super().__init__(message, details)


class ToolNotFoundError(ToolError):
    """Requested tool is not available."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}", tool_name)


class ToolExecutionError(ToolError):
    """Error during tool execution."""

    def __init__(self, tool_name: str, message: str, cause: Optional[Exception] = None):
        self.cause = cause
        details = {}
        if cause:
            details["cause_type"] = type(cause).__name__
            details["cause_message"] = str(cause)
        super().__init__(f"[{tool_name}] {message}", tool_name, **details)


# =============================================================================
# Exception Handling Utilities
# =============================================================================


import functools
import logging
from contextlib import contextmanager
from typing import TypeVar, Callable, Type, Union, Tuple

T = TypeVar("T")
ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]

_logger = logging.getLogger(__name__)


@contextmanager
def handle_exceptions(
    *exception_types: Type[Exception],
    default: Any = None,
    reraise_as: Optional[Type[CompanyResearcherError]] = None,
    log_level: int = logging.WARNING,
    context: str = "",
):
    """
    Context manager for standardized exception handling.

    Usage:
        with handle_exceptions(NetworkError, AIError, default=None):
            result = await make_request()

        # Or with re-raising as different type:
        with handle_exceptions(Exception, reraise_as=ToolExecutionError):
            do_something()

    Args:
        *exception_types: Exception types to catch
        default: Default value to use if exception caught (only if not reraising)
        reraise_as: Re-raise caught exceptions as this type
        log_level: Logging level for caught exceptions
        context: Additional context for error messages
    """
    try:
        yield
    except exception_types as e:
        error_msg = f"{context}: {e}" if context else str(e)
        _logger.log(log_level, error_msg)

        if reraise_as:
            if isinstance(e, CompanyResearcherError):
                raise reraise_as(str(e), details=e.details) from e
            raise reraise_as(str(e)) from e

        # If not reraising and default provided, suppress exception
        # Note: This only works for expressions that can accept a default


def safe_execute(
    func: Callable[..., T],
    *args,
    default: T = None,
    exceptions: ExceptionTypes = Exception,
    log_errors: bool = True,
    context: str = "",
    **kwargs,
) -> T:
    """
    Execute a function with exception handling.

    Usage:
        result = safe_execute(risky_function, arg1, arg2, default="fallback")

    Args:
        func: Function to execute
        *args: Positional arguments to pass to function
        default: Default value if exception occurs
        exceptions: Exception types to catch
        log_errors: Whether to log caught exceptions
        context: Additional context for error messages
        **kwargs: Keyword arguments to pass to function

    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            error_msg = f"{context}: {e}" if context else str(e)
            _logger.warning(error_msg)
        return default


async def async_safe_execute(
    func: Callable[..., T],
    *args,
    default: T = None,
    exceptions: ExceptionTypes = Exception,
    log_errors: bool = True,
    context: str = "",
    **kwargs,
) -> T:
    """
    Execute an async function with exception handling.

    Usage:
        result = await async_safe_execute(risky_async_func, default="fallback")

    Args:
        func: Async function to execute
        *args: Positional arguments to pass to function
        default: Default value if exception occurs
        exceptions: Exception types to catch
        log_errors: Whether to log caught exceptions
        context: Additional context for error messages
        **kwargs: Keyword arguments to pass to function

    Returns:
        Function result or default value
    """
    try:
        return await func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            error_msg = f"{context}: {e}" if context else str(e)
            _logger.warning(error_msg)
        return default


def exception_handler(
    *exception_types: Type[Exception],
    default: Any = None,
    reraise_as: Optional[Type[CompanyResearcherError]] = None,
    log_level: int = logging.WARNING,
):
    """
    Decorator for standardized exception handling.

    Usage:
        @exception_handler(NetworkError, AIError, default=None)
        def my_function():
            ...

        @exception_handler(Exception, reraise_as=ToolExecutionError)
        async def my_async_function():
            ...

    Args:
        *exception_types: Exception types to catch
        default: Default value to return if exception caught
        reraise_as: Re-raise caught exceptions as this type
        log_level: Logging level for caught exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                _logger.log(log_level, f"{func.__name__}: {e}")
                if reraise_as:
                    raise reraise_as(str(e)) from e
                return default

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_types as e:
                _logger.log(log_level, f"{func.__name__}: {e}")
                if reraise_as:
                    raise reraise_as(str(e)) from e
                return default

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Base
    "CompanyResearcherError",
    # AI
    "AIError",
    "AIProviderError",
    "AIRateLimitError",
    "AITimeoutError",
    "AIResponseError",
    "AIModelNotFoundError",
    # Network
    "NetworkError",
    "ConnectionFailedError",
    "NetworkTimeoutError",
    "HTTPError",
    "RateLimitedError",
    # Validation
    "ValidationError",
    "ConfigValidationError",
    "InputValidationError",
    "SchemaValidationError",
    # Search
    "SearchError",
    "SearchProviderError",
    "NoResultsError",
    "SearchQuotaExceededError",
    # Pipeline
    "PipelineError",
    "StageError",
    "OrchestratorError",
    "PipelineTimeoutError",
    "TimeoutBudgetExhaustedError",
    # Tools
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    # Utilities
    "handle_exceptions",
    "safe_execute",
    "async_safe_execute",
    "exception_handler",
]
