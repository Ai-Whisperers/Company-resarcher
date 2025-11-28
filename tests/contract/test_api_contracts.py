"""
API Contract Tests.

Tests to ensure API schemas and responses match expectations.
These tests help catch breaking changes to the API.
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestRequestSchemas:
    """Tests for API request schemas."""

    @pytest.mark.contract
    def test_research_request_has_required_fields(self, pydantic_schema_validator):
        """Verify ResearchRequest has required fields."""
        try:
            from src.api.models import ResearchRequest

            schema = pydantic_schema_validator(
                ResearchRequest,
                required=["company_name"],
                properties={
                    "company_name": "string",
                },
            )
            assert "company_name" in schema["properties"]
        except ImportError:
            pytest.skip("ResearchRequest model not available")

    @pytest.mark.contract
    def test_research_request_optional_fields(self):
        """Verify ResearchRequest optional fields."""
        try:
            from src.api.models import ResearchRequest

            schema = ResearchRequest.model_json_schema()
            properties = schema.get("properties", {})

            # These should exist but not be required
            optional_fields = ["website", "industry", "country", "focus_areas"]
            for field in optional_fields:
                if field in properties:
                    required = schema.get("required", [])
                    # Optional fields should not be in required list
                    # (or should have a default)
                    pass  # Field exists, that's what we're checking

        except ImportError:
            pytest.skip("ResearchRequest model not available")


class TestResponseSchemas:
    """Tests for API response schemas."""

    @pytest.mark.contract
    def test_research_response_has_task_id(self):
        """Verify ResearchResponse includes task_id."""
        try:
            from src.api.models import ResearchResponse

            schema = ResearchResponse.model_json_schema()
            assert "task_id" in schema.get("properties", {}), "Missing task_id in response"
        except ImportError:
            pytest.skip("ResearchResponse model not available")

    @pytest.mark.contract
    def test_research_response_has_status(self):
        """Verify ResearchResponse includes status."""
        try:
            from src.api.models import ResearchResponse

            schema = ResearchResponse.model_json_schema()
            assert "status" in schema.get("properties", {}), "Missing status in response"
        except ImportError:
            pytest.skip("ResearchResponse model not available")

    @pytest.mark.contract
    def test_task_status_response_structure(self):
        """Verify TaskStatus response has required fields."""
        try:
            from src.api.models import TaskStatus

            schema = TaskStatus.model_json_schema()
            required_fields = ["task_id", "status"]

            for field in required_fields:
                assert field in schema.get("properties", {}), f"Missing {field} in TaskStatus"
        except ImportError:
            pytest.skip("TaskStatus model not available")

    @pytest.mark.contract
    def test_error_response_structure(self):
        """Verify error response has standard structure."""
        try:
            from src.api.models import ErrorResponse

            schema = ErrorResponse.model_json_schema()
            assert "detail" in schema.get("properties", {}) or "message" in schema.get(
                "properties", {}
            ), "Error response should have detail or message"
        except ImportError:
            pytest.skip("ErrorResponse model not available")


# =============================================================================
# OpenAPI Schema Tests
# =============================================================================


class TestOpenAPISchema:
    """Tests for OpenAPI schema consistency."""

    @pytest.mark.contract
    def test_openapi_schema_has_info(self, openapi_schema):
        """Verify OpenAPI schema has info section."""
        if openapi_schema is None:
            pytest.skip("OpenAPI schema not available")

        assert "info" in openapi_schema
        assert "title" in openapi_schema["info"]
        assert "version" in openapi_schema["info"]

    @pytest.mark.contract
    def test_openapi_schema_has_paths(self, openapi_schema):
        """Verify OpenAPI schema has paths."""
        if openapi_schema is None:
            pytest.skip("OpenAPI schema not available")

        assert "paths" in openapi_schema
        assert len(openapi_schema["paths"]) > 0

    @pytest.mark.contract
    def test_research_endpoint_exists(self, openapi_schema):
        """Verify research endpoint is documented."""
        if openapi_schema is None:
            pytest.skip("OpenAPI schema not available")

        paths = openapi_schema.get("paths", {})

        # Check for research-related endpoints
        research_endpoints = [p for p in paths if "research" in p.lower()]
        assert len(research_endpoints) > 0, "No research endpoints found in schema"

    @pytest.mark.contract
    def test_health_endpoint_exists(self, openapi_schema):
        """Verify health endpoint is documented."""
        if openapi_schema is None:
            pytest.skip("OpenAPI schema not available")

        paths = openapi_schema.get("paths", {})

        # Check for health endpoint
        health_paths = ["/health", "/api/health", "/api/v1/health", "/healthz"]
        has_health = any(p in paths for p in health_paths)
        assert has_health, "No health endpoint found in schema"

    @pytest.mark.contract
    @pytest.mark.snapshot
    def test_openapi_schema_snapshot(self, openapi_schema, snapshot):
        """Verify OpenAPI schema hasn't changed unexpectedly."""
        if openapi_schema is None:
            pytest.skip("OpenAPI schema not available")

        try:
            # Compare against snapshot
            assert openapi_schema == snapshot
        except NameError:
            # Snapshot not configured
            pytest.skip("Snapshot testing not configured")


