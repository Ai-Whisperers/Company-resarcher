# BUG-053: Search Fallback Chain Not Triggering on Tavily Rate Limit

## Summary
When Tavily returns "exceeds your plan's set usage limit" error, the search fallback chain does NOT trigger fallback to DuckDuckGo or other providers. Instead, searches fail completely with 0 results.

## Severity
**CRITICAL** - Complete search failure when primary provider is rate-limited

## Symptoms
### Log Evidence (from latest test run)
```
15:58:32 - search_tool - ERROR - Search failed for 'industry market size and growth': This request exceeds your plan's set usage limit. Please upgrade your plan or contact support@tavily.com
15:58:32 - search_tool - ERROR - Search failed for 'Personal Paraguay target audience demographics': This request exceeds your plan's set usage limit. Please upgrade your plan or contact support@tavily.com
15:58:32 - search_tool - ERROR - Search failed for 'Personal Paraguay industry trends': This request exceeds your plan's set usage limit. Please upgrade your plan or contact support@tavily.com
15:58:32 - search_tool - ERROR - Search failed for 'Personal Paraguay market share industry': This request exceeds your plan's set usage limit. Please upgrade your plan or contact support@tavily.com
15:58:32 - pipeline - INFO - [search_execution] Search completed total_sources=0 successful_queries=4 failed_queries=0
```

### Critical Observations
1. All 4 queries failed with "exceeds your plan's set usage limit"
2. **total_sources=0** - No results returned
3. **failed_queries=0** - Failures not counted correctly!
4. DuckDuckGo fallback was NOT attempted
5. All 5 research phases completed with 0 sources

### Expected Behavior
When Tavily fails with rate limit:
1. RateLimitError should be raised
2. SearchManager should catch and try next provider (DuckDuckGo)
3. If DuckDuckGo fails, try Jina, then LangSearch, then Serper

## Root Cause Analysis

### 1. Rate Limit Detection Pattern Not Matching
Despite adding patterns in BUG-038, the error isn't being detected:
```python
# tavily_provider.py - Current patterns
rate_limit_patterns = [
    "usage limit",      # Should match "exceeds your plan's set usage limit"
    "rate limit",
    "quota",
    "exceeds your plan",  # Should match!
    "upgrade your plan",
    "too many requests",
    "429",
]
```

The pattern "exceeds your plan" SHOULD match, but it's not being triggered.

### 2. Exception Not Propagating as RateLimitError
The Tavily client may be wrapping the error differently:
```python
# Possible issue - exception type not caught
except Exception as e:
    error_str = str(e).lower()
    # If e is a complex exception object, str(e) might not contain the message
```

### 3. SearchManager Not Catching RateLimitError Correctly
```python
# src/tools/search/manager.py
async def search(self, query: str, max_results: int = 10):
    for provider in self.providers:
        try:
            results = await provider.search(query, max_results)
            if results:
                return results
        except RateLimitError:
            continue  # Try next provider
        except SearchError:
            continue  # Try next provider
```

If exception isn't RateLimitError, it might be re-raised and not caught.

### 4. search_tool.py Swallowing Exceptions
The search_tool wrapper might be catching and logging errors without re-raising:
```python
# Possible anti-pattern in search_tool.py
try:
    results = await manager.search(query)
    return results
except Exception as e:
    logger.error(f"Search failed: {e}")
    return []  # Returns empty list instead of trying fallback!
```

## Affected Files
- `src/tools/search/tavily_provider.py` - Rate limit detection
- `src/tools/search/manager.py` - Fallback chain logic
- `src/tools/search_tool.py` - Search tool wrapper
- `src/pipeline/stages/search_execution.py` - Search invocation

## Investigation Steps

### Step 1: Add Debug Logging
```python
# tavily_provider.py
except Exception as e:
    error_str = str(e).lower()
    logger.debug(f"Tavily error type: {type(e).__name__}")
    logger.debug(f"Tavily error string: {error_str}")

    for pattern in rate_limit_patterns:
        if pattern in error_str:
            logger.info(f"Matched rate limit pattern: {pattern}")
            raise RateLimitError(self.name, query)
```

### Step 2: Check Exception Chain
```python
# Check if error is nested
if hasattr(e, '__cause__') and e.__cause__:
    logger.debug(f"Cause: {e.__cause__}")
if hasattr(e, 'response') and e.response:
    logger.debug(f"Response: {e.response}")
```

## Proposed Solutions

