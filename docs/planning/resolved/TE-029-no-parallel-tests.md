# TE-029: Tests Don't Run in Parallel

**Priority**: Low
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Small
**Completed**: 2025-11-28
**Resolution**: `pytest-xdist` already in dependencies. Added `serial` marker for non-parallelizable tests. Updated `tests/README.md` with parallel execution documentation. Added isolation fixtures in `conftest.py`.

## Description

Tests run sequentially, even though most are independent. Parallel execution would significantly reduce test suite runtime.

## Current State

- Tests run one at a time
- No pytest-xdist configured
- Full suite takes longer than necessary
- CI wait times extended

## Impact

- **Slow feedback**: Tests take longer than needed
- **CI costs**: Extended runner time
- **Developer friction**: Waiting for tests
- **Underutilized resources**: Single-core test execution

## Proposed Solution

1. **Install pytest-xdist**:

   ```bash
   pip install pytest-xdist
   ```

2. **Configure parallel execution**:

   ```ini
   # pytest.ini
   [pytest]
   addopts = -n auto  # Use all available CPUs
   ```

3. **Run tests in parallel**:

   ```bash
   # Auto-detect cores
   pytest -n auto

   # Specific number of workers
   pytest -n 4

   # Load balance by test duration
   pytest -n auto --dist=loadscope
   ```

4. **Ensure test isolation**:

   ```python
   # Tests must not share state
   # BAD: Shared database connection
   db = create_db()

   def test_one():
       db.insert(...)

   def test_two():
       db.query(...)  # Depends on test_one!

   # GOOD: Each test creates own state
   @pytest.fixture
   def db():
       return create_test_db()

   def test_one(db):
       db.insert(...)

   def test_two(db):
       db.query(...)  # Independent
   ```

5. **Handle non-parallelizable tests**:

   ```python
   @pytest.mark.serial
   def test_database_migration():
       """Must run alone - modifies schema."""
       pass

   # Run serial tests separately
   # pytest -m "not serial" -n auto && pytest -m serial
   ```

6. **Configure CI for parallel tests**:

   ```yaml
   test:
     runs-on: ubuntu-latest
     steps:
       - name: Run tests in parallel
         run: pytest -n auto --dist=loadscope
   ```

7. **Distribution strategies**:

   | Strategy | Flag | Best For |
   |----------|------|----------|
   | Load | `--dist=load` | Varied test durations |
   | Scope | `--dist=loadscope` | Tests with shared fixtures |
   | File | `--dist=loadfile` | File-level isolation |
   | Each | `--dist=each` | Maximum parallelism |

## Expected Improvement

| Scenario | Sequential | Parallel (4 workers) |
|----------|------------|---------------------|
| 100 unit tests | 2 min | 30s |
| 50 integration | 5 min | 1.5 min |
| Full suite | 10 min | 3 min |

## Acceptance Criteria

- [ ] pytest-xdist installed
- [ ] Default parallel execution configured
- [ ] Tests verified to be isolated
- [ ] Non-parallelizable tests marked
- [ ] CI uses parallel execution
- [ ] Test time reduced by 50%+

## Related Issues

- [TE-013](TE-013-slow-tests.md) - Tests are too slow
- [TE-032](TE-032-no-test-isolation.md) - Tests not properly isolated
