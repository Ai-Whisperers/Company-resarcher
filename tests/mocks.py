"""
Comprehensive mock implementations for external services.

This module provides mock classes and fixtures for all external services
used in the codebase, ensuring tests can run without real API calls.
"""

import asyncio
import json
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

from tests.constants import (
    TEST_OPENAI_API_KEY,
    TEST_TAVILY_API_KEY,
    MOCK_RESPONSE_DELAY_FAST,
)
from tests.factories import (
    AIResponseFactory,
    SearchResultFactory,
    CompanyFactory,
    FinancialDataFactory,
)


# =============================================================================
# Mock AI Clients
# =============================================================================


@dataclass
class MockOpenAICompletion:
    """Mock OpenAI chat completion response."""

    content: str = "This is a mock AI response"
    role: str = "assistant"
    finish_reason: str = "stop"
    prompt_tokens: int = 100
    completion_tokens: int = 50
    total_tokens: int = 150
    model: str = "gpt-4"

    @property
    def choices(self) -> List[Any]:
        choice = MagicMock()
        choice.message.content = self.content
        choice.message.role = self.role
        choice.finish_reason = self.finish_reason
        return [choice]

    @property
    def usage(self) -> MagicMock:
        usage = MagicMock()
        usage.prompt_tokens = self.prompt_tokens
        usage.completion_tokens = self.completion_tokens
        usage.total_tokens = self.total_tokens
        return usage


class MockOpenAIClient:
    """Mock OpenAI client for testing."""

    def __init__(
        self,
        default_response: str = "Mock OpenAI response",
        responses: Optional[List[str]] = None,
        raise_error: Optional[Exception] = None,
        delay: float = 0,
    ):
        self.default_response = default_response
        self.responses = responses or []
        self.response_index = 0
        self.raise_error = raise_error
        self.delay = delay
        self.call_history: List[Dict[str, Any]] = []

    def _get_response(self) -> str:
        if self.responses:
            response = self.responses[self.response_index % len(self.responses)]
            self.response_index += 1
            return response
        return self.default_response

    @property
    def chat(self) -> "MockOpenAIClient":
        return self

    @property
    def completions(self) -> "MockOpenAIClient":
        return self

    async def create(
        self,
        model: str = "gpt-4",
        messages: Optional[List[Dict]] = None,
        **kwargs,
    ) -> MockOpenAICompletion:
        """Mock chat completion."""
        if self.delay:
            await asyncio.sleep(self.delay)

        if self.raise_error:
            raise self.raise_error

        self.call_history.append({
            "model": model,
            "messages": messages,
            "kwargs": kwargs,
            "timestamp": datetime.now().isoformat(),
        })

        return MockOpenAICompletion(
            content=self._get_response(),
            model=model,
        )


class MockAnthropicClient:
    """Mock Anthropic client for testing."""

    def __init__(
        self,
        default_response: str = "Mock Anthropic response",
        raise_error: Optional[Exception] = None,
    ):
        self.default_response = default_response
        self.raise_error = raise_error
        self.call_history: List[Dict[str, Any]] = []

    @property
    def messages(self) -> "MockAnthropicClient":
        return self

    async def create(
        self,
        model: str = "claude-3-sonnet",
        messages: Optional[List[Dict]] = None,
        **kwargs,
    ) -> MagicMock:
        """Mock message creation."""
        if self.raise_error:
            raise self.raise_error

        self.call_history.append({
            "model": model,
            "messages": messages,
            "kwargs": kwargs,
        })

        response = MagicMock()
        response.content = [MagicMock()]
        response.content[0].text = self.default_response
        response.model = model
        return response


# =============================================================================
# Mock Search Clients
# =============================================================================


class MockTavilyClient:
    """Mock Tavily search client for testing."""

    def __init__(
        self,
        results: Optional[List[Dict]] = None,
        num_results: int = 5,
        raise_error: Optional[Exception] = None,
    ):
        self.results = results
        self.num_results = num_results
        self.raise_error = raise_error
        self.call_history: List[Dict[str, Any]] = []

    def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mock search."""
        if self.raise_error:
            raise self.raise_error

        self.call_history.append({
            "query": query,
            "max_results": max_results,
            "kwargs": kwargs,
        })

        results = self.results or SearchResultFactory.create_batch(
            min(max_results, self.num_results)
        )

        return {
            "results": results,
            "query": query,
        }

    async def asearch(
        self,
        query: str,
        max_results: int = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mock async search."""
        return self.search(query, max_results, **kwargs)


