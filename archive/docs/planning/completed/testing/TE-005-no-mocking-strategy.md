# TE-005: No Consistent Mocking Strategy

**Priority**: High
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Created `tests/mocks.py` with comprehensive mocks for OpenAI, Anthropic, Tavily, DDGSearch, Browser, AIOHTTP, Database, Cache, YFinance, and RateLimiter. Added `mock_all_external_services` context manager. Updated `conftest.py` with mock fixtures and factory-based test data generation.

## Description

The codebase lacks a consistent strategy for mocking external dependencies. While `conftest.py` has some mock fixtures, they are basic and not consistently used across tests. This leads to tests that either hit real APIs (slow, flaky) or skip testing entirely.

## Current State

- Basic mocks exist in `conftest.py`:
  - `mock_ai_client` - Simple MagicMock
  - `mock_search_tool` - Returns hardcoded results
  - `mock_browser_tool` - Returns static response
- No mocks for:
  - Database operations
  - File system operations
  - LLM provider-specific clients
  - External APIs (NewsAPI, Tavily, SEC)

## Impact

- **Flaky tests**: Tests depend on external services
- **Slow tests**: Real API calls are slow
- **Inconsistent results**: External data changes
- **Cost**: Real API calls cost money
- **Rate limits**: Tests can hit rate limits

## Proposed Solution

1. **Create comprehensive mock fixtures**:

   ```python
   # conftest.py additions
   @pytest.fixture
   def mock_openai_client():
       """Mock OpenAI client with realistic responses."""
       with patch("openai.AsyncOpenAI") as mock:
           mock.return_value.chat.completions.create = AsyncMock(
               return_value=MockCompletion(content="Test response")
           )
           yield mock

   @pytest.fixture
   def mock_tavily_client():
       """Mock Tavily search client."""
       with patch("tavily.TavilyClient") as mock:
           mock.return_value.search = MagicMock(
               return_value={"results": [...]}
           )
           yield mock
   ```

2. **Create response factories**:

   ```python
   # tests/factories.py
   class MockResponseFactory:
       @staticmethod
       def ai_response(content: str = "Test", tokens: int = 100):
           return {"content": content, "usage": {"total_tokens": tokens}}

       @staticmethod
       def search_results(count: int = 5):
           return [{"title": f"Result {i}", "url": f"http://example.com/{i}"} for i in range(count)]
   ```

3. **Use context managers for isolation**:

   ```python
   @contextmanager
   def mock_all_external_services():
       """Context manager to mock all external services."""
       with patch("src.core.ai_client.OpenAI"):
           with patch("src.tools.search.TavilyClient"):
               with patch("src.tools.browser.playwright"):
                   yield
   ```

4. **Document mocking patterns**:
   - Create `tests/README.md` with mocking guidelines
   - Provide examples for common scenarios

## Acceptance Criteria

- [ ] Mock fixtures exist for all external services
- [ ] Response factories provide realistic test data
- [ ] All unit tests use mocks (no real API calls)
- [ ] Mocking patterns documented in `tests/README.md`
- [ ] Integration tests can optionally use real services with flag

## Related Issues

- [TE-001](TE-001-no-unit-tests.md) - No unit test coverage
- [TE-006](TE-006-no-fixtures.md) - No shared test fixtures
- [TE-009](TE-009-flaky-tests.md) - Tests depend on external services
