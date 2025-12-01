# INT-002: Search Provider Alternatives & Fallback Chain

## Priority: Critical
## Category: Integration
## Status: Backlog

## Summary

Implement multiple search provider integrations with automatic fallback to ensure research never fails due to API limits. Replace expensive Tavily dependency with cheaper/free alternatives.

## Problem

Current system relies solely on Tavily API which:
- Has strict usage limits (1,000 free/month)
- Costs $0.008 per request on paid plans
- No fallback when limits exceeded
- Research fails completely when Tavily unavailable

## Proposed Solution

### Search Provider Hierarchy

```
1. DuckDuckGo (DDGS)     → FREE, unlimited (with rate limits)
2. Jina AI Search        → FREE 10M tokens, then $0.02/M
3. Serper.dev            → 2,500 free, then $1/1K queries
4. DataForSEO            → $0.60/1K (cheapest at scale)
5. Tavily                → Existing, use as premium fallback
```

### Provider Comparison

| Provider | Free Tier | Paid Cost | Speed | Quality |
|----------|-----------|-----------|-------|---------|
| DuckDuckGo (DDGS) | Unlimited | FREE | ~2s | Good |
| Jina AI | 10M tokens | $0.02/M tokens | Fast | Good |
| Serper.dev | 2,500 queries | $0.30-1.00/1K | 1-2s | Excellent (Google) |
| DataForSEO | $1 credit | $0.60/1K | 2-3s | Excellent |
| Scrapingdog | Limited | $0.29/1K | 1.8s | Excellent |
| Tavily | 1,000/month | $8/1K | 2-3s | Excellent |

### Annual Cost Projection (100K searches/month)

| Provider | Monthly Cost | Annual Cost |
|----------|--------------|-------------|
| DuckDuckGo | $0 | $0 |
| Jina AI | ~$20 | ~$240 |
| Serper.dev | $75 | $900 |
| DataForSEO | $60 | $720 |
| Tavily | $800 | $9,600 |

## Implementation Design

### 1. Search Provider Interface

```python
# src/tools/search/base.py
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # Provider name

class SearchProvider(ABC):
    name: str
    priority: int  # Lower = higher priority

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and has quota."""
        pass
```

### 2. DuckDuckGo Provider (FREE)

```python
# src/tools/search/duckduckgo.py
from duckduckgo_search import DDGS
import asyncio

class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"
    priority = 1  # Highest priority (free)

    def __init__(self):
        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        try:
            # Run sync DDGS in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.ddgs.text(query, max_results=max_results)
            )
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                    source="duckduckgo"
                )
                for r in results
            ]
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            raise

    def is_available(self) -> bool:
        return True  # Always available, no API key needed
```

### 3. Jina AI Provider (FREE 10M tokens)

```python
# src/tools/search/jina.py
import httpx

class JinaSearchProvider(SearchProvider):
    name = "jina"
    priority = 2

    SEARCH_URL = "https://s.jina.ai/"
    READER_URL = "https://r.jina.ai/"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        async with httpx.AsyncClient() as client:
            # Jina search endpoint
            response = await client.get(
                f"{self.SEARCH_URL}",
                params={"q": query},
                headers={"Accept": "application/json"}
            )
            data = response.json()
            return self._parse_results(data, max_results)

    async def read_url(self, url: str) -> str:
        """Use Jina Reader to extract content from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.READER_URL}{url}")
            return response.text

    def is_available(self) -> bool:
        return True  # Free tier, no key required
```

### 4. Serper.dev Provider

```python
# src/tools/search/serper.py
import httpx
from ..core.config import settings

class SerperProvider(SearchProvider):
    name = "serper"
    priority = 3

    API_URL = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = settings.SERPER_API_KEY

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.API_URL,
                headers={"X-API-KEY": self.api_key},
                json={"q": query, "num": max_results}
            )
            data = response.json()
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("link", ""),
                    snippet=r.get("snippet", ""),
                    source="serper"
                )
                for r in data.get("organic", [])
            ]

    def is_available(self) -> bool:
        return bool(self.api_key)
```

### 5. Search Manager with Fallback

