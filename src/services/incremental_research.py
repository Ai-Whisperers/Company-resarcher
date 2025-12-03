"""
Incremental Research Service - Smart research that builds on existing data.

This service orchestrates intelligent incremental research by:
1. Analyzing existing outputs to understand what data we have
2. Loading the persistent source registry to avoid duplicate fetches
3. Generating targeted queries for missing data only
4. Filtering search results against already-seen URLs
5. Detecting and skipping semantically similar content
6. Merging new findings with existing data (not overwriting)
7. Updating the registry with newly fetched sources

This enables efficient multi-run research that gets better each iteration.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.logger import setup_logger
from ..core.types import ResearchSource
from .persistent_source_registry import (
    PersistentSourceRegistry,
    SourceRecord,
    get_source_registry,
)
from .existing_data_analyzer import (
    CompanyDataAnalysis,
    DataGapInfo,
    ExistingDataAnalyzer,
    get_data_analyzer,
)
from .official_site_crawler import (
    OfficialSiteCrawler,
    CrawlResult,
    detect_official_website,
    get_priority_paths_for_data,
)

logger = setup_logger("incremental_research")


@dataclass
class IncrementalStats:
    """Statistics for an incremental research run."""
    urls_skipped_seen: int = 0
    urls_skipped_similar: int = 0
    urls_fetched_new: int = 0
    queries_skipped_covered: int = 0
    queries_executed: int = 0
    gaps_before: int = 0
    gaps_filled: int = 0
    gaps_remaining: int = 0
    duration_seconds: float = 0.0
    # Official site crawling stats
    official_site_detected: bool = False
    official_site_url: Optional[str] = None
    official_pages_discovered: int = 0
    official_pages_crawled: int = 0
    official_pages_skipped: int = 0
    official_pages_failed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "urls_skipped_seen": self.urls_skipped_seen,
            "urls_skipped_similar": self.urls_skipped_similar,
            "urls_fetched_new": self.urls_fetched_new,
            "queries_skipped_covered": self.queries_skipped_covered,
            "queries_executed": self.queries_executed,
            "gaps_before": self.gaps_before,
            "gaps_filled": self.gaps_filled,
            "gaps_remaining": self.gaps_remaining,
            "duration_seconds": round(self.duration_seconds, 2),
            "efficiency_rate": self._calc_efficiency(),
            "official_site": {
                "detected": self.official_site_detected,
                "url": self.official_site_url,
                "pages_discovered": self.official_pages_discovered,
                "pages_crawled": self.official_pages_crawled,
                "pages_skipped": self.official_pages_skipped,
                "pages_failed": self.official_pages_failed,
            } if self.official_site_detected else None,
        }

    def _calc_efficiency(self) -> str:
        """Calculate research efficiency."""
        total_considered = self.urls_skipped_seen + self.urls_skipped_similar + self.urls_fetched_new
        if total_considered == 0:
            return "N/A"
        skipped = self.urls_skipped_seen + self.urls_skipped_similar
        return f"{skipped / total_considered:.0%} dedup rate"


@dataclass
class IncrementalResearchResult:
    """Result of incremental research."""
    company_name: str
    success: bool
    stats: IncrementalStats
    new_sources: List[ResearchSource]
    filled_gaps: List[str]
    remaining_gaps: List[str]
    analysis_before: Optional[CompanyDataAnalysis]
    analysis_after: Optional[CompanyDataAnalysis]
    error: Optional[str] = None


@dataclass
class FilteredSearchResult:
    """A search result that passed incremental filtering."""
    url: str
    title: str
    snippet: str
    relevance_score: float
    is_new: bool  # True if URL not seen before
    fills_gap: bool  # True if likely to fill a known gap
    target_gaps: List[str] = field(default_factory=list)


class IncrementalResearchService:
    """
    Service for intelligent incremental research.

    Integrates:
    - PersistentSourceRegistry: Track seen URLs across runs
    - ExistingDataAnalyzer: Understand current data state
    - RelevanceFilter: Score and filter results
    - Content deduplication: Skip similar content

    Usage:
        service = IncrementalResearchService("outputs")

        # Run incremental research
        result = await service.research_incremental(
            company_name="Claro Paraguay",
            industry="telecommunications",
        )

        # Check what was skipped vs fetched
        print(f"Skipped: {result.stats.urls_skipped_seen}")
        print(f"New: {result.stats.urls_fetched_new}")
    """

    def __init__(
        self,
        base_dir: str = "outputs",
        search_tool=None,
        browser_tool=None,
    ):
        """
        Initialize service.

        Args:
            base_dir: Base output directory
            search_tool: Optional search tool (lazy loaded if not provided)
            browser_tool: Optional browser tool (lazy loaded if not provided)
        """
        self.base_dir = Path(base_dir).resolve()
        self._search_tool = search_tool
        self._browser_tool = browser_tool
        self._ai_client = None

    async def _get_search_tool(self):
        """Lazy load search tool."""
        if self._search_tool is None:
            from ..tools import get_shared_search_tool
            self._search_tool = get_shared_search_tool()
        return self._search_tool

    async def _get_browser_tool(self):
        """Lazy load browser tool."""
        if self._browser_tool is None:
            from ..tools import get_shared_browser_tool
            self._browser_tool = get_shared_browser_tool()
        return self._browser_tool

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            from ..core.ai_client import get_ai_manager
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def research_incremental(
        self,
        company_name: str,
        industry: str = "telecommunications",
        country: str = "Paraguay",
        max_queries: int = 30,
        max_sources_per_query: int = 5,
        force_refetch_stale: bool = True,
    ) -> IncrementalResearchResult:
        """
        Run incremental research for a company.

        This method:
        1. Analyzes existing data to find gaps
        2. Loads source registry to know what URLs we've seen
        3. Generates queries targeting only gaps
        4. Filters search results against registry
        5. Fetches only truly new content
        6. Updates outputs with new data
        7. Records new sources in registry

        Args:
            company_name: Company to research
            industry: Industry context
            country: Country context
            max_queries: Maximum queries to execute
            max_sources_per_query: Max results per query
            force_refetch_stale: Re-fetch sources marked stale

        Returns:
            IncrementalResearchResult with stats and findings
        """
        start_time = datetime.now()
        stats = IncrementalStats()

        logger.info(f"Starting incremental research for {company_name}")

        try:
            # 1. Analyze existing data
            analyzer = get_data_analyzer(str(self.base_dir))
            analysis_before = analyzer.analyze_company(company_name)
            stats.gaps_before = len(analysis_before.all_gaps)

            logger.info(
                f"Existing data: {analysis_before.overall_completeness:.0%} complete, "
                f"{stats.gaps_before} gaps"
            )

            # 2. Load source registry
            registry = get_source_registry(company_name, str(self.base_dir))
            registry_stats = registry.get_statistics()

            logger.info(
                f"Source registry: {registry_stats['total_sources']} sources, "
                f"{registry_stats['stale_sources']} stale"
            )

            # 3. Crawl official website first (if detected)
            official_sources = await self._crawl_official_site(
                company_name=company_name,
                registry=registry,
                stats=stats,
                industry=industry,
            )

            # If we got official sources, add them to our new sources
            new_sources_official: List[ResearchSource] = []
            if official_sources:
                new_sources_official.extend(official_sources)
                logger.info(f"Official site crawl yielded {len(official_sources)} new sources")

            # 4. Generate delta queries (targeting gaps only)
            delta_queries = analyzer.get_delta_queries(analysis_before, max_queries)
            stats.queries_executed = len(delta_queries)

            if not delta_queries:
                logger.info("No gaps to fill - research is complete!")
                return IncrementalResearchResult(
                    company_name=company_name,
                    success=True,
                    stats=stats,
                    new_sources=[],
                    filled_gaps=[],
                    remaining_gaps=[g.field_name for g in analysis_before.all_gaps],
                    analysis_before=analysis_before,
                    analysis_after=analysis_before,
                )

            logger.info(f"Generated {len(delta_queries)} delta queries targeting gaps")

            # 4. Execute searches with filtering
            search_tool = await self._get_search_tool()
            filtered_results: List[FilteredSearchResult] = []

            for query_info in delta_queries:
                query = query_info["query"]
                target_field = query_info["target_field"]

                try:
                    results = await search_tool.search(query, max_results=max_sources_per_query)

                    for result in results:
                        url = result.get("url", "")
                        if not url:
                            continue

                        # Check if URL already seen
                        if registry.is_url_seen(url):
                            stats.urls_skipped_seen += 1
                            logger.debug(f"Skipping seen URL: {url[:60]}...")
                            continue

                        filtered_results.append(FilteredSearchResult(
                            url=url,
                            title=result.get("title", ""),
                            snippet=result.get("snippet", ""),
                            relevance_score=result.get("_relevance_score", 0.5),
                            is_new=True,
                            fills_gap=True,
                            target_gaps=[target_field],
                        ))

                except Exception as e:
                    logger.warning(f"Search failed for '{query[:50]}...': {e}")

                # Small delay between queries
                await asyncio.sleep(0.3)

            logger.info(
                f"Search complete: {len(filtered_results)} new URLs, "
                f"{stats.urls_skipped_seen} already seen"
            )

            # 5. Fetch new content with similarity check
            browser_tool = await self._get_browser_tool()
            new_sources: List[ResearchSource] = []

            for result in filtered_results[:50]:  # Limit fetches
                try:
                    # Fetch content
                    fetch_result = await browser_tool.fetch(result.url)
                    content = fetch_result.get("content", "")

                    if not content or len(content) < 100:
                        continue

                    # Check for similar content already in registry
                    is_similar, similar_url = registry.has_similar_content(content)
                    if is_similar:
                        stats.urls_skipped_similar += 1
                        logger.debug(
                            f"Skipping similar content: {result.url[:50]}... "
                            f"(similar to {similar_url[:50]}...)"
                        )
                        continue

                    # New unique content!
                    stats.urls_fetched_new += 1

                    source = ResearchSource(
                        url=result.url,
                        title=result.title,
                        content=content,
                        source_type="web",
                    )
                    new_sources.append(source)

                    # Record in registry
                    registry.add_source(
                        url=result.url,
                        content=content,
                        title=result.title,
                        data_types_found=set(result.target_gaps),
                        usefulness_score=0.6,  # Default, can be updated later
                    )

                    logger.debug(f"Fetched new source: {result.title[:50]}...")

                except Exception as e:
                    logger.warning(f"Fetch failed for {result.url[:50]}...: {e}")

                # Rate limiting
                await asyncio.sleep(0.5)

            logger.info(
                f"Fetching complete: {stats.urls_fetched_new} new, "
                f"{stats.urls_skipped_similar} similar skipped"
            )

            # 6. Combine official site sources with search sources
            all_new_sources = new_sources_official + new_sources
            logger.info(f"Total new sources: {len(all_new_sources)} ({len(new_sources_official)} official, {len(new_sources)} search)")

            # 7. Extract data from new sources and update outputs
            filled_gaps = []
            if all_new_sources:
                filled_gaps = await self._extract_and_update(
                    company_name=company_name,
                    sources=all_new_sources,
                    gaps=analysis_before.priority_gaps,
                    industry=industry,
                )
                stats.gaps_filled = len(filled_gaps)

            # 7. Re-analyze to get final state
            analysis_after = analyzer.analyze_company(company_name)
            stats.gaps_remaining = len(analysis_after.all_gaps)

            # Calculate duration
            stats.duration_seconds = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Incremental research complete: "
                f"{stats.gaps_filled} gaps filled, {stats.gaps_remaining} remaining"
            )

            return IncrementalResearchResult(
                company_name=company_name,
                success=True,
                stats=stats,
                new_sources=new_sources,
                filled_gaps=filled_gaps,
                remaining_gaps=[g.field_name for g in analysis_after.all_gaps],
                analysis_before=analysis_before,
                analysis_after=analysis_after,
            )

        except Exception as e:
            logger.error(f"Incremental research failed: {e}")
            stats.duration_seconds = (datetime.now() - start_time).total_seconds()

            return IncrementalResearchResult(
                company_name=company_name,
                success=False,
                stats=stats,
                new_sources=[],
                filled_gaps=[],
                remaining_gaps=[],
                analysis_before=None,
                analysis_after=None,
                error=str(e),
            )

    async def _extract_and_update(
        self,
        company_name: str,
        sources: List[ResearchSource],
        gaps: List[DataGapInfo],
        industry: str,
    ) -> List[str]:
        """
        Extract data from sources and update output files.

        Returns list of gap field names that were filled.
        """
        ai_client = await self._get_ai_client()
        filled_gaps: List[str] = []

        # Group gaps by file
        gaps_by_file: Dict[str, List[DataGapInfo]] = {}
        for gap in gaps:
            if gap.source_file:
                if gap.source_file not in gaps_by_file:
                    gaps_by_file[gap.source_file] = []
                gaps_by_file[gap.source_file].append(gap)

        # Build context from all sources
        source_context = "\n\n".join([
            f"SOURCE: {s.title}\n{s.content[:2000]}"
            for s in sources[:10]  # Limit to 10 sources
        ])

        # Try to fill each gap
        for gap in gaps[:20]:  # Limit to 20 gaps per run
            prompt = f"""Extract the {gap.field_name} for {company_name} from the following sources.

