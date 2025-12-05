"""
Crawl4AI Tool - Comprehensive Web Crawling Solution

Implements:
- FEAT-001: Crawl4AI Browser Integration
- FEAT-002: BFS/DFS Deep Crawling
- FEAT-003: Multiple Extraction Strategies
- FEAT-007: URL Scoring for Prioritization
- FEAT-008: Semantic Content Clustering
- FEAT-009: Regex-Based Data Extraction
"""

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable
from urllib.parse import urljoin, urlparse
import hashlib

from src.core.logging import setup_logger

logger = setup_logger("crawl4ai_tool")


# =============================================================================
# Data Models
# =============================================================================


class CrawlStrategy(Enum):
    """Crawling strategy for deep crawls."""

    BFS = "bfs"  # Breadth-First Search
    DFS = "dfs"  # Depth-First Search


class CacheMode(Enum):
    """Cache mode for crawling."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    BYPASS = "bypass"
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"


@dataclass
class CrawlResult:
    """Result of a single URL crawl."""

    url: str
    success: bool
    markdown: Optional[str] = None
    html: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    links: List[str] = field(default_factory=list)
    error: Optional[str] = None
    depth: int = 0
    score: float = 0.0


@dataclass
class DeepCrawlResult:
    """Result of a deep crawl operation."""

    root_url: str
    strategy: CrawlStrategy
    max_depth: int
    pages_crawled: int
    pages_failed: int
    results: List[CrawlResult] = field(default_factory=list)
    total_time_seconds: float = 0.0


# =============================================================================
# FEAT-007: URL Scoring System
# =============================================================================


class URLScorer(ABC):
    """Abstract base class for URL scorers."""

    @abstractmethod
    def score(self, url: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Score a URL. Higher score = higher priority."""
        pass


class KeywordScorer(URLScorer):
    """Score URLs based on keyword presence."""

    def __init__(self, keywords: List[str], weight: float = 10.0):
        self.keywords = [kw.lower() for kw in keywords]
        self.weight = weight

    def score(self, url: str, context: Optional[Dict[str, Any]] = None) -> float:
        url_lower = url.lower()
        score = 0.0
        for kw in self.keywords:
            if kw in url_lower:
                score += self.weight
        return score


class PathDepthScorer(URLScorer):
    """Score URLs based on path depth (shorter paths score higher)."""

    def __init__(self, max_depth: int = 5, weight: float = 5.0):
        self.max_depth = max_depth
        self.weight = weight

    def score(self, url: str, context: Optional[Dict[str, Any]] = None) -> float:
        path = urlparse(url).path
        depth = len([p for p in path.split("/") if p])
        # Invert: shorter paths get higher scores
        return max(0, (self.max_depth - depth)) * self.weight


class SectionScorer(URLScorer):
    """Score URLs based on important section patterns."""

    HIGH_PRIORITY_PATTERNS = [
        r"/investor",
        r"/annual-report",
        r"/financials",
        r"/earnings",
        r"/about",
        r"/leadership",
        r"/press",
        r"/news",
        r"/blog",
    ]

    LOW_PRIORITY_PATTERNS = [
        r"/privacy",
        r"/terms",
        r"/cookie",
        r"/legal",
        r"/sitemap",
        r"/careers",
        r"/jobs",
    ]

    def __init__(self, high_weight: float = 20.0, low_weight: float = -10.0):
        self.high_weight = high_weight
        self.low_weight = low_weight

    def score(self, url: str, context: Optional[Dict[str, Any]] = None) -> float:
        url_lower = url.lower()
        score = 0.0

        for pattern in self.HIGH_PRIORITY_PATTERNS:
            if re.search(pattern, url_lower):
                score += self.high_weight

        for pattern in self.LOW_PRIORITY_PATTERNS:
            if re.search(pattern, url_lower):
                score += self.low_weight

        return score


class CompositeScorer(URLScorer):
    """Combine multiple scorers."""

    def __init__(self, scorers: List[URLScorer]):
        self.scorers = scorers

    def score(self, url: str, context: Optional[Dict[str, Any]] = None) -> float:
        return sum(s.score(url, context) for s in self.scorers)


# =============================================================================
# FEAT-003 & FEAT-009: Extraction Strategies
# =============================================================================


