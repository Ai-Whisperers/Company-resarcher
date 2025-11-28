"""
Unit tests for API models.

Tests Pydantic models for request/response validation including:
- Field validation
- Type coercion
- Error handling
- Edge cases
"""

import pytest
from pydantic import ValidationError

from src.api.models import (
    ResearchRequest,
    ResearchResponse,
    TaskStatusResponse,
)


# =============================================================================
# ResearchRequest Tests
# =============================================================================


class TestResearchRequest:
    """Tests for ResearchRequest model."""

    @pytest.mark.unit
    def test_valid_request_with_required_fields(self):
        """Verify valid request with only required fields."""
        request = ResearchRequest(company_name="Test Corp")

        assert request.company_name == "Test Corp"
        assert request.url is None
        assert request.industry is None
        assert request.country == "USA"  # Default value

    @pytest.mark.unit
    def test_valid_request_with_all_fields(self):
        """Verify valid request with all fields."""
        request = ResearchRequest(
            company_name="Test Corp",
            url="https://testcorp.com",
            industry="Technology",
            country="Germany",
        )

        assert request.company_name == "Test Corp"
        assert str(request.url) == "https://testcorp.com/"
        assert request.industry == "Technology"
        assert request.country == "Germany"

    @pytest.mark.unit
    def test_company_name_required(self):
        """Verify company_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ResearchRequest()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("company_name",) for e in errors)

    @pytest.mark.unit
    def test_company_name_cannot_be_empty(self):
        """Verify empty company_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResearchRequest(company_name="")

        errors = exc_info.value.errors()
        assert any("company_name" in str(e) for e in errors)

    @pytest.mark.unit
    def test_company_name_cannot_be_whitespace(self):
        """Verify whitespace-only company_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResearchRequest(company_name="   ")

        errors = exc_info.value.errors()
        assert any("empty" in str(e).lower() or "whitespace" in str(e).lower() for e in errors)

    @pytest.mark.unit
    def test_company_name_is_stripped(self):
        """Verify company_name whitespace is stripped."""
        request = ResearchRequest(company_name="  Test Corp  ")
        assert request.company_name == "Test Corp"

    @pytest.mark.unit
    def test_company_name_max_length(self):
        """Verify company_name max length is enforced."""
        long_name = "A" * 201

        with pytest.raises(ValidationError) as exc_info:
            ResearchRequest(company_name=long_name)

        errors = exc_info.value.errors()
        assert any("company_name" in str(e) for e in errors)

    @pytest.mark.unit
    def test_company_name_at_max_length(self):
        """Verify company_name at exactly max length is accepted."""
        name = "A" * 200
        request = ResearchRequest(company_name=name)
        assert request.company_name == name

    @pytest.mark.unit
    def test_url_validation(self):
        """Verify URL is validated."""
        with pytest.raises(ValidationError):
            ResearchRequest(company_name="Test", url="not-a-url")

    @pytest.mark.unit
    def test_valid_url_formats(self):
        """Verify various valid URL formats are accepted."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com",
            "https://sub.domain.example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            request = ResearchRequest(company_name="Test", url=url)
            assert request.url is not None

    @pytest.mark.unit
    def test_industry_is_stripped(self):
        """Verify industry whitespace is stripped."""
        request = ResearchRequest(company_name="Test", industry="  Technology  ")
        assert request.industry == "Technology"

    @pytest.mark.unit
    def test_industry_empty_becomes_none(self):
        """Verify empty/whitespace industry becomes None."""
        request = ResearchRequest(company_name="Test", industry="   ")
        assert request.industry is None

    @pytest.mark.unit
    def test_industry_max_length(self):
        """Verify industry max length is enforced."""
        long_industry = "A" * 101

        with pytest.raises(ValidationError):
            ResearchRequest(company_name="Test", industry=long_industry)

    @pytest.mark.unit
    def test_country_default(self):
        """Verify country has default value."""
        request = ResearchRequest(company_name="Test")
        assert request.country == "USA"

    @pytest.mark.unit
    def test_country_is_stripped(self):
        """Verify country whitespace is stripped."""
        request = ResearchRequest(company_name="Test", country="  Germany  ")
        assert request.country == "Germany"

    @pytest.mark.unit
    def test_country_max_length(self):
        """Verify country max length is enforced."""
        long_country = "A" * 101

        with pytest.raises(ValidationError):
            ResearchRequest(company_name="Test", country=long_country)


# =============================================================================
# ResearchRequest Edge Cases
# =============================================================================


