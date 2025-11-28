# TE-013: Tests Are Too Slow

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

Current tests take too long to run, discouraging developers from running them frequently. Slow tests reduce the feedback loop and make TDD impractical.

## Current State

- Tests hit real external services (slow)
- No parallel test execution
- No test categorization by speed
- Full test suite time unknown (not measured)
- No fast subset for quick feedback

## Impact

- **Reduced test frequency**: Developers skip tests
- **Slow CI**: Long wait times for PR feedback
- **TDD impractical**: Can't run tests frequently
- **Developer frustration**: Tests feel like a burden

## Proposed Solution

1. **Categorize tests by speed**:

   ```python
   @pytest.mark.fast  # < 100ms
   def test_config_loading():
       pass

   @pytest.mark.medium  # < 1s
   def test_agent_initialization():
       pass

   @pytest.mark.slow  # > 1s
   def test_full_research_flow():
       pass
   ```

2. **Enable parallel execution**:

   ```bash
   pip install pytest-xdist

   # Run tests in parallel
   pytest -n auto  # Use all CPU cores
   pytest -n 4     # Use 4 workers
   ```

3. **Create fast test subset**:

   ```bash
   # Quick smoke tests
   pytest -m "fast" --timeout=10

   # Full suite excluding slow tests
   pytest -m "not slow"
   ```

4. **Add test timeouts**:

   ```python
   @pytest.mark.timeout(5)
   def test_should_be_fast():
       """This test should complete in 5 seconds."""
       pass
   ```

5. **Profile slow tests**:

   ```bash
   pytest --durations=20  # Show 20 slowest tests
   ```

## Acceptance Criteria

- [ ] All tests categorized by speed (fast/medium/slow)
- [ ] Parallel execution enabled with pytest-xdist
- [ ] Fast test suite runs in < 30 seconds
- [ ] Full test suite runs in < 5 minutes
- [ ] Slowest tests identified and optimized
- [ ] CI uses parallel execution

## Related Issues

- [TE-008](TE-008-no-ci-integration.md) - No CI/CD test integration
- [TE-009](TE-009-flaky-tests.md) - Tests depend on external services
