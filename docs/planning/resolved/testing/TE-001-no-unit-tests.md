# TE-001: No Unit Test Coverage for Core Logic

**Priority**: Critical
**Category**: Testing
**Status**: Open
**Estimated Effort**: Large

## Description

The codebase lacks comprehensive unit test coverage for core business logic. Current tests are minimal - only basic health checks and manual scripts exist. Core modules like `ai_client.py`, `cached_ai_client.py`, `smart_router.py`, and agent logic have no automated unit tests.

## Current State

- `tests/unit/test_api.py`: Only 2 tests (health check, validation)
- `tests/unit/test_pdf.py`: Manual script, not a pytest test
- No tests for:
  - `src/core/ai_client.py`
  - `src/core/cached_ai_client.py`
  - `src/core/smart_router.py`
  - `src/core/config.py`
  - `src/agents/*.py` (all agent logic)
  - `src/tools/*.py` (tool logic)

## Impact

- **Risk of regressions**: Changes can break existing functionality without detection
- **Low confidence in changes**: Developers hesitate to refactor
- **Technical debt accumulation**: Issues discovered late in production
- **Slower development**: Manual testing required for every change

## Proposed Solution

1. **Create unit tests for core modules**:
   - `test_ai_client.py` - Test AI client abstraction
   - `test_cached_ai_client.py` - Test caching behavior
   - `test_smart_router.py` - Test routing logic
   - `test_config.py` - Test configuration loading

2. **Create unit tests for agents**:
   - `test_base_agent.py` - Test base agent functionality
   - `test_factory.py` - Test agent factory
   - `test_orchestrator.py` - Test orchestration logic

3. **Create unit tests for tools**:
   - `test_browser.py` - Test browser tool
   - `test_search.py` - Test search tool
   - `test_financial_data.py` - Test financial data tool

4. **Target coverage**: 80%+ for core logic

## Acceptance Criteria

- [ ] Unit tests exist for all core modules (`src/core/`)
- [ ] Unit tests exist for all agent classes (`src/agents/`)
- [ ] Unit tests exist for all tool classes (`src/tools/`)
- [ ] All unit tests use mocks for external dependencies
- [ ] Tests are fast (<1s per test)
- [ ] Coverage report shows 80%+ coverage for tested modules

## Related Issues

- [TE-005](TE-005-no-mocking-strategy.md) - No consistent mocking strategy
- [TE-006](TE-006-no-fixtures.md) - No shared test fixtures
- [TE-007](TE-007-no-coverage-tracking.md) - No test coverage tracking
