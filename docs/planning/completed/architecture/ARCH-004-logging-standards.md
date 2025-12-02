# ARCH-004: Logging Standards and Structure

## Priority: Medium
## Category: Architecture
## Status: Complete ✅

## Summary

Establish consistent logging standards across all modules.

## Implementation Tasks

- [x] Define logging levels usage guide
- [x] Add structured logging fields
- [x] Implement log correlation (request IDs)
- [x] Add log aggregation support (JSON formatter)
- [x] Document logging standards

## Implementation Details

### Location

`src/core/logger.py`

### Logging Levels Usage Guide

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic info | Function entry/exit, variable values |
| INFO | General operational events | Request started, task completed |
| WARNING | Unexpected but recoverable | Missing optional config, deprecated usage |
| ERROR | Errors affecting specific operations | API call failed, parsing error |
| CRITICAL | Severe errors, system shutdown | Database unavailable, out of memory |

### Structured Logging Features

1. **LogContext for Structured Fields**

   ```python
   from src.core.logger import LogContext, set_log_context, update_log_context

   # Set context at request start
   ctx = LogContext(request_id="req-123", company="Acme Corp")
   token = set_log_context(ctx)

   # Add fields during processing
   update_log_context(stage="research", provider="openai")
   ```

2. **Request ID Correlation**

   ```python
   from src.core.logger import set_request_id, get_request_id

   # Set at request entry point
   token = set_request_id("req-123")

   # All logs automatically include [req-123] prefix
   logger.info("Processing started")  # -> [req-123] Processing started
   ```

3. **Timing Decorator**

   ```python
   from src.core.logger import timed

   @timed
   async def slow_operation():
       # Automatically logs: "slow_operation completed in 1.234s"
       pass
   ```

### Formatters

1. **ColoredFormatter** - Development (console)
   - Color-coded by level (DEBUG=cyan, INFO=green, etc.)
   - Request ID prefix
   - API key sanitization

2. **SanitizingFormatter** - File output
   - Standard format with timestamps
   - API key redaction

3. **StructuredJSONFormatter** - Production/aggregation

   ```json
   {
     "timestamp": "2024-01-15T10:30:00+00:00",
     "level": "INFO",
     "logger": "src.pipeline.orchestrator",
     "message": "Research completed",
     "request_id": "req-123",
     "context": {"company": "Acme", "stage": "analysis"},
     "extra": {"duration_ms": 1234}
   }
   ```

### Setup Functions

```python
from src.core.logger import setup_logger, get_logger

# Basic setup
logger = setup_logger(__name__)

# Production with JSON output
logger = setup_logger(__name__, json_output=True)

# Environment-aware setup
logger = get_logger(__name__)  # Checks LOG_FORMAT and LOG_LEVEL env vars
```

### Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| LOG_FORMAT | json, text | Output format (default: text) |
| LOG_LEVEL | DEBUG, INFO, WARNING, ERROR | Minimum level |
| LOG_DIR | path | Directory for log files |

### Security Features

- API key sanitization with 20+ provider patterns
- Covers OpenAI, Anthropic, Google, AWS, Stripe, GitHub, etc.
- Pre-compiled regex for performance
