"""
Shared pytest fixtures for the Company Researcher test suite.

This module provides common fixtures used across unit, integration, and manual tests.
"""

import os
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Environment & Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory, creating it if needed."""
    test_data = project_root / "tests" / "data"
    test_data.mkdir(parents=True, exist_ok=True)
    return test_data


@pytest.fixture(scope="function")
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary output directory for test outputs."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture(scope="session")
def env_vars() -> dict:
    """Return commonly used environment variables for testing."""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-key"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", "test-key"),
        "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY", "test-key"),
    }


# ============================================================================
# Mock AI Client Fixtures
# ============================================================================


@pytest.fixture
def mock_ai_client() -> MagicMock:
    """Provide a mock AI client for testing without API calls."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock AI response")
    client.generate_structured = AsyncMock(return_value={"key": "value"})
    return client


@pytest.fixture
def mock_search_tool() -> MagicMock:
    """Provide a mock search tool for testing without web requests."""
    tool = MagicMock()
    tool.search = AsyncMock(
        return_value=[
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "content": "Test content 1",
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/2",
                "content": "Test content 2",
            },
        ]
    )
    return tool


@pytest.fixture
def mock_browser_tool() -> MagicMock:
    """Provide a mock browser tool for testing without web requests."""
    tool = MagicMock()
    tool.fetch_content = AsyncMock(
        return_value={
            "url": "https://example.com",
            "title": "Test Page",
            "content": "Test page content for testing purposes.",
            "status": 200,
        }
    )
    return tool


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_company_profile() -> dict:
    """Provide a sample company profile for testing."""
    return {
        "name": "Test Corp",
        "website": "https://testcorp.com",
        "industry": "Technology",
        "country": "USA",
        "description": "A test company for unit testing purposes.",
        "target_audience": "Developers and engineers",
        "competitors": ["Competitor A", "Competitor B"],
    }


@pytest.fixture
def sample_research_sources() -> list:
    """Provide sample research sources for testing."""
    return [
        {
            "url": "https://example.com/article1",
            "title": "Industry Analysis Report",
            "content": "Detailed analysis of the technology industry...",
            "source_type": "article",
            "category": "market_intelligence",
            "reliability_score": 0.85,
        },
        {
            "url": "https://example.com/article2",
            "title": "Company Overview",
            "content": "Test Corp was founded in 2020...",
            "source_type": "company_page",
            "category": "company_info",
            "reliability_score": 0.95,
        },
    ]


@pytest.fixture
def sample_financial_data() -> dict:
    """Provide sample financial data for testing."""
    return {
        "ticker": "TEST",
        "basic_info": {
            "name": "Test Corp",
            "sector": "Technology",
            "industry": "Software",
        },
        "market_data": {
            "market_cap": 1000000000,
            "current_price": 150.00,
            "52_week_high": 180.00,
            "52_week_low": 100.00,
        },
        "financials": {
            "revenue": 500000000,
            "net_income": 50000000,
            "profit_margin": 0.10,
        },
        "employees": 1000,
    }


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture
def api_client():
    """Provide a FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.api.app import app

    return TestClient(app)


# ============================================================================
# Graph State Fixtures
# ============================================================================


@pytest.fixture
def initial_research_state(sample_company_profile: dict) -> dict:
    """Provide an initial research state for graph testing."""
    return {
        "company_name": sample_company_profile["name"],
        "website": sample_company_profile["website"],
        "industry": sample_company_profile.get("industry"),
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
    }


# ============================================================================
# Async Fixtures
# ============================================================================


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Markers for Test Categories
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, may use external services)"
    )
    config.addinivalue_line(
        "markers", "manual: marks tests that require manual verification or setup"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require real API keys"
    )
