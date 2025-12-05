# DO-014: Error Codes Not Documented

**Priority**: Medium
**Category**: Documentation
**Status**: Open
**Effort**: Small (1-2 hours)

## Problem

Custom error codes and exception types are not documented.

## Impact

- API consumers cannot handle errors properly
- Inconsistent error handling across codebase
- Support cannot reference error codes

## Current Error Handling

### HTTP Status Codes (API)
| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid input |
| 404 | Not Found | Task ID not found |
| 413 | Payload Too Large | Request body > 1MB |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Unexpected error |

### Custom Exceptions
Located in `src/core/exceptions.py` (if exists):
- Need to audit and document

### LLM-Specific Errors
- Rate limit errors
- Token limit errors
- API key errors
- Model availability errors

## Solution

Create `docs/reference/ERROR_CODES.md` with:
1. HTTP status code reference
2. Custom exception types
3. Error response format
4. Handling recommendations

## Error Response Format

```json
{
    "detail": "Human-readable error message",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60
}
```

## Acceptance Criteria

- [ ] HTTP status codes documented
- [ ] Custom exceptions documented
- [ ] Error response format defined
- [ ] Client handling examples provided
