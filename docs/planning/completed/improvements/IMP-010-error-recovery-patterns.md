# IMP-010: Improved Error Recovery Patterns

## Problem Statement

When an agent fails (e.g., API error, parsing error), the whole workflow often crashes. We need better resilience.

## Proposed Solution

Implement robust error recovery patterns found in `MCP-Agents`:

- **Retry with Backoff**: Automatically retry transient errors.
- **Fallback Strategies**: If Strategy A fails, try Strategy B (e.g., if LLM extraction fails, try Regex).
- **Graceful Degradation**: Return partial results instead of crashing.

## Implementation Steps

1.  Create a `RetryDecorator` with exponential backoff.
2.  Wrap critical tool calls with try/except blocks that trigger fallbacks.
3.  Ensure agents return a "Partial Success" status if some sub-tasks failed.

## Code Example

```python
@retry(max_attempts=3, backoff=2)
async def robust_fetch(url):
    try:
        return await fetch(url)
    except NetworkError:
        return await fetch_from_archive(url)
```

## Acceptance Criteria

- [ ] System recovers from network glitches automatically.
- [ ] Workflows complete even if one non-critical step fails.
- [ ] Errors are logged but don't stop the show.

## Source References

- Repo: `AI-Software-Engineering-Team-MCP-Multi-Agent-System`
