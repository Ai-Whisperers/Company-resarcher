# TO-006: API Keys Exposed in URLs

## Status: NOT APPLICABLE

## Priority: Critical

## Description

Some external API calls may include API keys in URL parameters, exposing them in logs and browser history.

## Location

- **File**: `src/tools/search.py`
- **File**: `src/tools/youtube_tool.py`

## Recommended Fix

```python
# Use headers instead of URL params
headers = {"Authorization": f"Bearer {api_key}"}
response = await session.get(url, headers=headers)
```

## Impact

- **Severity**: High
- **Risk**: Credential exposure

## Resolution

**Reviewed**: 2024-11-28

Upon code review, this issue is **not applicable**:

1. **search.py**: Uses `TavilyClient` which handles API key internally via headers (not URL params)
2. **youtube_tool.py**: Uses `YouTubeTranscriptApi` which does NOT require any API key - it scrapes public transcripts

No API keys are exposed in URLs in either file.
