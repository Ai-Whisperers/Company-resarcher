# TE-007: No Test Coverage Tracking

**Priority**: High
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Small
**Completed**: 2025-11-28
**Resolution**: Configured coverage tracking in `pyproject.toml` with `[tool.coverage.run]`, `[tool.coverage.report]`, and `[tool.coverage.html]` sections. Added XML/JSON output formats. Set 60% coverage threshold with branch coverage.

## Description

The project has `pytest-cov` in dependencies but no coverage tracking is configured or enforced. There's no visibility into which code is tested and which is not.

## Current State

- `pytest-cov` is listed in requirements
- No coverage configuration in `pytest.ini` or `pyproject.toml`
- No coverage reports generated
- No coverage thresholds enforced
- No coverage badges or visibility

## Impact

- **Unknown coverage**: No idea what percentage of code is tested
- **Blind spots**: Critical code may be untested
- **No progress tracking**: Can't measure testing improvements
- **Quality uncertainty**: No objective measure of test quality

## Proposed Solution

1. **Configure pytest-cov in pytest.ini**:

   ```ini
   [pytest]
   addopts = -v --tb=short -ra --cov=src --cov-report=term-missing --cov-report=html
   ```

2. **Add coverage configuration to pyproject.toml**:

   ```toml
   [tool.coverage.run]
   source = ["src"]
   branch = true
   omit = [
       "*/tests/*",
       "*/__init__.py",
       "*/conftest.py",
   ]

   [tool.coverage.report]
   exclude_lines = [
       "pragma: no cover",
       "def __repr__",
       "raise NotImplementedError",
       "if TYPE_CHECKING:",
   ]
   fail_under = 60
   show_missing = true

   [tool.coverage.html]
   directory = "htmlcov"
   ```

3. **Add coverage report generation**:

   ```bash
   # Generate coverage report
   pytest --cov=src --cov-report=html --cov-report=xml

   # View report
   open htmlcov/index.html
   ```

4. **Add to CI pipeline**:

   ```yaml
   - name: Run tests with coverage
     run: pytest --cov=src --cov-report=xml --cov-fail-under=60

   - name: Upload coverage to Codecov
     uses: codecov/codecov-action@v3
   ```

5. **Add coverage badge to README**:

   ```markdown
   ![Coverage](https://codecov.io/gh/org/repo/branch/main/graph/badge.svg)
   ```

## Acceptance Criteria

- [ ] Coverage tracking configured in pytest.ini
- [ ] Coverage report generated on each test run
- [ ] HTML coverage report available
- [ ] Coverage threshold enforced (start at 60%)
- [ ] Coverage visible in CI pipeline
- [ ] Coverage badge in README

## Target Coverage Goals

| Phase | Target |
|-------|--------|
| Initial | 60% |
| Q1 | 70% |
| Q2 | 80% |
| Long-term | 85% |

## Related Issues

- [TE-001](TE-001-no-unit-tests.md) - No unit test coverage
- [TE-008](TE-008-no-ci-integration.md) - No CI/CD test integration
