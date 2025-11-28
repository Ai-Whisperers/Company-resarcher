# TE-028: No Test Categorization

**Priority**: Low
**Category**: Testing
**Status**: Partially Addressed
**Estimated Effort**: Small

## Description

While pytest markers exist in `conftest.py`, tests are not consistently categorized. This makes it difficult to run specific test subsets.

## Current State

Markers defined but underutilized:
- `@pytest.mark.unit` - Rarely used
- `@pytest.mark.integration` - Rarely used
- `@pytest.mark.manual` - Inconsistently used
- `@pytest.mark.slow` - Not used
- `@pytest.mark.requires_api` - Not used

## Impact

- **Can't run fast tests**: No way to run only quick tests
- **CI inefficiency**: All tests run every time
- **No selective testing**: Can't test specific components
- **Unclear test scope**: Unknown what each test covers

## Proposed Solution

1. **Define complete category system**:

   | Category | Marker | Description | Run Time |
   |----------|--------|-------------|----------|
   | Unit | `@pytest.mark.unit` | Isolated, no deps | <100ms |
   | Integration | `@pytest.mark.integration` | With mock deps | <5s |
   | E2E | `@pytest.mark.e2e` | Full workflows | <60s |
   | Smoke | `@pytest.mark.smoke` | Quick checks | <2s |
   | Slow | `@pytest.mark.slow` | Long-running | >10s |
   | API | `@pytest.mark.requires_api` | Needs real APIs | varies |

2. **Add component markers**:

   ```python
   # conftest.py additions
   def pytest_configure(config):
       config.addinivalue_line("markers", "core: tests for core module")
       config.addinivalue_line("markers", "agents: tests for agents module")
       config.addinivalue_line("markers", "tools: tests for tools module")
       config.addinivalue_line("markers", "api: tests for API module")
       config.addinivalue_line("markers", "graph: tests for graph module")
   ```

3. **Categorize all existing tests**:

   ```python
   # tests/unit/test_api.py
   import pytest

   @pytest.mark.unit
   @pytest.mark.api
   def test_health_endpoint_returns_200():
       ...

   @pytest.mark.unit
   @pytest.mark.api
   def test_research_validation():
       ...
   ```

4. **Create run configurations**:

   ```bash
   # Fast feedback (unit tests only)
   pytest -m "unit" --timeout=10

   # Pre-commit (unit + fast integration)
   pytest -m "unit or (integration and not slow)"

   # Full CI
   pytest -m "not manual and not requires_api"

   # Component-specific
   pytest -m "core"
   pytest -m "agents"
   pytest -m "api"
   ```

5. **Add default markers in conftest.py**:

   ```python
   def pytest_collection_modifyitems(items):
       """Auto-mark tests based on location."""
       for item in items:
           if "unit" in str(item.fspath):
               item.add_marker(pytest.mark.unit)
           elif "integration" in str(item.fspath):
               item.add_marker(pytest.mark.integration)
           elif "e2e" in str(item.fspath):
               item.add_marker(pytest.mark.e2e)
   ```

6. **Document run profiles**:

   ```markdown
   ## Test Profiles

   | Profile | Command | When to Use |
   |---------|---------|-------------|
   | Quick | `pytest -m unit` | During development |
   | Standard | `pytest -m "not slow"` | Before commit |
   | Full | `pytest` | CI pipeline |
   | API | `pytest -m requires_api` | Manual API testing |
   ```

## Acceptance Criteria

- [ ] All markers registered in conftest.py
- [ ] All tests have appropriate markers
- [ ] Component markers applied
- [ ] Auto-marking based on directory
- [ ] Run profiles documented
- [ ] CI uses appropriate profile

## Related Issues

- [TE-013](TE-013-slow-tests.md) - Tests are too slow
- [TE-025](TE-025-no-test-docs.md) - No test documentation