class TestResearchRequestEdgeCases:
    """Edge case tests for ResearchRequest."""

    @pytest.mark.unit
    def test_unicode_company_name(self):
        """Verify unicode company names are accepted."""
        request = ResearchRequest(company_name="测试公司")
        assert request.company_name == "测试公司"

    @pytest.mark.unit
    def test_company_name_with_special_characters(self):
        """Verify company names with special characters are accepted."""
        request = ResearchRequest(company_name="Test & Co., Inc.")
        assert request.company_name == "Test & Co., Inc."

    @pytest.mark.unit
    def test_company_name_with_numbers(self):
        """Verify company names with numbers are accepted."""
        request = ResearchRequest(company_name="3M Company")
        assert request.company_name == "3M Company"

    @pytest.mark.unit
    def test_single_character_company_name(self):
        """Verify single character company name is accepted."""
        request = ResearchRequest(company_name="X")
        assert request.company_name == "X"

    @pytest.mark.unit
    def test_url_with_port(self):
        """Verify URL with port is accepted."""
        request = ResearchRequest(
            company_name="Test",
            url="https://example.com:8080"
        )
        assert request.url is not None

    @pytest.mark.unit
    def test_json_serialization(self):
        """Verify model can be serialized to JSON."""
        request = ResearchRequest(
            company_name="Test Corp",
            url="https://test.com",
            industry="Tech",
        )

        json_str = request.model_dump_json()
        assert "Test Corp" in json_str
        assert "Tech" in json_str

    @pytest.mark.unit
    def test_dict_conversion(self):
        """Verify model can be converted to dict."""
        request = ResearchRequest(company_name="Test Corp")
        data = request.model_dump()

        assert isinstance(data, dict)
        assert data["company_name"] == "Test Corp"


# =============================================================================
# ResearchResponse Tests
# =============================================================================


class TestResearchResponse:
    """Tests for ResearchResponse model."""

    @pytest.mark.unit
    def test_valid_response(self):
        """Verify valid response creation."""
        response = ResearchResponse(
            task_id="task-123",
            status="pending",
            message="Research started",
        )

        assert response.task_id == "task-123"
        assert response.status == "pending"
        assert response.message == "Research started"

    @pytest.mark.unit
    def test_all_fields_required(self):
        """Verify all fields are required."""
        with pytest.raises(ValidationError):
            ResearchResponse(task_id="123")

        with pytest.raises(ValidationError):
            ResearchResponse(task_id="123", status="pending")

    @pytest.mark.unit
    def test_json_serialization(self):
        """Verify model serializes to JSON."""
        response = ResearchResponse(
            task_id="task-123",
            status="completed",
            message="Done",
        )

        json_str = response.model_dump_json()
        assert "task-123" in json_str


# =============================================================================
# TaskStatusResponse Tests
# =============================================================================


class TestTaskStatusResponse:
    """Tests for TaskStatusResponse model."""

    @pytest.mark.unit
    def test_valid_pending_response(self):
        """Verify valid pending status response."""
        response = TaskStatusResponse(
            task_id="task-123",
            status="pending",
        )

        assert response.task_id == "task-123"
        assert response.status == "pending"
        assert response.result is None
        assert response.error is None

    @pytest.mark.unit
    def test_valid_completed_response(self):
        """Verify valid completed status response with result."""
        response = TaskStatusResponse(
            task_id="task-123",
            status="completed",
            result={"reports": ["report1", "report2"]},
        )

        assert response.status == "completed"
        assert response.result == {"reports": ["report1", "report2"]}

    @pytest.mark.unit
    def test_valid_failed_response(self):
        """Verify valid failed status response with error."""
        response = TaskStatusResponse(
            task_id="task-123",
            status="failed",
            error="Something went wrong",
        )

        assert response.status == "failed"
        assert response.error == "Something went wrong"

    @pytest.mark.unit
    def test_result_optional(self):
        """Verify result field is optional."""
        response = TaskStatusResponse(
            task_id="task-123",
            status="running",
        )

        assert response.result is None

    @pytest.mark.unit
    def test_error_optional(self):
        """Verify error field is optional."""
        response = TaskStatusResponse(
            task_id="task-123",
            status="completed",
            result={"data": "test"},
        )

        assert response.error is None

    @pytest.mark.unit
    def test_complex_result_structure(self):
        """Verify complex result structures are accepted."""
        complex_result = {
            "reports": {
                "financial": {"revenue": 1000000},
                "market": {"share": 0.15},
            },
            "sources": ["url1", "url2"],
            "metadata": {
                "duration": 120,
                "agents": ["FinancialAgent", "MarketAgent"],
            },
        }

        response = TaskStatusResponse(
            task_id="task-123",
            status="completed",
            result=complex_result,
        )

        assert response.result["reports"]["financial"]["revenue"] == 1000000


# =============================================================================
# Security-Related Tests
# =============================================================================


class TestSecurityValidation:
    """Security-related validation tests."""

    @pytest.mark.unit
    @pytest.mark.security
    def test_rejects_script_tags_in_name(self):
        """Verify script tags in company name don't cause issues."""
        # Note: We're testing that the value is stored safely, not sanitized
        # XSS prevention should happen at output, not input
        request = ResearchRequest(company_name="<script>alert('xss')</script>")
        assert "<script>" in request.company_name

    @pytest.mark.unit
    @pytest.mark.security
    def test_sql_injection_attempt_stored_safely(self):
        """Verify SQL injection attempts are stored as plain text."""
        request = ResearchRequest(company_name="'; DROP TABLE users; --")
        assert "DROP TABLE" in request.company_name

    @pytest.mark.unit
    @pytest.mark.security
    def test_path_traversal_stored_safely(self):
        """Verify path traversal attempts are stored as plain text."""
        request = ResearchRequest(company_name="../../../etc/passwd")
        assert "../" in request.company_name

    @pytest.mark.unit
    @pytest.mark.security
    def test_null_byte_handling(self):
        """Verify null bytes in company name are handled."""
        # Pydantic should handle this gracefully
        request = ResearchRequest(company_name="Test\x00Corp")
        assert request.company_name is not None