```python
# src/tools/search/manager.py
from typing import List, Optional
import asyncio

class SearchManager:
    """Manages multiple search providers with automatic fallback."""

    def __init__(self):
        self.providers: List[SearchProvider] = []
        self._init_providers()

    def _init_providers(self):
        """Initialize providers in priority order."""
        # Always add free providers
        self.providers.append(DuckDuckGoProvider())
        self.providers.append(JinaSearchProvider())

        # Add paid providers if configured
        if settings.SERPER_API_KEY:
            self.providers.append(SerperProvider())
        if settings.DATAFORSEO_LOGIN:
            self.providers.append(DataForSEOProvider())
        if settings.TAVILY_API_KEY:
            self.providers.append(TavilyProvider())

        # Sort by priority
        self.providers.sort(key=lambda p: p.priority)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        preferred_provider: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search with automatic fallback.

        Args:
            query: Search query
            max_results: Maximum results to return
            preferred_provider: Force specific provider (optional)

        Returns:
            List of search results from first successful provider
        """
        errors = []

        for provider in self.providers:
            if preferred_provider and provider.name != preferred_provider:
                continue

            if not provider.is_available():
                continue

            try:
                logger.info(f"Searching with {provider.name}: {query[:50]}...")
                results = await provider.search(query, max_results)

                if results:
                    logger.info(f"Got {len(results)} results from {provider.name}")
                    return results

            except RateLimitError as e:
                logger.warning(f"{provider.name} rate limited: {e}")
                errors.append((provider.name, str(e)))
                continue

            except Exception as e:
                logger.warning(f"{provider.name} failed: {e}")
                errors.append((provider.name, str(e)))
                continue

        # All providers failed
        raise SearchError(f"All search providers failed: {errors}")
```

### 6. Configuration

Add to `.env`:
```env
# Search Provider API Keys (all optional, system uses free providers first)

# Serper.dev - 2,500 free queries, then $1/1K
SERPER_API_KEY=

# DataForSEO - $1 free credit, then $0.60/1K
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=

# Tavily - 1,000 free/month (existing)
TAVILY_API_KEY=tvly-...

# Search Configuration
SEARCH_PROVIDER_PRIORITY=duckduckgo,jina,serper,dataforseo,tavily
SEARCH_MAX_RETRIES=3
SEARCH_TIMEOUT_SECONDS=30
```

### 7. Integration with Pipeline

```python
# src/pipeline/stages/search.py

class SearchStage(Stage):
    def __init__(self):
        self.search_manager = SearchManager()

    async def execute(self, ctx: RequestContext, queries: List[str]) -> List[SearchResult]:
        all_results = []

        for query in queries:
            try:
                results = await self.search_manager.search(
                    query,
                    max_results=settings.MAX_SEARCH_RESULTS
                )
                all_results.extend(results)
            except SearchError as e:
                logger.error(f"Search failed for '{query}': {e}")
                ctx.add_warning(f"Search failed: {query}")

        return all_results
```

## Dependencies to Add

```txt
# requirements.txt additions
duckduckgo-search>=6.0.0    # Free DuckDuckGo search
httpx>=0.27.0               # Async HTTP client (for Jina, Serper)
```

## Implementation Tasks

- [ ] Create `src/tools/search/` package structure
- [ ] Implement `SearchProvider` base class
- [ ] Implement `DuckDuckGoProvider` (FREE)
- [ ] Implement `JinaSearchProvider` (FREE)
- [ ] Implement `SerperProvider` (paid)
- [ ] Implement `DataForSEOProvider` (paid)
- [ ] Refactor existing `TavilyProvider`
- [ ] Create `SearchManager` with fallback logic
- [ ] Add configuration options to `.env.example`
- [ ] Update pipeline to use `SearchManager`
- [ ] Add unit tests for each provider
- [ ] Add integration tests for fallback chain
- [ ] Update documentation

## Testing Plan

### Unit Tests
```python
def test_duckduckgo_search():
    provider = DuckDuckGoProvider()
    results = asyncio.run(provider.search("python programming", max_results=5))
    assert len(results) > 0
    assert all(r.url for r in results)

def test_fallback_chain():
    manager = SearchManager()
    # Mock first provider to fail
    results = asyncio.run(manager.search("test query"))
    assert len(results) > 0
```

### Integration Tests
```python
@pytest.mark.integration
async def test_real_search_fallback():
    """Test that search works even if primary provider fails."""
    manager = SearchManager()
    results = await manager.search("Personal Paraguay telecommunications")
    assert len(results) >= 3
```

## Success Criteria

- [ ] Research works with zero API keys configured (using DDGS)
- [ ] Automatic fallback when provider fails/rate-limited
- [ ] 90%+ reduction in search costs
- [ ] No degradation in search quality
- [ ] Provider metrics logged for monitoring

## Migration Path

1. **Phase 1**: Add DDGS as primary provider (immediate cost savings)
2. **Phase 2**: Add Jina AI for enhanced scraping
3. **Phase 3**: Add Serper.dev as Google-quality option
4. **Phase 4**: Deprecate Tavily as primary (keep as fallback)

## References

- [DuckDuckGo Search PyPI](https://pypi.org/project/duckduckgo-search/)
- [Jina AI Reader](https://jina.ai/reader/)
- [Serper.dev](https://serper.dev/)
- [DataForSEO Pricing](https://dataforseo.com/apis/serp-api/pricing)
- [KDnuggets: Free Web Search APIs](https://www.kdnuggets.com/7-free-web-search-apis-for-ai-agents)
