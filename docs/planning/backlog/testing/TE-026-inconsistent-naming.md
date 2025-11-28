# TE-026: Inconsistent Test Naming

**Priority**: Low
**Category**: Testing
**Status**: Open
**Estimated Effort**: Small

## Description

Test names follow different conventions across the codebase. Inconsistent naming makes it harder to understand what tests verify and to locate specific tests.

## Current State

Examples of inconsistent naming:

```python
# Style 1: Simple name
def test_health_check():

# Style 2: Module prefix
def test_api_health_check():

# Style 3: Action based
def test_start_research_validation():

# Style 4: Should style
def test_search_should_return_results():

# Style 5: Given-when-then
def test_given_invalid_url_when_fetch_then_error():
```

## Impact

- **Hard to find tests**: No predictable naming pattern
- **Unclear purpose**: Names don't explain what's tested
- **Duplicate tests**: Similar names for different scenarios
- **Poor readability**: Test reports hard to understand

## Proposed Solution

1. **Define naming convention**:

   ```
   test_<action>_<scenario>_<expected_result>

   Examples:
   - test_search_with_valid_query_returns_results
   - test_search_with_empty_query_raises_error
   - test_fetch_with_timeout_retries_three_times
   ```

2. **Create naming guidelines**:

   | Component | Convention | Example |
   |-----------|------------|---------|
   | Prefix | Always `test_` | `test_` |
   | Action | Verb describing action | `search`, `fetch`, `create` |
   | Scenario | Condition being tested | `with_valid_input`, `when_rate_limited` |
   | Result | Expected outcome | `returns_data`, `raises_error` |

3. **Rename existing tests**:

   ```python
   # Before
   def test_health_check():
   def test_start_research_validation():

   # After
   def test_health_endpoint_returns_200():
   def test_research_with_missing_fields_returns_422():
   ```

4. **Add linting rule**:

   ```python
   # In ruff.toml or similar
   [lint.per-file-ignores]
   "tests/*.py" = ["N802"]  # Allow test naming convention

   # Custom rule for test naming
   # test_<verb>_<scenario>_<result>
   ```

5. **Update test files**:

   ```python
   # tests/unit/test_api.py

   # Health endpoint tests
   def test_health_endpoint_returns_200_when_healthy():
       ...

   def test_health_endpoint_returns_503_when_unhealthy():
       ...

   # Research endpoint tests
   def test_research_with_valid_input_returns_task_id():
       ...

   def test_research_with_missing_company_name_returns_422():
       ...

   def test_research_with_invalid_url_returns_422():
       ...
   ```

## Class-Based Test Naming

For test classes, use descriptive class names:

```python
class TestSearchTool:
    """Tests for SearchTool functionality."""

    def test_search_with_valid_query_returns_results(self):
        ...

    def test_search_with_empty_query_raises_value_error(self):
        ...

class TestSearchToolRateLimiting:
    """Tests for SearchTool rate limiting behavior."""

    def test_search_when_rate_limited_waits_and_retries(self):
        ...
```

## Acceptance Criteria

- [ ] Naming convention documented
- [ ] All existing tests renamed to follow convention
- [ ] Test names clearly describe behavior
- [ ] Class-based tests use descriptive class names
- [ ] Linting configured to check naming
- [ ] New test template provided

## Related Issues

- [TE-025](TE-025-no-test-docs.md) - No test documentation
- [TE-028](TE-028-no-test-categories.md) - No test categorization
