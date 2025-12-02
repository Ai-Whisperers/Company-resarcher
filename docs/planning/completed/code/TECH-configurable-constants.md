# TECH-004 to TECH-016: Configurable Constants

## Status: RESOLVED

## Resolution Date: 2024-12-01

## Summary

Made all hardcoded constants configurable via environment variables across the codebase.

## Resolved Items

### Agent Configuration (TECH-004)

**File:** `src/agents/base_agent.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `MAX_CONCURRENT_QUERIES` | `AGENT_MAX_CONCURRENT_QUERIES` | 5 |
| `LLM_TIMEOUT_SECONDS` | `LLM_TIMEOUT_SECONDS` | 120 |
| `LLM_MAX_RETRIES` | `LLM_MAX_RETRIES` | 3 |

### Browser Configuration (TECH-005, TECH-012, TECH-013)

**File:** `src/tools/browser.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `FETCH_OVERALL_TIMEOUT` | `BROWSER_FETCH_TIMEOUT_SECONDS` | 60 |
| `PAGE_NAVIGATION_TIMEOUT_MS` | `BROWSER_PAGE_TIMEOUT_MS` | 30000 |
| `DEFAULT_MAX_CONCURRENT` | `BROWSER_MAX_CONCURRENT` | 5 |

### Search Configuration (TECH-006)

**File:** `src/tools/search_tool.py`, `src/tools/search/tavily_provider.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `SEARCH_TIMEOUT_SECONDS` | `SEARCH_TIMEOUT_SECONDS` | 30 |

### Graph Configuration (TECH-007, TECH-016)

**File:** `src/graph/graph_builder.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `DEFAULT_NODE_TIMEOUT` | `GRAPH_NODE_TIMEOUT_SECONDS` | 300 |
| `MAX_RETRY_ATTEMPTS` | `GRAPH_MAX_RETRY_ATTEMPTS` | 3 |
| `RETRY_BACKOFF_BASE` | `GRAPH_RETRY_BACKOFF_BASE` | 2 |
| `CIRCUIT_BREAKER_THRESHOLD` | `GRAPH_CIRCUIT_BREAKER_THRESHOLD` | 5 |
| `CIRCUIT_BREAKER_RESET_TIME` | `GRAPH_CIRCUIT_BREAKER_RESET_SECONDS` | 60 |

### Vault Configuration (TECH-008, TECH-015)

**File:** `src/core/vault.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `VAULT_STORAGE_PATH` | `VAULT_STORAGE_PATH` | "data/vault" |
| `FILE_OPERATION_TIMEOUT` | `VAULT_FILE_TIMEOUT_SECONDS` | 30 |

### Smart Router Configuration (TECH-009)

**File:** `src/core/smart_router.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `CHEAP_MODEL` | `ROUTER_CHEAP_MODEL` | "gpt-3.5-turbo" |
| `EXPENSIVE_MODEL` | `ROUTER_EXPENSIVE_MODEL` | "gpt-4-turbo-preview" |

### CORS Configuration (TECH-011, TECH-014)

**File:** `src/api/app.py`

| Constant | Environment Variable | Default |
|----------|---------------------|---------|
| `CORS_ORIGINS` | `CORS_ORIGINS` | "http://localhost:3000,http://localhost:8000" |
| `CORS_METHODS` | `CORS_METHODS` | "GET,POST,DELETE,OPTIONS" |
| `CORS_MAX_AGE` | `CORS_MAX_AGE` | 600 |

## Additional Resolved Items

### CODE-001: Configurable Research Tone

**File:** `src/core/config.py`

Added `ResearchConfig` class with configurable tone:

| Setting | Environment Variable | Default | Options |
|---------|---------------------|---------|---------|
| `tone` | `RESEARCH__TONE` | "Objective" | Objective, Analytical, Casual, Professional, Academic |
| `max_iterations` | `RESEARCH__MAX_ITERATIONS` | 3 | - |
| `min_sources` | `RESEARCH__MIN_SOURCES` | 5 | - |
| `max_sources` | `RESEARCH__MAX_SOURCES` | 20 | - |

### CODE-002: Unknown Title Fallback

**File:** `src/core/types.py`

- Added `@model_validator` to `ResearchSource` class
- Automatically replaces "Unknown" title with domain name from URL
- Handles patterns: "unknown", "unknown source", "", "untitled", "no title"
- Removes "www." prefix from domain for cleaner display

### TECH-025: Exception Handling Standardization

**File:** `src/core/exceptions.py`

- Comprehensive exception hierarchy implemented
- Base `CompanyResearcherError` with structured error details
- Specific exceptions for AI, Network, Validation, Search, Pipeline errors
- `to_dict()` method for structured logging/API responses

### TECH-031: Windows Unicode Console Encoding

**File:** `src/core/logger.py`

- `SafeStreamHandler` class implemented
- Gracefully handles Unicode encoding errors on Windows
- Uses `errors='replace'` to substitute unencodable characters
- Console output no longer crashes with non-ASCII characters

## Usage Example

```bash
# Configure via environment variables
export BROWSER_FETCH_TIMEOUT_SECONDS=90
export GRAPH_MAX_RETRY_ATTEMPTS=5
export CORS_ORIGINS="https://myapp.com,https://api.myapp.com"
export ROUTER_CHEAP_MODEL="gpt-4o-mini"

# Or in .env file
BROWSER_FETCH_TIMEOUT_SECONDS=90
GRAPH_MAX_RETRY_ATTEMPTS=5
```

## Acceptance Criteria Met

- [x] All timeout values configurable via environment
- [x] All concurrency limits configurable
- [x] CORS fully configurable for production deployment
- [x] Model names configurable per deployment
- [x] Path configurations externalized
- [x] Exception handling standardized
- [x] Windows Unicode issues resolved
