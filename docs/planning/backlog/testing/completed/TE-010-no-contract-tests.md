# TE-010: No API Contract Tests

**Priority**: High
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Created tests/contract/test_api_contracts.py with schema validation, OpenAPI tests, response validation, and backward compatibility tests. Added pydantic_schema_validator and openapi_schema fixtures to conftest.py. Added pact-python to dependencies.

## Description

The API has no contract tests to verify that request/response schemas match documentation and client expectations. Schema changes could break clients without detection.

## Current State

- FastAPI generates OpenAPI schema automatically
- No tests verify schema correctness
- No tests for backward compatibility
- No schema versioning
- No consumer contract testing

## Impact

- **Breaking changes undetected**: Schema changes break clients
- **Documentation drift**: Docs don't match implementation
- **Integration failures**: Consumers get unexpected responses
- **Version management**: No clear API versioning

## Proposed Solution

1. **Create schema validation tests**:

   ```python
   def test_research_request_schema():
       """Verify research request schema matches spec."""
       from src.api.models import ResearchRequest
       schema = ResearchRequest.model_json_schema()

       assert "company_name" in schema["properties"]
       assert schema["properties"]["company_name"]["type"] == "string"
       assert "company_name" in schema["required"]

   def test_research_response_schema():
       """Verify research response schema matches spec."""
       from src.api.models import ResearchResponse
       schema = ResearchResponse.model_json_schema()

       assert "task_id" in schema["properties"]
       assert "status" in schema["properties"]
   ```

2. **Add OpenAPI snapshot tests**:

   ```python
   def test_openapi_schema_unchanged(snapshot):
       """Verify OpenAPI schema hasn't changed unexpectedly."""
       from src.api.app import app
       schema = app.openapi()
       assert schema == snapshot
   ```

3. **Add response validation**:

   ```python
   def test_api_response_matches_schema(api_client):
       """Verify actual response matches declared schema."""
       response = api_client.post("/api/v1/research", json={
           "company_name": "Test Corp",
           "website": "https://test.com"
       })

       # Validate against Pydantic model
       from src.api.models import ResearchResponse
       ResearchResponse.model_validate(response.json())
   ```

4. **Add backward compatibility tests**:

   ```python
   def test_v1_request_still_works():
       """Verify old request format still works."""
       old_format_request = {
           "company_name": "Test",
           # Old format fields
       }
       response = api_client.post("/api/v1/research", json=old_format_request)
       assert response.status_code == 200
   ```

5. **Consider Pact for consumer-driven contracts**:

   ```python
   # If external consumers exist
   from pact import Consumer, Provider

   pact = Consumer('WebClient').has_pact_with(Provider('ResearchAPI'))
   ```

## Acceptance Criteria

- [ ] Schema validation tests for all request/response models
- [ ] OpenAPI schema snapshot test
- [ ] Response validation against Pydantic models
- [ ] Backward compatibility tests for existing endpoints
- [ ] Schema versioning strategy documented
- [ ] Tests fail if schema changes unexpectedly

## Related Issues

- [TE-002](TE-002-no-integration-tests.md) - No integration test suite
- [TE-011](TE-011-no-snapshot-tests.md) - No snapshot testing
