# TE-031: Hardcoded Test Values

**Priority**: Low
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Small
**Completed**: 2025-11-28
**Resolution**: Created `tests/constants.py` with centralized constants for URLs, API keys, timeouts, limits, HTTP status codes, content types, task states, AI/LLM constants, regex patterns, error messages, and test data defaults.

## Description

Tests contain hardcoded values (URLs, API responses, file paths) instead of using fixtures or constants. This makes tests brittle and hard to maintain.

## Current State

Examples of hardcoded values:

```python
# Hardcoded URLs
response = client.get("https://example.com/api/test")

# Hardcoded paths
with open("/tmp/test_file.txt") as f:

# Hardcoded API responses
mock_response = {"status": "success", "data": {"id": 123}}

# Hardcoded company data
company = {"name": "Test Corp", "website": "https://test.com"}
```

## Impact

- **Fragile tests**: Changes require multiple updates
- **Unclear intent**: Magic values don't explain purpose
- **Duplication**: Same values repeated across tests
- **Maintenance burden**: Finding all occurrences difficult

## Proposed Solution

1. **Create test constants file**:

   ```python
   # tests/constants.py
   """Test constants and shared values."""

   # URLs
   TEST_API_BASE_URL = "https://api.example.com"
   TEST_COMPANY_URL = "https://testcorp.com"
   MOCK_SEARCH_URL = "https://search.example.com"

   # API Keys (fake)
   TEST_API_KEY = "test-api-key-12345"
   TEST_TAVILY_KEY = "tvly-test-key"

   # Timeouts
   TEST_TIMEOUT_SHORT = 5
   TEST_TIMEOUT_LONG = 30

   # Limits
   TEST_MAX_RESULTS = 10
   TEST_PAGE_SIZE = 20
   ```

2. **Use fixtures for complex data**:

   ```python
   # conftest.py
   @pytest.fixture
   def test_company():
       """Standard test company profile."""
       return {
           "name": "Test Corp",
           "website": "https://testcorp.com",
           "industry": "Technology",
           "employees": 1000,
       }

   @pytest.fixture
   def mock_api_response():
       """Standard successful API response."""
       return {
           "status": "success",
           "data": {"id": "test-123", "name": "Test Result"},
           "metadata": {"count": 1, "page": 1},
       }
   ```

3. **Use factories for varied data**:

   ```python
   # tests/factories.py
   class ResponseFactory:
       @staticmethod
       def success(data=None):
           return {
               "status": "success",
               "data": data or {"id": "test-123"},
           }

       @staticmethod
       def error(message="Error occurred"):
           return {
               "status": "error",
               "message": message,
           }
   ```

4. **Refactor existing tests**:

   ```python
   # Before
   def test_search():
       response = mock_search("test query")
       assert response["status"] == "success"
       assert len(response["results"]) == 5

   # After
   def test_search(test_company, mock_api_response):
       response = mock_search(test_company["name"])
       assert response["status"] == mock_api_response["status"]
   ```

5. **Use parametrize for variations**:

   ```python
   @pytest.mark.parametrize("company_name,expected_results", [
       ("Apple", 10),
       ("Unknown Corp", 0),
       ("", 0),
   ])
   def test_search_variations(company_name, expected_results):
       results = search(company_name)
       assert len(results) == expected_results
   ```

6. **Environment-specific values**:

   ```python
   # tests/conftest.py
   @pytest.fixture
   def api_base_url():
       """Return appropriate API URL for environment."""
       return os.getenv("TEST_API_URL", "https://api.test.com")
   ```

## Acceptance Criteria

- [ ] `tests/constants.py` created for shared values
- [ ] Fixtures for all complex test data
- [ ] Factories for generating varied data
- [ ] No magic numbers in tests
- [ ] No hardcoded paths (use tmp_path)
- [ ] Existing tests refactored

## Related Issues

- [TE-006](TE-006-no-fixtures.md) - No shared test fixtures
- [TE-014](TE-014-no-test-data.md) - No test data generation