class MockDDGSearch:
    """Mock DuckDuckGo search for testing."""

    def __init__(
        self,
        results: Optional[List[Dict]] = None,
        num_results: int = 5,
    ):
        self.results = results
        self.num_results = num_results
        self.call_history: List[str] = []

    def text(
        self,
        query: str,
        max_results: int = 10,
        **kwargs,
    ) -> List[Dict]:
        """Mock text search."""
        self.call_history.append(query)

        if self.results:
            return self.results[:max_results]

        return SearchResultFactory.create_batch(min(max_results, self.num_results))


# =============================================================================
# Mock Browser/HTTP
# =============================================================================


@dataclass
class MockHTTPResponse:
    """Mock HTTP response."""

    status_code: int = 200
    content: bytes = b""
    text: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    url: str = "https://example.com"

    def json(self) -> Dict[str, Any]:
        """Parse JSON content."""
        return json.loads(self.text or self.content.decode())

    def raise_for_status(self) -> None:
        """Raise exception for error status codes."""
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


class MockBrowserTool:
    """Mock browser tool for testing."""

    def __init__(
        self,
        default_content: str = "<html><body>Mock content</body></html>",
        responses: Optional[Dict[str, str]] = None,
        raise_error: Optional[Exception] = None,
    ):
        self.default_content = default_content
        self.responses = responses or {}
        self.raise_error = raise_error
        self.call_history: List[str] = []

    async def fetch_content(
        self,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mock content fetching."""
        if self.raise_error:
            raise self.raise_error

        self.call_history.append(url)

        content = self.responses.get(url, self.default_content)

        return {
            "url": url,
            "title": "Mock Page Title",
            "content": content,
            "status": 200,
        }

    async def screenshot(self, url: str, **kwargs) -> bytes:
        """Mock screenshot."""
        self.call_history.append(f"screenshot:{url}")
        return b"fake-screenshot-data"


class MockAIOHTTPSession:
    """Mock aiohttp ClientSession."""

    def __init__(
        self,
        responses: Optional[Dict[str, MockHTTPResponse]] = None,
        default_response: Optional[MockHTTPResponse] = None,
    ):
        self.responses = responses or {}
        self.default_response = default_response or MockHTTPResponse(
            status_code=200,
            text="Mock response",
        )
        self.call_history: List[Dict] = []

    @asynccontextmanager
    async def get(self, url: str, **kwargs):
        """Mock GET request."""
        self.call_history.append({"method": "GET", "url": url, "kwargs": kwargs})
        yield self.responses.get(url, self.default_response)

    @asynccontextmanager
    async def post(self, url: str, **kwargs):
        """Mock POST request."""
        self.call_history.append({"method": "POST", "url": url, "kwargs": kwargs})
        yield self.responses.get(url, self.default_response)

    async def close(self) -> None:
        """Mock close."""
        pass


# =============================================================================
# Mock Database
# =============================================================================


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}
        self.call_history: List[Dict] = []

    async def get(self, table: str, key: str) -> Optional[Dict[str, Any]]:
        """Mock get operation."""
        self.call_history.append({"op": "get", "table": table, "key": key})
        return self.data.get(table, {}).get(key)

    async def set(self, table: str, key: str, value: Dict[str, Any]) -> None:
        """Mock set operation."""
        self.call_history.append({"op": "set", "table": table, "key": key})
        if table not in self.data:
            self.data[table] = {}
        self.data[table][key] = value

    async def delete(self, table: str, key: str) -> bool:
        """Mock delete operation."""
        self.call_history.append({"op": "delete", "table": table, "key": key})
        if table in self.data and key in self.data[table]:
            del self.data[table][key]
            return True
        return False

    async def list(self, table: str) -> List[Dict[str, Any]]:
        """Mock list operation."""
        self.call_history.append({"op": "list", "table": table})
        return list(self.data.get(table, {}).values())

    def clear(self) -> None:
        """Clear all data."""
        self.data.clear()
        self.call_history.clear()


# =============================================================================
# Mock Cache
# =============================================================================


class MockCache:
    """Mock cache for testing."""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.ttls: Dict[str, float] = {}
        self.call_history: List[Dict] = []

    async def get(self, key: str) -> Optional[Any]:
        """Mock get."""
        self.call_history.append({"op": "get", "key": key})
        return self.data.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Mock set."""
        self.call_history.append({"op": "set", "key": key, "ttl": ttl})
        self.data[key] = value
        if ttl:
            self.ttls[key] = ttl

    async def delete(self, key: str) -> bool:
        """Mock delete."""
        self.call_history.append({"op": "delete", "key": key})
        if key in self.data:
            del self.data[key]
            self.ttls.pop(key, None)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Mock exists check."""
        return key in self.data

    def clear(self) -> None:
        """Clear cache."""
        self.data.clear()
        self.ttls.clear()
        self.call_history.clear()


# =============================================================================
# Mock Financial Data Provider
# =============================================================================


class MockYFinance:
    """Mock yfinance for testing."""

    def __init__(
        self,
        ticker_data: Optional[Dict[str, Dict]] = None,
        raise_error: Optional[Exception] = None,
    ):
        self.ticker_data = ticker_data or {}
        self.raise_error = raise_error

    def Ticker(self, symbol: str) -> "MockYFinanceTicker":
        """Get mock ticker."""
        if self.raise_error:
            raise self.raise_error

        data = self.ticker_data.get(
            symbol,
            FinancialDataFactory.create(ticker=symbol),
        )
        return MockYFinanceTicker(symbol, data)


class MockYFinanceTicker:
    """Mock yfinance Ticker object."""

    def __init__(self, symbol: str, data: Dict[str, Any]):
        self.symbol = symbol
        self._data = data

    @property
    def info(self) -> Dict[str, Any]:
        """Get ticker info."""
        return self._data

    @property
    def history(self) -> MagicMock:
        """Get price history."""
        mock = MagicMock()
        mock.return_value = MagicMock()
        return mock


# =============================================================================
# Context Managers for Mocking
# =============================================================================


@contextmanager
def mock_all_external_services(
    ai_response: str = "Mock AI response",
    search_results: Optional[List[Dict]] = None,
):
    """
    Context manager to mock all external services at once.

    Usage:
        with mock_all_external_services() as mocks:
            result = await function_under_test()
            assert mocks['ai'].call_history
    """
    ai_client = MockOpenAIClient(default_response=ai_response)
    search_client = MockTavilyClient(results=search_results)
    browser = MockBrowserTool()

    with patch("openai.AsyncOpenAI", return_value=ai_client):
        with patch("tavily.TavilyClient", return_value=search_client):
            with patch("src.tools.browser.BrowserTool", return_value=browser):
                yield {
                    "ai": ai_client,
                    "search": search_client,
                    "browser": browser,
                }


@asynccontextmanager
async def mock_async_services():
    """
    Async context manager for mocking services in async tests.

    Usage:
        async with mock_async_services() as mocks:
            result = await async_function()
    """
    mocks = {
        "ai": MockOpenAIClient(),
        "search": MockTavilyClient(),
        "cache": MockCache(),
        "db": MockDatabase(),
    }
    yield mocks


# =============================================================================
# Rate Limiting Mocks
# =============================================================================


class MockRateLimiter:
    """Mock rate limiter for testing."""

    def __init__(
        self,
        allow: bool = True,
        remaining: int = 100,
    ):
        self.allow = allow
        self.remaining = remaining
        self.call_count = 0

    async def acquire(self) -> bool:
        """Acquire rate limit permit."""
        self.call_count += 1
        if not self.allow:
            raise Exception("Rate limit exceeded")
        return True

    async def check(self) -> Dict[str, Any]:
        """Check rate limit status."""
        return {
            "allowed": self.allow,
            "remaining": self.remaining,
            "reset_at": datetime.now().isoformat(),
        }


# =============================================================================
# Error Generators
# =============================================================================


def create_rate_limit_error():
    """Create a mock rate limit error."""
    error = Exception("Rate limit exceeded")
    error.status_code = 429
    return error


def create_timeout_error():
    """Create a mock timeout error."""
    return asyncio.TimeoutError("Request timed out")


def create_connection_error():
    """Create a mock connection error."""
    return ConnectionError("Failed to connect")


def create_auth_error():
    """Create a mock authentication error."""
    error = Exception("Authentication failed")
    error.status_code = 401
    return error


# =============================================================================
# Fixture Helpers
# =============================================================================


def get_mock_ai_client(
    response: str = "Mock response",
    responses: Optional[List[str]] = None,
) -> MockOpenAIClient:
    """Get a configured mock AI client."""
    return MockOpenAIClient(
        default_response=response,
        responses=responses,
    )


def get_mock_search_client(
    num_results: int = 5,
    results: Optional[List[Dict]] = None,
) -> MockTavilyClient:
    """Get a configured mock search client."""
    return MockTavilyClient(
        num_results=num_results,
        results=results,
    )


def get_mock_browser() -> MockBrowserTool:
    """Get a configured mock browser tool."""
    return MockBrowserTool()
