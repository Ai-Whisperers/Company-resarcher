"""Tests for Result type and error handling utilities."""

import pytest
from src.core.result import (
    Result,
    Ok,
    Err,
    ResultError,
    AIError,
    SearchError,
    ValidationError,
    try_result,
    try_result_async,
    collect_results,
    first_ok,
)


class TestOk:
    """Tests for the Ok variant."""

    def test_is_ok_returns_true(self):
        result: Result[int, str] = Ok(42)
        assert result.is_ok is True
        assert result.is_err is False

    def test_unwrap_returns_value(self):
        result = Ok("hello")
        assert result.unwrap() == "hello"

    def test_unwrap_err_raises(self):
        result = Ok(42)
        with pytest.raises(ResultError):
            result.unwrap_err()

    def test_unwrap_or_returns_value(self):
        result = Ok(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_else_returns_value(self):
        result = Ok(42)
        assert result.unwrap_or_else(lambda e: 0) == 42

    def test_map_transforms_value(self):
        result = Ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 10

    def test_map_err_returns_ok_unchanged(self):
        result: Result[int, str] = Ok(5)
        mapped = result.map_err(lambda e: f"Error: {e}")
        assert mapped.unwrap() == 5

    def test_flat_map_chains_operations(self):
        def double_if_positive(x: int) -> Result[int, str]:
            if x > 0:
                return Ok(x * 2)
            return Err("must be positive")

        result = Ok(5)
        chained = result.flat_map(double_if_positive)
        assert chained.unwrap() == 10

    def test_or_else_returns_ok_unchanged(self):
        result: Result[int, str] = Ok(42)
        recovered = result.or_else(lambda e: Ok(0))
        assert recovered.unwrap() == 42

    def test_ok_returns_value(self):
        result = Ok(42)
        assert result.ok() == 42

    def test_err_returns_none(self):
        result = Ok(42)
        assert result.err() is None

    def test_expect_returns_value(self):
        result = Ok(42)
        assert result.expect("should not fail") == 42

    def test_expect_err_raises(self):
        result = Ok(42)
        with pytest.raises(ResultError):
            result.expect_err("should fail")

    def test_bool_returns_true(self):
        result = Ok(42)
        assert bool(result) is True

    def test_repr(self):
        result = Ok(42)
        assert repr(result) == "Ok(42)"


class TestErr:
    """Tests for the Err variant."""

    def test_is_err_returns_true(self):
        result: Result[int, str] = Err("error")
        assert result.is_err is True
        assert result.is_ok is False

    def test_unwrap_raises(self):
        result = Err("error")
        with pytest.raises(ResultError) as exc_info:
            result.unwrap()
        assert "error" in str(exc_info.value)

    def test_unwrap_err_returns_error(self):
        result = Err("my error")
        assert result.unwrap_err() == "my error"

    def test_unwrap_or_returns_default(self):
        result: Result[int, str] = Err("error")
        assert result.unwrap_or(42) == 42

    def test_unwrap_or_else_computes_from_error(self):
        result: Result[int, str] = Err("error")
        assert result.unwrap_or_else(lambda e: len(e)) == 5

    def test_map_returns_err_unchanged(self):
        result: Result[int, str] = Err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap_err() == "error"

    def test_map_err_transforms_error(self):
        result: Result[int, str] = Err("error")
        mapped = result.map_err(lambda e: f"Got: {e}")
        assert mapped.unwrap_err() == "Got: error"

    def test_flat_map_returns_err_unchanged(self):
        result: Result[int, str] = Err("error")
        chained = result.flat_map(lambda x: Ok(x * 2))
        assert chained.unwrap_err() == "error"

    def test_or_else_recovers_from_error(self):
        result: Result[int, str] = Err("error")
        recovered = result.or_else(lambda e: Ok(len(e)))
        assert recovered.unwrap() == 5

    def test_ok_returns_none(self):
        result = Err("error")
        assert result.ok() is None

    def test_err_returns_error(self):
        result = Err("my error")
        assert result.err() == "my error"

    def test_expect_raises_with_message(self):
        result = Err("error")
        with pytest.raises(ResultError) as exc_info:
            result.expect("custom message")
        assert "custom message" in str(exc_info.value)

    def test_expect_err_returns_error(self):
        result = Err("my error")
        assert result.expect_err("should not fail") == "my error"

    def test_bool_returns_false(self):
        result = Err("error")
        assert bool(result) is False

    def test_repr(self):
        result = Err("error")
        assert repr(result) == "Err('error')"


class TestAIError:
    """Tests for AIError domain error type."""

    def test_timeout_factory(self):
        error = AIError.timeout()
        assert error.code == AIError.TIMEOUT
        assert error.recoverable is True

    def test_rate_limited_factory(self):
        error = AIError.rate_limited("Too many requests")
        assert error.code == AIError.RATE_LIMITED
        assert "Too many requests" in error.message

    def test_invalid_response_factory(self):
        error = AIError.invalid_response("Bad JSON", {"raw": "..."})
        assert error.code == AIError.INVALID_RESPONSE
        assert error.details == {"raw": "..."}
        assert error.recoverable is False

    def test_parse_error_factory(self):
        error = AIError.parse_error("Cannot parse", raw_output="garbage")
        assert error.code == AIError.PARSE_ERROR
        assert error.details["raw_output"] == "garbage"

    def test_connection_error_factory(self):
        error = AIError.connection_error("Network down")
        assert error.code == AIError.CONNECTION_ERROR
        assert error.recoverable is True

    def test_auth_error_factory(self):
        error = AIError.auth_error()
        assert error.code == AIError.AUTHENTICATION_ERROR
        assert error.recoverable is False

    def test_str_representation(self):
        error = AIError.timeout("Request timed out")
        assert "[AI_TIMEOUT] Request timed out" == str(error)


class TestSearchError:
    """Tests for SearchError domain error type."""

    def test_timeout_factory(self):
        error = SearchError.timeout("python tutorials")
        assert error.code == SearchError.TIMEOUT
        assert error.query == "python tutorials"

    def test_no_results_factory(self):
        error = SearchError.no_results("obscure query")
        assert error.code == SearchError.NO_RESULTS
        assert error.recoverable is False

    def test_invalid_query_factory(self):
        error = SearchError.invalid_query("", "empty query")
        assert error.code == SearchError.INVALID_QUERY

    def test_api_error_factory(self):
        error = SearchError.api_error("test", "API returned 500")
        assert error.code == SearchError.API_ERROR
        assert error.recoverable is True

    def test_str_with_query(self):
        error = SearchError.timeout("test query")
        assert "test query" in str(error)


class TestValidationError:
    """Tests for ValidationError domain error type."""

    def test_required_factory(self):
        error = ValidationError.required("email")
        assert error.code == ValidationError.REQUIRED_FIELD
        assert error.field == "email"

    def test_invalid_format_factory(self):
        error = ValidationError.invalid_format("email", "valid email address", "notanemail")
        assert error.code == ValidationError.INVALID_FORMAT
        assert error.value == "notanemail"

    def test_out_of_range_factory(self):
        error = ValidationError.out_of_range("age", min_val=0, max_val=150, value=-5)
        assert error.code == ValidationError.OUT_OF_RANGE
        assert "min=0" in error.message
        assert "max=150" in error.message

    def test_str_with_field(self):
        error = ValidationError.required("username")
        assert "username" in str(error)


class TestTryResult:
    """Tests for try_result utility function."""

    def test_returns_ok_on_success(self):
        result = try_result(
            lambda: 42,
            lambda e: str(e)
        )
        assert result.is_ok
        assert result.unwrap() == 42

    def test_returns_err_on_exception(self):
        def failing_fn():
            raise ValueError("something went wrong")

        result = try_result(
            failing_fn,
            lambda e: f"Failed: {e}"
        )
        assert result.is_err
        assert "something went wrong" in result.unwrap_err()


class TestTryResultAsync:
    """Tests for try_result_async utility function."""

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        async def async_fn():
            return 42

        result = await try_result_async(
            async_fn,
            lambda e: str(e)
        )
        assert result.is_ok
        assert result.unwrap() == 42

    @pytest.mark.asyncio
    async def test_returns_err_on_exception(self):
        async def failing_async_fn():
            raise ValueError("async error")

        result = await try_result_async(
            failing_async_fn,
            lambda e: f"Async failed: {e}"
        )
        assert result.is_err
        assert "async error" in result.unwrap_err()


class TestCollectResults:
    """Tests for collect_results utility function."""

    def test_all_ok_returns_ok_with_values(self):
        results = [Ok(1), Ok(2), Ok(3)]
        collected = collect_results(results)
        assert collected.is_ok
        assert collected.unwrap() == [1, 2, 3]

    def test_any_err_returns_err_with_errors(self):
        results: list[Result[int, str]] = [Ok(1), Err("error1"), Ok(3), Err("error2")]
        collected = collect_results(results)
        assert collected.is_err
        errors = collected.unwrap_err()
        assert len(errors) == 2
        assert "error1" in errors
        assert "error2" in errors

    def test_empty_list_returns_ok_empty(self):
        results: list[Result[int, str]] = []
        collected = collect_results(results)
        assert collected.is_ok
        assert collected.unwrap() == []


class TestFirstOk:
    """Tests for first_ok utility function."""

    def test_returns_first_ok(self):
        results: list[Result[int, str]] = [Err("e1"), Ok(42), Ok(100)]
        first = first_ok(results)
        assert first.is_ok
        assert first.unwrap() == 42

    def test_all_err_returns_err_with_all_errors(self):
        results: list[Result[int, str]] = [Err("e1"), Err("e2"), Err("e3")]
        first = first_ok(results)
        assert first.is_err
        errors = first.unwrap_err()
        assert len(errors) == 3

    def test_empty_list_returns_err(self):
        results: list[Result[int, str]] = []
        first = first_ok(results)
        assert first.is_err
        assert first.unwrap_err() == []


class TestResultChaining:
    """Tests for chaining multiple Result operations."""

    def test_map_chain(self):
        result = (
            Ok(5)
            .map(lambda x: x * 2)
            .map(lambda x: x + 1)
            .map(str)
        )
        assert result.unwrap() == "11"

    def test_flat_map_chain(self):
        def safe_divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Err("division by zero")
            return Ok(a / b)

        result = (
            Ok((10, 2))
            .flat_map(lambda t: safe_divide(t[0], t[1]))
            .map(lambda x: x * 10)
        )
        assert result.unwrap() == 50.0

    def test_flat_map_chain_with_error(self):
        def safe_divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Err("division by zero")
            return Ok(a / b)

        result = (
            Ok((10, 0))
            .flat_map(lambda t: safe_divide(t[0], t[1]))
            .map(lambda x: x * 10)
        )
        assert result.is_err
        assert result.unwrap_err() == "division by zero"

    def test_error_recovery_chain(self):
        result: Result[int, str] = (
            Err("initial error")
            .or_else(lambda e: Err(f"wrapped: {e}"))
            .or_else(lambda e: Ok(42))
        )
        assert result.unwrap() == 42
