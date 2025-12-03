"""
Smoke tests for quick deployment verification.

These tests verify that core functionality works after deployment.
All smoke tests should complete in under 2 minutes total.
"""

import pytest
from pathlib import Path


# =============================================================================
# Import Smoke Tests - Verify modules can be imported
# =============================================================================


class TestImports:
    """Verify critical modules can be imported without errors."""

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_core_config(self):
        """Verify core config module imports."""
        from src.core.config import Settings, get_settings
        assert Settings is not None
        assert get_settings is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_ai_client(self):
        """Verify AI client module imports."""
        from src.core.ai.ai_client import (
            BaseAIClient,
            MockAIClient,
            AIClientManager,
        )
        assert BaseAIClient is not None
        assert MockAIClient is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_smart_router(self):
        """Verify smart router module imports."""
        from src.core.ai.routing.smart_router import SmartAIRouter
        assert SmartAIRouter is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_cache(self):
        """Verify cache module imports."""
        from src.core.cache import AICache, get_ai_cache
        assert AICache is not None
        assert get_ai_cache is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_api_app(self):
        """Verify API app module imports."""
        from src.api.app import app
        assert app is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_graph_builder(self):
        """Verify graph builder module imports."""
        from src.graph.graph_builder import build_graph
        assert build_graph is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_import_agents(self):
        """Verify agent modules import."""
        from src.agents.base_agent import BaseAgent
        from src.agents.factory import AgentFactory
        assert BaseAgent is not None
        assert AgentFactory is not None


# =============================================================================
# API Smoke Tests
# =============================================================================


class TestAPISmoke:
    """Smoke tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Get test client."""
        from fastapi.testclient import TestClient
        from src.api.app import app
        return TestClient(app)

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    def test_health_endpoint_responds(self, client):
        """Verify health endpoint responds with 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    def test_api_accepts_valid_request(self, client):
        """Verify API accepts valid research request format."""
        response = client.post(
            "/api/v1/research",
            json={
                "company_name": "Test Corp",
                "website": "https://testcorp.com"
            }
        )
        # Should either accept (200/202) or reject gracefully (4xx)
        # Should NOT return 500
        assert response.status_code != 500

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    def test_api_rejects_invalid_request(self, client):
        """Verify API rejects invalid request with 422."""
        response = client.post("/api/v1/research", json={})
        assert response.status_code == 422


# =============================================================================
# Configuration Smoke Tests
# =============================================================================


class TestConfigSmoke:
    """Smoke tests for configuration."""

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_settings_loads(self):
        """Verify settings can be loaded."""
        from src.core.config import get_settings, clear_settings
        clear_settings()
        settings = get_settings()
        assert settings is not None
        clear_settings()

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_settings_has_required_fields(self):
        """Verify settings has required fields."""
        from src.core.config import get_settings, clear_settings
        clear_settings()
        settings = get_settings()

        # Check required fields exist (may be None)
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'ai')
        assert hasattr(settings, 'BASE_DIR')
        clear_settings()

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_base_dir_exists(self):
        """Verify BASE_DIR points to valid directory."""
        from src.core.config import get_settings, clear_settings
        clear_settings()
        settings = get_settings()

        assert settings.BASE_DIR.exists()
        clear_settings()


# =============================================================================
# Mock AI Client Smoke Tests
# =============================================================================


class TestMockAISmoke:
    """Smoke tests for mock AI functionality."""

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_mock_client_generates_response(self):
        """Verify mock AI client can generate response."""
        from src.core.ai.ai_client import MockAIClient

        client = MockAIClient()
        response = await client.generate("Test prompt")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_mock_client_generates_json(self):
        """Verify mock AI client can generate JSON response."""
        import json
        from src.core.ai.ai_client import MockAIClient

        client = MockAIClient()
        response = await client.generate("Test prompt", response_format="json")

        assert response is not None
        # Should be valid JSON
        data = json.loads(response)
        assert isinstance(data, dict)


# =============================================================================
# Cache Smoke Tests
# =============================================================================


class TestCacheSmoke:
    """Smoke tests for caching functionality."""

    @pytest.mark.smoke
    @pytest.mark.timeout(10)
    def test_cache_can_set_and_get(self, tmp_path):
        """Verify cache can store and retrieve values."""
        from src.core.cache import AICache

        # Reset singleton for isolated test
        AICache._instance = None

        cache = AICache()
        cache.cache_dir = tmp_path / ".cache"
        cache.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set value
        cache.set("test prompt", "test response", "system", 0.7, 4096)

        # Get value
        result = cache.get("test prompt", "system", 0.7, 4096)

        assert result == "test response"

        # Cleanup
        AICache._instance = None


# =============================================================================
# File System Smoke Tests
# =============================================================================


class TestFileSystemSmoke:
    """Smoke tests for file system operations."""

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_project_structure_exists(self):
        """Verify expected project directories exist."""
        from src.core.config import get_settings, clear_settings
        clear_settings()
        settings = get_settings()
        base = settings.BASE_DIR

        expected_dirs = [
            base / "src",
            base / "src" / "core",
            base / "src" / "agents",
            base / "src" / "tools",
            base / "src" / "api",
            base / "tests",
        ]

        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Missing directory: {dir_path}"

        clear_settings()

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_templates_directory_exists(self):
        """Verify templates directory exists."""
        from src.core.config import get_settings, clear_settings
        clear_settings()
        settings = get_settings()

        templates_dir = settings.BASE_DIR / "src" / "templates"
        assert templates_dir.exists(), "Templates directory missing"
        clear_settings()


# =============================================================================
# Dependency Smoke Tests
# =============================================================================


class TestDependencySmoke:
    """Smoke tests for critical dependencies."""

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_pydantic_available(self):
        """Verify Pydantic is available."""
        from pydantic import BaseModel
        assert BaseModel is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_fastapi_available(self):
        """Verify FastAPI is available."""
        from fastapi import FastAPI
        assert FastAPI is not None

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_langraph_available(self):
        """Verify LangGraph is available."""
        try:
            from langgraph.graph import StateGraph
            assert StateGraph is not None
        except ImportError:
            pytest.skip("LangGraph not installed")

    @pytest.mark.smoke
    @pytest.mark.timeout(5)
    def test_asyncio_available(self):
        """Verify asyncio is available."""
        import asyncio
        assert asyncio is not None
