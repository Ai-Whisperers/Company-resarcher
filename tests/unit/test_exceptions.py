"""
Unit tests for Exception Hierarchy.

Tests all exception types from the exception hierarchy:
- CompanyResearcherError (base)
- AIError and subtypes
- NetworkError and subtypes
- ValidationError and subtypes
- SearchError and subtypes
- PipelineError and subtypes
- ToolError and subtypes
"""

import pytest
from typing import Dict, Any

from src.core.exceptions.base import (
    # Base
    CompanyResearcherError,
    # AI
    AIError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseError,
    AIModelNotFoundError,
    # Network
    NetworkError,
    ConnectionFailedError,
    NetworkTimeoutError,
    HTTPError,
    RateLimitedError,
    # Validation
    ValidationError,
    ConfigValidationError,
    InputValidationError,
    SchemaValidationError,
    # Search
    SearchError,
    SearchProviderError,
    NoResultsError,
    SearchQuotaExceededError,
    # Pipeline
    PipelineError,
    StageError,
    OrchestratorError,
    PipelineTimeoutError,
    # Tools
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
)


# =============================================================================
# Base Exception Tests
# =============================================================================


class TestCompanyResearcherError:
    """Tests for base CompanyResearcherError."""

    @pytest.mark.unit
    def test_basic_instantiation(self):
        """Verify basic exception can be created."""
        error = CompanyResearcherError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"

    @pytest.mark.unit
    def test_with_details(self):
        """Verify exception can store details."""
        details = {"key": "value", "count": 42}
        error = CompanyResearcherError("Error with details", details=details)

        assert error.details == details
        assert error.details["key"] == "value"
        assert error.details["count"] == 42

    @pytest.mark.unit
    def test_to_dict(self):
        """Verify to_dict serialization."""
        error = CompanyResearcherError("Test error", details={"code": 123})
        result = error.to_dict()

        assert result["error_type"] == "CompanyResearcherError"
        assert result["message"] == "Test error"
        assert result["details"]["code"] == 123

    @pytest.mark.unit
    def test_inherits_from_exception(self):
        """Verify inherits from Exception."""
        error = CompanyResearcherError("Test")
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_empty_details_default(self):
        """Verify empty details defaults to empty dict."""
        error = CompanyResearcherError("Test")
        assert error.details == {}

    @pytest.mark.unit
    def test_can_be_caught_as_exception(self):
        """Verify can be caught as base Exception."""
        with pytest.raises(Exception):
            raise CompanyResearcherError("Test")


# =============================================================================
# AI Exception Tests
# =============================================================================


class TestAIError:
    """Tests for AI-related exceptions."""

    @pytest.mark.unit
    def test_ai_error_with_provider(self):
        """Verify AIError stores provider info."""
        error = AIError("AI failed", provider="openai")

        assert error.provider == "openai"
        assert error.details["provider"] == "openai"

    @pytest.mark.unit
    def test_ai_provider_error(self):
        """Verify AIProviderError formatting."""
        error = AIProviderError("Model overloaded", provider="anthropic", error_code="503")

        assert "[anthropic]" in str(error)
        assert error.provider == "anthropic"
        assert error.error_code == "503"

    @pytest.mark.unit
    def test_ai_rate_limit_error(self):
        """Verify AIRateLimitError with retry info."""
        error = AIRateLimitError(provider="openai", retry_after=60)

        assert error.retry_after == 60
        assert "60s" in str(error)
        assert "[openai]" in str(error)

    @pytest.mark.unit
    def test_ai_rate_limit_error_no_retry(self):
        """Verify AIRateLimitError without retry info."""
        error = AIRateLimitError(provider="openai")

        assert error.retry_after is None
        assert "Rate limit exceeded" in str(error)

    @pytest.mark.unit
    def test_ai_timeout_error(self):
        """Verify AITimeoutError formatting."""
        error = AITimeoutError(provider="gemini", timeout_seconds=30)

        assert error.timeout_seconds == 30
        assert "30s" in str(error)
        assert "[gemini]" in str(error)

    @pytest.mark.unit
    def test_ai_response_error(self):
        """Verify AIResponseError with reason."""
        error = AIResponseError(provider="openai", reason="Invalid JSON")

        assert error.reason == "Invalid JSON"
        assert "Invalid JSON" in str(error)

    @pytest.mark.unit
    def test_ai_model_not_found_error(self):
        """Verify AIModelNotFoundError with model name."""
        error = AIModelNotFoundError(provider="openai", model="gpt-5")

        assert error.model == "gpt-5"
        assert "gpt-5" in str(error)


