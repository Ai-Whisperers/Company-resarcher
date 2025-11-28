"""
Shared pytest fixtures for the Company Researcher test suite.

This module provides common fixtures used across unit, integration, and manual tests.
Includes comprehensive mocking strategy, factory fixtures, and assertion helpers.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

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
# Settings Fixtures
# ============================================================================


@pytest.fixture
def mock_settings():
    """
    Provide mock settings for testing without real configuration.

    Usage:
        def test_something(mock_settings):
            mock_settings.OPENAI_API_KEY = "test-key"
            # Test code that uses settings
    """
    settings = MagicMock()
    settings.OPENAI_API_KEY = None
    settings.ANTHROPIC_API_KEY = None
    settings.GEMINI_API_KEY = None
    settings.GROQ_API_KEY = None
    settings.TAVILY_API_KEY = None
    settings.ai.primary = "openai"
    settings.ai.fallback = None
    settings.ai.openai.model = "gpt-4"
    settings.ai.anthropic.model = "claude-3"
    settings.BASE_DIR = PROJECT_ROOT
    settings.MAX_SEARCH_RESULTS = 5
    settings.CONCURRENT_SEARCHES = 3
    return settings


@pytest.fixture
def reset_settings():
    """
    Reset the settings cache before and after a test.

    Usage:
        def test_settings_change(reset_settings):
            # Test modifies settings
            pass
            # Settings are reset after test
    """
    from src.core.config import clear_settings
    clear_settings()
    yield
    clear_settings()


# ============================================================================
# AI Client Fixtures
# ============================================================================


@pytest.fixture
def mock_openai_response():
    """
    Provide a mock OpenAI API response structure.

    Usage:
        def test_openai(mock_openai_response):
            mock_openai_response.choices[0].message.content = "custom response"
    """
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Test response from OpenAI"
    response.usage.total_tokens = 100
    return response


@pytest.fixture
def mock_anthropic_response():
    """
    Provide a mock Anthropic API response structure.

    Usage:
        def test_anthropic(mock_anthropic_response):
            mock_anthropic_response.content[0].text = "custom response"
    """
    response = MagicMock()
    response.content = [MagicMock()]
    response.content[0].text = "Test response from Anthropic"
    return response


# ============================================================================
# Cache Fixtures
# ============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path):
    """
    Provide a temporary cache directory for testing.

    Usage:
        def test_caching(temp_cache_dir):
            cache = AICache()
            cache.cache_dir = temp_cache_dir
    """
    cache_dir = tmp_path / ".cache" / "ai_responses"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def reset_cache_singleton():
    """Reset the AICache singleton for isolated testing."""
    from src.core.cache import AICache
    original = AICache._instance
    AICache._instance = None
    yield
    AICache._instance = original


# ============================================================================
# Response Factories
# ============================================================================


class MockResponseFactory:
    """Factory for creating mock responses."""

    @staticmethod
    def ai_response(content: str = "Test AI response", tokens: int = 100) -> dict:
        """Create a mock AI response."""
        return {
            "content": content,
            "usage": {"total_tokens": tokens},
        }

    @staticmethod
    def search_results(count: int = 5) -> list:
        """Create mock search results."""
        return [
            {
                "title": f"Search Result {i}",
                "url": f"https://example.com/result/{i}",
                "content": f"Content for result {i}. This is sample text.",
                "score": 0.9 - (i * 0.1),
            }
            for i in range(count)
        ]

    @staticmethod
    def browser_response(url: str = "https://example.com", status: int = 200) -> dict:
        """Create a mock browser response."""
        return {
            "url": url,
            "title": "Test Page Title",
            "content": "This is the page content extracted from the URL.",
            "status": status,
            "headers": {"content-type": "text/html"},
        }

    @staticmethod
    def error_response(message: str = "An error occurred") -> dict:
        """Create a mock error response."""
        return {
            "error": True,
            "message": message,
            "status": "error",
        }


@pytest.fixture
def response_factory():
    """Provide the MockResponseFactory for creating test responses."""
    return MockResponseFactory()


# ============================================================================
# Edge Case Data Fixtures
# ============================================================================


@pytest.fixture(params=[
    "",                          # Empty string
    "   ",                       # Whitespace only
    "A",                         # Single character
    "A" * 10000,                 # Very long string
    "Test\nWith\nNewlines",      # Newlines
    "Test\tWith\tTabs",          # Tabs
    "测试中文",                    # Chinese
    "مرحبا",                      # Arabic
    "🚀🎉💻",                      # Emojis
    "<script>alert(1)</script>", # XSS attempt
    "'; DROP TABLE users; --",   # SQL injection attempt
])
def edge_case_string(request):
    """
    Provide various edge case strings for boundary testing.

    Usage:
        def test_handles_edge_cases(edge_case_string):
            result = process_string(edge_case_string)
            assert result is not None
    """
    return request.param


@pytest.fixture(params=[
    0,
    -1,
    1,
    100,
    1000000,
    float("inf"),
])
def edge_case_number(request):
    """Provide various edge case numbers for boundary testing."""
    return request.param


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
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests (quick verification)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "regression: marks tests as regression tests"
    )
    config.addinivalue_line(
        "markers", "concurrent: marks tests that test concurrency"
    )


# ============================================================================
# Auto-marking based on directory
# ============================================================================


def pytest_collection_modifyitems(items):
    """Auto-mark tests based on their directory location."""
    for item in items:
        # Get the test file path
        test_path = str(item.fspath)

        # Auto-add markers based on directory
        if "/unit/" in test_path or "\\unit\\" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path or "\\integration\\" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in test_path or "\\e2e\\" in test_path:
            item.add_marker(pytest.mark.e2e)
        elif "/smoke/" in test_path or "\\smoke\\" in test_path:
            item.add_marker(pytest.mark.smoke)
        elif "/manual/" in test_path or "\\manual\\" in test_path:
            item.add_marker(pytest.mark.manual)


# ============================================================================
# Comprehensive Mock Fixtures (from tests/mocks.py)
# ============================================================================


@pytest.fixture
def mock_openai_client():
    """
    Provide a comprehensive mock OpenAI client.

    Usage:
        def test_with_openai(mock_openai_client):
            mock_openai_client.default_response = "Custom response"
            result = await function_under_test()
    """
    from tests.mocks import MockOpenAIClient
    return MockOpenAIClient()


@pytest.fixture
def mock_anthropic_client():
    """Provide a comprehensive mock Anthropic client."""
    from tests.mocks import MockAnthropicClient
    return MockAnthropicClient()


@pytest.fixture
def mock_tavily_client():
    """Provide a mock Tavily search client."""
    from tests.mocks import MockTavilyClient
    return MockTavilyClient()


@pytest.fixture
def mock_browser():
    """Provide a mock browser tool."""
    from tests.mocks import MockBrowserTool
    return MockBrowserTool()


@pytest.fixture
def mock_cache():
    """Provide a mock cache."""
    from tests.mocks import MockCache
    return MockCache()


@pytest.fixture
def mock_database():
    """Provide a mock database."""
    from tests.mocks import MockDatabase
    return MockDatabase()


@pytest.fixture
def mock_rate_limiter():
    """Provide a mock rate limiter."""
    from tests.mocks import MockRateLimiter
    return MockRateLimiter()


@pytest.fixture
def mock_all_services():
    """
    Mock all external services at once.

    Usage:
        def test_isolated(mock_all_services):
            # All external calls are mocked
            result = await run_full_workflow()
    """
    from tests.mocks import mock_all_external_services
    with mock_all_external_services() as mocks:
        yield mocks


# ============================================================================
# Factory Fixtures (from tests/factories.py)
# ============================================================================


@pytest.fixture
def company_factory():
    """Provide CompanyFactory for generating test companies."""
    from tests.factories import CompanyFactory
    return CompanyFactory


@pytest.fixture
def financial_factory():
    """Provide FinancialDataFactory for generating test financial data."""
    from tests.factories import FinancialDataFactory
    return FinancialDataFactory


@pytest.fixture
def search_result_factory():
    """Provide SearchResultFactory for generating test search results."""
    from tests.factories import SearchResultFactory
    return SearchResultFactory


@pytest.fixture
def ai_response_factory():
    """Provide AIResponseFactory for generating test AI responses."""
    from tests.factories import AIResponseFactory
    return AIResponseFactory


@pytest.fixture
def edge_case_generator():
    """Provide EdgeCaseGenerator for generating edge case test data."""
    from tests.factories import EdgeCaseGenerator
    return EdgeCaseGenerator


# ============================================================================
# Singleton Reset Fixtures
# ============================================================================


@pytest.fixture(autouse=False)
def reset_all_singletons():
    """
    Reset all singleton instances for isolated testing.

    Use this fixture when tests modify global state.
    """
    # Store original instances
    originals = {}

    try:
        from src.core.ai_client import AIClient
        if hasattr(AIClient, '_instance'):
            originals['AIClient'] = AIClient._instance
            AIClient._instance = None
    except ImportError:
        pass

    try:
        from src.core.smart_router import SmartRouter
        if hasattr(SmartRouter, '_instance'):
            originals['SmartRouter'] = SmartRouter._instance
            SmartRouter._instance = None
    except ImportError:
        pass

    yield

    # Restore originals
    try:
        from src.core.ai_client import AIClient
        if 'AIClient' in originals:
            AIClient._instance = originals['AIClient']
    except ImportError:
        pass

    try:
        from src.core.smart_router import SmartRouter
        if 'SmartRouter' in originals:
            SmartRouter._instance = originals['SmartRouter']
    except ImportError:
        pass


# ============================================================================
# Test Isolation Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    """
    Isolate test environment by setting fake API keys.

    This prevents accidental real API calls in tests.
    """
    from tests.constants import (
        TEST_OPENAI_API_KEY,
        TEST_TAVILY_API_KEY,
        TEST_ANTHROPIC_API_KEY,
    )

    # Set fake API keys to prevent real calls
    monkeypatch.setenv("OPENAI_API_KEY", TEST_OPENAI_API_KEY)
    monkeypatch.setenv("TAVILY_API_KEY", TEST_TAVILY_API_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", TEST_ANTHROPIC_API_KEY)


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Ensure temporary files are cleaned up after each test."""
    yield
    # tmp_path is automatically cleaned by pytest


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """
    Provide an isolated cache directory for testing.

    Prevents test pollution from shared cache.
    """
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("CACHE_DIR", str(cache_dir))
    return cache_dir


