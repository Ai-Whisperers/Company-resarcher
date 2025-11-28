"""
Result type for explicit error handling.

This module provides a Result[T, E] type that makes success/failure states
explicit in function signatures, eliminating the need for try/except blocks
and making error handling more predictable.

Benefits:
1. Compile-time visibility of error states
2. Forces explicit handling of both success and error cases
3. Composable with map(), flat_map(), etc.
4. No hidden exceptions - errors are values

Usage:
    # Returning results
    def divide(a: int, b: int) -> Result[float, str]:
        if b == 0:
            return Err("Division by zero")
        return Ok(a / b)

    # Handling results
    result = divide(10, 2)
    if result.is_ok():
        print(f"Result: {result.unwrap()}")
    else:
        print(f"Error: {result.error}")

    # Chaining operations
    result = (
        divide(10, 2)
        .map(lambda x: x * 2)
        .map(lambda x: f"Answer: {x}")
    )

    # With default values
    value = divide(10, 0).unwrap_or(0.0)
"""

from __future__ import annotations
from typing import TypeVar, Generic, Callable, Union, Optional, Any, overload
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Type variables for Result
T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Mapped success type
F = TypeVar("F")  # Mapped error type


class ResultError(Exception):
    """Exception raised when unwrapping a failed Result."""

    def __init__(self, error: Any):
        self.error = error
        super().__init__(f"Called unwrap() on an Err value: {error}")


