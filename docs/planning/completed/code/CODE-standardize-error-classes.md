# [RESOLVED] CODE: Standardize Error Classes

**Status**: RESOLVED
**Original File**: 08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** We have `ResultSearchError`, `ProviderSearchError`, etc.

**Acceptance Criteria:**
- [ ] Create a unified `ResearchError` hierarchy in `src/core/exceptions.py`.
- [ ] Ensure all tools raise/return these standard errors.

## Resolution

Comprehensive exception hierarchy implemented in `src/core/exceptions.py`.

### Implementation Details

**Base Exception:** `CompanyResearcherError`

**Hierarchy:**
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
│   ├── PipelineTimeoutError
│   └── TimeoutBudgetExhaustedError
└── ToolError
    ├── ToolNotFoundError
    └── ToolExecutionError
```

### Features

- **Structured details** - All exceptions have `to_dict()` for API/logging
- **Context preservation** - Provider, URL, stage info in exception details
- **Cause chaining** - `cause` parameter for wrapped exceptions
- **Comprehensive coverage** - AI, Network, Validation, Search, Pipeline, Tool errors

### Files

- `src/core/exceptions.py` - 399 lines, 21 exception classes

### Usage

```python
from src.core.exceptions import (
    AIRateLimitError,
    SearchProviderError,
    StageError,
)

raise AIRateLimitError(provider="openai", retry_after=60)
raise SearchProviderError("API Error", provider="tavily", query="test")
raise StageError(stage="research", message="Failed", cause=original_error)
```

### Exports

All 21 exception classes exported via `__all__`.
