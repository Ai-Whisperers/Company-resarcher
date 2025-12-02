# TE-025: No Test Documentation

**Priority**: Low
**Category**: Testing
**Status**: Open
**Estimated Effort**: Small

## Description

Tests lack documentation. There's no README explaining test structure, how to run tests, or testing conventions. New developers must figure out testing practices by reading code.

## Current State

- No `tests/README.md`
- No testing guidelines document
- Test docstrings inconsistent
- No explanation of test markers
- No documentation of fixtures

## Impact

- **Slow onboarding**: New devs don't know how to test
- **Inconsistent practices**: Each developer tests differently
- **Knowledge loss**: Testing decisions not documented
- **Maintenance overhead**: Understanding tests takes time

## Proposed Solution

1. **Create tests/README.md**:

   ```markdown
   # Test Suite

   ## Quick Start

   ```bash
   # Run all tests
   pytest

   # Run unit tests only
   pytest -m unit

   # Run with coverage
   pytest --cov=src --cov-report=html
   ```

   ## Test Structure

   ```
   tests/
   ├── unit/           # Fast, isolated tests
   ├── integration/    # Tests with dependencies
   ├── e2e/           # End-to-end tests
   ├── smoke/         # Quick verification tests
   ├── regression/    # Bug fix verification
   └── conftest.py    # Shared fixtures
   ```

   ## Test Markers

   | Marker | Description | Run Command |
   |--------|-------------|-------------|
   | `@pytest.mark.unit` | Fast, isolated | `pytest -m unit` |
   | `@pytest.mark.integration` | Uses external deps | `pytest -m integration` |
   | `@pytest.mark.slow` | Takes >1s | `pytest -m "not slow"` |
   | `@pytest.mark.requires_api` | Needs API keys | `pytest -m requires_api` |

   ## Writing Tests

   ### Test Naming
   - Test files: `test_<module>.py`
   - Test functions: `test_<action>_<scenario>()`
   - Example: `test_search_returns_empty_for_invalid_query()`

   ### Using Fixtures
   See `conftest.py` for available fixtures.
   ```

2. **Document fixtures in conftest.py**:

   ```python
   @pytest.fixture
   def mock_ai_client() -> MagicMock:
       """
       Provide a mock AI client for testing without API calls.

       Usage:
           def test_something(mock_ai_client):
               mock_ai_client.generate.return_value = "custom response"
               result = my_function(mock_ai_client)

       Returns:
           MagicMock with async generate() and generate_structured() methods.
       """
   ```

3. **Create testing guidelines document**:

   ```markdown
   # Testing Guidelines

   ## Principles
   1. Tests should be independent
   2. Tests should be fast
   3. Tests should be deterministic

   ## Dos and Don'ts
   - DO use mocks for external services
   - DO test edge cases
   - DON'T test implementation details
   - DON'T use sleep() in tests
   ```

## Acceptance Criteria

- [ ] `tests/README.md` created with structure and usage
- [ ] All fixtures documented with docstrings
- [ ] Test markers documented
- [ ] Testing guidelines created
- [ ] Naming conventions documented
- [ ] Examples provided for common scenarios

## Related Issues

- [TE-026](TE-026-inconsistent-naming.md) - Inconsistent test naming
- [TE-019](TE-019-inconsistent-assertions.md) - Inconsistent assertion patterns