SOURCES:
{source_context[:8000]}

INSTRUCTIONS:
- Extract ONLY the {gap.field_name} value
- Be precise with numbers, percentages, dates
- If multiple values found, use the most recent/authoritative
- If not found, respond with exactly "NOT_FOUND"

{gap.field_name} for {company_name}:"""

            try:
                response = await ai_client.generate(
                    prompt=prompt,
                    system="You are a data extraction assistant. Extract specific values from sources accurately.",
                    max_tokens=150,
                    temperature=0.1,
                )

                value = response.strip()
                if value and value != "NOT_FOUND" and "not found" not in value.lower():
                    # Update the file
                    if gap.source_file and await self._update_gap_in_file(
                        gap.source_file, gap.field_name, value
                    ):
                        filled_gaps.append(gap.field_name)
                        logger.info(f"Filled gap: {gap.field_name} = {value[:50]}...")

            except Exception as e:
                logger.warning(f"Failed to extract {gap.field_name}: {e}")

        return filled_gaps

    async def _update_gap_in_file(
        self,
        file_path: str,
        field_name: str,
        value: str,
    ) -> bool:
        """Update a single gap in a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False

            content = path.read_text(encoding="utf-8")
            original_content = content

            # Patterns to replace N/A with value
            patterns = [
                (rf'(\|\s*\*\*{re.escape(field_name)}\*\*\s*\|)\s*N/A\s*\|',
                 rf'\1 {value} |'),
                (rf'(\*\*{re.escape(field_name)}:\*\*)\s*N/A',
                 rf'\1 {value}'),
                (rf'(\*\*{re.escape(field_name)}:\*\*)\s*Unknown',
                 rf'\1 {value}'),
                (rf'({re.escape(field_name)}[^|]*\|)[^|]*N/A[^|]*\|',
                 rf'\1 {value} |'),
            ]

            for pattern, replacement in patterns:
                content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
                if count > 0:
                    break

            if content != original_content:
                path.write_text(content, encoding="utf-8")
                return True

            return False

        except Exception as e:
            logger.warning(f"Failed to update {file_path}: {e}")
            return False

    async def _crawl_official_site(
        self,
        company_name: str,
        registry: PersistentSourceRegistry,
        stats: IncrementalStats,
        industry: str,
    ) -> List[ResearchSource]:
        """
        Crawl the company's official website if detected.

        This method:
        1. Tries to detect/determine the official website URL
        2. Creates an OfficialSiteCrawler and runs comprehensive crawl
        3. Updates stats with crawl results
        4. Returns list of ResearchSource from official site

        Args:
            company_name: Company name
            registry: Source registry
            stats: Stats object to update
            industry: Industry for context

        Returns:
            List of ResearchSource from official site
        """
        # Try to find official website URL
        official_url = await self._find_official_website(company_name, registry)

        if not official_url:
            logger.info(f"No official website detected for {company_name}")
            return []

        logger.info(f"Official website detected: {official_url}")
        stats.official_site_detected = True
        stats.official_site_url = official_url

        try:
            # Create crawler and run
            crawler = OfficialSiteCrawler(
                company_name=company_name,
                company_website=official_url,
                source_registry=registry,
                max_pages=50,  # Reasonable limit for official site
                max_depth=3,
            )

            crawl_result = await crawler.crawl()

            # Update stats
            stats.official_pages_discovered = crawl_result.pages_discovered
            stats.official_pages_crawled = crawl_result.pages_crawled
            stats.official_pages_skipped = crawl_result.pages_skipped_seen
            stats.official_pages_failed = crawl_result.pages_failed

            logger.info(
                f"Official site crawl complete: "
                f"{crawl_result.pages_crawled} pages from {crawl_result.pages_discovered} discovered"
            )

            return crawl_result.sources

        except Exception as e:
            logger.error(f"Official site crawl failed: {e}")
            return []

    async def _find_official_website(
        self,
        company_name: str,
        registry: PersistentSourceRegistry,
    ) -> Optional[str]:
        """
        Find the official website URL for a company.

        Strategy:
        1. Check if we already have official URLs in registry
        2. Search for official website
        3. Use heuristics to detect official domain

        Returns:
            Official website URL or None
        """
        # Strategy 1: Check existing sources for official domain
        try:
            stats = registry.get_statistics()
            # Look for URLs that might be official
            # This could be enhanced with stored metadata
        except Exception:
            pass

        # Strategy 2: Known patterns for common companies
        company_lower = company_name.lower()
        known_patterns = {
            "claro paraguay": "https://www.claro.com.py",
            "claro": "https://www.claro.com",
            "personal paraguay": "https://www.personal.com.py",
            "tigo paraguay": "https://www.tigo.com.py",
            "copaco": "https://www.copaco.com.py",
            "telecom argentina": "https://www.telecom.com.ar",
            "movistar": "https://www.movistar.com",
        }

        for pattern, url in known_patterns.items():
            if pattern in company_lower:
                return url

        # Strategy 3: Search for official website
        try:
            search_tool = await self._get_search_tool()
            query = f"{company_name} official website"
            results = await search_tool.search(query, max_results=5)

            for result in results:
                url = result.get("url", "")
                if detect_official_website(url, company_name):
                    # Extract base URL
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    return base_url

        except Exception as e:
            logger.warning(f"Failed to search for official website: {e}")

        return None

    def filter_search_results(
        self,
        results: List[Dict[str, Any]],
        registry: PersistentSourceRegistry,
        target_gaps: Optional[List[str]] = None,
    ) -> Tuple[List[FilteredSearchResult], IncrementalStats]:
        """
        Filter search results against registry.

        Args:
            results: Raw search results
            registry: Source registry to check against
            target_gaps: Optional list of gaps these results target

        Returns:
            Tuple of (filtered results, stats)
        """
        stats = IncrementalStats()
        filtered: List[FilteredSearchResult] = []

        for result in results:
            url = result.get("url", "")
            if not url:
                continue

            # Check if seen
            if registry.is_url_seen(url):
                stats.urls_skipped_seen += 1
                continue

            # Passed filter
            filtered.append(FilteredSearchResult(
                url=url,
                title=result.get("title", ""),
                snippet=result.get("snippet", ""),
                relevance_score=result.get("_relevance_score", 0.5),
                is_new=True,
                fills_gap=bool(target_gaps),
                target_gaps=target_gaps or [],
            ))

        return filtered, stats

    def get_research_status(self, company_name: str) -> Dict[str, Any]:
        """
        Get current research status for a company.

        Returns dict with:
        - completeness: Overall data completeness
        - gaps_count: Number of data gaps
        - sources_count: Number of sources in registry
        - stale_sources: Number of stale sources
        - last_research: Date of last research
        """
        analyzer = get_data_analyzer(str(self.base_dir))
        analysis = analyzer.analyze_company(company_name)

        registry = get_source_registry(company_name, str(self.base_dir))
        registry_stats = registry.get_statistics()

        return {
            "company": company_name,
            "completeness": f"{analysis.overall_completeness:.0%}",
            "gaps_count": len(analysis.all_gaps),
            "priority_gaps": [g.field_name for g in analysis.priority_gaps[:5]],
            "sources_count": registry_stats["total_sources"],
            "stale_sources": registry_stats["stale_sources"],
            "last_research": registry_stats["last_fetch_date"],
            "data_types_found": list(registry_stats["data_types_found"].keys()),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_incremental_research(
    company_name: str,
    industry: str = "telecommunications",
    country: str = "Paraguay",
    base_dir: str = "outputs",
    max_queries: int = 30,
) -> IncrementalResearchResult:
    """
    Convenience function to run incremental research.

    Args:
        company_name: Company to research
        industry: Industry context
        country: Country context
        base_dir: Output directory
        max_queries: Max queries to run

    Returns:
        IncrementalResearchResult
    """
    service = IncrementalResearchService(base_dir)
    return await service.research_incremental(
        company_name=company_name,
        industry=industry,
        country=country,
        max_queries=max_queries,
    )


async def run_incremental_batch(
    company_names: List[str],
    industry: str = "telecommunications",
    country: str = "Paraguay",
    base_dir: str = "outputs",
) -> Dict[str, IncrementalResearchResult]:
    """
    Run incremental research for multiple companies.

    Args:
        company_names: List of company names
        industry: Industry context
        country: Country context
        base_dir: Output directory

    Returns:
        Dict mapping company name to result
    """
    service = IncrementalResearchService(base_dir)
    results = {}

    for company in company_names:
        logger.info(f"\n{'='*60}")
        logger.info(f"Incremental research: {company}")
        logger.info(f"{'='*60}\n")

        result = await service.research_incremental(
            company_name=company,
            industry=industry,
            country=country,
        )
        results[company] = result

        # Print summary
        print(f"\n{company}:")
        print(f"  - URLs skipped (seen): {result.stats.urls_skipped_seen}")
        print(f"  - URLs skipped (similar): {result.stats.urls_skipped_similar}")
        print(f"  - New URLs fetched: {result.stats.urls_fetched_new}")
        print(f"  - Gaps filled: {result.stats.gaps_filled}")
        print(f"  - Gaps remaining: {result.stats.gaps_remaining}")

    return results


def print_incremental_report(result: IncrementalResearchResult) -> None:
    """Print a formatted report of incremental research results."""
    print(f"\n{'='*60}")
    print(f"INCREMENTAL RESEARCH REPORT: {result.company_name}")
    print(f"{'='*60}\n")

    # Official site crawl section
    if result.stats.official_site_detected:
        print("OFFICIAL SITE CRAWL:")
        print(f"  - Website: {result.stats.official_site_url}")
        print(f"  - Pages discovered: {result.stats.official_pages_discovered}")
        print(f"  - Pages crawled: {result.stats.official_pages_crawled}")
        print(f"  - Pages skipped (seen): {result.stats.official_pages_skipped}")
        print(f"  - Pages failed: {result.stats.official_pages_failed}")
        print()

    print("EFFICIENCY METRICS:")
    print(f"  - URLs checked: {result.stats.urls_skipped_seen + result.stats.urls_skipped_similar + result.stats.urls_fetched_new}")
    print(f"  - Already seen (skipped): {result.stats.urls_skipped_seen}")
    print(f"  - Similar content (skipped): {result.stats.urls_skipped_similar}")
    print(f"  - New content fetched: {result.stats.urls_fetched_new}")
    print(f"  - Deduplication rate: {result.stats.to_dict()['efficiency_rate']}")

    print("\nGAP FILLING:")
    print(f"  - Gaps before: {result.stats.gaps_before}")
    print(f"  - Gaps filled: {result.stats.gaps_filled}")
    print(f"  - Gaps remaining: {result.stats.gaps_remaining}")

    if result.filled_gaps:
        print("\n  Filled gaps:")
        for gap in result.filled_gaps[:10]:
            print(f"    - {gap}")

    if result.remaining_gaps:
        print("\n  Remaining gaps (top 5):")
        for gap in result.remaining_gaps[:5]:
            print(f"    - {gap}")

    print(f"\nDuration: {result.stats.duration_seconds:.1f} seconds")
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")

    if result.error:
        print(f"Error: {result.error}")


__all__ = [
    "IncrementalStats",
    "IncrementalResearchResult",
    "FilteredSearchResult",
    "IncrementalResearchService",
    "run_incremental_research",
    "run_incremental_batch",
    "print_incremental_report",
]
