# TE-018: No Regression Test Suite

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

There's no dedicated regression test suite that captures previously fixed bugs. Bugs can be reintroduced without detection.

## Current State

- No documented bug fixes with corresponding tests
- No regression test directory
- No tracking of bug-to-test mapping
- Past issues may resurface

## Impact

- **Bug recurrence**: Fixed bugs come back
- **Lost knowledge**: Bug fixes not documented in tests
- **Wasted effort**: Re-fixing same issues
- **Quality degradation**: Accumulated regressions

## Proposed Solution

1. **Create regression test directory**:

   ```
   tests/
   └── regression/
       ├── __init__.py
       ├── test_issue_001_cache_key_collision.py
       ├── test_issue_002_rate_limit_handling.py
       └── README.md
   ```

2. **Document regression tests**:

   ```python
   # test_issue_001_cache_key_collision.py
   """
   Regression test for Issue #001: Cache key collision

   Bug: Cache keys didn't include model name, causing wrong
        responses to be returned for different models.

   Fix: Added model name to cache key generation.
   Commit: abc123
   Date: 2024-01-15
   """

   def test_cache_key_includes_model():
       """Verify cache keys are unique per model."""
       key1 = generate_cache_key("prompt", model="gpt-4")
       key2 = generate_cache_key("prompt", model="claude-3")

       assert key1 != key2
   ```

3. **Create bug tracking template**:

   ```markdown
   # Regression Test: Issue #XXX

   ## Bug Description
   [What was broken]

   ## Root Cause
   [Why it happened]

   ## Fix Applied
   [How it was fixed]

   ## Test Coverage
   - [ ] Unit test for specific fix
   - [ ] Integration test for workflow
   - [ ] Edge cases covered

   ## References
   - Issue: #XXX
   - Commit: abc123
   - PR: #YYY
   ```

4. **Add regression marker**:

   ```python
   @pytest.mark.regression
   @pytest.mark.bug("GH-001")
   def test_cache_key_collision_fixed():
       """Regression test for GitHub issue #001."""
       pass
   ```

5. **Run regression suite before releases**:

   ```bash
   # Run all regression tests
   pytest -m regression -v

   # Run specific bug regression
   pytest -m "bug(GH-001)"
   ```

## Process for New Bugs

1. Bug is reported/discovered
2. Create failing test that reproduces bug
3. Fix the bug
4. Verify test passes
5. Move test to `tests/regression/`
6. Document in test docstring

## Acceptance Criteria

- [ ] `tests/regression/` directory created
- [ ] Template for regression tests documented
- [ ] Pytest marker `@pytest.mark.regression` available
- [ ] At least 5 regression tests added for known issues
- [ ] Regression suite runs in CI before releases
- [ ] Process documented in `tests/regression/README.md`

## Related Issues

- [TE-011](TE-011-no-snapshot-tests.md) - No snapshot testing
- [TE-025](TE-025-no-test-docs.md) - No test documentation
