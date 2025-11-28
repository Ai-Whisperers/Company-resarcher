# TE-014: No Test Data Generation

**Priority**: Medium
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Enhanced tests/factories.py with BulkDataGenerator (stress_test_companies, diverse_companies, mixed_quality_sources), ResearchStateFactory (create_initial, create_with_data, create_completed, create_with_errors), and EdgeCaseGenerator.all_edge_cases(). Added bulk_data_generator and research_state_factory fixtures.

## Description

Tests use hardcoded data or minimal fixtures. There's no strategy for generating realistic test data at scale, making it difficult to test edge cases or stress scenarios.

## Current State

- Basic fixtures in `conftest.py` with static data
- No factories for generating varied test data
- No fake data generation (Faker)
- No parameterized test data
- Sample data doesn't cover edge cases

## Impact

- **Limited test coverage**: Same data tested repeatedly
- **Missing edge cases**: Unusual data not tested
- **Brittle tests**: Tests break when data changes
- **Manual data creation**: Time spent creating test data

## Proposed Solution

1. **Install Faker for realistic data**:

   ```bash
   pip install faker
   ```

2. **Create data factories**:

   ```python
   # tests/factories.py
   from faker import Faker
   from typing import Optional

   fake = Faker()

   class CompanyFactory:
       @staticmethod
       def create(
           name: Optional[str] = None,
           website: Optional[str] = None,
           industry: Optional[str] = None,
       ) -> dict:
           return {
               "name": name or fake.company(),
               "website": website or fake.url(),
               "industry": industry or fake.job()[:20],
               "description": fake.paragraph(),
               "employees": fake.random_int(10, 100000),
               "founded": fake.year(),
           }

   class FinancialDataFactory:
       @staticmethod
       def create(ticker: Optional[str] = None) -> dict:
           return {
               "ticker": ticker or fake.lexify("????").upper(),
               "market_cap": fake.random_int(1000000, 1000000000000),
               "revenue": fake.random_int(100000, 10000000000),
               "profit_margin": fake.pyfloat(min_value=-0.5, max_value=0.5),
               "pe_ratio": fake.pyfloat(min_value=5, max_value=100),
           }
   ```

3. **Create parameterized fixtures**:

   ```python
   @pytest.fixture(params=[
       {"industry": "Technology"},
       {"industry": "Healthcare"},
       {"industry": "Finance"},
       {"industry": "Manufacturing"},
   ])
   def company_by_industry(request):
       """Generate company profiles for different industries."""
       return CompanyFactory.create(**request.param)
   ```

4. **Create edge case data**:

   ```python
   @pytest.fixture(params=[
       "",                          # Empty string
       "A" * 1000,                  # Very long string
       "Test\nCompany",             # Newline in name
       "<script>alert(1)</script>", # XSS attempt
       "Test; DROP TABLE;",         # SQL injection attempt
       "测试公司",                    # Unicode
   ])
   def edge_case_company_name(request):
       """Company names for edge case testing."""
       return request.param
   ```

5. **Create bulk data generators**:

   ```python
   def generate_research_sources(count: int = 10) -> list:
       """Generate bulk research sources for testing."""
       return [
           {
               "url": fake.url(),
               "title": fake.sentence(),
               "content": fake.paragraph(nb_sentences=10),
               "source_type": fake.random_element(["article", "blog", "news"]),
               "reliability_score": fake.pyfloat(min_value=0, max_value=1),
           }
           for _ in range(count)
       ]
   ```

## Acceptance Criteria

- [ ] Faker library installed
- [ ] Data factories for Company, Financial, Research data
- [ ] Parameterized fixtures for common variations
- [ ] Edge case data generators
- [ ] Bulk data generation for stress tests
- [ ] Factories documented and easily extensible

## Related Issues

- [TE-006](TE-006-no-fixtures.md) - No shared test fixtures
- [TE-015](TE-015-no-boundary-tests.md) - Missing boundary condition tests
