# Company Researcher Test Suite

## Quick Start

```bash
# Run all tests
pytest

# Run unit tests only (fast)
pytest -m unit

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests in parallel (faster)
pytest -n auto

# Run specific test file
pytest tests/unit/test_ai_client.py

# Run specific test
pytest tests/unit/test_ai_client.py::TestMockAIClient::test_generate_returns_text_response

# Generate HTML test report
pytest --html=reports/test-report.html --self-contained-html
```

## Test Structure

```text
tests/
├── unit/                    # Fast, isolated tests (no external deps)
│   ├── test_ai_client.py    # AI client abstraction tests
│   ├── test_smart_router.py # Smart router tests
│   ├── test_api_models.py   # API model tests
│   ├── test_boundary_conditions.py # Edge case/boundary tests
│   ├── test_error_paths.py  # Error handling tests
│   ├── test_concurrency.py  # Concurrency/race condition tests
│   └── ...                  # Other unit tests
├── integration/             # Tests with mocked external services
│   ├── conftest.py          # Integration-specific fixtures
│   ├── test_graph_workflow.py # Graph workflow tests
│   ├── test_api_endpoints.py  # API endpoint integration tests
│   └── ...                  # Other integration tests
├── contract/                # API contract tests
│   └── test_api_contracts.py
├── snapshot/                # Snapshot comparison tests
│   └── test_snapshots.py
├── chaos/                   # Chaos engineering tests
│   ├── conftest.py          # Chaos fixtures (timeouts, failures)
│   └── test_resilience.py   # Resilience tests
├── fuzz/                    # Fuzz testing with Hypothesis
│   └── test_fuzz_inputs.py
├── e2e/                     # End-to-end tests
├── security/                # Security tests
├── load/                    # Load/performance tests
├── property/                # Property-based tests
├── regression/              # Regression tests
├── smoke/                   # Smoke tests (quick validation)
├── manual/                  # Tests requiring manual setup/verification
│   ├── test_new_tools.py
│   └── test_local_research.py
├── conftest.py              # Shared fixtures (mocks, factories)
├── constants.py             # Test constants and shared values
├── assertions.py            # Custom assertion helpers
├── mocks.py                 # Mock implementations for external services
├── factories.py             # Test data factories
└── README.md                # This file
```

## Test Markers

| Marker | Description | Run Command |
|--------|-------------|-------------|
| `@pytest.mark.unit` | Fast, isolated tests | `pytest -m unit` |
| `@pytest.mark.integration` | Uses mocked external services | `pytest -m integration` |
| `@pytest.mark.e2e` | End-to-end workflow tests | `pytest -m e2e` |
| `@pytest.mark.slow` | Takes >10s | `pytest -m "not slow"` |
| `@pytest.mark.fast` | Quick tests (<100ms) | `pytest -m fast` |
| `@pytest.mark.requires_api` | Needs real API keys | `pytest -m requires_api` |
| `@pytest.mark.manual` | Requires manual setup | `pytest -m manual` |
| `@pytest.mark.smoke` | Quick validation tests | `pytest -m smoke` |
| `@pytest.mark.chaos` | Chaos/fault injection tests | `pytest -m chaos` |
| `@pytest.mark.concurrent` | Concurrency tests | `pytest -m concurrent` |
| `@pytest.mark.contract` | API contract tests | `pytest -m contract` |
| `@pytest.mark.snapshot` | Snapshot comparison tests | `pytest -m snapshot` |
| `@pytest.mark.security` | Security-related tests | `pytest -m security` |
| `@pytest.mark.regression` | Regression tests | `pytest -m regression` |
| `@pytest.mark.property` | Property-based tests | `pytest -m property` |
| `@pytest.mark.load` | Load/performance tests | `pytest -m load` |
| `@pytest.mark.serial` | Must run serially (no parallel) | `pytest -m serial -n0` |
| `@pytest.mark.flaky` | May fail intermittently | `pytest -m flaky` |
| `@pytest.mark.vcr` | Uses VCR for HTTP recording | `pytest -m vcr` |

## Running Tests

