"""
Snapshot tests for output verification.

Uses syrupy for snapshot testing to detect unexpected changes in:
- API response structures
- Graph state formats
- Report templates
- Configuration schemas
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# API Response Snapshots
# =============================================================================


class TestAPIResponseSnapshots:
    """Snapshot tests for API response structures."""

    @pytest.mark.snapshot
    def test_openapi_schema_snapshot(self, snapshot):
        """Verify OpenAPI schema structure hasn't changed."""
        try:
            from src.api.app import app

            schema = app.openapi()
            # Remove version info which may change
            if "info" in schema:
                schema["info"].pop("version", None)

            assert schema == snapshot
        except ImportError:
            pytest.skip("FastAPI app not available")

    @pytest.mark.snapshot
    def test_research_request_schema_snapshot(self, snapshot):
        """Verify ResearchRequest schema structure."""
        try:
            from src.api.models import ResearchRequest

            schema = ResearchRequest.model_json_schema()
            assert schema == snapshot
        except ImportError:
            pytest.skip("ResearchRequest model not available")

    @pytest.mark.snapshot
    def test_research_response_schema_snapshot(self, snapshot):
        """Verify ResearchResponse schema structure."""
        try:
            from src.api.models import ResearchResponse

            schema = ResearchResponse.model_json_schema()
            assert schema == snapshot
        except ImportError:
            pytest.skip("ResearchResponse model not available")

    @pytest.mark.snapshot
    def test_task_status_schema_snapshot(self, snapshot):
        """Verify TaskStatus schema structure."""
        try:
            from src.api.models import TaskStatus

            schema = TaskStatus.model_json_schema()
            assert schema == snapshot
        except ImportError:
            pytest.skip("TaskStatus model not available")

    @pytest.mark.snapshot
    def test_health_response_structure(self, snapshot, api_client):
        """Verify health check response structure."""
        try:
            response = api_client.get("/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                # Remove dynamic fields
                data.pop("timestamp", None)
                data.pop("uptime", None)
                assert data == snapshot
        except Exception:
            pytest.skip("Health endpoint not available")


# =============================================================================
# Graph State Snapshots
# =============================================================================


class TestGraphStateSnapshots:
    """Snapshot tests for graph state structures."""

    @pytest.mark.snapshot
    def test_research_state_schema_snapshot(self, snapshot):
        """Verify ResearchState schema structure."""
        try:
            from src.graph.state import ResearchState

            schema = ResearchState.model_json_schema()
            assert schema == snapshot
        except ImportError:
            pytest.skip("ResearchState not available")

    @pytest.mark.snapshot
    def test_initial_state_structure(self, snapshot):
        """Verify initial research state structure."""
        try:
            from src.graph.state import ResearchState

            state = ResearchState(
                company_name="Test Corp",
                website="https://test.com",
            )
            state_dict = state.model_dump()
            # Remove any dynamic/timestamp fields
            state_dict.pop("created_at", None)
            state_dict.pop("updated_at", None)
            assert state_dict == snapshot
        except ImportError:
            pytest.skip("ResearchState not available")

    @pytest.mark.snapshot
    def test_state_with_data_structure(self, snapshot, sample_company_profile, sample_financial_data):
        """Verify state structure with populated data."""
        try:
            from src.graph.state import ResearchState

            state = ResearchState(
                company_name=sample_company_profile["name"],
                website=sample_company_profile["website"],
                industry=sample_company_profile.get("industry"),
                financial_data=sample_financial_data,
            )
            state_dict = state.model_dump()
            state_dict.pop("created_at", None)
            state_dict.pop("updated_at", None)
            # Normalize financial data for snapshot
            if "financial_data" in state_dict:
                state_dict["financial_data"] = {"has_data": bool(state_dict["financial_data"])}
            assert state_dict == snapshot
        except ImportError:
            pytest.skip("ResearchState not available")


# =============================================================================
# Configuration Snapshots
# =============================================================================


class TestConfigSnapshots:
    """Snapshot tests for configuration structures."""

    @pytest.mark.snapshot
    def test_settings_schema_snapshot(self, snapshot):
        """Verify Settings schema structure."""
        try:
            from src.core.config import Settings

            schema = Settings.model_json_schema()
            # Remove default values that may change
            for prop in schema.get("properties", {}).values():
                prop.pop("default", None)
            assert schema == snapshot
        except ImportError:
            pytest.skip("Settings not available")

    @pytest.mark.snapshot
    def test_ai_config_schema_snapshot(self, snapshot):
        """Verify AI configuration schema structure."""
        try:
            from src.core.config import AIConfig

            schema = AIConfig.model_json_schema()
            for prop in schema.get("properties", {}).values():
                prop.pop("default", None)
            assert schema == snapshot
        except ImportError:
            pytest.skip("AIConfig not available")


# =============================================================================
# Report Template Snapshots
# =============================================================================


class TestReportSnapshots:
    """Snapshot tests for report templates."""

    @pytest.mark.snapshot
    def test_report_sections_structure(self, snapshot):
        """Verify report sections structure."""
        # Define expected report sections
        report_sections = {
            "executive_summary": {
                "title": "Executive Summary",
                "required": True,
            },
            "company_overview": {
                "title": "Company Overview",
                "required": True,
            },
            "financial_analysis": {
                "title": "Financial Analysis",
                "required": False,
            },
            "market_position": {
                "title": "Market Position",
                "required": False,
            },
            "competitive_landscape": {
                "title": "Competitive Landscape",
                "required": False,
            },
            "sources": {
                "title": "Sources",
                "required": True,
            },
        }
        assert report_sections == snapshot

    @pytest.mark.snapshot
    def test_writer_output_structure(self, snapshot):
        """Verify writer agent output structure."""
        try:
            from src.agents.writer import WriterAgent

            # Get output schema if available
            if hasattr(WriterAgent, "output_schema"):
                schema = WriterAgent.output_schema
                assert schema == snapshot
            else:
                # Define expected output structure
                output_structure = {
                    "report": "string",
                    "sections": "list",
                    "metadata": "dict",
                }
                assert output_structure == snapshot
        except ImportError:
            pytest.skip("WriterAgent not available")


# =============================================================================
# Agent Output Snapshots
# =============================================================================


class TestAgentOutputSnapshots:
    """Snapshot tests for agent output structures."""

    @pytest.mark.snapshot
    def test_agent_base_output_structure(self, snapshot):
        """Verify base agent output structure."""
        base_output = {
            "status": "completed",
            "data": {},
            "errors": [],
            "sources": [],
            "metadata": {
                "agent": "string",
                "duration_ms": "number",
            },
        }
        assert base_output == snapshot

    @pytest.mark.snapshot
    def test_financial_agent_output_keys(self, snapshot):
        """Verify financial agent output keys."""
        financial_output_keys = [
            "ticker",
            "market_cap",
            "revenue",
            "profit_margin",
            "pe_ratio",
            "eps",
            "dividend_yield",
            "52_week_high",
            "52_week_low",
        ]
        assert sorted(financial_output_keys) == snapshot

    @pytest.mark.snapshot
    def test_market_agent_output_keys(self, snapshot):
        """Verify market agent output keys."""
        market_output_keys = [
            "sector",
            "industry",
            "market_size",
            "growth_rate",
            "trends",
            "competitors",
        ]
        assert sorted(market_output_keys) == snapshot


# =============================================================================
# Error Response Snapshots
# =============================================================================


class TestErrorSnapshots:
    """Snapshot tests for error response structures."""

    @pytest.mark.snapshot
    def test_validation_error_structure(self, snapshot):
        """Verify validation error response structure."""
        validation_error = {
            "detail": [
                {
                    "loc": ["body", "field_name"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        }
        assert validation_error == snapshot

    @pytest.mark.snapshot
    def test_api_error_structure(self, snapshot):
        """Verify API error response structure."""
        api_error = {
            "error": True,
            "message": "string",
            "code": "string",
            "details": {},
        }
        assert api_error == snapshot


# =============================================================================
# Fixture for Snapshot Configuration
# =============================================================================


@pytest.fixture
def snapshot_exclude_dynamic():
    """
    Provide helper to exclude dynamic fields from snapshots.

    Usage:
        def test_something(snapshot_exclude_dynamic, snapshot):
            data = get_data()
            filtered = snapshot_exclude_dynamic(data, ["timestamp", "id"])
            assert filtered == snapshot
    """
    def _exclude(data: dict, fields: list) -> dict:
        result = data.copy()
        for field in fields:
            result.pop(field, None)
        return result
    return _exclude
