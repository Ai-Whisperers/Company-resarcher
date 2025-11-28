# TE-006: No Shared Test Fixtures

**Priority**: High
**Category**: Testing
**Status**: Partially Addressed
**Estimated Effort**: Small

## Description

While `conftest.py` exists with some fixtures, the fixture coverage is incomplete. Many common test scenarios require repetitive setup code that should be shared across tests.

## Current State

Existing fixtures in `conftest.py`:
- ✅ `project_root` - Project root directory
- ✅ `test_data_dir` - Test data directory
- ✅ `temp_output_dir` - Temporary output directory
- ✅ `env_vars` - Environment variables
- ✅ `mock_ai_client` - Basic AI client mock
- ✅ `mock_search_tool` - Search tool mock
- ✅ `mock_browser_tool` - Browser tool mock
- ✅ `sample_company_profile` - Company profile data
- ✅ `sample_research_sources` - Research sources
- ✅ `sample_financial_data` - Financial data
- ✅ `api_client` - FastAPI test client
- ✅ `initial_research_state` - Graph state

Missing fixtures:
- ❌ Database session fixture
- ❌ Mock LLM response fixtures (varied responses)
- ❌ File-based test data fixtures
- ❌ Agent instance fixtures
- ❌ Tool instance fixtures
- ❌ Graph instance fixtures

## Impact

- **Code duplication**: Same setup code in multiple tests
- **Inconsistent test data**: Each test creates different data
- **Maintenance burden**: Changes require multiple updates
- **Slow test development**: More time setting up than testing

## Proposed Solution

1. **Add database fixtures**:

   ```python
   @pytest.fixture
   async def db_session():
       """Provide a test database session."""
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       async with AsyncSession(engine) as session:
           yield session
   ```

2. **Add agent fixtures**:

   ```python
   @pytest.fixture
   def mock_financial_agent(mock_ai_client, mock_search_tool):
       """Provide a configured financial agent."""
       return FinancialAgent(
           ai_client=mock_ai_client,
           search_tool=mock_search_tool
       )
   ```

3. **Add varied response fixtures**:

   ```python
   @pytest.fixture(params=["success", "error", "empty"])
   def ai_response_scenario(request):
       """Provide various AI response scenarios."""
       scenarios = {
           "success": {"content": "Valid response", "status": "ok"},
           "error": {"error": "API error", "status": "error"},
           "empty": {"content": "", "status": "ok"},
       }
       return scenarios[request.param]
   ```

4. **Add file-based fixtures**:

   ```python
   @pytest.fixture
   def sample_pdf_path(test_data_dir) -> Path:
       """Provide path to sample PDF file."""
       return test_data_dir / "sample.pdf"

   @pytest.fixture
   def sample_html_content() -> str:
       """Provide sample HTML content."""
       return "<html><body><h1>Test</h1></body></html>"
   ```

## Acceptance Criteria

- [ ] Database session fixture available
- [ ] Agent instance fixtures for all agents
- [ ] Tool instance fixtures for all tools
- [ ] Varied response fixtures for edge cases
- [ ] File-based test data fixtures
- [ ] All fixtures documented with docstrings

## Related Issues

- [TE-005](TE-005-no-mocking-strategy.md) - No consistent mocking strategy
- [TE-014](TE-014-no-test-data.md) - No test data generation