### During Development (Fast Feedback)
```bash
# Run only unit tests
pytest -m unit --timeout=10

# Run tests for specific module
pytest tests/unit/test_ai_client.py -v
```

### Before Commit
```bash
# Run unit + fast integration tests
pytest -m "unit or (integration and not slow)" --timeout=60
```

### Full CI Run
```bash
# Run all automated tests
pytest -m "not manual and not requires_api" --cov=src
```

### With Real API Keys
```bash
# Run tests that need API keys (set keys in .env first)
pytest -m requires_api
```

## Writing Tests

### Test Naming Convention

Follow the naming pattern: `test_<action>_<scenario>_<expected_result>`

```
test_<action>_<scenario>_<expected_result>

Examples:
- test_generate_with_valid_prompt_returns_response
- test_search_with_empty_query_raises_error
- test_fetch_with_timeout_retries_three_times
- test_research_with_missing_company_name_returns_422
```

#### Naming Guidelines

| Component | Convention | Examples |
|-----------|------------|----------|
| Prefix | Always `test_` | `test_` |
| Action | Verb describing the action | `generate`, `search`, `fetch`, `create`, `validate` |
| Scenario | Condition being tested | `with_valid_input`, `when_rate_limited`, `with_empty_query` |
| Result | Expected outcome | `returns_data`, `raises_error`, `retries_three_times` |

#### Class-Based Test Naming

```python
class TestSearchTool:
    """Tests for SearchTool functionality."""

    def test_search_with_valid_query_returns_results(self):
        """Verify search returns results for valid queries."""
        ...

    def test_search_with_empty_query_raises_value_error(self):
        """Verify empty query raises appropriate error."""
        ...

class TestSearchToolRateLimiting:
    """Tests for SearchTool rate limiting behavior."""

    def test_search_when_rate_limited_waits_and_retries(self):
        """Verify rate limited requests are retried with backoff."""
        ...
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_with_mock_ai(mock_ai_client):
    """Use mock AI client."""
    mock_ai_client.generate.return_value = "custom response"
    result = my_function(mock_ai_client)
    assert result == "custom response"

def test_with_company_profile(sample_company_profile):
    """Use sample company data."""
    assert sample_company_profile["name"] == "Test Corp"

def test_file_operations(temp_output_dir):
    """Use temporary directory (auto-cleaned)."""
    output_file = temp_output_dir / "report.md"
    # File will be cleaned up automatically
```

### Test Structure

```python
import pytest

class TestFeatureName:
    """Tests for FeatureName functionality."""

    @pytest.fixture
    def specific_fixture(self):
        """Fixture specific to this test class."""
        return SomeObject()

    @pytest.mark.unit
    def test_action_scenario_expected_result(self, specific_fixture):
        """Verify that action produces expected result in scenario."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = specific_fixture.action(input_data)

        # Assert
        assert result == expected_value
```

### Mocking External Services

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mocked_api():
    """Test with mocked external API."""
    with patch("src.module.external_api") as mock_api:
        mock_api.call = AsyncMock(return_value={"data": "test"})

        result = await function_under_test()

        mock_api.call.assert_called_once()
        assert result["data"] == "test"
```

## Coverage

### Generate Coverage Report
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
open htmlcov/index.html
```

### Coverage Targets
- Unit tests: 80%+
- Integration tests: 60%+
- Overall: 70%+

## Troubleshooting

### Tests Hang
- Check for missing `await` on async calls
- Look for infinite loops
- Add `--timeout=30` to fail slow tests

### Import Errors
- Ensure you're in the project root
- Check `PYTHONPATH` includes `src/`
- Run `pip install -e .`

### Flaky Tests
- Check for time-dependent code
- Look for shared state between tests
- Consider using `pytest-randomly` to detect order dependencies

## Parallel Test Execution

Tests can run in parallel using pytest-xdist for faster feedback:

```bash
# Auto-detect CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4

# Run serial tests separately
pytest -m serial -n0
pytest -m "not serial" -n auto
```

**Note:** Tests marked with `@pytest.mark.serial` will not run in parallel to prevent race conditions.

