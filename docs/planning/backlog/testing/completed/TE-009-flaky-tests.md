# TE-009: Tests Depend on External Services

**Priority**: High
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Added pytest-vcr and pytest-rerunfailures to dependencies. Created VCR configuration fixtures in conftest.py with API key filtering. Added flaky/vcr markers to pytest config. Comprehensive mocks in tests/mocks.py prevent real API calls.

## Description

Many existing tests make real calls to external services (LLM APIs, search APIs, websites), making them flaky, slow, and unreliable. Tests fail intermittently due to network issues, rate limits, or service changes.

## Current State

Tests that hit external services:
- `tests/integration/test_graph.py` - Calls real LLM APIs
- `tests/integration/test_sector.py` - Calls search APIs
- `tests/integration/test_sales.py` - Calls multiple APIs
- `tests/manual/*` - All require real API keys

Issues observed:
- Tests fail due to API rate limits
- Tests fail due to network timeouts
- Test results vary based on external data
- Tests require valid API keys to run

## Impact

- **Unreliable CI**: Tests pass/fail randomly
- **Developer frustration**: "Works on my machine"
- **Cost**: Each test run costs API credits
- **Slow feedback**: External calls add latency
- **Blocked development**: Rate limits block testing

## Proposed Solution

1. **Identify and categorize tests**:

   | Category | External Services | Action |
   |----------|-------------------|--------|
   | Unit | None | Keep as-is |
   | Integration | Mocked | Convert to use mocks |
   | E2E | Real | Mark and run separately |

2. **Add service mocking**:

   ```python
   @pytest.fixture
   def mock_external_services(monkeypatch):
       """Mock all external service calls."""
       # Mock OpenAI
       monkeypatch.setattr(
           "openai.AsyncOpenAI",
           MockOpenAIClient
       )
       # Mock Tavily
       monkeypatch.setattr(
           "tavily.TavilyClient",
           MockTavilyClient
       )
   ```

3. **Use VCR for HTTP recording**:

   ```python
   import pytest_vcr

   @pytest.mark.vcr()
   def test_search_results():
       """Test search with recorded HTTP responses."""
       results = search_tool.search("test query")
       assert len(results) > 0
   ```

4. **Add retry logic for E2E tests**:

   ```python
   @pytest.mark.flaky(reruns=3, reruns_delay=5)
   @pytest.mark.requires_api
   def test_real_api_call():
       """Test with real API (may be flaky)."""
       pass
   ```

5. **Create test categories**:

   ```python
   # Run only unit tests (fast, no external deps)
   pytest -m "unit"

   # Run integration tests (mocked external deps)
   pytest -m "integration and not requires_api"

   # Run E2E tests (real external deps, may be flaky)
   pytest -m "requires_api"
   ```

## Acceptance Criteria

- [ ] All unit tests run without external services
- [ ] Integration tests use mocked services by default
- [ ] E2E tests clearly marked with `@pytest.mark.requires_api`
- [ ] VCR or similar tool records HTTP interactions
- [ ] Tests categorized and can run in isolation
- [ ] CI runs only non-flaky tests by default

## Related Issues

- [TE-005](TE-005-no-mocking-strategy.md) - No consistent mocking strategy
- [TE-008](TE-008-no-ci-integration.md) - No CI/CD test integration