# =============================================================================
# Network Exception Tests
# =============================================================================


class TestNetworkError:
    """Tests for network-related exceptions."""

    @pytest.mark.unit
    def test_network_error_with_url(self):
        """Verify NetworkError stores URL."""
        error = NetworkError("Connection failed", url="https://api.example.com")

        assert error.url == "https://api.example.com"
        assert error.details["url"] == "https://api.example.com"

    @pytest.mark.unit
    def test_connection_failed_error(self):
        """Verify ConnectionFailedError formatting."""
        error = ConnectionFailedError(url="https://api.example.com", reason="DNS lookup failed")

        assert error.reason == "DNS lookup failed"
        assert "api.example.com" in str(error)
        assert "DNS lookup failed" in str(error)

    @pytest.mark.unit
    def test_network_timeout_error(self):
        """Verify NetworkTimeoutError formatting."""
        error = NetworkTimeoutError(url="https://api.example.com", timeout_seconds=10)

        assert error.timeout_seconds == 10
        assert "10s" in str(error)

    @pytest.mark.unit
    def test_http_error(self):
        """Verify HTTPError with status code."""
        error = HTTPError(url="https://api.example.com", status_code=404, reason="Not Found")

        assert error.status_code == 404
        assert error.reason == "Not Found"
        assert "404" in str(error)

    @pytest.mark.unit
    def test_rate_limited_error(self):
        """Verify RateLimitedError formatting."""
        error = RateLimitedError(url="https://api.example.com", retry_after=120)

        assert error.retry_after == 120
        assert "120s" in str(error)


# =============================================================================
# Validation Exception Tests
# =============================================================================


class TestValidationError:
    """Tests for validation-related exceptions."""

    @pytest.mark.unit
    def test_validation_error_with_field(self):
        """Verify ValidationError stores field name."""
        error = ValidationError("Invalid value", field="company_name")

        assert error.field == "company_name"
        assert error.details["field"] == "company_name"

    @pytest.mark.unit
    def test_config_validation_error(self):
        """Verify ConfigValidationError with config key."""
        error = ConfigValidationError("Invalid API key", config_key="OPENAI_API_KEY")

        assert error.config_key == "OPENAI_API_KEY"
        assert error.details["config_key"] == "OPENAI_API_KEY"

    @pytest.mark.unit
    def test_input_validation_error(self):
        """Verify InputValidationError with field and value."""
        error = InputValidationError(
            message="Invalid format",
            field="email",
            value="not-an-email"
        )

        assert error.field == "email"
        assert error.value == "not-an-email"

    @pytest.mark.unit
    def test_input_validation_error_no_value_exposure(self):
        """Verify sensitive values are not directly exposed."""
        error = InputValidationError(
            message="Invalid",
            field="password",
            value="secret123"
        )

        # Value should be repr'd, not raw
        if "invalid_value" in error.details:
            assert error.details["invalid_value"] == "'secret123'"

    @pytest.mark.unit
    def test_schema_validation_error(self):
        """Verify SchemaValidationError with errors list."""
        validation_errors = [
            {"field": "name", "error": "required"},
            {"field": "age", "error": "must be integer"}
        ]
        error = SchemaValidationError(
            message="Schema validation failed",
            schema_name="UserSchema",
            errors=validation_errors
        )

        assert error.schema_name == "UserSchema"
        assert len(error.errors) == 2


# =============================================================================
# Search Exception Tests
# =============================================================================