## Test Reports

### HTML Reports

Generate detailed HTML test reports:

```bash
# Basic HTML report
pytest --html=reports/test-report.html --self-contained-html

# With coverage
pytest --cov=src --cov-report=html --html=reports/test-report.html
```

### JUnit XML (for CI)

```bash
pytest --junitxml=reports/junit.xml
```

### Coverage Reports

```bash
# Terminal + HTML
pytest --cov=src --cov-report=term-missing --cov-report=html

# XML for CI tools (Codecov, etc.)
pytest --cov=src --cov-report=xml

# JSON format
pytest --cov=src --cov-report=json
```

## Test Infrastructure

### Test Constants

Use constants from `tests/constants.py` instead of magic values:

```python
from tests.constants import (
    TEST_OPENAI_API_KEY,
    TEST_TIMEOUT_FAST,
    HTTP_OK,
    DEFAULT_COMPANY_NAME,
)

def test_api_call():
    response = client.get("/api/v1/health")
    assert response.status_code == HTTP_OK
```

### Custom Assertions

Use assertion helpers from `tests/assertions.py`:

```python
from tests.assertions import (
    assert_valid_response,
    assert_json_response,
    assert_valid_company_profile,
    assert_non_empty_string,
)

def test_company_endpoint(client):
    response = client.get("/api/v1/company/test")
    assert_valid_response(response, expected_status=200)
    data = assert_json_response(response, required_fields=["name", "website"])
    assert_valid_company_profile(data)
```

### Mock Fixtures

Pre-configured mocks available in `conftest.py`:

```python
def test_with_openai_mock(mock_openai_client):
    """Mock OpenAI client with configurable responses."""
    mock_openai_client.set_response("Custom AI response")
    # Your test code

def test_with_all_services_mocked(mock_all_services):
    """All external services mocked at once."""
    # Tests run in complete isolation

@pytest.mark.asyncio
async def test_browser_mock(mock_browser):
    """Mock browser for web scraping tests."""
    mock_browser.set_html("<html>Test</html>")
    result = await mock_browser.fetch("https://example.com")
```

### Test Factories

Generate realistic test data with factories:

```python
def test_with_factory_data(company_factory, financial_factory):
    """Use factories for realistic test data."""
    company = company_factory()
    financials = financial_factory(revenue=1000000)

    result = analyze_company(company, financials)
    assert result is not None
```

## Adding New Tests

1. Create test file in appropriate directory (`unit/`, `integration/`, etc.)
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Use existing fixtures from `conftest.py`
4. Use constants from `tests/constants.py`
5. Use assertion helpers from `tests/assertions.py`
6. Follow naming conventions
7. Add docstrings explaining test purpose

## Advanced Testing

### Mutation Testing

Mutation testing verifies test quality by introducing bugs (mutations) and checking if tests catch them:

```bash
# Run mutation tests on core module
mutmut run --paths-to-mutate=src/core/

# View mutation results
mutmut results

# Show surviving mutants (tests missed)
mutmut show <mutant_id>

# Generate HTML report
mutmut html
```

**Target:** 70%+ mutation score for core modules.

### Fuzz Testing

Property-based fuzz testing with Hypothesis discovers edge cases:

```bash
# Run fuzz tests
pytest tests/fuzz/ -v

# Run with more examples
pytest tests/fuzz/ -v --hypothesis-settings='{"max_examples": 1000}'
```

Fuzz tests cover:

- String inputs (unicode, special chars, XSS attempts)
- URL validation
- JSON parsing
- Numeric boundaries
- Date/time handling

### Chaos Engineering

Chaos tests verify system resilience under failure conditions:

```bash
# Run chaos tests
pytest -m chaos -v

# Skip chaos tests in normal runs
pytest -m "not chaos"
```

Chaos scenarios tested:

- Network timeouts
- API failures
- Rate limiting
- Database disconnection
- Memory pressure

## CI Configuration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest -m "not manual and not requires_api" --cov=src --junitxml=reports/junit.xml
      - uses: codecov/codecov-action@v4
```
