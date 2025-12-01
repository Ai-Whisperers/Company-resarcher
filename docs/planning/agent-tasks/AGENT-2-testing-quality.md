# Agent 2: Testing & Quality Assurance

## Focus Area
Test coverage, quality scoring, and validation systems.

## Priority: HIGH

---

## Task 1: Critical Test Coverage Gaps (TEST-001)
**File:** `docs/planning/backlog/testing/TEST-001-test-suite-gaps.md`

### Subtasks
- [ ] Add unit tests for OutputManager
- [ ] Add mock tests for SearchTool
- [ ] Create integration test for full research pipeline
- [ ] Add security-focused test cases

### Files to Create
- `tests/unit/test_output_manager.py`
- `tests/unit/test_search_tool.py`
- `tests/integration/test_full_pipeline.py`
- `tests/security/test_injection.py`

---

## Task 2: Advanced Testing (TEST-001-advanced)
**File:** `docs/planning/backlog/testing/TEST-001-advanced-testing.md`

### Subtasks
- [ ] Implement agent behavior testing framework
- [ ] Create golden output tests for report consistency
- [ ] Add chaos testing for resilience verification
- [ ] Set up property-based testing with Hypothesis

### Files to Create
- `tests/behavior/test_agent_behavior.py`
- `tests/golden/` directory with expected outputs
- `tests/chaos/test_failure_scenarios.py`
- `tests/property/test_invariants.py`

---

## Task 3: Report Quality System (FEAT-010)
**File:** `docs/planning/backlog/features/FEAT-010-report-quality.md`

### Subtasks
- [ ] Create `src/templates/report_schema.py` with Pydantic models
- [ ] Implement `src/services/report_scorer.py` with multi-dimensional scoring
- [ ] Add depth indicators detection (percentages, financial figures)
- [ ] Create source bibliography generator
- [ ] Add boilerplate text detection and rejection

### Files to Create
- `src/templates/report_schema.py`
- `src/services/report_scorer.py`

### Quality Scoring Dimensions
```python
scores = {
    "completeness": 0.85,    # Expected sections present
    "source_quality": 0.72,  # Authoritative sources used
    "depth": 0.68,           # Specific data vs generic
    "actionability": 0.75,   # Useful recommendations
    "freshness": 0.90,       # Recent sources used
}
```

---

## Task 4: Validation Systems
**Files:** `docs/planning/backlog/validation/VAL-001-*.md` through `VAL-006-*.md`

### Subtasks
- [ ] Implement research request validation (VAL-001)
- [ ] Add search query validation (VAL-002)
- [ ] Add prompt path validation (VAL-003)
- [ ] Implement vault filename validation (VAL-004)
- [ ] Add URL revalidation for search results (VAL-005)

### Files to Create
- `src/core/validators.py` (consolidated validation module)

### Files to Modify
- `src/api/models.py`
- `src/tools/search_tool.py`
- `src/core/prompt_store.py`

---

## Task 5: Error Handling Tests (TEST-005)
**File:** `docs/planning/backlog/testing/TEST-005-error-handling-tests.md`

### Subtasks
- [ ] Test all exception types from exception hierarchy
- [ ] Verify error messages are user-friendly
- [ ] Test error recovery paths
- [ ] Verify no sensitive data in error responses

### Files to Create
- `tests/unit/test_exceptions.py`
- `tests/unit/test_error_recovery.py`

---

## Acceptance Criteria
- [ ] Test coverage > 80% for critical paths
- [ ] All reports pass schema validation
- [ ] Quality scores generated for every report
- [ ] Reports below 0.60 threshold flagged for review
- [ ] All validation modules have corresponding tests

## Estimated Scope
- **Test files to create:** 10-15
- **Source files to create:** 3-4
- **Source files to modify:** 5-7

---

## Getting Started

```bash
# Check current coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with verbose failure output
pytest tests/ -v --tb=short
```

## Test Organization
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests
├── behavior/       # Agent behavior tests
├── golden/         # Expected output comparisons
├── chaos/          # Failure scenario tests
├── security/       # Security-focused tests
└── property/       # Property-based tests
```

## Related Documentation
- [FEAT-010-report-quality.md](../backlog/features/FEAT-010-report-quality.md)
- [TEST-001-test-suite-gaps.md](../backlog/testing/TEST-001-test-suite-gaps.md)
