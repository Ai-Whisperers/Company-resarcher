# BUG-027: CORS Origins Whitespace Parsing

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:65` splits CORS origins by comma without stripping whitespace, causing validation issues.

## Current Code

```python
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "...").split(",")
# "http://a.com, http://b.com" -> ["http://a.com", " http://b.com"]
```

## Implementation Tasks

- [ ] Strip whitespace from each origin
- [ ] Validate origin format
- [ ] Log invalid origins
- [ ] Add configuration tests
