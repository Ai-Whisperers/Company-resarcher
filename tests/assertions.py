"""
Custom assertion helpers for consistent test validation.

This module provides reusable assertion functions for common test scenarios,
ensuring consistent error messages and validation patterns across the test suite.
"""

from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
import re
import pytest


# =============================================================================
# Response Assertions
# =============================================================================


def assert_valid_response(
    response: Any,
    expected_status: int = 200,
    expected_content_type: Optional[str] = None,
) -> None:
    """
    Assert that an HTTP response is valid with expected status.

    Args:
        response: The HTTP response object
        expected_status: Expected HTTP status code
        expected_content_type: Expected content type (optional)

    Raises:
        AssertionError: If response doesn't meet expectations
    """
    assert response is not None, "Response is None"
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {getattr(response, 'text', str(response)[:200])}"
    )
    if expected_content_type:
        content_type = response.headers.get("content-type", "")
        assert expected_content_type in content_type, (
            f"Expected content-type '{expected_content_type}', "
            f"got '{content_type}'"
        )


def assert_json_response(
    response: Any,
    required_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Assert response is valid JSON and optionally contains required fields.

    Args:
        response: The HTTP response object
        required_fields: List of fields that must be present

    Returns:
        The parsed JSON data

    Raises:
        AssertionError: If response is not valid JSON or missing fields
    """
    assert response is not None, "Response is None"

    try:
        data = response.json()
    except Exception as e:
        pytest.fail(f"Response is not valid JSON: {e}")

    if required_fields:
        for field in required_fields:
            assert field in data, f"Missing required field: '{field}'"

    return data


def assert_error_response(
    response: Any,
    expected_status: int = 400,
    expected_error_type: Optional[str] = None,
) -> None:
    """
    Assert response is an error response with expected characteristics.

    Args:
        response: The HTTP response object
        expected_status: Expected HTTP status code
        expected_error_type: Expected error type in response body
    """
    assert response is not None, "Response is None"
    assert response.status_code == expected_status, (
        f"Expected error status {expected_status}, got {response.status_code}"
    )

    if expected_error_type:
        data = response.json()
        error = data.get("error") or data.get("detail") or data.get("message")
        assert error is not None, "Error response missing error message"


# =============================================================================
# Data Structure Assertions
# =============================================================================


def assert_valid_company_profile(profile: Dict[str, Any]) -> None:
    """
    Assert that a company profile has required structure and valid data.

    Args:
        profile: Company profile dictionary
    """
    assert isinstance(profile, dict), f"Profile must be dict, got {type(profile)}"

    required_fields = ["name", "website"]
    for field in required_fields:
        assert field in profile, f"Company profile missing required field: '{field}'"
        assert profile[field], f"Company profile field '{field}' is empty"

    # Validate website format if present
    if profile.get("website"):
        assert profile["website"].startswith(("http://", "https://")), (
            f"Invalid website URL format: {profile['website']}"
        )


def assert_valid_research_state(state: Dict[str, Any]) -> None:
    """
    Assert that a research state has required structure.

    Args:
        state: Research state dictionary
    """
    assert isinstance(state, dict), f"State must be dict, got {type(state)}"

    required_fields = ["company_name"]
    for field in required_fields:
        assert field in state, f"Research state missing required field: '{field}'"

    # Validate errors list
    if "errors" in state:
        assert isinstance(state["errors"], list), "errors must be a list"


def assert_valid_financial_data(data: Dict[str, Any]) -> None:
    """
    Assert that financial data has required structure and valid values.

    Args:
        data: Financial data dictionary
    """
    assert isinstance(data, dict), f"Data must be dict, got {type(data)}"

    if "market_cap" in data:
        assert isinstance(data["market_cap"], (int, float)), (
            "market_cap must be numeric"
        )
        assert data["market_cap"] >= 0, "market_cap cannot be negative"

    if "profit_margin" in data:
        assert isinstance(data["profit_margin"], (int, float)), (
            "profit_margin must be numeric"
        )
        assert -1 <= data["profit_margin"] <= 1, (
            "profit_margin must be between -1 and 1"
        )


def assert_valid_search_results(results: List[Dict[str, Any]]) -> None:
    """
    Assert that search results have required structure.

    Args:
        results: List of search result dictionaries
    """
    assert isinstance(results, list), f"Results must be list, got {type(results)}"

    for i, result in enumerate(results):
        assert isinstance(result, dict), f"Result {i} must be dict"
        assert "url" in result or "link" in result, f"Result {i} missing URL"
        assert "title" in result or "name" in result, f"Result {i} missing title"


# =============================================================================
# Exception Assertions
# =============================================================================


def assert_raises_with_message(
    exception_type: Type[Exception],
    message_pattern: str,
    callable_obj: Any,
    *args,
    **kwargs,
) -> Exception:
    """
    Assert that calling a function raises an exception with matching message.

    Args:
        exception_type: Expected exception type
        message_pattern: Regex pattern to match in exception message
        callable_obj: Function to call
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        The raised exception

    Raises:
        AssertionError: If exception not raised or message doesn't match
    """
    with pytest.raises(exception_type, match=message_pattern) as exc_info:
        callable_obj(*args, **kwargs)
    return exc_info.value


async def assert_raises_async(
    exception_type: Type[Exception],
    coro,
    message_pattern: Optional[str] = None,
) -> Exception:
    """
    Assert that an async function raises an exception.

    Args:
        exception_type: Expected exception type
        coro: Coroutine to await
        message_pattern: Optional regex pattern to match

    Returns:
        The raised exception
    """
    with pytest.raises(exception_type, match=message_pattern) as exc_info:
        await coro
    return exc_info.value


# =============================================================================
# Collection Assertions
# =============================================================================


def assert_contains_all(
    collection: Union[List, Dict, set],
    required_items: List[Any],
) -> None:
    """
    Assert that a collection contains all required items.

    Args:
        collection: Collection to check
        required_items: Items that must be present
    """
    for item in required_items:
        assert item in collection, (
            f"Collection missing required item: {item}. "
            f"Collection contains: {list(collection)[:10]}..."
        )


def assert_contains_none(
    collection: Union[List, Dict, set],
    forbidden_items: List[Any],
) -> None:
    """
    Assert that a collection contains none of the forbidden items.

    Args:
        collection: Collection to check
        forbidden_items: Items that must not be present
    """
    for item in forbidden_items:
        assert item not in collection, (
            f"Collection contains forbidden item: {item}"
        )


def assert_list_length(
    collection: List,
    expected_length: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> None:
    """
    Assert that a list has expected length or within bounds.

    Args:
        collection: List to check
        expected_length: Exact expected length
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    """
    actual = len(collection)

    if expected_length is not None:
        assert actual == expected_length, (
            f"Expected length {expected_length}, got {actual}"
        )

    if min_length is not None:
        assert actual >= min_length, (
            f"Length {actual} is less than minimum {min_length}"
        )

    if max_length is not None:
        assert actual <= max_length, (
            f"Length {actual} exceeds maximum {max_length}"
        )


# =============================================================================
# Numeric Assertions
# =============================================================================


def assert_approximately_equal(
    actual: float,
    expected: float,
    tolerance: float = 1e-6,
) -> None:
    """
    Assert that two floats are approximately equal.

    Args:
        actual: Actual value
        expected: Expected value
        tolerance: Relative tolerance
    """
    assert actual == pytest.approx(expected, rel=tolerance), (
        f"Expected {expected} (within {tolerance}), got {actual}"
    )


def assert_in_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> None:
    """
    Assert that a value is within a range.

    Args:
        value: Value to check
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
    """
    if min_value is not None:
        assert value >= min_value, (
            f"Value {value} is less than minimum {min_value}"
        )

    if max_value is not None:
        assert value <= max_value, (
            f"Value {value} exceeds maximum {max_value}"
        )


def assert_positive(value: Union[int, float], allow_zero: bool = False) -> None:
    """
    Assert that a value is positive.

    Args:
        value: Value to check
        allow_zero: Whether zero is allowed
    """
    if allow_zero:
        assert value >= 0, f"Expected non-negative value, got {value}"
    else:
        assert value > 0, f"Expected positive value, got {value}"


# =============================================================================
# String Assertions
# =============================================================================


def assert_non_empty_string(value: Any) -> None:
    """
    Assert that a value is a non-empty string.

    Args:
        value: Value to check
    """
    assert isinstance(value, str), f"Expected string, got {type(value)}"
    assert len(value.strip()) > 0, "String is empty or whitespace only"


def assert_matches_pattern(value: str, pattern: str) -> None:
    """
    Assert that a string matches a regex pattern.

    Args:
        value: String to check
        pattern: Regex pattern to match
    """
    assert re.match(pattern, value), (
        f"String '{value}' doesn't match pattern '{pattern}'"
    )


def assert_valid_url(url: str) -> None:
    """
    Assert that a string is a valid URL.

    Args:
        url: URL string to validate
    """
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    assert re.match(url_pattern, url), f"Invalid URL format: {url}"


def assert_valid_email(email: str) -> None:
    """
    Assert that a string is a valid email address.

    Args:
        email: Email string to validate
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert re.match(email_pattern, email), f"Invalid email format: {email}"


# =============================================================================
# Temporal Assertions
# =============================================================================


def assert_recent_timestamp(
    timestamp: Union[datetime, str],
    max_age_seconds: float = 60,
) -> None:
    """
    Assert that a timestamp is recent (within max_age_seconds of now).

    Args:
        timestamp: Timestamp to check
        max_age_seconds: Maximum allowed age in seconds
    """
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    age = (now - timestamp).total_seconds()

    assert age <= max_age_seconds, (
        f"Timestamp is {age}s old, exceeds maximum {max_age_seconds}s"
    )


def assert_timestamp_order(
    earlier: Union[datetime, str],
    later: Union[datetime, str],
) -> None:
    """
    Assert that one timestamp is before another.

    Args:
        earlier: Timestamp that should be earlier
        later: Timestamp that should be later
    """
    if isinstance(earlier, str):
        earlier = datetime.fromisoformat(earlier.replace("Z", "+00:00"))
    if isinstance(later, str):
        later = datetime.fromisoformat(later.replace("Z", "+00:00"))

    assert earlier <= later, (
        f"Expected {earlier} to be before {later}"
    )


# =============================================================================
# AI/ML Assertions
# =============================================================================


def assert_valid_ai_response(response: Dict[str, Any]) -> None:
    """
    Assert that an AI response has valid structure.

    Args:
        response: AI response dictionary
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"

    # Should have content or error
    has_content = "content" in response or "text" in response or "message" in response
    has_error = "error" in response

    assert has_content or has_error, (
        "AI response must have content or error field"
    )

    # If has usage, validate structure
    if "usage" in response:
        usage = response["usage"]
        assert isinstance(usage, dict), "usage must be dict"


def assert_valid_embedding(
    embedding: List[float],
    expected_dimensions: Optional[int] = None,
) -> None:
    """
    Assert that an embedding vector is valid.

    Args:
        embedding: Embedding vector
        expected_dimensions: Expected number of dimensions
    """
    assert isinstance(embedding, list), f"Embedding must be list, got {type(embedding)}"
    assert len(embedding) > 0, "Embedding is empty"
    assert all(isinstance(x, (int, float)) for x in embedding), (
        "All embedding values must be numeric"
    )

    if expected_dimensions:
        assert len(embedding) == expected_dimensions, (
            f"Expected {expected_dimensions} dimensions, got {len(embedding)}"
        )


def assert_probability_distribution(
    distribution: Dict[str, float],
    tolerance: float = 0.01,
) -> None:
    """
    Assert that values form a valid probability distribution.

    Args:
        distribution: Dictionary of probabilities
        tolerance: Tolerance for sum to equal 1.0
    """
    assert isinstance(distribution, dict), "Distribution must be dict"
    assert len(distribution) > 0, "Distribution is empty"

    values = list(distribution.values())
    assert all(0 <= v <= 1 for v in values), (
        "All probabilities must be between 0 and 1"
    )

    total = sum(values)
    assert abs(total - 1.0) <= tolerance, (
        f"Probabilities sum to {total}, expected 1.0 (tolerance: {tolerance})"
    )
