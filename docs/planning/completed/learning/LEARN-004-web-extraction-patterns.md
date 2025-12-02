# LEARN-004: Web Extraction Patterns

## Status: RESOLVED

**Resolved Date:** 2025-12-01
**Implementation:** [src/tools/crawl4ai_tool.py](../../../../src/tools/crawl4ai_tool.py)

## Topic Overview

Modern web extraction patterns for handling dynamic content, anti-bot measures, and unstructured data.

## Key Concepts Implemented

- **Headless Browsers**: Playwright-based async crawling
- **DOM Traversal**: CSS/XPath selectors
- **LLM Extraction**: AI-powered content parsing
- **Chunking**: Semantic content clustering

## Implementation Details

### 1. Crawl4AITool (`crawl4ai_tool.py`)
```python
class Crawl4AITool:
    """
    Advanced web crawling tool with:
    - Single URL and deep crawling
    - BFS/DFS strategies
    - URL scoring for prioritization
    - Multiple extraction strategies
    """
    async def crawl(self, url, extraction_strategy) -> CrawlResult
    async def deep_crawl(self, root_url, max_depth, strategy) -> DeepCrawlResult
```

### 2. Deep Crawling Strategies
```python
class CrawlStrategy(Enum):
    BFS = "bfs"  # Breadth-First Search
    DFS = "dfs"  # Depth-First Search
```

### 3. URL Scoring System
```python
class CompositeScorer(URLScorer):
    # Combines multiple scoring factors
    scorers = [
        KeywordScorer(["investor", "annual", "report"]),
        PathDepthScorer(max_depth=5),
        SectionScorer()  # Prioritizes /investor, /financials, etc.
    ]
```

### 4. Extraction Strategies

| Strategy | Description |
|----------|-------------|
| `RegexExtractionStrategy` | Pattern-based extraction (emails, currency, dates) |
| `CSSExtractionStrategy` | CSS selector-based extraction |
| `LLMExtractionStrategy` | AI-powered structured extraction |

### 5. Semantic Content Clustering
```python
class SemanticClusterer:
    """Cluster content using sentence transformers."""
    async def cluster_content(self, text, semantic_filter, threshold):
        # Returns relevant chunks with similarity scores
```

### 6. Factory Function
```python
def create_research_crawler(keywords=None):
    """Create configured crawler for company research."""
    return crawler, scorer, extraction_strategy
```

## Usage Example

```python
from src.tools.crawl4ai_tool import Crawl4AITool, CrawlStrategy

crawler = Crawl4AITool(headless=True)

# Single page crawl
result = await crawler.crawl("https://company.com/about")

# Deep crawl with scoring
result = await crawler.deep_crawl(
    "https://company.com",
    max_depth=2,
    strategy=CrawlStrategy.BFS,
    max_pages=50
)

# Semantic clustering
clusters = await crawler.crawl_with_clustering(
    "https://company.com/investors",
    semantic_filter="revenue growth"
)
```

## Learning Resources Applied

- [x] Crawl4AI library patterns
- [x] Playwright for headless browsing
- [x] Sentence transformers for semantic similarity
- [x] BeautifulSoup fallback for simple cases

## Acceptance Criteria - COMPLETED

- [x] Headless browser crawling
- [x] Deep crawling (BFS/DFS)
- [x] URL scoring and prioritization
- [x] Multiple extraction strategies
- [x] Semantic content clustering
- [x] Fallback when crawl4ai unavailable