### Solution 1: Fix Exception String Extraction
```python
# tavily_provider.py
except Exception as e:
    # Try multiple ways to get error message
    error_messages = [
        str(e).lower(),
        getattr(e, 'message', '').lower(),
        repr(e).lower(),
    ]

    # Check response body if available
    if hasattr(e, 'response'):
        try:
            error_messages.append(str(e.response.text).lower())
        except:
            pass

    combined_error = ' '.join(error_messages)

    if any(pattern in combined_error for pattern in rate_limit_patterns):
        logger.warning(f"Tavily rate limited: {e}")
        raise RateLimitError(self.name, query)
```

### Solution 2: Fix SearchManager Fallback
```python
# src/tools/search/manager.py
async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
    """Search with automatic provider fallback."""
    errors = []

    for provider in sorted(self.providers, key=lambda p: p.priority):
        if not provider.is_available():
            continue

        try:
            logger.info(f"Trying provider: {provider.name}")
            results = await provider.search(query, max_results)
            if results:
                logger.info(f"Provider {provider.name} returned {len(results)} results")
                return results
            else:
                logger.warning(f"Provider {provider.name} returned 0 results")
                # Continue to next provider if no results
                continue

        except RateLimitError as e:
            logger.warning(f"Provider {provider.name} rate limited, trying next")
            errors.append((provider.name, e))
            continue

        except SearchError as e:
            logger.warning(f"Provider {provider.name} failed: {e}")
            errors.append((provider.name, e))
            continue

        except Exception as e:
            # Catch ANY exception and try next provider
            logger.error(f"Provider {provider.name} unexpected error: {e}")
            errors.append((provider.name, e))
            continue

    # All providers failed
    if errors:
        logger.error(f"All search providers failed: {errors}")
    return []
```

### Solution 3: Fix search_tool.py Wrapper
```python
# src/tools/search_tool.py
async def search(query: str, max_results: int = 10) -> List[SearchResult]:
    """Execute search - let manager handle fallback."""
    manager = get_search_manager()

    # Don't catch exceptions here - let manager handle fallback
    results = await manager.search(query, max_results)

    if not results:
        logger.warning(f"No results found for '{query}' from any provider")

    return results
```

### Solution 4: Ensure DuckDuckGo is in Provider Chain
```python
# src/tools/search/manager.py
def _init_default_providers(self):
    """Initialize default provider chain."""
    # DuckDuckGo should ALWAYS be available (no API key needed)
    self.providers.append(DuckDuckGoProvider())  # Priority 1

    # Add other providers based on API key availability
    if jina_available:
        self.providers.append(JinaSearchProvider())  # Priority 2

    # ... etc
```

## Test Cases
```python
async def test_fallback_on_tavily_rate_limit():
    """Ensure fallback to DuckDuckGo when Tavily is rate limited."""
    # Mock Tavily to always raise rate limit error
    with patch.object(TavilyProvider, 'search') as mock_tavily:
        mock_tavily.side_effect = RateLimitError("tavily", "test query")

        manager = SearchManager()
        results = await manager.search("test query")

        # Should get results from DuckDuckGo
        assert len(results) > 0
        assert results[0].source == "duckduckgo"

async def test_fallback_counts_correctly():
    """Ensure failed queries are counted correctly."""
    # All providers fail
    manager = SearchManager()
    # ... mock all to fail

    stats = await manager.search_with_stats("test")
    assert stats.failed_queries > 0 or stats.total_sources == 0

async def test_rate_limit_pattern_detection():
    """Ensure rate limit error is detected from Tavily response."""
    provider = TavilyProvider(api_key="test")

    with pytest.raises(RateLimitError):
        # Simulate the exact error message
        raise Exception("This request exceeds your plan's set usage limit")
```

## Acceptance Criteria
- [ ] Tavily rate limit error triggers RateLimitError exception
- [ ] SearchManager catches RateLimitError and tries next provider
- [ ] DuckDuckGo (free, no API key) is always available as fallback
- [ ] Logs clearly show fallback chain execution
- [ ] failed_queries count is accurate
- [ ] At least one provider returns results (not all 0)

## Priority
This is the **most critical bug** because it causes complete search failure. Without search results, no research can be conducted.

## Related Issues
- BUG-038: Search fallback not triggering (previous partial fix)
- BUG-047: AI provider rate limits

## Labels
`critical`, `bug`, `search`, `fallback`, `rate-limiting`