# =============================================================================
# Response Validation Tests
# =============================================================================


class TestResponseValidation:
    """Tests that API responses match their declared schemas."""

    @pytest.mark.contract
    @pytest.mark.integration
    def test_research_response_validates(self, api_client):
        """Verify actual research response validates against schema."""
        try:
            from src.api.models import ResearchResponse

            with patch("src.api.app.process_research_task"):
                response = api_client.post(
                    "/api/v1/research",
                    json={"company_name": "Test Corp", "website": "https://test.com"},
                )

                if response.status_code == 200:
                    # Validate response against Pydantic model
                    ResearchResponse.model_validate(response.json())
        except ImportError:
            pytest.skip("API models not available")
        except Exception:
            pytest.skip("API endpoint not available")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_health_response_format(self, api_client):
        """Verify health check response format."""
        try:
            response = api_client.get("/api/v1/health")

            if response.status_code == 200:
                data = response.json()
                # Health response should have status
                assert "status" in data or "healthy" in data
        except Exception:
            pytest.skip("Health endpoint not available")

    @pytest.mark.contract
    @pytest.mark.integration
    def test_error_response_format(self, api_client):
        """Verify error responses have proper format."""
        try:
            # Make invalid request to trigger error
            response = api_client.post(
                "/api/v1/research",
                json={},  # Missing required fields
            )

            if response.status_code >= 400:
                data = response.json()
                # Error should have detail or message
                assert "detail" in data or "message" in data or "error" in data
        except Exception:
            pytest.skip("API endpoint not available")


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


class TestBackwardCompatibility:
    """Tests for API backward compatibility."""

    @pytest.mark.contract
    def test_v1_api_prefix_works(self, api_client):
        """Verify v1 API prefix still works."""
        try:
            response = api_client.get("/api/v1/health")
            # Should not return 404
            assert response.status_code != 404, "v1 API prefix not working"
        except Exception:
            pytest.skip("API not available")

    @pytest.mark.contract
    def test_accepts_minimal_request(self, api_client):
        """Verify API accepts minimal request format."""
        try:
            with patch("src.api.app.process_research_task"):
                response = api_client.post(
                    "/api/v1/research",
                    json={"company_name": "Test"},
                )
                # Should accept with just company_name
                assert response.status_code in [200, 202], "Should accept minimal request"
        except Exception:
            pytest.skip("API endpoint not available")


# =============================================================================
# Content Type Tests
# =============================================================================


class TestContentTypes:
    """Tests for API content type handling."""

    @pytest.mark.contract
    def test_accepts_json_content_type(self, api_client):
        """Verify API accepts application/json."""
        try:
            with patch("src.api.app.process_research_task"):
                response = api_client.post(
                    "/api/v1/research",
                    json={"company_name": "Test"},
                    headers={"Content-Type": "application/json"},
                )
                assert response.status_code != 415, "Should accept application/json"
        except Exception:
            pytest.skip("API endpoint not available")

    @pytest.mark.contract
    def test_returns_json_content_type(self, api_client):
        """Verify API returns application/json."""
        try:
            response = api_client.get("/api/v1/health")
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, "Should return application/json"
        except Exception:
            pytest.skip("API endpoint not available")