class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies."""

    @abstractmethod
    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        """Extract data from content."""
        pass


class RegexExtractionStrategy(ExtractionStrategy):
    """Extract data using regex patterns."""

    DEFAULT_PATTERNS = {
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone_numbers": r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "urls": r"https?://[^\s<>\"']+",
        "currency": r"\$[\d,]+(?:\.\d{2})?",
        "percentages": r"\d+(?:\.\d+)?%",
        "dates": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    }

    def __init__(self, patterns: Optional[Dict[str, str]] = None):
        self.patterns = patterns or self.DEFAULT_PATTERNS

    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        results = {}
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            results[name] = list(set(matches))  # Deduplicate
        return results


class CSSExtractionStrategy(ExtractionStrategy):
    """Extract data using CSS selectors."""

    def __init__(self, selectors: Dict[str, str]):
        """
        Args:
            selectors: Dict mapping field names to CSS selectors
        """
        self.selectors = selectors

    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")
            results = {}

            for field, selector in self.selectors.items():
                elements = soup.select(selector)
                if elements:
                    results[field] = [el.get_text(strip=True) for el in elements]

            return results
        except Exception as e:
            logger.error(f"CSS extraction failed: {e}")
            return {"error": str(e)}


class LLMExtractionStrategy(ExtractionStrategy):
    """Extract structured data using LLM."""

    def __init__(
        self,
        schema: Dict[str, Any],
        ai_client: Optional[Any] = None,
        provider: str = "openai",
    ):
        """
        Args:
            schema: JSON schema or Pydantic model schema for extraction
            ai_client: AI client to use for extraction
            provider: AI provider name
        """
        self.schema = schema
        self.ai_client = ai_client
        self.provider = provider

    async def extract(self, content: str, url: str) -> Dict[str, Any]:
        if not self.ai_client:
            return {"error": "No AI client configured for LLM extraction"}

        try:
            prompt = f"""Extract the following information from this content.

Schema: {self.schema}

Content:
{content[:8000]}  # Truncate for token limits