class Result(Generic[T, E], ABC):
    """
    A Result type representing either success (Ok) or failure (Err).

    This is an abstract base class - use Ok() or Err() to create instances.
    """

    @property
    @abstractmethod
    def is_ok(self) -> bool:
        """Returns True if this is an Ok result."""
        ...

    @property
    @abstractmethod
    def is_err(self) -> bool:
        """Returns True if this is an Err result."""
        ...

    @abstractmethod
    def unwrap(self) -> T:
        """
        Returns the success value.

        Raises:
            ResultError: If this is an Err result.
        """
        ...

    @abstractmethod
    def unwrap_err(self) -> E:
        """
        Returns the error value.

        Raises:
            ResultError: If this is an Ok result.
        """
        ...

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the success value or a default if Err."""
        ...

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        """Returns the success value or computes it from the error."""
        ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        """
        Transforms the success value using the given function.

        If this is Err, returns Err unchanged.
        """
        ...

    @abstractmethod
    def map_err(self, f: Callable[[E], F]) -> Result[T, F]:
        """
        Transforms the error value using the given function.

        If this is Ok, returns Ok unchanged.
        """
        ...

    @abstractmethod
    def flat_map(self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """
        Chains Result-returning operations.

        Also known as `and_then` or `bind`.
        """
        ...

    @abstractmethod
    def or_else(self, f: Callable[[E], Result[T, F]]) -> Result[T, F]:
        """
        Handles the error case with a Result-returning function.

        If Ok, returns Ok unchanged.
        """
        ...

    @abstractmethod
    def ok(self) -> Optional[T]:
        """Returns the success value as Optional, or None if Err."""
        ...

    @abstractmethod
    def err(self) -> Optional[E]:
        """Returns the error value as Optional, or None if Ok."""
        ...

    @abstractmethod
    def expect(self, message: str) -> T:
        """
        Returns the success value, or raises with a custom message.

        Raises:
            ResultError: With the custom message if this is Err.
        """
        ...

    @abstractmethod
    def expect_err(self, message: str) -> E:
        """
        Returns the error value, or raises with a custom message.

        Raises:
            ResultError: With the custom message if this is Ok.
        """
        ...

    def __bool__(self) -> bool:
        """Returns True if Ok, False if Err."""
        return self.is_ok


@dataclass(frozen=True)
class Ok(Result[T, E]):
    """
    Represents a successful Result containing a value.

    Usage:
        result: Result[int, str] = Ok(42)
    """

    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_err(self) -> E:
        raise ResultError(f"Called unwrap_err() on an Ok value: {self.value}")

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return self.value

    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        return Ok(f(self.value))

    def map_err(self, f: Callable[[E], F]) -> Result[T, F]:
        return Ok(self.value)

    def flat_map(self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return f(self.value)

    def or_else(self, f: Callable[[E], Result[T, F]]) -> Result[T, F]:
        return Ok(self.value)

    def ok(self) -> Optional[T]:
        return self.value

    def err(self) -> Optional[E]:
        return None

    def expect(self, message: str) -> T:
        return self.value

    def expect_err(self, message: str) -> E:
        raise ResultError(message)

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


@dataclass(frozen=True)
class Err(Result[T, E]):
    """
    Represents a failed Result containing an error.

    Usage:
        result: Result[int, str] = Err("Something went wrong")
    """

    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ResultError(self.error)

    def unwrap_err(self) -> E:
        return self.error

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self.error)

    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        return Err(self.error)

    def map_err(self, f: Callable[[E], F]) -> Result[T, F]:
        return Err(f(self.error))

    def flat_map(self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return Err(self.error)

    def or_else(self, f: Callable[[E], Result[T, F]]) -> Result[T, F]:
        return f(self.error)

    def ok(self) -> Optional[T]:
        return None

    def err(self) -> Optional[E]:
        return self.error

    def expect(self, message: str) -> T:
        raise ResultError(f"{message}: {self.error}")

    def expect_err(self, message: str) -> E:
        return self.error

    def __repr__(self) -> str:
        return f"Err({self.error!r})"


# =============================================================================
# Error Types for Domain-Specific Errors
# =============================================================================


@dataclass(frozen=True)
class AIError:
    """Error from AI operations (LLM calls, parsing, etc.)."""

    code: str
    message: str
    details: Optional[dict] = None
    recoverable: bool = True

    # Common error codes
    TIMEOUT = "AI_TIMEOUT"
    RATE_LIMITED = "AI_RATE_LIMITED"
    INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    PARSE_ERROR = "AI_PARSE_ERROR"
    CONNECTION_ERROR = "AI_CONNECTION_ERROR"
    AUTHENTICATION_ERROR = "AI_AUTHENTICATION_ERROR"
    MODEL_ERROR = "AI_MODEL_ERROR"

    @classmethod
    def timeout(cls, message: str = "AI request timed out") -> "AIError":
        return cls(code=cls.TIMEOUT, message=message, recoverable=True)

    @classmethod
    def rate_limited(cls, message: str = "Rate limit exceeded") -> "AIError":
        return cls(code=cls.RATE_LIMITED, message=message, recoverable=True)

    @classmethod
    def invalid_response(cls, message: str, details: Optional[dict] = None) -> "AIError":
        return cls(code=cls.INVALID_RESPONSE, message=message, details=details, recoverable=False)

    @classmethod
    def parse_error(cls, message: str, raw_output: Optional[str] = None) -> "AIError":
        return cls(
            code=cls.PARSE_ERROR,
            message=message,
            details={"raw_output": raw_output} if raw_output else None,
            recoverable=False,
        )

    @classmethod
    def connection_error(cls, message: str) -> "AIError":
        return cls(code=cls.CONNECTION_ERROR, message=message, recoverable=True)

    @classmethod
    def auth_error(cls, message: str = "Authentication failed") -> "AIError":
        return cls(code=cls.AUTHENTICATION_ERROR, message=message, recoverable=False)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True)
class SearchError:
    """Error from search operations."""

    code: str
    message: str
    query: Optional[str] = None
    recoverable: bool = True

    # Common error codes
    TIMEOUT = "SEARCH_TIMEOUT"
    NO_RESULTS = "SEARCH_NO_RESULTS"
    INVALID_QUERY = "SEARCH_INVALID_QUERY"
    API_ERROR = "SEARCH_API_ERROR"
    RATE_LIMITED = "SEARCH_RATE_LIMITED"

    @classmethod
    def timeout(cls, query: str) -> "SearchError":
        return cls(code=cls.TIMEOUT, message=f"Search timed out", query=query, recoverable=True)

    @classmethod
    def no_results(cls, query: str) -> "SearchError":
        return cls(code=cls.NO_RESULTS, message=f"No results found", query=query, recoverable=False)

    @classmethod
    def invalid_query(cls, query: str, reason: str = "") -> "SearchError":
        msg = f"Invalid query" + (f": {reason}" if reason else "")
        return cls(code=cls.INVALID_QUERY, message=msg, query=query, recoverable=False)

    @classmethod
    def api_error(cls, query: str, message: str) -> "SearchError":
        return cls(code=cls.API_ERROR, message=message, query=query, recoverable=True)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}" + (f" (query: {self.query})" if self.query else "")


@dataclass(frozen=True)
class ValidationError:
    """Error from validation operations."""

    code: str
    message: str
    field: Optional[str] = None
    value: Any = None

    # Common error codes
    REQUIRED_FIELD = "VALIDATION_REQUIRED"
    INVALID_FORMAT = "VALIDATION_FORMAT"
    OUT_OF_RANGE = "VALIDATION_RANGE"
    TYPE_MISMATCH = "VALIDATION_TYPE"

    @classmethod
    def required(cls, field: str) -> "ValidationError":
        return cls(code=cls.REQUIRED_FIELD, message=f"Required field missing", field=field)

    @classmethod
    def invalid_format(cls, field: str, expected: str, value: Any = None) -> "ValidationError":
        return cls(
            code=cls.INVALID_FORMAT,
            message=f"Invalid format, expected {expected}",
            field=field,
            value=value,
        )

    @classmethod
    def out_of_range(cls, field: str, min_val: Any = None, max_val: Any = None, value: Any = None) -> "ValidationError":
        bounds = []
        if min_val is not None:
            bounds.append(f"min={min_val}")
        if max_val is not None:
            bounds.append(f"max={max_val}")
        return cls(
            code=cls.OUT_OF_RANGE,
            message=f"Value out of range ({', '.join(bounds)})",
            field=field,
            value=value,
        )

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.field:
            base += f" (field: {self.field})"
        return base


# =============================================================================
# Utility Functions
# =============================================================================


def try_result(f: Callable[[], T], error_handler: Callable[[Exception], E]) -> Result[T, E]:
    """
    Wraps a function call in a Result, catching exceptions.

    Args:
        f: Function to call
        error_handler: Function to convert exceptions to error type

    Returns:
        Ok(value) on success, Err(error) on exception

    Example:
        result = try_result(
            lambda: json.loads(data),
            lambda e: AIError.parse_error(str(e))
        )
    """
    try:
        return Ok(f())
    except Exception as e:
        return Err(error_handler(e))


async def try_result_async(
    f: Callable[[], Any],  # Returns Awaitable[T]
    error_handler: Callable[[Exception], E],
) -> Result[T, E]:
    """
    Async version of try_result.

    Args:
        f: Async function to call
        error_handler: Function to convert exceptions to error type

    Returns:
        Ok(value) on success, Err(error) on exception
    """
    try:
        return Ok(await f())
    except Exception as e:
        return Err(error_handler(e))


def collect_results(results: list[Result[T, E]]) -> Result[list[T], list[E]]:
    """
    Collects a list of Results into a Result of lists.

    If all results are Ok, returns Ok with all values.
    If any results are Err, returns Err with all errors.

    Args:
        results: List of Results to collect

    Returns:
        Ok([values]) if all Ok, Err([errors]) if any Err
    """
    values: list[T] = []
    errors: list[E] = []

    for result in results:
        if result.is_ok:
            values.append(result.unwrap())
        else:
            errors.append(result.unwrap_err())

    if errors:
        return Err(errors)
    return Ok(values)


def first_ok(results: list[Result[T, E]]) -> Result[T, list[E]]:
    """
    Returns the first Ok result, or Err with all errors if none succeed.

    Useful for fallback chains.

    Args:
        results: List of Results to check

    Returns:
        First Ok result, or Err with all accumulated errors
    """
    errors: list[E] = []

    for result in results:
        if result.is_ok:
            return Ok(result.unwrap())
        errors.append(result.unwrap_err())

    return Err(errors)


# =============================================================================
# Type Aliases for Common Result Types
# =============================================================================

# AI operation results
AIResult = Result[T, AIError]

# Search operation results
SearchResult = Result[T, SearchError]

# Validation results
ValidResult = Result[T, ValidationError]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core types
    "Result",
    "Ok",
    "Err",
    "ResultError",
    # Error types
    "AIError",
    "SearchError",
    "ValidationError",
    # Utilities
    "try_result",
    "try_result_async",
    "collect_results",
    "first_ok",
    # Type aliases
    "AIResult",
]
