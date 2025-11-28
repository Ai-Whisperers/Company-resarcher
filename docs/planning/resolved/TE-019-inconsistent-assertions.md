# TE-019: Inconsistent Assertion Patterns

**Priority**: Medium
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Small
**Completed**: 2025-11-28
**Resolution**: Created `tests/assertions.py` with 18 custom assertion helpers covering responses, data structures, exceptions, collections, numerics, strings, timestamps, and AI/ML validations.

## Description

Tests use varying assertion styles and patterns, making them harder to read and maintain. There's no standard for how assertions should be written.

## Current State

Mixed assertion styles observed:
- `assert x == y` (basic assert)
- `assert x is not None`
- Manual exception checking
- No custom assertion helpers
- Inconsistent error messages

## Impact

- **Readability issues**: Tests harder to understand
- **Maintenance burden**: Different patterns for same checks
- **Poor error messages**: Failures don't explain why
- **Code duplication**: Same checks written differently

## Examples of Inconsistency

```python
# Style 1: Basic assert
assert response.status_code == 200

# Style 2: Assert with message
assert response.status_code == 200, f"Expected 200, got {response.status_code}"

# Style 3: Multiple asserts for same concept
assert response is not None
assert response.status_code == 200
assert "data" in response.json()

# Style 4: Exception checking variations
try:
    do_something()
    assert False, "Should have raised"
except ValueError:
    pass

# vs
with pytest.raises(ValueError):
    do_something()
```

## Proposed Solution

1. **Define assertion standards**:

   ```python
   # PREFERRED: Use pytest.raises for exceptions
   with pytest.raises(ValueError, match="expected error message"):
       function_that_raises()

   # PREFERRED: Use descriptive messages
   assert result.status == "success", f"Expected success, got {result.status}"

   # PREFERRED: Use pytest assertions for collections
   assert "key" in dictionary
   assert item in list

   # PREFERRED: Use pytest.approx for floats
   assert value == pytest.approx(expected, rel=1e-6)
   ```

2. **Create custom assertion helpers**:

   ```python
   # tests/assertions.py
   def assert_valid_response(response, expected_status=200):
       """Assert response is valid with expected status."""
       assert response is not None, "Response is None"
       assert response.status_code == expected_status, \
           f"Expected status {expected_status}, got {response.status_code}"

   def assert_valid_research_state(state):
       """Assert research state has required fields."""
       assert state.company_name, "company_name is required"
       assert state.website, "website is required"
       assert isinstance(state.errors, list), "errors must be a list"

   def assert_report_structure(report, required_sections):
       """Assert report contains required sections."""
       for section in required_sections:
           assert section in report, f"Missing section: {section}"
   ```

3. **Use pytest-check for soft assertions**:

   ```python
   from pytest_check import check

   def test_multiple_conditions():
       """Test multiple conditions without stopping on first failure."""
       with check:
           assert condition1
       with check:
           assert condition2
       with check:
           assert condition3
   ```

4. **Document assertion patterns**:

   ```markdown
   # Assertion Guidelines

   ## Response Assertions
   - Use `assert_valid_response(response, expected_status)`
   - Always check status code first

   ## Exception Assertions
   - Use `pytest.raises(ExceptionType, match="pattern")`
   - Include match pattern when possible

   ## Float Assertions
   - Use `pytest.approx(value, rel=tolerance)`
   - Default tolerance: 1e-6
   ```

## Acceptance Criteria

- [ ] Assertion standards documented
- [ ] Custom assertion helpers in `tests/assertions.py`
- [ ] Existing tests refactored to use standards
- [ ] All assertions have descriptive messages
- [ ] pytest-check used for multi-condition tests
- [ ] Linting rule added for bare asserts

## Related Issues

- [TE-026](TE-026-inconsistent-naming.md) - Inconsistent test naming
- [TE-025](TE-025-no-test-docs.md) - No test documentation
