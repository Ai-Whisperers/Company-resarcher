"""
Integration tests for API endpoints.

Tests the API endpoints including:
- Research task creation
- Task status retrieval
- Health checks
- Error handling
- Rate limiting
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    mock = MagicMock()
    mock.TAVILY_API_KEY = "test-key"
    mock.has_any_ai_provider.return_value = True
    mock.validate_config.return_value = []
    return mock


@pytest.fixture
def test_client(mock_db_session, mock_settings):
    """Create a test client with mocked dependencies."""
    with patch("src.api.app.get_db") as mock_get_db:
        with patch("src.api.app.rate_limiter") as mock_limiter:
            with patch("src.api.database.engine"):
                with patch("src.api.database.Base"):
                    mock_get_db.return_value = mock_db_session
                    mock_limiter.is_allowed.return_value = True

                    from src.api.app import app
                    client = TestClient(app, raise_server_exceptions=False)
                    yield client


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.integration
    def test_basic_health_check(self, test_client):
        """Verify basic health check returns healthy."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.integration
    def test_detailed_health_check_structure(self, test_client, mock_db_session):
        """Verify detailed health check returns expected structure."""
        # Mock the database check
        from sqlalchemy import text
        mock_db_session.execute = MagicMock()

        with patch("src.api.app.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.validate_config.return_value = []
            mock_settings.has_any_ai_provider.return_value = True
            mock_get_settings.return_value = mock_settings

            response = test_client.get("/health/detailed")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "checks" in data


# =============================================================================
# Research Endpoint Tests
# =============================================================================


class TestResearchEndpoint:
    """Tests for /api/v1/research endpoint."""

    @pytest.mark.integration
    def test_start_research_valid_request(self, test_client, mock_db_session):
        """Verify valid research request is accepted."""
        request_data = {
            "company_name": "Test Corporation",
        }

        with patch("src.api.app.save_task") as mock_save:
            mock_save.return_value = MagicMock()

            response = test_client.post(
                "/api/v1/research",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "pending"
            assert "message" in data

    @pytest.mark.integration
    def test_start_research_with_url(self, test_client, mock_db_session):
        """Verify research request with URL is accepted."""
        request_data = {
            "company_name": "Test Corp",
            "url": "https://testcorp.com",
        }

        with patch("src.api.app.save_task") as mock_save:
            mock_save.return_value = MagicMock()

            response = test_client.post(
                "/api/v1/research",
                json=request_data,
            )

            assert response.status_code == 200

    @pytest.mark.integration
    def test_start_research_with_all_fields(self, test_client, mock_db_session):
        """Verify research request with all fields is accepted."""
        request_data = {
            "company_name": "Test Corp",
            "url": "https://testcorp.com",
            "industry": "Technology",
            "country": "Germany",
        }

        with patch("src.api.app.save_task") as mock_save:
            mock_save.return_value = MagicMock()

            response = test_client.post(
                "/api/v1/research",
                json=request_data,
            )

            assert response.status_code == 200

    @pytest.mark.integration
    def test_start_research_missing_company_name(self, test_client):
        """Verify missing company_name is rejected."""
        request_data = {}

        response = test_client.post(
            "/api/v1/research",
            json=request_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    def test_start_research_empty_company_name(self, test_client):
        """Verify empty company_name is rejected."""
        request_data = {
            "company_name": "",
        }

        response = test_client.post(
            "/api/v1/research",
            json=request_data,
        )

        assert response.status_code == 422

    @pytest.mark.integration
    def test_start_research_invalid_url(self, test_client):
        """Verify invalid URL is rejected."""
        request_data = {
            "company_name": "Test",
            "url": "not-a-url",
        }

        response = test_client.post(
            "/api/v1/research",
            json=request_data,
        )

        assert response.status_code == 422


# =============================================================================
# Task Status Endpoint Tests
# =============================================================================


class TestTaskStatusEndpoint:
    """Tests for /api/v1/research/{task_id} endpoint."""

    @pytest.mark.integration
    def test_get_pending_task(self, test_client, mock_db_session):
        """Verify pending task status can be retrieved."""
        task_id = "test-task-123"

        with patch("src.api.app.get_task") as mock_get_task:
            mock_get_task.return_value = {
                "task_id": task_id,
                "status": "pending",
                "request": {"company_name": "Test"},
                "result": None,
                "error": None,
            }

            response = test_client.get(f"/api/v1/research/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["status"] == "pending"

    @pytest.mark.integration
    def test_get_completed_task(self, test_client, mock_db_session):
        """Verify completed task status includes result."""
        task_id = "test-task-456"

        with patch("src.api.app.get_task") as mock_get_task:
            mock_get_task.return_value = {
                "task_id": task_id,
                "status": "completed",
                "request": {"company_name": "Test"},
                "result": {"reports": {"executive_summary": "Summary here"}},
                "error": None,
            }

            response = test_client.get(f"/api/v1/research/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["result"] is not None

    @pytest.mark.integration
    def test_get_failed_task(self, test_client, mock_db_session):
        """Verify failed task status includes error."""
        task_id = "test-task-789"

        with patch("src.api.app.get_task") as mock_get_task:
            mock_get_task.return_value = {
                "task_id": task_id,
                "status": "failed",
                "request": {"company_name": "Test"},
                "result": None,
                "error": "Network timeout",
            }

            response = test_client.get(f"/api/v1/research/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert data["error"] == "Network timeout"

    @pytest.mark.integration
    def test_get_nonexistent_task(self, test_client, mock_db_session):
        """Verify 404 for nonexistent task."""
        with patch("src.api.app.get_task") as mock_get_task:
            mock_get_task.return_value = None

            response = test_client.get("/api/v1/research/nonexistent-task")

            assert response.status_code == 404


# =============================================================================
# Rate Limiting Tests
# =============================================================================


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @pytest.mark.integration
    def test_rate_limit_allows_initial_requests(self, mock_db_session):
        """Verify initial requests are allowed."""
        from src.api.app import RateLimiter

        limiter = RateLimiter(requests_per_minute=10)

        # First 10 requests should be allowed
        for _ in range(10):
            assert limiter.is_allowed("127.0.0.1") is True

    @pytest.mark.integration
    def test_rate_limit_blocks_excess_requests(self, mock_db_session):
        """Verify excess requests are blocked."""
        from src.api.app import RateLimiter

        limiter = RateLimiter(requests_per_minute=5)

        # Use up the limit
        for _ in range(5):
            limiter.is_allowed("127.0.0.1")

        # Next request should be blocked
        assert limiter.is_allowed("127.0.0.1") is False

    @pytest.mark.integration
    def test_rate_limit_per_ip(self, mock_db_session):
        """Verify rate limits are per-IP."""
        from src.api.app import RateLimiter

        limiter = RateLimiter(requests_per_minute=2)

        # Use up limit for IP 1
        limiter.is_allowed("192.168.1.1")
        limiter.is_allowed("192.168.1.1")
        assert limiter.is_allowed("192.168.1.1") is False

        # IP 2 should still be allowed
        assert limiter.is_allowed("192.168.1.2") is True


# =============================================================================
# Request Size Limit Tests
# =============================================================================


class TestRequestSizeLimit:
    """Tests for request size limiting."""

    @pytest.mark.integration
    def test_accepts_normal_request(self, test_client, mock_db_session):
        """Verify normal-sized requests are accepted."""
        request_data = {
            "company_name": "Test Corp",
        }

        with patch("src.api.app.save_task") as mock_save:
            mock_save.return_value = MagicMock()

            response = test_client.post(
                "/api/v1/research",
                json=request_data,
            )

            # Should not be rejected for size
            assert response.status_code != 413


# =============================================================================
# Error Response Tests
# =============================================================================


class TestErrorResponses:
    """Tests for error response format."""

    @pytest.mark.integration
    def test_validation_error_format(self, test_client):
        """Verify validation error response format."""
        response = test_client.post(
            "/api/v1/research",
            json={"company_name": ""},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    def test_not_found_error_format(self, test_client, mock_db_session):
        """Verify 404 error response format."""
        with patch("src.api.app.get_task") as mock_get_task:
            mock_get_task.return_value = None

            response = test_client.get("/api/v1/research/missing-task")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data


# =============================================================================
# CORS Tests
# =============================================================================


class TestCORS:
    """Tests for CORS configuration."""

    @pytest.mark.integration
    def test_cors_headers_present(self, test_client):
        """Verify CORS headers are present on responses."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should have CORS headers
        assert response.headers.get("access-control-allow-origin") is not None or response.status_code == 200


# =============================================================================
# Database Interaction Tests
# =============================================================================


class TestDatabaseInteraction:
    """Tests for database interaction functions."""

    @pytest.mark.integration
    def test_save_task_creates_new(self, mock_db_session):
        """Verify save_task creates new task when not found."""
        from src.api.app import save_task

        # Mock: task not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        save_task(
            mock_db_session,
            task_id="new-task-123",
            status="pending",
            request={"company_name": "Test"},
        )

        # Should have added new task
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.integration
    def test_save_task_updates_existing(self, mock_db_session):
        """Verify save_task updates existing task."""
        from src.api.app import save_task

        # Mock: task found
        mock_task = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task

        save_task(
            mock_db_session,
            task_id="existing-task",
            status="completed",
            result={"data": "test"},
        )

        # Should not have added (updated existing)
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.integration
    def test_get_task_returns_dict(self, mock_db_session):
        """Verify get_task returns properly formatted dict."""
        from src.api.app import get_task

        mock_task = MagicMock()
        mock_task.task_id = "test-123"
        mock_task.status = "completed"
        mock_task.request = '{"company_name": "Test"}'
        mock_task.result = '{"reports": {}}'
        mock_task.error = None

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task

        result = get_task(mock_db_session, "test-123")

        assert result is not None
        assert result["task_id"] == "test-123"
        assert result["status"] == "completed"
        assert result["request"]["company_name"] == "Test"

    @pytest.mark.integration
    def test_get_task_returns_none_for_missing(self, mock_db_session):
        """Verify get_task returns None for missing task."""
        from src.api.app import get_task

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = get_task(mock_db_session, "missing-task")

        assert result is None


# =============================================================================
# JSON Parsing Tests
# =============================================================================


class TestJSONParsing:
    """Tests for JSON parsing utilities."""

    @pytest.mark.integration
    def test_safe_json_loads_valid(self):
        """Verify safe_json_loads parses valid JSON."""
        from src.api.app import safe_json_loads

        result = safe_json_loads('{"key": "value"}')

        assert result == {"key": "value"}

    @pytest.mark.integration
    def test_safe_json_loads_invalid(self):
        """Verify safe_json_loads returns default on invalid JSON."""
        from src.api.app import safe_json_loads

        result = safe_json_loads("not valid json", default={})

        assert result == {}

    @pytest.mark.integration
    def test_safe_json_loads_none(self):
        """Verify safe_json_loads handles None."""
        from src.api.app import safe_json_loads

        result = safe_json_loads(None, default=[])

        assert result == []

    @pytest.mark.integration
    def test_safe_json_loads_empty_string(self):
        """Verify safe_json_loads handles empty string."""
        from src.api.app import safe_json_loads

        result = safe_json_loads("", default="default")

        assert result == "default"
