# TE-021: No Mutation Testing

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

There's no mutation testing to verify test quality. Tests might pass but fail to detect actual bugs in the code. Mutation testing introduces bugs and checks if tests catch them.

## Current State

- No mutation testing tools configured
- Test quality unmeasured
- Unknown if tests would catch real bugs
- No mutation score metrics

## Impact

- **False confidence**: Tests pass but don't detect bugs
- **Weak assertions**: Tests don't verify important behavior
- **Low test quality**: Coverage without effectiveness
- **Missed bugs**: Real bugs slip through "passing" tests

## What is Mutation Testing?

Mutation testing creates "mutants" of your code by making small changes:

| Mutation Type | Original | Mutant |
|--------------|----------|--------|
| Boundary | `if x > 0` | `if x >= 0` |
| Negation | `if x > 0` | `if x <= 0` |
| Return | `return True` | `return False` |
| Arithmetic | `x + y` | `x - y` |
| Removal | `log(message)` | (removed) |

Good tests should "kill" mutants (fail when mutant runs). Surviving mutants indicate test gaps.

## Proposed Solution

1. **Install mutmut**:

   ```bash
   pip install mutmut
   ```

2. **Configure mutmut**:

   ```ini
   # setup.cfg
   [mutmut]
   paths_to_mutate = src/
   tests_dir = tests/
   runner = python -m pytest -x
   ```

3. **Run mutation testing**:

   ```bash
   # Run mutation tests
   mutmut run

   # View results
   mutmut results

   # Show surviving mutants
   mutmut show <mutant_id>

   # Generate HTML report
   mutmut html
   ```

4. **Interpret results**:

   ```
   Mutation score: 75% (300 killed / 400 total)

   Surviving mutants indicate test gaps:
   - src/core/ai_client.py: 10 survivors
   - src/agents/base_agent.py: 5 survivors
   ```

5. **Add to CI (optional, slow)**:

   ```yaml
   mutation-testing:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - name: Run mutation tests
         run: |
           pip install mutmut
           mutmut run --paths-to-mutate=src/core/
           mutmut results
       - name: Check mutation score
         run: |
           SCORE=$(mutmut results --CI)
           if [ "$SCORE" -lt 70 ]; then
             echo "Mutation score too low: $SCORE%"
             exit 1
           fi
   ```

6. **Focus on critical code**:

   ```bash
   # Mutate only critical modules
   mutmut run --paths-to-mutate=src/core/ai_client.py,src/core/smart_router.py
   ```

## Acceptance Criteria

- [ ] mutmut installed and configured
- [ ] Initial mutation test run completed
- [ ] Mutation score baseline established
- [ ] Top surviving mutants analyzed
- [ ] Tests added to kill critical mutants
- [ ] Target: 70% mutation score for core modules

## Expected Output

```
Legend for output:
🎉 Killed mutants (tests caught the bug)
🙈 Survived mutants (tests missed the bug)
⏰ Timeout mutants
🔇 Suspicious mutants

Mutants killed: 280
Mutants survived: 95
Mutation score: 74.7%
```

## Related Issues

- [TE-007](TE-007-no-coverage-tracking.md) - No test coverage tracking
- [TE-001](TE-001-no-unit-tests.md) - No unit test coverage
