# TE-020: No Property-Based Testing

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

Tests use specific example inputs. Property-based testing with Hypothesis would find edge cases and generate diverse test inputs automatically.

## Current State

- All tests use hardcoded inputs
- Edge cases must be manually identified
- Limited input diversity
- No Hypothesis or similar tools

## Impact

- **Missed edge cases**: Manual examples don't cover all scenarios
- **Brittle tests**: Tests coupled to specific values
- **Limited coverage**: Only tested scenarios covered
- **Bug discovery**: Unusual inputs not tested

## Property-Based Testing Concepts

Property-based testing verifies that properties hold for ALL valid inputs, not just specific examples:

| Example-Based | Property-Based |
|---------------|----------------|
| `assert add(2, 3) == 5` | `assert add(a, b) == add(b, a)` for all a, b |
| Test specific company | Test any valid company profile |
| Test known URL | Test any well-formed URL |

## Proposed Solution

1. **Install Hypothesis**:

   ```bash
   pip install hypothesis
   ```

2. **Create property tests for data models**:

   ```python
   from hypothesis import given, strategies as st

   @given(st.text(min_size=1, max_size=100))
   def test_company_name_roundtrip(name):
       """Company name survives serialization."""
       profile = CompanyProfile(name=name)
       serialized = profile.model_dump_json()
       restored = CompanyProfile.model_validate_json(serialized)
       assert restored.name == name

   @given(st.integers(min_value=0))
   def test_market_cap_non_negative(market_cap):
       """Market cap calculations preserve non-negativity."""
       data = FinancialData(market_cap=market_cap)
       assert data.market_cap >= 0
   ```

3. **Create property tests for functions**:

   ```python
   from hypothesis import given, strategies as st

   @given(st.text())
   def test_cache_key_deterministic(prompt):
       """Same input always produces same cache key."""
       key1 = generate_cache_key(prompt)
       key2 = generate_cache_key(prompt)
       assert key1 == key2

   @given(st.lists(st.text(), min_size=0, max_size=100))
   def test_search_results_preserve_order(queries):
       """Search results maintain query order."""
       # Property: order of results matches order of queries
       pass
   ```

4. **Create custom strategies**:

   ```python
   from hypothesis import strategies as st

   # Custom strategy for company profiles
   company_strategy = st.fixed_dictionaries({
       "name": st.text(min_size=1, max_size=100),
       "website": st.from_regex(r"https://[a-z]+\.com", fullmatch=True),
       "industry": st.sampled_from(["Tech", "Finance", "Healthcare"]),
   })

   @given(company_strategy)
   def test_company_profile_valid(profile):
       """Any generated company profile is valid."""
       result = validate_company_profile(profile)
       assert result.is_valid
   ```

5. **Add stateful testing**:

   ```python
   from hypothesis.stateful import RuleBasedStateMachine, rule

   class ResearchStateMachine(RuleBasedStateMachine):
       """Test research state transitions."""

       def __init__(self):
           super().__init__()
           self.state = ResearchState()

       @rule(data=st.text())
       def add_source(self, data):
           self.state.add_source(data)
           assert data in self.state.sources

       @rule()
       def clear_sources(self):
           self.state.clear_sources()
           assert len(self.state.sources) == 0
   ```

## Acceptance Criteria

- [ ] Hypothesis installed and configured
- [ ] Property tests for data model serialization
- [ ] Property tests for cache key generation
- [ ] Custom strategies for domain objects
- [ ] At least 10 property-based tests
- [ ] Hypothesis settings configured in conftest.py

## Configuration

```python
# conftest.py
from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=1000)
settings.register_profile("dev", max_examples=100)
settings.load_profile("dev")
```

## Related Issues

- [TE-014](TE-014-no-test-data.md) - No test data generation
- [TE-022](TE-022-no-fuzz-tests.md) - No fuzz testing
