"""
Integration test fixtures and configuration.

Provides fixtures specific to integration testing, including
mocked external services and database setups.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Create a mock database session for integration tests."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.add = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.close = MagicMock()
    return mock_session


@pytest.fixture
def test_database(tmp_path):
    """Create a temporary SQLite database for testing."""
    db_path = tmp_path / "test.db"
    yield str(db_path)
    # Cleanup is handled by tmp_path


# =============================================================================
# API Client Fixtures
# =============================================================================


@pytest.fixture
def integration_test_client(mock_db_session):
    """
    Create a test client with mocked external services.

    This client mocks:
    - Database session
    - Rate limiter
    - AI providers
    - Search providers
    """
    with patch("src.api.app.get_db") as mock_get_db:
        with patch("src.api.app.rate_limiter") as mock_limiter:
            with patch("src.api.database.engine"):
                with patch("src.api.database.Base"):
                    mock_get_db.return_value = mock_db_session
                    mock_limiter.is_allowed.return_value = True

                    from fastapi.testclient import TestClient
                    from src.api.app import app

                    client = TestClient(app, raise_server_exceptions=False)
                    yield client


# =============================================================================
# Graph Fixtures
# =============================================================================


@pytest.fixture
def mock_graph_state():
    """Create a mock research graph state."""
    return {
        "company_name": "Integration Test Corp",
        "website": "https://integration-test.com",
        "industry": "Technology",
        "country": "USA",
        "raw_data": {},
        "source_log": [],
        "financial_data": {},
        "market_data": {},
        "sales_data": {},
        "competitor_data": {},
        "brand_data": {},
        "drafts": {},
        "errors": [],
        "iteration": 0,
        "max_iterations": 3,
    }


@pytest.fixture
def mock_graph_with_all_agents(mock_graph_state):
    """Create a mock graph with all agents mocked."""
    from tests.mocks import MockOpenAIClient

    ai_client = MockOpenAIClient(
        default_response="Mocked agent response for integration testing"
    )

    with patch("src.agents.base_agent.get_ai_client", return_value=ai_client):
        with patch("src.tools.search.TavilyClient") as mock_tavily:
            mock_tavily.return_value.search.return_value = {
                "results": [
                    {"title": "Test Result", "url": "https://example.com", "content": "Test"},
                ]
            }
            yield {
                "state": mock_graph_state,
                "ai_client": ai_client,
                "search_client": mock_tavily,
            }


# =============================================================================
# External Service Fixtures
# =============================================================================


@pytest.fixture
def mock_external_apis():
    """Mock all external API calls for isolated testing."""
    from tests.mocks import (
        MockOpenAIClient,
        MockTavilyClient,
        MockBrowserTool,
    )

    patches = [
        patch("openai.AsyncOpenAI", return_value=MockOpenAIClient()),
        patch("tavily.TavilyClient", return_value=MockTavilyClient()),
        patch("src.tools.browser.BrowserTool", return_value=MockBrowserTool()),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


# =============================================================================
# File System Fixtures
# =============================================================================


@pytest.fixture
def integration_output_dir(tmp_path):
    """Create a temporary output directory for integration tests."""
    output_dir = tmp_path / "integration_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup handled by tmp_path


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing file operations."""
    files = {}

    # Create sample PDF placeholder
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    files["pdf"] = pdf_path

    # Create sample HTML
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body><h1>Test</h1></body></html>")
    files["html"] = html_path

    # Create sample JSON
    json_path = tmp_path / "sample.json"
    json_path.write_text('{"key": "value", "items": [1, 2, 3]}')
    files["json"] = json_path

    # Create sample text
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("Sample text content for testing")
    files["txt"] = txt_path

    return files


# =============================================================================
# Task Fixtures
# =============================================================================


@pytest.fixture
def sample_task():
    """Create a sample research task."""
    return {
        "task_id": "integration-test-task-001",
        "status": "pending",
        "request": {
            "company_name": "Integration Corp",
            "website": "https://integration-corp.com",
            "industry": "Technology",
        },
        "result": None,
        "error": None,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
    }


@pytest.fixture
def completed_task(sample_task):
    """Create a completed research task."""
    return {
        **sample_task,
        "status": "completed",
        "result": {
            "reports": {
                "executive_summary": "Test executive summary",
                "market_analysis": "Test market analysis",
            },
            "metadata": {
                "sources_count": 10,
                "duration_seconds": 120,
            },
        },
    }


# =============================================================================
# Concurrency Fixtures
# =============================================================================


@pytest.fixture
def concurrent_test_config():
    """Configuration for concurrency tests."""
    return {
        "num_concurrent_requests": 10,
        "request_timeout": 30,
        "expected_completion_rate": 0.9,  # 90% should complete
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def integration_cleanup():
    """Cleanup after each integration test."""
    yield
    # Add any necessary cleanup code here
    pass
