# BUG-002: Test API Authentication Failure

## Priority: High
## Category: Bug Fix / Testing
## Status: Backlog

## Summary

Unit tests in `tests/unit/test_api.py` are failing due to authentication response code mismatch. Tests expect HTTP 422 (Unprocessable Entity) but receive HTTP 401 (Unauthorized).

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `tests/unit/test_api.py` | 16+ | Test assertions expect wrong status code |
| `src/api/app.py` | 141-172 | API key verification logic |

## Current Behavior

```
FAILED tests/unit/test_api.py::test_invalid_request - Expected 422, got 401
```

The test sends a request without proper API key authentication, but expects a validation error (422) instead of an authentication error (401).

## Root Cause

The test fixtures don't properly handle the authentication middleware:
1. Requests hit the `verify_api_key` dependency first
2. Without a valid API key, returns 401 before validation runs
3. Tests expecting 422 (validation errors) never reach that code path

## Proposed Fix

### Option 1: Update Test Fixtures

```python
# tests/conftest.py

@pytest.fixture
def test_api_key():
    """Generate a test API key."""
    return "test-api-key-12345"

@pytest.fixture
def authenticated_client(test_client, test_api_key, monkeypatch):
    """Client with valid API key header."""
    monkeypatch.setenv("API_KEY", test_api_key)
    test_client.headers["X-API-Key"] = test_api_key
    return test_client
```

### Option 2: Add Unauthenticated Tests

```python
# tests/unit/test_api.py

def test_missing_api_key_returns_401(test_client):
    """Test that missing API key returns 401."""
    response = test_client.post("/api/v1/research", json={"company_name": "Test"})
    assert response.status_code == 401

def test_invalid_request_with_auth_returns_422(authenticated_client):
    """Test that invalid requests return 422 after authentication."""
    response = authenticated_client.post("/api/v1/research", json={})
    assert response.status_code == 422
```

## Implementation Tasks

- [ ] Review all test files for authentication assumptions
- [ ] Create `authenticated_client` fixture
- [ ] Update test assertions to match actual behavior
- [ ] Add explicit tests for 401 unauthorized scenarios
- [ ] Add explicit tests for 422 validation scenarios
- [ ] Verify CI pipeline passes

## Related Files

- `tests/conftest.py` - Test fixtures
- `tests/unit/test_api.py` - API unit tests
- `src/api/app.py` - API implementation
- `src/api/models.py` - Request/response models

## Success Criteria

- All API tests pass
- Tests cover both authentication and validation errors
- CI pipeline green
- No false positives in test results