# ============================================================================
# VCR Configuration (for HTTP recording)
# ============================================================================


@pytest.fixture(scope="module")
def vcr_config():
    """
    Configure VCR for HTTP recording and playback.

    Usage:
        @pytest.mark.vcr()
        def test_external_api(vcr_config):
            response = requests.get("https://api.example.com/data")
            assert response.status_code == 200
    """
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "api-key",
            "openai-api-key",
        ],
        "filter_query_parameters": [
            "api_key",
            "apiKey",
            "key",
        ],
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "decode_compressed_response": True,
    }


@pytest.fixture
def vcr_cassette_dir(request):
    """Return the directory for VCR cassettes based on test file location."""
    test_file = Path(request.fspath)
    return test_file.parent / "cassettes"


# ============================================================================
# Flaky Test Support
# ============================================================================


@pytest.fixture
def retry_config():
    """
    Configuration for flaky test retries.

    Usage:
        @pytest.mark.flaky(reruns=3, reruns_delay=2)
        def test_flaky_external_call(retry_config):
            # Test that may fail intermittently
            pass
    """
    return {
        "reruns": 3,
        "reruns_delay": 2,
        "only_rerun": ["ConnectionError", "TimeoutError", "RateLimitError"],
    }


# ============================================================================
# Enhanced Test Isolation
# ============================================================================


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Reset global state before and after each test.

    This ensures tests don't affect each other through shared state.
    """
    initial_env = dict(os.environ)

    yield

    os.environ.clear()
    os.environ.update(initial_env)


@pytest.fixture
def isolated_imports(monkeypatch):
    """
    Isolate module imports for testing.

    Clears cached imports so modules are re-imported fresh.
    """
    modules_to_clear = [
        "src.core.config",
        "src.core.ai_client",
        "src.core.smart_router",
        "src.core.cache",
    ]

    original_modules = {}
    for mod_name in modules_to_clear:
        if mod_name in sys.modules:
            original_modules[mod_name] = sys.modules[mod_name]
            del sys.modules[mod_name]

    yield

    for mod_name, mod in original_modules.items():
        sys.modules[mod_name] = mod


@pytest.fixture
def capture_global_state():
    """
    Capture and verify global state hasn't changed.

    Usage:
        def test_no_side_effects(capture_global_state):
            initial = capture_global_state()
            # ... test code ...
            final = capture_global_state()
            assert initial == final
    """
    def _capture():
        state = {
            "env_count": len(os.environ),
            "cwd": os.getcwd(),
        }

        try:
            from src.core.ai_client import AIClient
            state["AIClient._instance"] = id(getattr(AIClient, "_instance", None))
        except ImportError:
            pass

        try:
            from src.core.smart_router import SmartRouter
            state["SmartRouter._instance"] = id(getattr(SmartRouter, "_instance", None))
        except ImportError:
            pass

        return state

    return _capture


# ============================================================================
# API Contract Test Support
# ============================================================================


@pytest.fixture
def openapi_schema():
    """
    Provide the OpenAPI schema for contract testing.

    Usage:
        def test_schema_unchanged(openapi_schema, snapshot):
            assert openapi_schema == snapshot
    """
    try:
        from src.api.app import app
        return app.openapi()
    except ImportError:
        pytest.skip("FastAPI app not available")


@pytest.fixture
def pydantic_schema_validator():
    """
    Provide a validator for Pydantic model schemas.

    Usage:
        def test_model_schema(pydantic_schema_validator):
            from src.api.models import ResearchRequest
            pydantic_schema_validator(ResearchRequest, required=["company_name"])
    """
    def _validate(model_class, required=None, properties=None):
        schema = model_class.model_json_schema()

        if required:
            for field in required:
                assert field in schema.get("required", []), f"Field '{field}' should be required"

        if properties:
            for prop, expected_type in properties.items():
                assert prop in schema.get("properties", {}), f"Property '{prop}' missing"
                if expected_type:
                    actual_type = schema["properties"][prop].get("type")
                    assert actual_type == expected_type, f"Property '{prop}' type mismatch"

        return schema

    return _validate


# ============================================================================
# Test Cleanup Fixtures
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """
    Clean up test artifacts at start and end of test session.

    This ensures a clean slate for test runs and removes artifacts afterward.
    """
    import shutil

    # Directories to clean
    cleanup_patterns = [
        "data/test_*",
        "outputs/test_*",
        "outputs_test",
        ".pytest_cache",
    ]

    def cleanup_artifacts():
        for pattern in cleanup_patterns:
            for path in Path.cwd().glob(pattern):
                try:
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        path.unlink(missing_ok=True)
                except Exception:
                    pass  # Ignore cleanup errors

    # Setup: clean slate
    cleanup_artifacts()

    yield

    # Teardown: final cleanup
    cleanup_artifacts()


@pytest.fixture
def db_transaction():
    """
    Wrap test in database transaction that rolls back.

    Usage:
        def test_database_operation(db_transaction):
            # Changes are rolled back after test
            db_transaction.execute("INSERT INTO ...")
    """
    try:
        from src.api.database import get_db_session

        session = get_db_session()
        session.begin_nested()
        yield session
        session.rollback()
    except ImportError:
        pytest.skip("Database not available")


@pytest.fixture
async def browser_context():
    """
    Provide browser context that closes after test.

    Usage:
        async def test_browser_operation(browser_context):
            page = await browser_context.new_page()
            await page.goto("https://example.com")
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()
    except ImportError:
        pytest.skip("Playwright not available")


