# TE-016: Missing Error Path Tests

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

Tests primarily cover success scenarios. Error handling paths—exceptions, API failures, timeouts, invalid inputs—are not systematically tested.

## Current State

- Tests verify successful operations
- No tests for exception handling
- No tests for API error responses
- No tests for timeout scenarios
- No tests for partial failures

## Impact

- **Poor error messages**: Users see cryptic errors
- **Unhandled exceptions**: System crashes on errors
- **Data inconsistency**: Partial operations not rolled back
- **Silent failures**: Errors not properly logged

## Error Scenarios to Test

| Component | Error Scenarios |
|-----------|-----------------|
| AI Client | Rate limit, timeout, invalid response, quota exceeded |
| Search Tool | No results, timeout, invalid query |
| Browser | Page not found, timeout, JavaScript error |
| Database | Connection error, constraint violation |
| Graph | Node failure, state corruption |

## Proposed Solution

1. **AI Client error tests**:

   ```python
   @pytest.mark.asyncio
   async def test_ai_client_rate_limit_handling():
       """Test graceful handling of rate limits."""
       mock_client = AsyncMock()
       mock_client.generate.side_effect = RateLimitError("Rate limit exceeded")

       ai_client = AIClient(mock_client)
       result = await ai_client.generate("test prompt")

       assert result.error == "rate_limit"
       assert ai_client.retry_count > 0

   @pytest.mark.asyncio
   async def test_ai_client_timeout_handling():
       """Test timeout handling."""
       mock_client = AsyncMock()
       mock_client.generate.side_effect = asyncio.TimeoutError()

       ai_client = AIClient(mock_client)
       with pytest.raises(AITimeoutError):
           await ai_client.generate("test prompt")
   ```

2. **Search tool error tests**:

   ```python
   def test_search_no_results():
       """Test handling of empty search results."""
       mock_search = MagicMock()
       mock_search.search.return_value = []

       result = search_tool.search("nonexistent query xyz123")
       assert result == []
       assert search_tool.last_error is None

   def test_search_api_error():
       """Test handling of search API errors."""
       mock_search = MagicMock()
       mock_search.search.side_effect = SearchAPIError("Service unavailable")

       with pytest.raises(SearchAPIError):
           search_tool.search("test query")
   ```

3. **Browser error tests**:

   ```python
   @pytest.mark.asyncio
   async def test_browser_page_not_found():
       """Test handling of 404 pages."""
       result = await browser_tool.fetch("https://example.com/nonexistent")
       assert result.status == 404
       assert result.content is None

   @pytest.mark.asyncio
   async def test_browser_timeout():
       """Test handling of page load timeout."""
       with pytest.raises(BrowserTimeoutError):
           await browser_tool.fetch("https://slow-site.com", timeout=1)
   ```

4. **Database error tests**:

   ```python
   def test_database_connection_error(monkeypatch):
       """Test handling of database connection errors."""
       monkeypatch.setattr(
           "sqlalchemy.create_engine",
           MagicMock(side_effect=OperationalError("Connection refused"))
       )

       with pytest.raises(DatabaseConnectionError):
           init_database()

   def test_database_constraint_violation():
       """Test handling of constraint violations."""
       # Try to insert duplicate primary key
       with pytest.raises(IntegrityError):
           db.add(ResearchTask(id="duplicate-id", ...))
           db.add(ResearchTask(id="duplicate-id", ...))
   ```

5. **Graph error tests**:

   ```python
   @pytest.mark.asyncio
   async def test_graph_node_failure_recovery():
       """Test graph continues after node failure."""
       mock_financial_agent = AsyncMock()
       mock_financial_agent.run.side_effect = AgentError("API failed")

       result = await graph.ainvoke(initial_state)

       # Graph should continue with other nodes
       assert result.errors == ["financial: API failed"]
       assert result.market_data is not None  # Other nodes ran
   ```

## Acceptance Criteria

- [ ] Error tests for all AI client failure modes
- [ ] Error tests for all tool failure modes
- [ ] Error tests for database operations
- [ ] Error tests for graph node failures
- [ ] Each error test verifies proper error handling
- [ ] Error messages are user-friendly

## Related Issues

- [TE-015](TE-015-no-boundary-tests.md) - Missing boundary condition tests
- [TE-003](TE-003-no-security-tests.md) - No security testing
