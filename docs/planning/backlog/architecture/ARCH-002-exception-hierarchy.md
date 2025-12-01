# ARCH-002: Create Exception Hierarchy

## Priority: High
## Category: Architecture
## Status: Complete ✅

## Summary

Create a proper exception hierarchy for better error handling and differentiation.

## Implementation Tasks

- [x] Create src/core/exceptions.py
- [x] Define base CompanyResearcherError
- [x] Create AI-specific exceptions
- [x] Create network-specific exceptions
- [x] Create validation exceptions
- [x] Create search-specific exceptions
- [x] Create pipeline-specific exceptions
- [x] Create tool-specific exceptions

## Implementation Details

### Location

`src/core/exceptions.py`

### Exception Hierarchy

```
CompanyResearcherError (base)
├── AIError
│   ├── AIProviderError
│   ├── AIRateLimitError
│   ├── AITimeoutError
│   ├── AIResponseError
│   └── AIModelNotFoundError
├── NetworkError
│   ├── ConnectionFailedError
│   ├── NetworkTimeoutError
│   ├── HTTPError
│   └── RateLimitedError
├── ValidationError
│   ├── ConfigValidationError
│   ├── InputValidationError
│   └── SchemaValidationError
├── SearchError
│   ├── SearchProviderError
│   ├── NoResultsError
│   └── SearchQuotaExceededError
├── PipelineError
│   ├── StageError
│   ├── OrchestratorError
│   └── PipelineTimeoutError
└── ToolError
    ├── ToolNotFoundError
    └── ToolExecutionError
```

### Key Features

1. **Base Exception with Structured Data**

   ```python
   class CompanyResearcherError(Exception):
       def __init__(self, message: str, details: Optional[dict] = None):
           self.message = message
           self.details = details or {}

       def to_dict(self) -> dict:
           """Convert to dictionary for API responses/logging."""
   ```

2. **Contextual Information**

   Each exception type captures relevant context:
   - AI exceptions: provider, error_code, retry_after
   - Network exceptions: url, status_code, timeout
   - Validation exceptions: field, invalid_value
   - Search exceptions: query, provider
   - Pipeline exceptions: stage, cause

3. **Usage Example**

   ```python
   from src.core.exceptions import AIRateLimitError, SearchProviderError

   try:
       result = await ai_client.generate(prompt)
   except AIRateLimitError as e:
       logger.warning(f"Rate limited by {e.provider}, retry after {e.retry_after}s")
   except SearchProviderError as e:
       logger.error(f"Search failed: {e.to_dict()}")
   ```