@pytest.fixture
def temp_file_tracker(tmp_path):
    """
    Track and clean up temporary files created during test.

    Usage:
        def test_file_creation(temp_file_tracker):
            file_path = temp_file_tracker.create("test.txt")
            # File is automatically cleaned up
    """
    class FileTracker:
        def __init__(self, base_path: Path):
            self.base_path = base_path
            self.files = []

        def create(self, name: str, content: str = "") -> Path:
            file_path = self.base_path / name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            self.files.append(file_path)
            return file_path

        def cleanup(self):
            for f in self.files:
                if f.exists():
                    f.unlink()

    tracker = FileTracker(tmp_path)
    yield tracker
    tracker.cleanup()


@pytest.fixture
def verify_no_file_leaks():
    """
    Verify test doesn't leave files behind in specific directories.

    Usage:
        def test_something(verify_no_file_leaks):
            # Test code
            verify_no_file_leaks(["data", "outputs"])
    """
    def _verify(directories: list):
        for dir_name in directories:
            dir_path = Path.cwd() / dir_name
            if dir_path.exists():
                test_files = list(dir_path.glob("test_*"))
                assert not test_files, f"Test files leaked in {dir_name}: {test_files}"

    return _verify


# ============================================================================
# Additional Factory Fixtures
# ============================================================================


@pytest.fixture
def bulk_data_generator():
    """Provide BulkDataGenerator for stress testing."""
    from tests.factories import BulkDataGenerator
    return BulkDataGenerator


@pytest.fixture
def research_state_factory():
    """Provide ResearchStateFactory for state generation."""
    from tests.factories import ResearchStateFactory
    return ResearchStateFactory