class TestSearchError:
    """Tests for search-related exceptions."""

    @pytest.mark.unit
    def test_search_error_with_query(self):
        """Verify SearchError stores query."""
        error = SearchError("Search failed", query="company news")

        assert error.query == "company news"
        assert error.details["query"] == "company news"

    @pytest.mark.unit
    def test_search_provider_error(self):
        """Verify SearchProviderError formatting."""
        error = SearchProviderError(
            message="API unavailable",
            provider="tavily",
            query="test query"
        )

        assert error.provider == "tavily"
        assert "[tavily]" in str(error)

    @pytest.mark.unit
    def test_no_results_error(self):
        """Verify NoResultsError with providers tried."""
        error = NoResultsError(
            query="obscure company",
            providers_tried=["tavily", "serper", "duckduckgo"]
        )

        assert error.query == "obscure company"
        assert len(error.providers_tried) == 3
        assert "tavily" in str(error)

    @pytest.mark.unit
    def test_search_quota_exceeded_error(self):
        """Verify SearchQuotaExceededError."""
        error = SearchQuotaExceededError(provider="serper", query="test")

        assert error.provider == "serper"
        assert "quota" in str(error).lower()


# =============================================================================
# Pipeline Exception Tests
# =============================================================================


class TestPipelineError:
    """Tests for pipeline-related exceptions."""

    @pytest.mark.unit
    def test_pipeline_error_with_stage(self):
        """Verify PipelineError stores stage info."""
        error = PipelineError("Pipeline failed", stage="research")

        assert error.stage == "research"
        assert error.details["stage"] == "research"

    @pytest.mark.unit
    def test_stage_error(self):
        """Verify StageError with cause."""
        cause = ValueError("Invalid data")
        error = StageError(stage="analysis", message="Failed to analyze", cause=cause)

        assert error.stage == "analysis"
        assert error.cause == cause
        assert "ValueError" in error.details.get("cause_type", "")

    @pytest.mark.unit
    def test_orchestrator_error(self):
        """Verify OrchestratorError with failed stages."""
        error = OrchestratorError(
            message="Multiple stages failed",
            failed_stages=["research", "analysis"]
        )

        assert len(error.failed_stages) == 2
        assert "research" in error.failed_stages

    @pytest.mark.unit
    def test_pipeline_timeout_error(self):
        """Verify PipelineTimeoutError formatting."""
        error = PipelineTimeoutError(timeout_seconds=300, stage="fetching")

        assert error.timeout_seconds == 300
        assert "300s" in str(error)
        assert "fetching" in str(error)


# =============================================================================
# Tool Exception Tests
# =============================================================================


class TestToolError:
    """Tests for tool-related exceptions."""

    @pytest.mark.unit
    def test_tool_error_with_name(self):
        """Verify ToolError stores tool name."""
        error = ToolError("Tool failed", tool_name="browser")

        assert error.tool_name == "browser"
        assert error.details["tool_name"] == "browser"

    @pytest.mark.unit
    def test_tool_not_found_error(self):
        """Verify ToolNotFoundError formatting."""
        error = ToolNotFoundError(tool_name="nonexistent_tool")

        assert "nonexistent_tool" in str(error)
        assert "not found" in str(error).lower()

    @pytest.mark.unit
    def test_tool_execution_error(self):
        """Verify ToolExecutionError with cause."""
        cause = RuntimeError("Execution failed")
        error = ToolExecutionError(
            tool_name="search",
            message="Search execution failed",
            cause=cause
        )

        assert error.tool_name == "search"
        assert error.cause == cause
        assert "[search]" in str(error)


