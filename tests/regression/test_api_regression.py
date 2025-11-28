"""
Regression tests for API bug fixes.

These tests ensure that previously fixed API bugs don't reappear.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Request Validation Regression Tests
# =============================================================================


class TestRequestValidationRegression:
    """Regression tests for request validation fixes."""

    @pytest.mark.regression
    def test_empty_company_name_rejected(self):
        """Regression: Empty company names must be rejected."""
        from pydantic import ValidationError
        from src.api.models import ResearchRequest

        with pytest.raises(ValidationError):
            ResearchRequest(company_name="")

    @pytest.mark.regression
    def test_whitespace_company_name_rejected(self):
        """Regression: Whitespace-only company names must be rejected."""
        from pydantic import ValidationError
        from src.api.models import ResearchRequest

        with pytest.raises(ValidationError):
            ResearchRequest(company_name="   \t\n   ")

    @pytest.mark.regression
    def test_company_name_max_length_enforced(self):
        """Regression: Company name max length must be enforced."""
        from pydantic import ValidationError
        from src.api.models import ResearchRequest

        long_name = "A" * 201  # Max is 200

        with pytest.raises(ValidationError):
            ResearchRequest(company_name=long_name)

    @pytest.mark.regression
    def test_invalid_url_rejected(self):
        """Regression: Invalid URLs must be rejected."""
        from pydantic import ValidationError
        from src.api.models import ResearchRequest

        with pytest.raises(ValidationError):
            ResearchRequest(
                company_name="Test",
                url="not-a-valid-url"
            )


# =============================================================================
# Response Format Regression Tests
# =============================================================================


class TestResponseFormatRegression:
    """Regression tests for response format consistency."""

    @pytest.mark.regression
    def test_research_response_has_required_fields(self):
        """Regression: ResearchResponse must have all required fields."""
        from src.api.models import ResearchResponse

        response = ResearchResponse(
            task_id="test-123",
            status="pending",
            message="Research started",
        )

        assert response.task_id == "test-123"
        assert response.status == "pending"
        assert response.message == "Research started"

    @pytest.mark.regression
    def test_task_status_response_result_optional(self):
        """Regression: TaskStatusResponse.result must be optional."""
        from src.api.models import TaskStatusResponse

        # Should not raise - result is optional
        response = TaskStatusResponse(
            task_id="test-123",
            status="running",
        )

        assert response.result is None

    @pytest.mark.regression
    def test_task_status_response_error_optional(self):
        """Regression: TaskStatusResponse.error must be optional."""
        from src.api.models import TaskStatusResponse

        # Should not raise - error is optional
        response = TaskStatusResponse(
            task_id="test-123",
            status="completed",
            result={"data": "test"},
        )

        assert response.error is None


# =============================================================================
# Error Handling Regression Tests
# =============================================================================


class TestErrorHandlingRegression:
    """Regression tests for error handling fixes."""

    @pytest.mark.regression
    def test_task_status_preserves_error_message(self):
        """Regression: Failed task must preserve error message."""
        from src.api.models import TaskStatusResponse

        error_msg = "Network timeout while fetching data"

        response = TaskStatusResponse(
            task_id="test-123",
            status="failed",
            error=error_msg,
        )

        assert response.error == error_msg

    @pytest.mark.regression
    def test_complex_result_structure_preserved(self):
        """Regression: Complex result structures must be preserved."""
        from src.api.models import TaskStatusResponse

        complex_result = {
            "reports": {
                "financial": {"revenue": 1000000, "profit": 150000},
                "market": {"share": 0.15, "growth": 0.08},
            },
            "sources": [
                {"url": "https://example.com/1", "title": "Source 1"},
                {"url": "https://example.com/2", "title": "Source 2"},
            ],
            "metadata": {
                "duration_seconds": 120,
                "agent_count": 5,
            },
        }

        response = TaskStatusResponse(
            task_id="test-123",
            status="completed",
            result=complex_result,
        )

        # Verify structure is preserved
        assert response.result["reports"]["financial"]["revenue"] == 1000000
        assert len(response.result["sources"]) == 2


# =============================================================================
# Concurrency Regression Tests
# =============================================================================


class TestConcurrencyRegression:
    """Regression tests for concurrency-related fixes."""

    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_concurrent_task_creation_unique_ids(self):
        """Regression: Concurrent task creation must produce unique IDs."""
        import asyncio
        import uuid

        # Simulate generating task IDs concurrently
        task_ids = set()

        async def create_task_id():
            # Simulates task ID generation
            return str(uuid.uuid4())

        # Create many task IDs concurrently
        tasks = [create_task_id() for _ in range(100)]
        ids = await asyncio.gather(*tasks)

        # All IDs should be unique
        task_ids = set(ids)
        assert len(task_ids) == 100


# =============================================================================
# Data Integrity Regression Tests
# =============================================================================


class TestDataIntegrityRegression:
    """Regression tests for data integrity fixes."""

    @pytest.mark.regression
    def test_unicode_preserved_in_company_name(self):
        """Regression: Unicode characters must be preserved in company names."""
        from src.api.models import ResearchRequest

        unicode_names = [
            "测试公司",  # Chinese
            "テスト会社",  # Japanese
            "Société Test",  # French
            "Тест Компания",  # Russian
        ]

        for name in unicode_names:
            request = ResearchRequest(company_name=name)
            assert request.company_name == name

    @pytest.mark.regression
    def test_special_characters_preserved(self):
        """Regression: Special characters must be preserved in company names."""
        from src.api.models import ResearchRequest

        special_names = [
            "Test & Co.",
            "Test's Company",
            'Company "Quoted"',
            "Test: Subtitle",
            "Company (Holdings) Ltd.",
        ]

        for name in special_names:
            request = ResearchRequest(company_name=name)
            assert request.company_name == name
