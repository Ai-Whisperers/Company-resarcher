# PERF-001: Test Suite Performance Issues

## Priority: High
## Category: Performance / DevEx
## Status: Backlog

## Summary

The test suite takes an excessively long time to run, impacting developer productivity and CI/CD pipeline efficiency. Tests that should complete in seconds are taking minutes or timing out entirely.

## Observed Behavior

- Unit tests run for 10+ minutes without completing
- Individual test files appear to hang
- Test isolation may be insufficient
- Async tests may not be properly awaited

## Potential Root Causes

### 1. Real Network Calls
Tests may be making actual HTTP requests instead of using mocks:
- Browser tool initializing real Playwright browser
- Search tool calling real DuckDuckGo API
- AI client calling real OpenAI/Anthropic APIs

### 2. Database Issues
- Tests creating real database connections
- No cleanup between tests
- SQLite locks causing blocking

### 3. Async Test Issues
- `asyncio_mode = auto` may cause issues
- Event loop not properly cleaned between tests
- Async fixtures not awaited correctly

### 4. Missing Test Isolation
- Global state shared between tests
- Singletons not reset
- Environment variables leaking

## Investigation Plan

```bash
# Run tests with timing
pytest tests/unit/ -v --durations=20 --timeout=30

# Run individual test file
pytest tests/unit/test_config.py -v --timeout=30

# Check for real network calls
pytest tests/unit/ -v --timeout=30 2>&1 | grep -E "(HTTP|Connection|Timeout)"
```

## Proposed Fixes

### 1. Add Comprehensive Mocking

```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def mock_network(monkeypatch):
    """Block all real network calls in tests."""
    import socket
    def guard(*args, **kwargs):
        raise RuntimeError("Network call detected in test!")
    monkeypatch.setattr(socket, "socket", guard)

@pytest.fixture
def mock_browser():
    """Mock browser tool to avoid Playwright startup."""
    with patch("src.tools.browser.BrowserTool") as mock:
        mock.return_value.scrape.return_value = {"content": "Test content"}
        yield mock

@pytest.fixture
def mock_ai_client():
    """Mock AI client responses."""
    with patch("src.core.ai_client.AIClient") as mock:
        mock.return_value.generate.return_value = "Test response"
        yield mock
```

### 2. Add Test Timeouts

```ini
# pytest.ini
[pytest]
timeout = 30
timeout_method = signal
```

### 3. Proper Async Handling

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def cleanup_async_resources():
    """Cleanup after each async test."""
    yield
    # Cancel pending tasks
    import asyncio
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
```

### 4. Reset Singletons

```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton instances between tests."""
    from src.pipeline.orchestrator import reset_pipeline_orchestrator
    from src.core.config import clear_settings

    yield

    reset_pipeline_orchestrator()
    clear_settings()
```

## Implementation Tasks

- [ ] Profile test suite to identify slow tests
- [ ] Add `pytest-timeout` with 30s default
- [ ] Create comprehensive mock fixtures
- [ ] Block real network calls in test mode
- [ ] Reset singletons between tests
- [ ] Add parallel test execution (`pytest-xdist`)
- [ ] Document test best practices

## Success Criteria

- Full unit test suite runs in < 60 seconds
- No real network calls in unit tests
- Tests are properly isolated
- CI pipeline runs in < 5 minutes
- Clear documentation on writing fast tests