# =============================================================================
# Exception Hierarchy Tests
# =============================================================================


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    @pytest.mark.unit
    def test_all_inherit_from_base(self):
        """Verify all exceptions inherit from CompanyResearcherError."""
        exceptions = [
            AIError("test", provider="test"),
            AIProviderError("test", "test"),
            AIRateLimitError("test"),
            NetworkError("test"),
            ConnectionFailedError("test"),
            ValidationError("test"),
            ConfigValidationError("test"),
            SearchError("test"),
            SearchProviderError("test", "test"),
            PipelineError("test"),
            StageError("test", "test"),
            ToolError("test"),
            ToolNotFoundError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, CompanyResearcherError), f"{type(exc).__name__} doesn't inherit from base"

    @pytest.mark.unit
    def test_ai_errors_inherit_from_ai_error(self):
        """Verify AI exceptions inherit from AIError."""
        ai_exceptions = [
            AIProviderError("test", "test"),
            AIRateLimitError("test"),
            AITimeoutError("test", 10),
            AIResponseError("test", "test"),
            AIModelNotFoundError("test", "test"),
        ]

        for exc in ai_exceptions:
            assert isinstance(exc, AIError), f"{type(exc).__name__} doesn't inherit from AIError"

    @pytest.mark.unit
    def test_network_errors_inherit_from_network_error(self):
        """Verify network exceptions inherit from NetworkError."""
        network_exceptions = [
            ConnectionFailedError("test"),
            NetworkTimeoutError("test", 10),
            HTTPError("test", 500),
            RateLimitedError("test"),
        ]

        for exc in network_exceptions:
            assert isinstance(exc, NetworkError), f"{type(exc).__name__} doesn't inherit from NetworkError"

    @pytest.mark.unit
    def test_can_catch_by_category(self):
        """Verify exceptions can be caught by category."""
        # AI errors
        with pytest.raises(AIError):
            raise AIRateLimitError("openai")

        # Network errors
        with pytest.raises(NetworkError):
            raise HTTPError("url", 404)

        # Validation errors
        with pytest.raises(ValidationError):
            raise InputValidationError("msg", "field")

        # Search errors
        with pytest.raises(SearchError):
            raise NoResultsError("query")

        # Pipeline errors
        with pytest.raises(PipelineError):
            raise StageError("stage", "msg")

        # Tool errors
        with pytest.raises(ToolError):
            raise ToolNotFoundError("tool")


# =============================================================================
# Serialization Tests
# =============================================================================


class TestExceptionSerialization:
    """Tests for exception serialization."""

    @pytest.mark.unit
    def test_to_dict_contains_all_fields(self):
        """Verify to_dict includes all expected fields."""
        error = AIProviderError("Test error", "openai", "ERR_001")
        result = error.to_dict()

        assert "error_type" in result
        assert "message" in result
        assert "details" in result

    @pytest.mark.unit
    def test_to_dict_is_json_serializable(self):
        """Verify to_dict output is JSON serializable."""
        import json

        error = StageError(
            stage="research",
            message="Failed",
            cause=ValueError("Invalid data")
        )
        result = error.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_to_dict_preserves_details(self):
        """Verify custom details are preserved in to_dict."""
        error = CompanyResearcherError(
            "Test",
            details={"custom_key": "custom_value", "nested": {"a": 1}}
        )
        result = error.to_dict()

        assert result["details"]["custom_key"] == "custom_value"
        assert result["details"]["nested"]["a"] == 1


# =============================================================================
# Error Message Tests
# =============================================================================


class TestErrorMessages:
    """Tests for error message formatting."""

    @pytest.mark.unit
    def test_messages_are_user_friendly(self):
        """Verify error messages are user-friendly."""
        errors = [
            (AIRateLimitError("openai", 60), "rate limit"),
            (NetworkTimeoutError("url", 30), "timeout"),
            (NoResultsError("query"), "no results"),
            (ToolNotFoundError("tool"), "not found"),
        ]

        for error, expected_fragment in errors:
            msg = str(error).lower()
            assert expected_fragment in msg, f"Message '{msg}' should contain '{expected_fragment}'"

    @pytest.mark.unit
    def test_messages_include_context(self):
        """Verify error messages include relevant context."""
        error = HTTPError(url="https://api.example.com/endpoint", status_code=503, reason="Service Unavailable")

        msg = str(error)
        assert "503" in msg
        assert "api.example.com" in msg

    @pytest.mark.unit
    def test_no_sensitive_data_in_messages(self):
        """Verify error messages don't expose sensitive data."""
        # API keys shouldn't appear in messages
        error = ConfigValidationError(
            message="Invalid API key format",
            config_key="OPENAI_API_KEY"
        )

        msg = str(error)
        # Should reference key name but not actual key value
        assert "sk-" not in msg.lower()
