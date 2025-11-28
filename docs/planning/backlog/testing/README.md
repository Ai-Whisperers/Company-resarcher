# Testing Issues

**Category**: Cross-cutting Testing Concerns
**Status**: 32/32 issues resolved
**Remaining**: 0 open

## Overview

Testing infrastructure issues that affect all modules. These issues relate to test coverage, test quality, and testing practices.

## Completed Issues (32)

| # | Issue | Resolution |
|---|-------|------------|
| TE-001 | No unit tests | tests/unit/ has comprehensive coverage |
| TE-002 | No integration tests | tests/integration/ with automated graph workflow tests |
| TE-003 | No security tests | tests/security/ exists |
| TE-004 | No load tests | tests/load/ with Locust |
| TE-005 | No mocking strategy | tests/mocks.py with comprehensive mock implementations |
| TE-006 | No fixtures | conftest.py has shared fixtures |
| TE-007 | No coverage tracking | pyproject.toml configured with 50% threshold |
| TE-008 | No CI integration | .github/workflows/test.yml exists |
| TE-009 | Flaky tests | pytest-vcr/rerunfailures, VCR config fixtures |
| TE-010 | No contract tests | tests/contract/ with schema validation tests |
| TE-011 | No snapshot tests | tests/snapshot/ with syrupy snapshot tests |
| TE-012 | No E2E tests | tests/e2e/ exists |
| TE-013 | Slow tests | Speed markers (fast/slow), pytest-xdist parallel execution |
| TE-014 | No test data generation | factories.py with BulkDataGenerator, ResearchStateFactory |
| TE-015 | No boundary tests | tests/unit/test_boundary_conditions.py with comprehensive edge cases |
| TE-016 | No error tests | tests/unit/test_error_paths.py with error handling tests |
| TE-017 | No concurrency tests | tests/unit/test_concurrency.py with race condition tests |
| TE-018 | No regression tests | tests/regression/ exists |
| TE-019 | Inconsistent assertions | tests/assertions.py with custom helpers |
| TE-020 | No property tests | tests/property/ exists |
| TE-021 | No mutation tests | mutmut configured in pyproject.toml |
| TE-022 | No fuzz tests | tests/fuzz/test_fuzz_inputs.py with Hypothesis |
| TE-023 | No smoke tests | tests/smoke/ exists |
| TE-024 | No chaos tests | tests/chaos/ with resilience tests |
| TE-025 | No test docs | tests/README.md with comprehensive documentation |
| TE-026 | Inconsistent naming | Naming guidelines documented in tests/README.md |
| TE-027 | No test reports | pytest-html configured, README updated |
| TE-028 | No test categories | All markers defined, auto-marking by directory |
| TE-029 | No parallel tests | pytest-xdist configured, serial marker added |
| TE-030 | No test cleanup | session_cleanup, db_transaction, temp_file_tracker fixtures |
| TE-031 | Hardcoded values | tests/constants.py with centralized constants |
| TE-032 | No test isolation | autouse fixtures for env/singleton reset |

See [completed/](completed/) for detailed resolution notes.

## Test Infrastructure Status

| Type | Location | Status |
|------|----------|--------|
| Unit | tests/unit/ | Complete |
| Integration | tests/integration/ | Complete |
| Contract | tests/contract/ | Complete |
| Snapshot | tests/snapshot/ | Complete |
| E2E | tests/e2e/ | Complete |
| Security | tests/security/ | Complete |
| Load | tests/load/ | Complete |
| Property | tests/property/ | Complete |
| Regression | tests/regression/ | Complete |
| Smoke | tests/smoke/ | Complete |
| Chaos | tests/chaos/ | Complete |
| Fuzz | tests/fuzz/ | Complete |

## Test Markers

| Marker | Description | Run Command |
|--------|-------------|-------------|
| `unit` | Fast, isolated tests | `pytest -m unit` |
| `integration` | Uses mocked external services | `pytest -m integration` |
| `e2e` | End-to-end workflow tests | `pytest -m e2e` |
| `slow` | Takes >10s | `pytest -m "not slow"` |
| `fast` | Quick tests (<100ms) | `pytest -m fast` |
| `chaos` | Chaos/fault injection tests | `pytest -m chaos` |
| `concurrent` | Concurrency tests | `pytest -m concurrent` |
| `contract` | API contract tests | `pytest -m contract` |
| `snapshot` | Snapshot comparison tests | `pytest -m snapshot` |
| `security` | Security-related tests | `pytest -m security` |
| `serial` | Must run serially | `pytest -m serial -n0` |

## Running Tests

```bash
# Quick feedback (unit tests only)
pytest -m unit --timeout=10

# Pre-commit (unit + fast integration)
pytest -m "unit or (integration and not slow)"

# Full CI run
pytest -m "not manual and not requires_api" --cov=src

# Chaos tests (weekly)
pytest -m chaos

# Fuzz tests
pytest tests/fuzz/ -v
```