Return a JSON object matching the schema. Only include fields that have data."""

            response = await self.ai_client.generate(prompt)
            # Parse JSON from response
            import json

            return json.loads(response)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {"error": str(e)}


# =============================================================================
# FEAT-008: Semantic Content Clustering
# =============================================================================


class SemanticClusterer:
    """Cluster content semantically using embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.warning("sentence-transformers not installed")
                return None
        return self._model

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    async def cluster_content(
        self,
        text: str,
        semantic_filter: Optional[str] = None,
        word_count_threshold: int = 50,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Cluster text into semantic groups.

        Args:
            text: Full page text
            semantic_filter: Query to filter relevant clusters
            word_count_threshold: Minimum words per chunk
            similarity_threshold: Minimum similarity to include in results

        Returns:
            List of relevant text clusters with scores
        """
        model = self._get_model()
        if model is None:
            return [{"text": text, "score": 1.0, "error": "No embedding model"}]

        try:
            # Split into chunks
            chunks = self.chunk_text(text)

            # Filter by word count
            chunks = [c for c in chunks if len(c.split()) >= word_count_threshold]

            if not chunks:
                return []

            # Run embedding in thread pool
            embeddings = await asyncio.to_thread(model.encode, chunks)

            results = []

            if semantic_filter:
                # Compute query embedding
                query_embedding = await asyncio.to_thread(model.encode, [semantic_filter])

                # Compute similarities
                from sklearn.metrics.pairwise import cosine_similarity

                similarities = cosine_similarity(query_embedding, embeddings)[0]

                for chunk, score in zip(chunks, similarities):
                    if score >= similarity_threshold:
                        results.append({"text": chunk, "score": float(score)})

                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
            else:
                # Return all chunks without filtering
                results = [{"text": chunk, "score": 1.0} for chunk in chunks]

            return results

        except Exception as e:
            logger.error(f"Semantic clustering failed: {e}")
            return [{"text": text, "score": 1.0, "error": str(e)}]


# =============================================================================
# FEAT-001 & FEAT-002: Crawl4AI Tool
# =============================================================================


class Crawl4AITool:
    """
    Advanced web crawling tool using Crawl4AI library.

    Features:
    - Single URL crawling with markdown generation
    - Deep crawling (BFS/DFS) with configurable depth
    - URL scoring for prioritization
    - Multiple extraction strategies
    - Smart caching
    - Anti-bot detection handling
    """

    def __init__(
        self,
        headless: bool = True,
        cache_mode: CacheMode = CacheMode.ENABLED,
        user_agent: Optional[str] = None,
        timeout: int = 30000,
    ):
        self.headless = headless
        self.cache_mode = cache_mode
        self.user_agent = user_agent
        self.timeout = timeout
        self._crawler = None
        self.clusterer = SemanticClusterer()

    async def _get_crawler(self):
        """Get or create the async web crawler (CQ-104: ensure complete initialization)."""
        if self._crawler is None:
            crawler = None
            try:
                from crawl4ai import AsyncWebCrawler
                from crawl4ai.async_configs import BrowserConfig

                browser_config = BrowserConfig(
                    headless=self.headless,
                    user_agent=self.user_agent,
                )

                # Create crawler but don't assign to self._crawler until fully initialized
                crawler = AsyncWebCrawler(config=browser_config)
                await crawler.__aenter__()
                # Only assign after successful initialization
                self._crawler = crawler
            except ImportError:
                logger.error("crawl4ai not installed. Run: pip install crawl4ai")
                raise
            except Exception as e:
                # Cleanup partially initialized crawler
                if crawler is not None:
                    try:
                        await crawler.__aexit__(None, None, None)
                    except Exception:
                        pass  # Ignore cleanup errors
                logger.error(f"Failed to initialize crawler: {e}")
                raise
        return self._crawler

    async def close(self):
        """Close the crawler and release resources."""
        if self._crawler:
            await self._crawler.__aexit__(None, None, None)
            self._crawler = None

    async def crawl(
        self,
        url: str,
        extraction_strategy: Optional[ExtractionStrategy] = None,
        wait_for: Optional[str] = None,
        js_code: Optional[str] = None,
    ) -> CrawlResult:
        """
        Crawl a single URL.

        Args:
            url: URL to crawl
            extraction_strategy: Optional strategy for structured extraction
            wait_for: CSS selector to wait for before extracting
            js_code: JavaScript to execute on page

        Returns:
            CrawlResult with markdown content and extracted data
        """
        try:
            from crawl4ai.async_configs import CrawlerRunConfig

            crawler = await self._get_crawler()

            run_config = CrawlerRunConfig(
                cache_mode=self.cache_mode.value.upper(),
                wait_for=wait_for,
                js_code=js_code,
            )

            result = await crawler.arun(url=url, config=run_config)

            # Extract links from the page
            links = []
            if hasattr(result, "links") and result.links:
                links = [link.get("href", "") for link in result.links if link.get("href")]

            crawl_result = CrawlResult(
                url=url,
                success=result.success if hasattr(result, "success") else True,
                markdown=result.markdown if hasattr(result, "markdown") else None,
                html=result.html if hasattr(result, "html") else None,
                links=links,
            )

            # Apply extraction strategy if provided
            if extraction_strategy and crawl_result.markdown:
                crawl_result.extracted_data = await extraction_strategy.extract(
                    crawl_result.markdown, url
                )

            logger.info(f"Successfully crawled {url}")
            return crawl_result

        except ImportError:
            # Fallback to basic browser if crawl4ai not available
            logger.warning("crawl4ai not available, using fallback browser")
            return await self._fallback_crawl(url, extraction_strategy)

        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return CrawlResult(url=url, success=False, error=str(e))

    async def _fallback_crawl(
        self, url: str, extraction_strategy: Optional[ExtractionStrategy] = None
    ) -> CrawlResult:
        """Fallback crawl using aiohttp when crawl4ai is unavailable."""
        try:
            import aiohttp
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, "html.parser")

            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text(separator="\n", strip=True)

            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = urljoin(url, href)
                if href.startswith("http"):
                    links.append(href)

            result = CrawlResult(
                url=url,
                success=True,
                markdown=text,
                html=html,
                links=links,
            )

            if extraction_strategy:
                result.extracted_data = await extraction_strategy.extract(text, url)

            return result

        except Exception as e:
            return CrawlResult(url=url, success=False, error=str(e))

    async def deep_crawl(
        self,
        root_url: str,
        max_depth: int = 2,
        strategy: CrawlStrategy = CrawlStrategy.BFS,
        max_pages: int = 50,
        scorer: Optional[URLScorer] = None,
        same_domain_only: bool = True,
        url_filter: Optional[Callable[[str], bool]] = None,
        extraction_strategy: Optional[ExtractionStrategy] = None,
    ) -> DeepCrawlResult:
        """
        Perform deep crawling starting from a root URL.

        Args:
            root_url: Starting URL
            max_depth: Maximum crawl depth
            strategy: BFS or DFS crawling strategy
            max_pages: Maximum number of pages to crawl
            scorer: URL scorer for prioritization
            same_domain_only: Only follow links on same domain
            url_filter: Custom filter function for URLs
            extraction_strategy: Strategy for data extraction

        Returns:
            DeepCrawlResult with all crawled pages
        """
        import time

        start_time = time.time()

        root_domain = urlparse(root_url).netloc
        visited: Set[str] = set()
        results: List[CrawlResult] = []
        failed_count = 0

        # Initialize queue with root URL
        if strategy == CrawlStrategy.BFS:
            queue = [(root_url, 0)]  # (url, depth)
        else:  # DFS
            queue = [(root_url, 0)]

        # Default scorer combines multiple factors
        if scorer is None:
            scorer = CompositeScorer(
                [
                    KeywordScorer(["investor", "annual", "report", "financial", "earnings"]),
                    PathDepthScorer(),
                    SectionScorer(),
                ]
            )

        while queue and len(results) < max_pages:
            # Get next URL based on strategy
            if strategy == CrawlStrategy.BFS:
                current_url, depth = queue.pop(0)
            else:  # DFS
                current_url, depth = queue.pop()

            # Skip if already visited or exceeds depth
            url_hash = hashlib.md5(current_url.encode()).hexdigest()
            if url_hash in visited or depth > max_depth:
                continue

            visited.add(url_hash)

            # Crawl the page
            result = await self.crawl(current_url, extraction_strategy)
            result.depth = depth
            result.score = scorer.score(current_url)

            if result.success:
                results.append(result)
                logger.info(f"Crawled [{depth}] {current_url} (score: {result.score:.1f})")

                # Add links to queue if not at max depth
                if depth < max_depth:
                    new_links = []
                    for link in result.links:
                        # Normalize URL
                        if not link.startswith("http"):
                            link = urljoin(current_url, link)

                        # Apply filters
                        link_domain = urlparse(link).netloc
                        if same_domain_only and link_domain != root_domain:
                            continue

                        if url_filter and not url_filter(link):
                            continue

                        link_hash = hashlib.md5(link.encode()).hexdigest()
                        if link_hash not in visited:
                            new_links.append((link, depth + 1))

                    # Score and sort links
                    scored_links = [(url, d, scorer.score(url)) for url, d in new_links]
                    scored_links.sort(key=lambda x: x[2], reverse=True)

                    # Add to queue
                    for url, d, _ in scored_links:
                        queue.append((url, d))
            else:
                failed_count += 1

        end_time = time.time()

        return DeepCrawlResult(
            root_url=root_url,
            strategy=strategy,
            max_depth=max_depth,
            pages_crawled=len(results),
            pages_failed=failed_count,
            results=results,
            total_time_seconds=round(end_time - start_time, 2),
        )

    async def crawl_with_clustering(
        self,
        url: str,
        semantic_filter: str,
        word_count_threshold: int = 50,
        similarity_threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Crawl a URL and cluster content semantically.

        Args:
            url: URL to crawl
            semantic_filter: Query to filter relevant content
            word_count_threshold: Minimum words per chunk
            similarity_threshold: Minimum similarity score

        Returns:
            Dict with clusters and metadata
        """
        result = await self.crawl(url)

        if not result.success or not result.markdown:
            return {"url": url, "error": result.error, "clusters": []}

        clusters = await self.clusterer.cluster_content(
            result.markdown,
            semantic_filter=semantic_filter,
            word_count_threshold=word_count_threshold,
            similarity_threshold=similarity_threshold,
        )

        return {
            "url": url,
            "total_clusters": len(clusters),
            "clusters": clusters[:10],  # Top 10 most relevant
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_research_crawler(
    keywords: Optional[List[str]] = None,
) -> tuple[Crawl4AITool, URLScorer, ExtractionStrategy]:
    """
    Create a configured crawler for company research.

    Args:
        keywords: Keywords to prioritize in URL scoring

    Returns:
        Tuple of (crawler, scorer, extraction_strategy)
    """
    crawler = Crawl4AITool(headless=True, cache_mode=CacheMode.ENABLED)

    # Default research keywords
    if keywords is None:
        keywords = [
            "investor",
            "annual",
            "report",
            "financial",
            "earnings",
            "revenue",
            "profit",
            "sec",
            "10-k",
            "10-q",
        ]

    scorer = CompositeScorer(
        [
            KeywordScorer(keywords, weight=15.0),
            PathDepthScorer(max_depth=4, weight=3.0),
            SectionScorer(high_weight=20.0, low_weight=-15.0),
        ]
    )

    extraction_strategy = RegexExtractionStrategy(
        patterns={
            "revenue": r"\$[\d,.]+(?:\s*(?:million|billion|M|B))?",
            "percentages": r"[-+]?\d+(?:\.\d+)?%",
            "years": r"\b20\d{2}\b",
            "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        }
    )

    return crawler, scorer, extraction_strategy
