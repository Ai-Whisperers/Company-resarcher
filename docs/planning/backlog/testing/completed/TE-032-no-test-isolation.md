# TE-032: Tests Not Properly Isolated

**Priority**: Low
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Added autouse fixtures in conftest.py: reset_global_state (env vars), reset_all_singletons, isolate_environment (fake API keys). Added isolated_imports and capture_global_state fixtures. pytest-randomly already in dependencies for order verification.

## Description

Tests share state through global variables, singletons, or module-level objects. This causes tests to pass/fail depending on execution order.

## Current State

- Some tests modify global state
- Singleton instances shared between tests
- Module-level initialization persists
- Import side effects not reset

## Signs of Poor Isolation

```python
# Global state modified
global_counter = 0

def test_one():
    global global_counter
    global_counter += 1
    assert global_counter == 1  # Passes

def test_two():
    global global_counter
    global_counter += 1
    assert global_counter == 1  # Fails! (counter is 2)

# Singleton not reset
class AIClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

def test_client_one():
    client = AIClient.get_instance()
    client.config = "test1"

def test_client_two():
    client = AIClient.get_instance()
    assert client.config is None  # Fails! (config is "test1")
```

## Impact

- **Order-dependent tests**: Results vary by execution order
- **Flaky CI**: Random failures in parallel execution
- **Debug difficulty**: Failures don't reproduce locally
- **False confidence**: Tests pass due to lucky ordering

## Proposed Solution

1. **Reset singletons in fixtures**:

   ```python
   @pytest.fixture(autouse=True)
   def reset_singletons():
       """Reset all singletons before each test."""
       AIClient._instance = None
       SmartRouter._instance = None
       Cache._instance = None
       yield
       # Reset after test too
       AIClient._instance = None
       SmartRouter._instance = None
       Cache._instance = None
   ```

2. **Use dependency injection**:

   ```python
   # BAD: Using singleton
   def process_data():
       client = AIClient.get_instance()
       return client.generate(...)

   # GOOD: Injecting dependency
   def process_data(client: AIClient):
       return client.generate(...)

   def test_process_data(mock_ai_client):
       result = process_data(mock_ai_client)
       assert result is not None
   ```

3. **Avoid module-level state**:

   ```python
   # BAD: Module-level initialization
   # tools.py
   browser = Browser()  # Created at import time

   # GOOD: Lazy initialization
   # tools.py
   _browser = None

   def get_browser():
       global _browser
       if _browser is None:
           _browser = Browser()
       return _browser
   ```

4. **Use monkeypatch for environment**:

   ```python
   def test_with_env_var(monkeypatch):
       """Test with modified environment."""
       monkeypatch.setenv("API_KEY", "test-key")
       # Environment automatically restored after test

   def test_with_module_attr(monkeypatch):
       """Test with patched module attribute."""
       monkeypatch.setattr("src.core.config.DEBUG", True)
       # Attribute automatically restored
   ```

5. **Verify test isolation**:

   ```python
   @pytest.fixture(autouse=True)
   def verify_isolation():
       """Verify test hasn't polluted global state."""
       initial_state = capture_global_state()
       yield
       final_state = capture_global_state()

       if initial_state != final_state:
           pytest.fail(f"Test modified global state: {diff(initial_state, final_state)}")

   def capture_global_state():
       return {
           "AIClient._instance": AIClient._instance,
           "env_API_KEY": os.getenv("API_KEY"),
           "cwd": os.getcwd(),
       }
   ```

6. **Use pytest-randomly to detect issues**:

   ```bash
   pip install pytest-randomly

   # Run tests in random order
   pytest --randomly-seed=12345

   # If tests fail, seed is printed for reproduction
   ```

## Acceptance Criteria

- [ ] All singletons reset between tests
- [ ] Dependency injection used instead of singletons
- [ ] No module-level mutable state
- [ ] monkeypatch used for environment changes
- [ ] pytest-randomly used to verify isolation
- [ ] Tests pass in any execution order

## Related Issues

- [TE-029](TE-029-no-parallel-tests.md) - Tests don't run in parallel
- [TE-030](TE-030-no-test-cleanup.md) - No test cleanup procedures
