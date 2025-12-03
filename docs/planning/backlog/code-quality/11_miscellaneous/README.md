# Miscellaneous Issues

> **Total Issues**: 10 (0 HIGH, 6 MEDIUM, 4 LOW)
> **Priority**: Ongoing

## Overview

Miscellaneous issues that don't fit into other categories but still affect code quality.

## Issues Summary

### MEDIUM Severity (6)

| ID | File | Description |
|----|------|-------------|
| CQ-161 | pipeline/stage.py | datetime.utcnow() deprecated |
| CQ-162 | pipeline/pipeline.py | datetime.utcnow() deprecated |
| CQ-163 | api/app.py | Inconsistent logging levels |
| CQ-164 | api/app.py | Mixed response structures |
| CQ-165 | Various | Python 3.10+ syntax issues |
| CQ-166 | Various | Inconsistent import styles |

### LOW Severity (4)

| ID | File | Description |
|----|------|-------------|
| CQ-167 | Various | Unused variables |
| CQ-168 | Various | Naming convention issues |
| CQ-169 | Various | Long import lists |
| CQ-170 | Various | Minor code style issues |

## Fixes

### CQ-161/162: Deprecated datetime.utcnow()

**Problem**: Python 3.12 deprecates `datetime.utcnow()`
```python
# DEPRECATED
from datetime import datetime
now = datetime.utcnow()
```

**Solution**:
```python
# CORRECT
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### CQ-163: Inconsistent Logging Levels

**Problem**: Using warning for expected behavior
```python
# BAD - Warning for expected dev behavior
if not api_key:
    logger.warning("API key not configured")  # Expected in dev!
```

**Solution**:
```python
# GOOD - Info for expected conditions
if not api_key:
    logger.info("API key not configured, running in development mode")
```

### CQ-164: Mixed Response Structures

**Problem**: Endpoints return different structures
```python
# Inconsistent
@app.get("/cancel")
def cancel() -> dict:  # Returns dict
    return {"status": "cancelled"}

@app.post("/start")
def start() -> ResearchResponse:  # Returns model
    return ResearchResponse(...)
```

**Solution**: Use consistent response models
```python
# Consistent
from pydantic import BaseModel

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None

@app.get("/cancel")
def cancel() -> StatusResponse:
    return StatusResponse(status="cancelled")
```

### CQ-165: Python Version Compatibility

**Problem**: Using Python 3.10+ syntax
```python
# Python 3.10+ only
def get_result() -> tuple[str, int]:
    pass

def process(data: dict | None):
    pass
```

**Solution**: Use typing module for 3.9 compatibility
```python
# Python 3.9 compatible
from typing import Tuple, Optional, Union, Dict

def get_result() -> Tuple[str, int]:
    pass

def process(data: Optional[Dict[str, Any]]):
    pass
```

### CQ-166: Inconsistent Import Styles

**Problem**: Mixed import organization
```python
# Inconsistent
import asyncio
from typing import List
import os
from datetime import datetime
from .utils import helper
import json
```

**Solution**: Follow standard order
```python
# Standard library (alphabetical)
import asyncio
import json
import os
from datetime import datetime
from typing import List

# Third-party imports
import httpx
from pydantic import BaseModel

# Local imports
from .utils import helper
```

## Code Style Guidelines

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local imports
4. Each group separated by blank line
5. Alphabetical within each group

### Logging Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: Normal operation, expected events
- `WARNING`: Unexpected but recoverable situations
- `ERROR`: Errors that prevent specific operations
- `CRITICAL`: System-level failures

### Response Models
- All endpoints return Pydantic models
- Use consistent field naming (snake_case)
- Include timestamp in responses
- Use Optional for nullable fields

## Verification Checklist

- [ ] No deprecated datetime methods
- [ ] Logging levels appropriate for message type
- [ ] All endpoints return Pydantic models
- [ ] Python 3.9 compatible syntax
- [ ] Imports follow standard organization
- [ ] No unused variables
- [ ] Consistent naming conventions
