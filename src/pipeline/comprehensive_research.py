"""
Comprehensive Research Pipeline - Deep research generating 52+ files with ~1000 sources.

This module implements a comprehensive research pipeline that:
1. Executes 200+ queries across all sections
2. Collects ~1000 sources
3. Generates content for all 52+ output files
4. Tracks sources to their target sections/files
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jinja2

from ..core.types import CompanyProfile, ResearchSource
from ..core.comprehensive_queries import (
    COMPREHENSIVE_QUERIES,
    QueryTemplate,
    format_query,
)
from ..services.data import SourceTracker, reset_source_tracker
from ..services.content import robust_json_parse
from ..core.logging import setup_logger
from ..utils.url_utils import add_country_context_to_query
from ..core.content.relevance_filter import RelevanceFilter
from ..core.resilience.adaptive_timeout import get_adaptive_timeout_manager
from ..core.company_probe import probe_company_presence, CompanyPresence, RESEARCH_PROFILES
from ..core.cache.url_cache import reset_url_cache
from ..services.content import get_html_cache
from ..core.ai.features import get_query_planner, QueryPlan
from ..core.ai_enhancements import (
    AIEnhancementOrchestrator,
    get_ai_orchestrator,
    reset_ai_orchestrator,
)
# PERF-017 to PERF-020: New optimization modules
from ..core.adaptive_query_strategy import (
    AdaptiveQueryStrategy,
    get_query_strategy,
    QueryStrategy,
)
from ..core.cache import (
    get_cross_company_cache,
    reset_cross_company_cache,
)
from ..core.domain.domain_timeout import (
    get_timeout_manager,
    is_domain_circuit_open,
)
from ..core.resilience.search_fallback import (
    SearchFallbackManager,
    get_fallback_queries,
)
from ..core.logging.observability import ObservabilityContext
from ..tools.data.financial.sec import SECTool
from ..tools.data.social.reddit import RedditTool
from ..tools.data.social.twitter import TwitterTool
# ARCH-001: Unified Pipeline Orchestration
from ..core.sources.unified_fetcher import UnifiedDataFetcher, UnifiedResult
from ..core.sources.data_router import CompanyProfile as RouterProfile, create_profile_from_dict

logger = setup_logger("comprehensive_research")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SectionResearchResult:
    """Result of researching a single section."""
    section: str
    file: str
    sources: List[ResearchSource] = field(default_factory=list)
    content: str = ""
    error: Optional[str] = None
    retry_count: int = 0
    queries_executed: int = 0
    queries_failed: int = 0

    @property
    def needs_retry(self) -> bool:
        """
        Check if this section needs to be retried.

        Returns True if:
        - Has 0 sources and hasn't been retried yet
        - Has very few sources (< 2) relative to queries executed
        """
        # Don't retry if already retried max times
        max_retries = int(os.getenv("SECTION_MAX_RETRIES", "2"))
        if self.retry_count >= max_retries:
            return False

        # Retry if 0 sources
        if len(self.sources) == 0:
            return True

        # Retry if very low success rate (< 20% of queries got results)
        if self.queries_executed > 0:
            success_rate = len(self.sources) / self.queries_executed
            if success_rate < 0.2 and len(self.sources) < 3:
                return True

        return False

    @property
    def retry_priority(self) -> int:
        """
        Priority for retry (higher = retry first).

        Sections with 0 sources get highest priority.
        """
        if len(self.sources) == 0:
            return 100
        return max(0, 50 - len(self.sources) * 10)


@dataclass
class ComprehensiveResearchResult:
    """Result of comprehensive research across all sections."""
    company: CompanyProfile
    sections: Dict[str, Dict[str, SectionResearchResult]] = field(default_factory=dict)
    source_tracker: Optional[SourceTracker] = None
    total_sources: int = 0
    total_queries: int = 0
    duration_seconds: float = 0
    # Retry statistics
    sections_retried: int = 0
    retry_sources_gained: int = 0

    def get_failed_sections(self) -> List[Tuple[str, str, SectionResearchResult]]:
        """
        Get list of sections that need retry.

        Returns:
            List of (section_name, filename, result) tuples sorted by retry priority
        """
        failed = []
        for section_name, section_results in self.sections.items():
            for filename, result in section_results.items():
                if result.needs_retry:
                    failed.append((section_name, filename, result))

        # Sort by priority (highest first)
        failed.sort(key=lambda x: x[2].retry_priority, reverse=True)
        return failed


# =============================================================================
# Comprehensive Research Service
# =============================================================================

class ComprehensiveResearchService:
    """
    Service for executing comprehensive research across all sections.

    This replaces the basic 5-phase research with a comprehensive
    approach that generates 52+ files with ~1000 sources.
    """

    MAX_CONCURRENT_QUERIES = 15  # Increased for Gemini Tier 1 (2000 RPM)
    MAX_CONCURRENT_SECTIONS = 4  # Run 4 sections in parallel with high-limit providers
    MAX_RESULTS_PER_QUERY = 5
    # PERF-021: Enable parallel multi-engine search (DuckDuckGo + Jina + Tavily in parallel)
    PARALLEL_SEARCH_ENABLED = os.getenv("PARALLEL_SEARCH", "true").lower() == "true"
    PARALLEL_SEARCH_TIMEOUT = float(os.getenv("PARALLEL_SEARCH_TIMEOUT", "30"))

    def __init__(
        self,
        search_tool,
        browser_tool,
        ai_client,
        max_queries_per_section: int = 50,
    ):
        self.search_tool = search_tool
        self.browser_tool = browser_tool
        self.ai_client = ai_client
        self.max_queries_per_section = max_queries_per_section
        self.source_tracker = SourceTracker()

    async def research_all_sections(
        self,
        company: CompanyProfile,
    ) -> ComprehensiveResearchResult:
        """
        Execute comprehensive research across all sections.

        Performance optimizations (PERF-011 to PERF-017):
        - Resets URL cache for fresh research session
        - Probes company presence to adjust research depth
        - Uses relevance filtering before fetching
        - Applies adaptive timeouts based on query patterns

        Args:
            company: Company profile to research

        Returns:
            ComprehensiveResearchResult with all sections and sources
        """
        start_time = datetime.now()
        result = ComprehensiveResearchResult(company=company)

        # Initialize observability context for this research session
        self._obs_context = ObservabilityContext(
            company_name=company.name,
            research_type="comprehensive",
            metadata={
                "industry": company.industry or "Unknown",
                "country": company.country or "Global",
                "website": company.website or "",
            },
        )
        self._obs_context.__enter__()
        logger.info(f"Started observability trace for {company.name}")

        # PERF-011: Reset URL cache for new research session
        reset_url_cache()
        logger.info("URL cache reset for new research session")

        # Initialize HTML cache for this company
        get_html_cache().set_company(company.name)

        # Reset source tracker for new research
        reset_source_tracker()
        self.source_tracker = SourceTracker()

        # PERF-015: Probe company presence to adjust research depth
        presence_level = "substantial"  # Default
        try:
            probe_result = await probe_company_presence(
                company=company.name,
                website=company.website,
                country=company.country,
            )
            presence_level = probe_result.presence.value
            logger.info(
                f"Company probe: {company.name} -> {presence_level} "
                f"(profile: {probe_result.recommended_profile})"
            )

            # Adjust max queries based on presence
            if probe_result.presence == CompanyPresence.MINIMAL:
                self.max_queries_per_section = min(self.max_queries_per_section, 20)
                logger.info(f"Reduced queries per section to {self.max_queries_per_section} for minimal presence")
            elif probe_result.presence == CompanyPresence.LIMITED:
                self.max_queries_per_section = min(self.max_queries_per_section, 35)
                logger.info(f"Reduced queries per section to {self.max_queries_per_section} for limited presence")
        except Exception as e:
            logger.warning(f"Company probe failed, using default research depth: {e}")

        # Create relevance filter for this company
        self._relevance_filter = RelevanceFilter(
            company=company.name,
            country=company.country,
            industry=company.industry,
        )

        # Initialize AI query planner for smarter search queries
        self._query_planner = get_query_planner()
        self._query_plans: Dict[str, QueryPlan] = {}

        # Initialize AI enhancement orchestrator for comprehensive AI features
        reset_ai_orchestrator()  # Reset for new research session
        self._ai_orchestrator = get_ai_orchestrator(
            company=company.name,
            industry=company.industry or "Technology",
            country=company.country or "Global",
        )
        logger.info("AI Enhancement Orchestrator initialized")

        # PERF-017: Initialize adaptive query strategy based on company presence
        try:
            self._query_strategy = get_query_strategy(
                company=company.name,
                country=company.country or "Global",
                presence_level=presence_level,
            )
            logger.info(f"Query strategy: {self._query_strategy.strategy.value}")
        except Exception as e:
            logger.debug(f"Query strategy initialization skipped: {e}")
            self._query_strategy = None

        # PERF-018: Initialize search fallback manager
        self._fallback_manager = SearchFallbackManager(
            company=company.name,
            country=company.country or "Global",
            max_fallbacks=3,
        )

        # PERF-019: Initialize domain timeout manager
        self._domain_timeout = get_timeout_manager()

        # ====================================================================
        # ARCH-001: Unified Data Source Orchestration
        # Pre-fetch data from all available sources in parallel
        # ====================================================================
        enable_unified = os.getenv("ENABLE_UNIFIED_FETCH", "true").lower() == "true"
        self._unified_data: Optional[UnifiedResult] = None

        if enable_unified:
            try:
                unified_fetcher = UnifiedDataFetcher(timeout_seconds=60.0)
                # Convert CompanyProfile to RouterProfile for routing decisions
                router_profile = RouterProfile(
                    name=company.name,
                    country=company.country or "",
                    industry=company.industry or "",
                    website=company.website,
                    ticker=getattr(company, "ticker", None),
                    exchange=getattr(company, "exchange", None),
                )

                logger.info(f"=== UNIFIED ORCHESTRATION: Pre-fetching from available sources ===")
                self._unified_data = await unified_fetcher.fetch_all(router_profile)

                if self._unified_data.sources_used:
                    logger.info(
                        f"Unified fetch complete: {len(self._unified_data.sources_used)} sources "
                        f"({', '.join(s.value for s in self._unified_data.sources_used)}), "
                        f"{len(self._unified_data.sources_failed)} failed, "
                        f"{self._unified_data.total_duration_seconds:.2f}s"
                    )

                    # Store unified data for use by section research
                    result.sections["_unified_data"] = {
                        "sources_used": [s.value for s in self._unified_data.sources_used],
                        "sources_failed": [s.value for s in self._unified_data.sources_failed],
                        "metadata": self._unified_data.metadata,
                    }
                else:
                    logger.info("Unified fetch: No additional sources available")

                await unified_fetcher.close()

            except Exception as e:
                logger.warning(f"Unified data orchestration failed: {e}")
                self._unified_data = None

        # Execute research for each section with rate limiting
        # Use semaphore to limit concurrent sections and avoid rate limiting
        section_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_SECTIONS)

        async def run_section_with_limit(section_name: str, queries: list):
            """Run a section with concurrency limiting."""
            async with section_semaphore:
                logger.info(f"Researching section: {section_name} ({len(queries)} queries)")
                return await self._research_section(company, section_name, queries)

        section_tasks = []
        for section_name, queries in COMPREHENSIVE_QUERIES.items():
            section_tasks.append(
                run_section_with_limit(section_name, queries)
            )

        # Run sections with limited concurrency to avoid rate limiting
        section_results = await asyncio.gather(*section_tasks, return_exceptions=True)

        # Aggregate results
        for section_name, section_result in zip(COMPREHENSIVE_QUERIES.keys(), section_results):
            if isinstance(section_result, Exception):
                logger.error(f"Section {section_name} failed: {section_result}")
                continue
            if section_result:
                result.sections[section_name] = section_result
                for file_result in section_result.values():
                    result.total_sources += len(file_result.sources)

        # ====================================================================
        # SEC EDGAR Integration (for US-listed companies)
        # ====================================================================
        enable_sec = os.getenv("ENABLE_SEC_FILINGS", "true").lower() == "true"
        if enable_sec:
            try:
                # Check if company has SEC filings available
                sec_ticker = await self._detect_sec_filings_available(
                    company_name=company.name,
                    ticker=getattr(company, 'ticker', None),
                )

                if sec_ticker:
                    logger.info(f"=== SEC FILINGS: Researching {sec_ticker} ===")
                    sec_results = await self._research_sec_filings(
                        company=company,
                        ticker=sec_ticker,
                    )

                    # Add SEC results to main results
                    if sec_results:
                        result.sections["sec_filings"] = sec_results
                        sec_source_count = sum(
                            len(r.sources) for r in sec_results.values()
                        )
                        result.total_sources += sec_source_count
                        logger.info(
                            f"SEC filings added: {sec_source_count} sources "
                            f"across {len(sec_results)} files"
                        )
                else:
                    logger.info(f"No SEC filings available for {company.name}")
            except Exception as e:
                logger.warning(f"SEC integration failed: {e}")

        # ====================================================================
        # News Intelligence (NewsAPI)
        # ====================================================================
        try:
            # Get output directory for news reports
            output_dir = Path(os.getenv("OUTPUT_DIR", "outputs")) / company.name.replace(" ", "_")
            output_dir.mkdir(parents=True, exist_ok=True)

            news_results = await self._research_news_intelligence(
                company=company,
                output_dir=output_dir,
            )

            if news_results.get("enabled") and news_results.get("api_available"):
                logger.info(
                    f"News intelligence: {news_results.get('articles_found', 0)} articles, "
                    f"sentiment={news_results.get('sentiment_label', 'neutral')}, "
                    f"signals={news_results.get('signals_detected', 0)}"
                )
                if news_results.get("crisis_alert"):
                    logger.warning(f"CRISIS ALERT: Potential crisis indicators detected for {company.name}")
            elif news_results.get("error"):
                logger.debug(f"News intelligence skipped: {news_results.get('error')}")
        except Exception as e:
            logger.warning(f"News intelligence failed: {e}")

        # ====================================================================
        # Social Intelligence (Reddit + Twitter)
        # ====================================================================
        enable_social = os.getenv("ENABLE_SOCIAL_INTELLIGENCE", "true").lower() == "true"
        if enable_social:
            try:
                social_results = await self._research_social_intelligence(
                    company=company,
                    output_dir=output_dir,
                )

                if social_results.get("enabled"):
                    reddit_mentions = social_results.get("reddit_mentions", 0)
                    twitter_mentions = social_results.get("twitter_mentions", 0)
                    if reddit_mentions > 0 or twitter_mentions > 0:
                        logger.info(
                            f"Social intelligence: Reddit={reddit_mentions} mentions, "
                            f"Twitter={twitter_mentions} mentions, "
                            f"sentiment={social_results.get('overall_sentiment', 'neutral')}"
                        )
                    else:
                        logger.info("Social intelligence: No API credentials configured")
                elif social_results.get("error"):
                    logger.debug(f"Social intelligence skipped: {social_results.get('error')}")
            except Exception as e:
                logger.warning(f"Social intelligence failed: {e}")

        # ====================================================================
        # Financial Deep Dive (Financial Modeling Prep)
        # Only runs if company has a known ticker symbol
        # ====================================================================
        ticker = getattr(company, 'ticker', None)
        if not ticker and enable_sec:
            # Try to reuse ticker from SEC detection
            ticker = sec_ticker if 'sec_ticker' in dir() else None

        if ticker:
            try:
                fmp_results = await self._research_financial_deep_dive(
                    company=company,
                    ticker=ticker,
                    output_dir=output_dir,
                )

                if fmp_results.get("enabled") and fmp_results.get("api_available"):
                    logger.info(
                        f"Financial deep dive: {ticker} - "
                        f"Rating={fmp_results.get('rating', 'N/A')}, "
                        f"Recommendation={fmp_results.get('rating_recommendation', 'N/A')}"
                    )
                elif fmp_results.get("error"):
                    logger.debug(f"Financial deep dive skipped: {fmp_results.get('error')}")
            except Exception as e:
                logger.warning(f"Financial deep dive failed: {e}")
        else:
            logger.debug(f"Financial deep dive skipped: No ticker symbol for {company.name}")

        # Retry failed sections if enabled (default: enabled)
        enable_retry = os.getenv("SECTION_RETRY_ENABLED", "true").lower() == "true"
        if enable_retry:
            failed_count = len(result.get_failed_sections())
            if failed_count > 0:
                logger.info(f"Found {failed_count} sections with insufficient sources, starting retry pass...")
                retry_sources = await self._retry_failed_sections(company, result)
                result.retry_sources_gained = retry_sources
                result.sections_retried = failed_count
                result.total_sources += retry_sources

        result.source_tracker = self.source_tracker
        result.total_queries = sum(len(q) for q in COMPREHENSIVE_QUERIES.values())
        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Comprehensive research complete: {result.total_sources} sources, "
            f"{result.total_queries} queries, {result.duration_seconds:.1f}s"
            + (f", {result.sections_retried} retried (+{result.retry_sources_gained} sources)"
               if result.sections_retried > 0 else "")
        )

        # Close observability context - flush traces to Langfuse
        if hasattr(self, '_obs_context') and self._obs_context:
            self._obs_context.__exit__(None, None, None)
            logger.info(f"Completed observability trace for {company.name}")

        return result

    async def _research_section(
        self,
        company: CompanyProfile,
        section_name: str,
        queries: List[QueryTemplate],
    ) -> Dict[str, SectionResearchResult]:
        """Research a single section with all its queries."""
        logger.info(f"Researching section: {section_name} ({len(queries)} queries)")

        # Create observability span for this section
        section_span = None
        if hasattr(self, '_obs_context') and self._obs_context:
            section_span = self._obs_context.span(
                name=f"section_{section_name}",
                input_data={"query_count": len(queries)},
                metadata={"section": section_name},
            )

        # Get AI query plan for this section (provides context + smarter queries)
        query_plan = None
        ai_queries: List[str] = []
        try:
            query_plan = await self._query_planner.plan_research(
                company_name=company.name,
                section=section_name,
                industry=company.industry or "Technology",
                country=company.country or "Global",
            )
            self._query_plans[section_name] = query_plan
            ai_queries = query_plan.suggested_queries
            logger.info(
                f"  AI query plan: {len(ai_queries)} queries, "
                f"confidence={query_plan.confidence:.0%}, "
                f"known entities: {sum(len(v) for v in query_plan.key_entities.values())}"
            )
        except Exception as e:
            logger.debug(f"AI query planning skipped for {section_name}: {e}")

        # Group queries by target file
        queries_by_file: Dict[str, List[QueryTemplate]] = {}
        for query in queries[:self.max_queries_per_section]:
            file_key = query.file
            if file_key not in queries_by_file:
                queries_by_file[file_key] = []
            queries_by_file[file_key].append(query)

        # Research each file
        results = {}
        for filename, file_queries in queries_by_file.items():
            result = await self._research_file(
                company,
                section_name,
                filename,
                file_queries,
                ai_queries=ai_queries,
                query_plan=query_plan,
            )
            results[filename] = result

        # End observability span with results summary
        if section_span:
            total_sources = sum(len(r.sources) for r in results.values())
            section_span.end(
                output={"file_count": len(results), "total_sources": total_sources},
                metadata={"files": list(results.keys())},
            )

        return results

    async def _research_file(
        self,
        company: CompanyProfile,
        section: str,
        filename: str,
        queries: List[QueryTemplate],
        ai_queries: Optional[List[str]] = None,
        query_plan: Optional[QueryPlan] = None,
    ) -> SectionResearchResult:
        """Research for a single output file."""
        result = SectionResearchResult(section=section, file=filename)

        # Format template queries
        # Ensure country context is added to all queries (BUG-049)
        country_name = company.country if company.country != "Global" else ""
        template_queries = [
            add_country_context_to_query(
                format_query(
                    q,
                    company=company.name,
                    industry=company.industry or "industry",
                    country=country_name,
                    year=str(datetime.now().year),
                ),
                country_name,
            )
            for q in queries
        ]

        # Combine AI-suggested queries with template queries
        # AI queries are prioritized (usually more specific and targeted)
        if ai_queries and query_plan:
            formatted_queries = self._query_planner.get_combined_queries(
                query_plan,
                template_queries,
                max_queries=self.max_queries_per_section,
            )
            if len(ai_queries) > 0:
                logger.debug(
                    f"  {section}/{filename}: Using {len(formatted_queries)} queries "
                    f"({len(ai_queries)} AI + {len(template_queries)} template)"
                )
        else:
            formatted_queries = template_queries

        # PERF-017: Apply adaptive query strategy based on company presence
        if hasattr(self, '_query_strategy') and self._query_strategy:
            original_count = len(formatted_queries)
            formatted_queries = self._query_strategy.adapt_queries(
                formatted_queries,
                max_queries=self.max_queries_per_section,
            )
            if len(formatted_queries) != original_count:
                logger.debug(
                    f"  {section}/{filename}: Adapted queries {original_count} -> {len(formatted_queries)} "
                    f"(strategy: {self._query_strategy.strategy.value})"
                )

        # Execute queries with concurrency control
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_QUERIES)
        adaptive_timeout = get_adaptive_timeout_manager()

        async def search_query(query: str, is_fallback: bool = False) -> List[ResearchSource]:
            async with semaphore:
                try:
                    # PERF-013: Check if section should be skipped
                    if adaptive_timeout.should_skip_section(section):
                        logger.debug(f"Skipping query in {section} - too many failures")
                        return []

                    # PERF-021: Use parallel multi-engine search for faster results
                    if self.PARALLEL_SEARCH_ENABLED and hasattr(self.search_tool, 'search_parallel'):
                        search_results = await self.search_tool.search_parallel(
                            query,
                            max_results=self.MAX_RESULTS_PER_QUERY,
                            timeout_seconds=self.PARALLEL_SEARCH_TIMEOUT,
                        )
                    else:
                        search_results = await self.search_tool.search(
                            query,
                            max_results=self.MAX_RESULTS_PER_QUERY,
                        )

                    # PERF-020: If no results and not already a fallback, try fallback queries
                    if not search_results and not is_fallback and hasattr(self, '_fallback_manager'):
                        fallback_queries = self._fallback_manager.get_fallbacks(query)
                        for fallback_query in fallback_queries[:2]:  # Try up to 2 fallbacks
                            logger.debug(f"Trying fallback query: {fallback_query[:50]}...")
                            fallback_results = await search_query(fallback_query, is_fallback=True)
                            if fallback_results:
                                logger.info(f"Fallback successful for: {query[:30]}...")
                                return fallback_results
                        # All fallbacks failed
                        adaptive_timeout.record_failure(query, section, is_empty=True)
                        return []

                    # PERF-017: Filter search results for relevance BEFORE fetching
                    if hasattr(self, '_relevance_filter') and self._relevance_filter:
                        filtered_results = self._relevance_filter.filter_results(
                            search_results,
                            max_results=self.MAX_RESULTS_PER_QUERY,
                        )
                        if len(filtered_results) < len(search_results):
                            logger.debug(
                                f"Pre-fetch filter: {len(search_results)} -> {len(filtered_results)} results"
                            )
                        search_results = filtered_results

                    # AI-017: Use AI relevance scoring for smarter pre-fetch filtering
                    if hasattr(self, '_ai_orchestrator') and self._ai_orchestrator and search_results:
                        try:
                            search_results = await self._ai_orchestrator.score_search_results(
                                query=query,
                                results=search_results,
                                target_data=section,
                                threshold=0.4,
                            )
                        except Exception as ai_err:
                            logger.debug(f"AI relevance scoring skipped: {ai_err}")

                    urls = [r.get("url") for r in search_results if r.get("url")]
                    if urls:
                        # PERF-019: Check domain circuit breakers before fetching
                        if hasattr(self, '_domain_timeout') and self._domain_timeout:
                            filtered_urls = []
                            for url in urls:
                                if not is_domain_circuit_open(url):
                                    filtered_urls.append(url)
                                else:
                                    logger.debug(f"Skipping URL (circuit open): {url[:50]}...")
                            if filtered_urls:
                                urls = filtered_urls
                            elif urls:
                                # All URLs had open circuits, use original list anyway
                                logger.debug("All URLs have open circuits, using original list")

                        sources = await self.browser_tool.fetch_multiple(urls[:self.MAX_RESULTS_PER_QUERY])
                        # PERF-013: Record success/failure for adaptive timeout
                        if sources:
                            adaptive_timeout.record_success(query, section, result_count=len(sources))
                        else:
                            adaptive_timeout.record_failure(query, section, is_empty=True)
                        return sources
                    else:
                        adaptive_timeout.record_failure(query, section, is_empty=True)
                except Exception as e:
                    logger.debug(f"Query failed: {query[:50]}... - {e}")
                    adaptive_timeout.record_failure(query, section, is_timeout="timeout" in str(e).lower())
                return []

        # Execute all queries for this file
        all_sources_lists = await asyncio.gather(
            *[search_query(q) for q in formatted_queries],
            return_exceptions=True,
        )

        # Aggregate sources (with country filtering for BUG-049)
        target_industry = company.industry
        target_country_tld = company.get_country_tld()
        seen_urls = set()
        filtered_foreign_count = 0
        
        for sources in all_sources_lists:
            if isinstance(sources, Exception):
                continue
            for source in sources:
                if source.url and source.url not in seen_urls:
                    # Filter irrelevant foreign sources (BUG-049)
                    if not source.is_usable(target_industry, target_country_tld):
                        filtered_foreign_count += 1
                        continue
                    seen_urls.add(source.url)
                    result.sources.append(source)
                    # Track source
                    self.source_tracker.track_source(
                        source,
                        section=section,
                    )

        if filtered_foreign_count > 0:
            logger.info(f"  {section}/{filename}: Filtered {filtered_foreign_count} irrelevant foreign sources (BUG-049)")

        # Track query statistics for retry logic
        result.queries_executed = len(formatted_queries)
        result.queries_failed = sum(
            1 for sources in all_sources_lists
            if isinstance(sources, Exception) or (isinstance(sources, list) and len(sources) == 0)
        )

        logger.info(
            f"  {section}/{filename}: {len(result.sources)} sources from {len(formatted_queries)} queries "
            f"({result.queries_failed} failed)"
        )

        return result

    async def _retry_failed_sections(
        self,
        company: CompanyProfile,
        result: ComprehensiveResearchResult,
    ) -> int:
        """
        Retry sections that failed to get adequate search results.

        This method runs after the main research pass and attempts to recover
        sections that got 0 results or very few results (likely due to temporary
        network issues, rate limiting, or search timeouts).

        Args:
            company: Company profile being researched
            result: Research result containing failed sections

        Returns:
            Number of new sources gained from retries
        """
        failed_sections = result.get_failed_sections()
        if not failed_sections:
            logger.info("No failed sections to retry")
            return 0

        logger.info(f"=== RETRY PASS: {len(failed_sections)} sections need retry ===")

        # Wait before retry to let network/rate limits recover
        retry_delay = int(os.getenv("SECTION_RETRY_DELAY_SECONDS", "30"))
        logger.info(f"Waiting {retry_delay}s before retry pass...")
        await asyncio.sleep(retry_delay)

        total_new_sources = 0

        for section_name, filename, section_result in failed_sections:
            logger.info(
                f"Retrying {section_name}/{filename} "
                f"(attempt {section_result.retry_count + 1}, "
                f"current sources: {len(section_result.sources)})"
            )

            # Get original queries for this section/file
            section_queries = COMPREHENSIVE_QUERIES.get(section_name, [])
            file_queries = [q for q in section_queries if q.file == filename]

            if not file_queries:
                logger.warning(f"No queries found for {section_name}/{filename}, skipping")
                continue

            # Get AI query plan if available
            query_plan = self._query_plans.get(section_name)
            ai_queries = query_plan.suggested_queries if query_plan else []

            # Retry the file research
            old_source_count = len(section_result.sources)

            try:
                new_result = await self._research_file(
                    company,
                    section_name,
                    filename,
                    file_queries,
                    ai_queries=ai_queries,
                    query_plan=query_plan,
                )

                # Merge new sources with existing (avoiding duplicates)
                existing_urls = {s.url for s in section_result.sources}
                for source in new_result.sources:
                    if source.url not in existing_urls:
                        section_result.sources.append(source)
                        existing_urls.add(source.url)

                # Update stats
                section_result.retry_count += 1
                new_sources = len(section_result.sources) - old_source_count
                total_new_sources += new_sources

                logger.info(
                    f"  Retry result: {new_sources} new sources "
                    f"(total now: {len(section_result.sources)})"
                )

            except Exception as e:
                logger.error(f"Retry failed for {section_name}/{filename}: {e}")
                section_result.retry_count += 1

        logger.info(
            f"=== RETRY PASS COMPLETE: {total_new_sources} new sources from "
            f"{len(failed_sections)} retries ==="
        )

        return total_new_sources

    # =========================================================================
    # SEC EDGAR Integration (for US-listed companies)
    # =========================================================================

    async def _detect_sec_filings_available(
        self,
        company_name: str,
        ticker: Optional[str] = None
    ) -> Optional[str]:
        """
        Check if company has SEC filings and return ticker.

        Args:
            company_name: Company name to search for
            ticker: Optional known ticker symbol

        Returns:
            Ticker symbol if SEC filings exist, None otherwise
        """
        sec_tool = SECTool()

        # If ticker provided, verify it exists in SEC
        if ticker:
            if sec_tool.check_sec_availability(ticker):
                logger.info(f"SEC filings available for ticker: {ticker}")
                return ticker

        # Try to find ticker from company name
        found_ticker = sec_tool.find_ticker(company_name)
        if found_ticker and sec_tool.check_sec_availability(found_ticker):
            logger.info(f"Found SEC ticker '{found_ticker}' for company '{company_name}'")
            return found_ticker

        logger.debug(f"No SEC filings found for: {company_name}")
        return None

    async def _research_sec_filings(
        self,
        company: CompanyProfile,
        ticker: str,
    ) -> Dict[str, SectionResearchResult]:
        """
        Extract and analyze SEC filings for a US-listed company.

        Args:
            company: Company profile being researched
            ticker: SEC ticker symbol

        Returns:
            Dictionary of section results with SEC filing data
        """
        sec_tool = SECTool()
        results: Dict[str, SectionResearchResult] = {}

        # Define SEC output files and their extraction methods
        sec_files = [
            ("01-Business-Overview.md", "10-K", "business_overview"),
            ("02-Risk-Factors.md", "10-K", "risk_factors"),
            ("03-Financial-Highlights.md", "10-K", "financial_highlights"),
            ("04-MDA-Summary.md", "10-K", "mda"),
            ("05-Recent-Events.md", "8-K", "recent_events"),
            ("06-Executive-Compensation.md", "DEF 14A", "compensation"),
        ]

        # Get 10-K content (contains most sections)
        ten_k_content = ""
        try:
            ten_k_content = sec_tool.get_latest_10k_content(ticker)
            if ten_k_content:
                logger.info(f"Retrieved 10-K for {ticker}: {len(ten_k_content)} chars")
        except Exception as e:
            logger.warning(f"Failed to retrieve 10-K for {ticker}: {e}")

        # Get recent 8-K filings
        eight_k_filings = []
        try:
            eight_k_filings = sec_tool.get_8k_filings(ticker, limit=5)
            logger.info(f"Retrieved {len(eight_k_filings)} 8-K filings for {ticker}")
        except Exception as e:
            logger.warning(f"Failed to retrieve 8-K filings for {ticker}: {e}")

        # Process each SEC output file
        for filename, filing_type, section_type in sec_files:
            result = SectionResearchResult(
                section="10-SEC-Filings",
                file=filename,
            )

            try:
                if filing_type == "10-K" and ten_k_content:
                    # Extract relevant section from 10-K
                    extracted = await self._extract_10k_section(
                        ten_k_content, section_type, company.name
                    )
                    if extracted:
                        source = ResearchSource(
                            url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K",
                            title=f"{company.name} 10-K {section_type.replace('_', ' ').title()}",
                            content=extracted,
                            source_type="sec_filing",
                        )
                        result.sources.append(source)
                        self.source_tracker.track_source(source, "10-SEC-Filings")

                elif filing_type == "8-K" and eight_k_filings:
                    # Create sources from 8-K filings
                    for filing in eight_k_filings:
                        source = ResearchSource(
                            url=filing.get("url", ""),
                            title=f"{company.name} 8-K - {filing.get('filing_date', 'Unknown Date')}",
                            content=f"8-K filed on {filing.get('filing_date', 'Unknown')}",
                            source_type="sec_filing",
                        )
                        result.sources.append(source)
                        self.source_tracker.track_source(source, "10-SEC-Filings")

                result.queries_executed = 1
                logger.info(f"SEC {filename}: {len(result.sources)} sources")

            except Exception as e:
                logger.warning(f"Failed to process SEC {filename}: {e}")
                result.error = str(e)

            results[filename] = result

        return results

    async def _extract_10k_section(
        self,
        ten_k_text: str,
        section_type: str,
        company_name: str,
    ) -> str:
        """
        Use AI to extract a specific section from 10-K filing.

        Args:
            ten_k_text: Full 10-K text content
            section_type: Type of section to extract
            company_name: Company name for context

        Returns:
            Extracted and summarized section content
        """
        # Define extraction prompts for each section type
        prompts = {
            "business_overview": f"""Extract the Business Description (Item 1) from this 10-K filing for {company_name}.

Provide a structured summary including:
- Company overview and principal products/services
- Business segments and operations
- Geographic presence
- Key customers and markets
- Competitive position

10-K TEXT (first 80,000 chars):
{ten_k_text[:80000]}

Provide a concise, well-organized summary (500-1000 words).""",

            "risk_factors": f"""Extract the Risk Factors (Item 1A) from this 10-K filing for {company_name}.

Categorize and summarize the key risks:
1. Market/Industry Risks
2. Operational Risks
3. Financial Risks
4. Regulatory/Legal Risks
5. Technology/Cybersecurity Risks

10-K TEXT (first 80,000 chars):
{ten_k_text[:80000]}

Provide a structured summary of the top 10-15 most significant risks.""",

            "financial_highlights": f"""Extract Financial Highlights from this 10-K filing (Item 8) for {company_name}.

Include:
- Revenue and growth trends
- Profitability metrics (gross margin, operating margin, net income)
- Key balance sheet items (assets, liabilities, equity)
- Cash flow highlights
- Key financial ratios

10-K TEXT (first 80,000 chars):
{ten_k_text[:80000]}

Provide specific numbers and year-over-year comparisons where available.""",

            "mda": f"""Extract the Management Discussion & Analysis (Item 7) from this 10-K for {company_name}.

Summarize:
- Management's view of business performance
- Key factors affecting results
- Liquidity and capital resources
- Future outlook and guidance
- Critical accounting policies

10-K TEXT (first 80,000 chars):
{ten_k_text[:80000]}

Provide a concise executive summary (500-800 words).""",

            "compensation": f"""Extract executive compensation information from this filing for {company_name}.

If available, include:
- CEO compensation (base salary, bonus, stock awards, total)
- Other named executive officers' compensation
- Compensation philosophy
- Performance metrics tied to pay

10-K TEXT (first 80,000 chars):
{ten_k_text[:80000]}

Note: Executive compensation details are typically in the proxy statement (DEF 14A), not 10-K.
Extract any compensation-related information available.""",
        }

        prompt = prompts.get(section_type)
        if not prompt:
            return ""

        try:
            response = await self.ai_client.generate(
                prompt,
                temperature=0.3,
                max_tokens=2000,
            )
            return response
        except Exception as e:
            logger.warning(f"AI extraction failed for {section_type}: {e}")
            return ""

    # =========================================================================
    # News Intelligence Integration (NewsAPI)
    # =========================================================================

    async def _research_news_intelligence(
        self,
        company: CompanyProfile,
        output_dir: Path,
    ) -> Dict[str, Any]:
        """
        Fetch and analyze news using NewsAPI.

        This method uses the NewsAggregatorTool to:
        - Get recent company news (last 30 days)
        - Get industry news (last 14 days)
        - Analyze sentiment of articles
        - Detect business signals (funding, partnerships, etc.)

        Args:
            company: Company profile to research
            output_dir: Directory to write news reports

        Returns:
            Dict with news intelligence results and statistics
        """
        # Check if news intelligence is enabled
        enable_news = os.getenv("ENABLE_NEWS_INTELLIGENCE", "true").lower() == "true"
        if not enable_news:
            logger.info("News intelligence disabled via ENABLE_NEWS_INTELLIGENCE=false")
            return {"enabled": False, "articles_found": 0}

        try:
            from ..tools.data.content.news_aggregator import NewsAggregatorTool

            news_tool = NewsAggregatorTool()

            # Check if NewsAPI client is available
            if not news_tool.client:
                logger.warning("NewsAPI client not initialized (missing API key)")
                return {
                    "enabled": True,
                    "api_available": False,
                    "articles_found": 0,
                    "error": "NEWSAPI_KEY not configured",
                }

            # Get configurable parameters
            company_lookback = int(os.getenv("NEWS_COMPANY_LOOKBACK_DAYS", "30"))
            industry_lookback = int(os.getenv("NEWS_INDUSTRY_LOOKBACK_DAYS", "14"))

            logger.info(f"Fetching news intelligence for {company.name}...")

            # Fetch company news
            company_news = await news_tool.get_company_news(
                company_name=company.name,
                days_back=company_lookback,
                max_results=20,
            )
            logger.info(f"  Company news: {len(company_news)} articles")

            # Fetch industry news
            industry = company.industry or "technology"
            industry_news = await news_tool.get_industry_news(
                industry=industry,
                days_back=industry_lookback,
                max_results=15,
            )
            logger.info(f"  Industry news: {len(industry_news)} articles")

            # Analyze sentiment
            sentiment = await news_tool.analyze_sentiment(
                company_name=company.name,
                days_back=company_lookback,
            )
            logger.info(
                f"  Sentiment: {sentiment.get('overall_sentiment', {}).get('label', 'unknown')} "
                f"(compound: {sentiment.get('overall_sentiment', {}).get('compound', 0):.3f})"
            )

            # Detect signals
            signals = await news_tool.detect_signals(
                company_name=company.name,
                days_back=company_lookback,
            )
            total_signals = sum(
                len(v) for k, v in signals.items()
                if isinstance(v, list) and k != "total_articles"
            )
            logger.info(f"  Business signals: {total_signals} detected")

            # Write news reports
            await self._write_news_reports(
                output_dir=output_dir,
                company=company,
                company_news=company_news,
                industry_news=industry_news,
                sentiment=sentiment,
                signals=signals,
            )

            return {
                "enabled": True,
                "api_available": True,
                "articles_found": len(company_news),
                "industry_articles": len(industry_news),
                "sentiment_score": sentiment.get("overall_sentiment", {}).get("compound", 0),
                "sentiment_label": sentiment.get("overall_sentiment", {}).get("label", "neutral"),
                "sentiment_trend": sentiment.get("trend", "stable"),
                "crisis_alert": sentiment.get("crisis_alert", False),
                "signals_detected": total_signals,
                "signal_breakdown": {
                    k: len(v) for k, v in signals.items()
                    if isinstance(v, list) and k != "total_articles"
                },
            }

        except ImportError as e:
            logger.warning(f"NewsAggregatorTool not available: {e}")
            return {"enabled": True, "error": str(e), "articles_found": 0}
        except Exception as e:
            logger.error(f"News intelligence failed: {e}")
            return {"enabled": True, "error": str(e), "articles_found": 0}

    async def _write_news_reports(
        self,
        output_dir: Path,
        company: CompanyProfile,
        company_news: List,
        industry_news: List,
        sentiment: Dict[str, Any],
        signals: Dict[str, Any],
    ) -> None:
        """
        Write news intelligence reports as markdown files.

        Creates 4 files in the 11-News-Intelligence directory:
        - 01-Recent-News.md
        - 02-Sentiment-Analysis.md
        - 03-Business-Signals.md
        - 04-Crisis-Indicators.md
        """
        news_dir = output_dir / "11-News-Intelligence"
        news_dir.mkdir(parents=True, exist_ok=True)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 01-Recent-News.md
        recent_news_content = self._generate_recent_news_md(
            company, company_news, industry_news, generated_at
        )
        (news_dir / "01-Recent-News.md").write_text(recent_news_content, encoding="utf-8")

        # 02-Sentiment-Analysis.md
        sentiment_content = self._generate_sentiment_md(
            company, sentiment, generated_at
        )
        (news_dir / "02-Sentiment-Analysis.md").write_text(sentiment_content, encoding="utf-8")

        # 03-Business-Signals.md
        signals_content = self._generate_signals_md(
            company, signals, generated_at
        )
        (news_dir / "03-Business-Signals.md").write_text(signals_content, encoding="utf-8")

        # 04-Crisis-Indicators.md
        crisis_content = self._generate_crisis_md(
            company, sentiment, signals, generated_at
        )
        (news_dir / "04-Crisis-Indicators.md").write_text(crisis_content, encoding="utf-8")

        logger.info(f"  News reports written to {news_dir}")

    def _generate_recent_news_md(
        self,
        company: CompanyProfile,
        company_news: List,
        industry_news: List,
        generated_at: str,
    ) -> str:
        """Generate Recent News markdown."""
        md = f"""# Recent News

**Company:** {company.name}
**Industry:** {company.industry or 'N/A'}
**Generated:** {generated_at}

---

## Company News ({len(company_news)} articles)

"""
        if company_news:
            for article in company_news[:15]:
                title = article.title or "Untitled"
                url = article.url or "#"
                date = article.metadata.get("published_date", "")[:10] if article.metadata else ""
                source = article.metadata.get("source_name", "") if article.metadata else ""
                content = (article.content or "")[:200]

                md += f"### [{title}]({url})\n"
                if date or source:
                    md += f"*{date}* | *{source}*\n\n"
                if content:
                    md += f"{content}...\n\n"
                md += "---\n\n"
        else:
            md += "*No recent company news found.*\n\n"

        md += f"\n## Industry News ({len(industry_news)} articles)\n\n"
        if industry_news:
            for article in industry_news[:10]:
                title = article.title or "Untitled"
                url = article.url or "#"
                date = article.metadata.get("published_date", "")[:10] if article.metadata else ""
                md += f"- [{title}]({url}) ({date})\n"
        else:
            md += "*No recent industry news found.*\n"

        return md

    def _generate_sentiment_md(
        self,
        company: CompanyProfile,
        sentiment: Dict[str, Any],
        generated_at: str,
    ) -> str:
        """Generate Sentiment Analysis markdown."""
        overall = sentiment.get("overall_sentiment", {})
        compound = overall.get("compound", 0)
        label = overall.get("label", "neutral")
        trend = sentiment.get("trend", "stable")

        md = f"""# Sentiment Analysis

**Company:** {company.name}
**Generated:** {generated_at}

---

## Overall Sentiment

| Metric | Value |
|--------|-------|
| **Sentiment** | {label.title()} |
| **Compound Score** | {compound:.3f} |
| **Trend** | {trend.title()} |
| **Articles Analyzed** | {sentiment.get('article_count', 0)} |

### Breakdown

- **Positive Articles:** {sentiment.get('positive_count', 0)}
- **Negative Articles:** {sentiment.get('negative_count', 0)}
- **Neutral Articles:** {sentiment.get('neutral_count', 0)}

---

## Article-Level Sentiment

"""
        article_sentiments = sentiment.get("article_sentiments", [])
        if article_sentiments:
            md += "| Date | Title | Sentiment | Score |\n"
            md += "|------|-------|-----------|-------|\n"
            for item in article_sentiments[:15]:
                date = (item.get("date") or "")[:10]
                title = (item.get("title") or "")[:50]
                s = item.get("sentiment", {})
                s_label = s.get("label", "neutral")
                s_compound = s.get("compound", 0)
                md += f"| {date} | {title} | {s_label} | {s_compound:.2f} |\n"
        else:
            md += "*No article sentiment data available.*\n"

        return md

    def _generate_signals_md(
        self,
        company: CompanyProfile,
        signals: Dict[str, Any],
        generated_at: str,
    ) -> str:
        """Generate Business Signals markdown."""
        md = f"""# Business Signals

**Company:** {company.name}
**Generated:** {generated_at}

---

## Signal Summary

| Category | Count |
|----------|-------|
| Funding | {len(signals.get('funding', []))} |
| Partnerships | {len(signals.get('partnerships', []))} |
| Product Launches | {len(signals.get('product_launches', []))} |
| Leadership Changes | {len(signals.get('leadership_changes', []))} |
| Awards | {len(signals.get('awards', []))} |
| Acquisitions | {len(signals.get('acquisitions', []))} |

---

"""
        signal_categories = [
            ("funding", "Funding Signals"),
            ("partnerships", "Partnership Signals"),
            ("product_launches", "Product Launch Signals"),
            ("leadership_changes", "Leadership Change Signals"),
            ("awards", "Award & Recognition Signals"),
            ("acquisitions", "Acquisition & Merger Signals"),
        ]

        for key, title in signal_categories:
            items = signals.get(key, [])
            md += f"## {title}\n\n"
            if items:
                for item in items[:5]:
                    t = item.get("title", "Untitled")
                    u = item.get("url", "#")
                    d = (item.get("date") or "")[:10]
                    s = item.get("source", "")
                    md += f"- [{t}]({u})"
                    if d or s:
                        md += f" ({d}, {s})"
                    md += "\n"
            else:
                md += "*No signals detected in this category.*\n"
            md += "\n"

        return md

    def _generate_crisis_md(
        self,
        company: CompanyProfile,
        sentiment: Dict[str, Any],
        _signals: Dict[str, Any],  # Reserved for future crisis signal analysis
        generated_at: str,
    ) -> str:
        """Generate Crisis Indicators markdown."""
        crisis_alert = sentiment.get("crisis_alert", False)
        crisis_details = sentiment.get("crisis_details", [])

        alert_status = "**ACTIVE**" if crisis_alert else "**None Detected**"

        md = f"""# Crisis Indicators

**Company:** {company.name}
**Generated:** {generated_at}

---

## Alert Status

{alert_status}

---

## Crisis Keywords Detected

"""
        if crisis_details:
            for kw in crisis_details:
                md += f"- {kw}\n"
        else:
            md += "*No crisis keywords detected in recent news.*\n"

        md += "\n---\n\n## Sentiment Red Flags\n\n"

        # Check for negative sentiment trend
        trend = sentiment.get("trend", "stable")
        compound = sentiment.get("overall_sentiment", {}).get("compound", 0)

        red_flags_found = False
        if trend == "declining":
            md += "- **Declining sentiment trend detected**\n"
            red_flags_found = True
        if compound < -0.2:
            md += f"- **Negative overall sentiment** (score: {compound:.3f})\n"
            red_flags_found = True

        negative_count = sentiment.get("negative_count", 0)
        total_count = sentiment.get("article_count", 1)
        if total_count > 0 and negative_count / total_count > 0.5:
            md += f"- **High negative article ratio** ({negative_count}/{total_count})\n"
            red_flags_found = True

        if not red_flags_found:
            md += "*No red flags detected.*\n"

        md += "\n---\n\n## Recommended Actions\n\n"
        if crisis_alert or compound < -0.2:
            md += """1. **Monitor closely** - Set up alerts for new articles
2. **Review sources** - Examine negative articles for context
3. **Assess impact** - Evaluate potential business implications
4. **Prepare response** - Consider communication strategy
"""
        else:
            md += "*No immediate action required. Continue routine monitoring.*\n"

        return md

    # =========================================================================
    # Social Intelligence Integration (Reddit + Twitter)
    # =========================================================================

    async def _research_social_intelligence(
        self,
        company: CompanyProfile,
        output_dir: Path,
    ) -> Dict[str, Any]:
        """
        Fetch and analyze social media sentiment using Reddit and Twitter APIs.

        Args:
            company: Company profile to research
            output_dir: Directory to write social reports

        Returns:
            Dict with social intelligence results and statistics
        """
        results = {
            "enabled": True,
            "reddit_available": False,
            "twitter_available": False,
            "reddit_mentions": 0,
            "twitter_mentions": 0,
            "overall_sentiment": "neutral",
        }

        reddit_posts = []
        twitter_analysis = None
        reddit_analysis = None

        # Reddit analysis
        try:
            reddit_tool = RedditTool()
            if reddit_tool.is_available():
                results["reddit_available"] = True
                logger.info(f"Fetching Reddit mentions for {company.name}...")

                industry = company.industry or "technology"
                subreddits = await reddit_tool.find_relevant_subreddits(
                    company.name, industry
                )

                reddit_posts = await reddit_tool.search_company_mentions(
                    company_name=company.name,
                    subreddits=subreddits[:5],
                    limit=50,
                    time_filter="month",
                )
                results["reddit_mentions"] = len(reddit_posts)
                logger.info(f"  Reddit: {len(reddit_posts)} posts found")

                if subreddits:
                    reddit_analysis = await reddit_tool.get_subreddit_sentiment(
                        company.name, subreddits[0], limit=30
                    )
            else:
                logger.debug("Reddit API not configured")

        except ImportError:
            logger.debug("praw not installed - Reddit analysis skipped")
        except Exception as e:
            logger.warning(f"Reddit analysis failed: {e}")
            results["reddit_error"] = str(e)

        # Twitter analysis
        try:
            twitter_tool = TwitterTool()
            if twitter_tool.is_available():
                results["twitter_available"] = True
                logger.info(f"Fetching Twitter mentions for {company.name}...")

                twitter_analysis = await twitter_tool.analyze_mentions(
                    company_name=company.name,
                    hashtags=None,
                )
                results["twitter_mentions"] = twitter_analysis.total_mentions if twitter_analysis else 0
                logger.info(f"  Twitter: {results['twitter_mentions']} mentions found")
            else:
                logger.debug("Twitter API not configured")

        except Exception as e:
            logger.warning(f"Twitter analysis failed: {e}")
            results["twitter_error"] = str(e)

        # Calculate overall sentiment
        if reddit_analysis or twitter_analysis:
            positive = negative = neutral = 0

            if reddit_analysis:
                s = reddit_analysis.sentiment_breakdown
                positive += s.get("positive", 0)
                negative += s.get("negative", 0)
                neutral += s.get("neutral", 0)

            if twitter_analysis:
                s = twitter_analysis.sentiment_breakdown
                positive += s.get("positive", 0)
                negative += s.get("negative", 0)
                neutral += s.get("neutral", 0)

            total = positive + negative + neutral
            if total > 0:
                if positive / total > 0.4:
                    results["overall_sentiment"] = "positive"
                elif negative / total > 0.4:
                    results["overall_sentiment"] = "negative"

        # Write social intelligence reports
        if reddit_posts or (twitter_analysis and twitter_analysis.top_tweets):
            await self._write_social_reports(
                output_dir, company, reddit_posts, reddit_analysis, twitter_analysis
            )

        return results

    async def _write_social_reports(
        self,
        output_dir: Path,
        company: CompanyProfile,
        reddit_posts: List,
        reddit_analysis,
        twitter_analysis,
    ) -> None:
        """Write social intelligence reports as markdown files."""
        social_dir = output_dir / "12-Social-Intelligence"
        social_dir.mkdir(parents=True, exist_ok=True)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Write all 4 report files
        (social_dir / "01-Reddit-Analysis.md").write_text(
            self._generate_reddit_md(company, reddit_posts, reddit_analysis, generated_at),
            encoding="utf-8"
        )
        (social_dir / "02-Twitter-Analysis.md").write_text(
            self._generate_twitter_md(company, twitter_analysis, generated_at),
            encoding="utf-8"
        )
        (social_dir / "03-Sentiment-Summary.md").write_text(
            self._generate_social_sentiment_md(company, reddit_analysis, twitter_analysis, generated_at),
            encoding="utf-8"
        )
        (social_dir / "04-Social-Risks.md").write_text(
            self._generate_social_risks_md(company, reddit_posts, generated_at),
            encoding="utf-8"
        )

        logger.info(f"  Social reports written to {social_dir}")

    def _generate_reddit_md(self, company: CompanyProfile, posts: List, analysis, generated_at: str) -> str:
        """Generate Reddit Analysis markdown."""
        md = f"# Reddit Analysis\n\n**Company:** {company.name}\n**Generated:** {generated_at}\n\n---\n\n"

        if analysis:
            md += f"## Overview\n\n| Metric | Value |\n|--------|-------|\n"
            md += f"| **Subreddit** | r/{analysis.subreddit} |\n"
            md += f"| **Mentions** | {analysis.mention_count} |\n"
            md += f"| **Avg Score** | {analysis.avg_score:.1f} |\n\n"
        else:
            md += "*No Reddit analysis data available.*\n\n"

        md += f"## Top Posts ({len(posts)} total)\n\n"
        for post in posts[:10]:
            md += f"### [{post.title}]({post.url})\n"
            md += f"r/{post.subreddit} | Score: {post.score} | Comments: {post.num_comments}\n\n---\n\n"

        return md if posts else md + "*No posts found.*\n"

    def _generate_twitter_md(self, company: CompanyProfile, analysis, generated_at: str) -> str:
        """Generate Twitter Analysis markdown."""
        md = f"# Twitter/X Analysis\n\n**Company:** {company.name}\n**Generated:** {generated_at}\n\n---\n\n"

        if analysis:
            md += f"## Overview\n\n| Metric | Value |\n|--------|-------|\n"
            md += f"| **Total Mentions** | {analysis.total_mentions} |\n"
            md += f"| **Avg Engagement** | {analysis.avg_engagement:.1f} |\n\n"

            if analysis.hashtags:
                md += "## Trending Hashtags\n\n"
                for tag in analysis.hashtags[:10]:
                    md += f"- #{tag}\n"
                md += "\n"

            if analysis.top_tweets:
                md += "## Top Tweets\n\n"
                for tweet in analysis.top_tweets[:5]:
                    md += f"**@{tweet.author_username or 'unknown'}** | {tweet.likes} likes\n"
                    md += f"> {tweet.text[:200]}...\n\n---\n\n"
        else:
            md += "*No Twitter analysis data available.*\n"

        return md

    def _generate_social_sentiment_md(self, company: CompanyProfile, reddit_analysis, twitter_analysis, generated_at: str) -> str:
        """Generate Social Sentiment Summary markdown."""
        md = f"# Social Sentiment Summary\n\n**Company:** {company.name}\n**Generated:** {generated_at}\n\n---\n\n"

        total_pos = total_neg = total_neu = 0
        if reddit_analysis:
            s = reddit_analysis.sentiment_breakdown
            total_pos += s.get("positive", 0)
            total_neg += s.get("negative", 0)
            total_neu += s.get("neutral", 0)
        if twitter_analysis:
            s = twitter_analysis.sentiment_breakdown
            total_pos += s.get("positive", 0)
            total_neg += s.get("negative", 0)
            total_neu += s.get("neutral", 0)

        total = total_pos + total_neg + total_neu
        if total > 0:
            overall = "Positive" if total_pos / total > 0.4 else ("Negative" if total_neg / total > 0.4 else "Neutral")
            md += f"## Overall Sentiment: **{overall}**\n\n"
            md += f"| Sentiment | Count |\n|-----------|-------|\n"
            md += f"| Positive | {total_pos} |\n| Negative | {total_neg} |\n| Neutral | {total_neu} |\n"
        else:
            md += "*No sentiment data available.*\n"

        return md

    def _generate_social_risks_md(self, company: CompanyProfile, reddit_posts: List, generated_at: str) -> str:
        """Generate Social Risks markdown."""
        md = f"# Social Media Risks\n\n**Company:** {company.name}\n**Generated:** {generated_at}\n\n---\n\n"

        risks = []
        if reddit_posts:
            negative_posts = [p for p in reddit_posts if p.score < 0]
            if len(negative_posts) > 3:
                risks.append(f"- {len(negative_posts)} posts with negative scores")

            complaint_kw = ["scam", "fraud", "terrible", "worst", "avoid"]
            complaints = [p for p in reddit_posts if any(kw in p.title.lower() for kw in complaint_kw)]
            if complaints:
                risks.append(f"- {len(complaints)} posts with complaint keywords")

        if risks:
            md += "## Risk Indicators\n\n" + "\n".join(risks) + "\n"
        else:
            md += "**No significant risks detected.**\n"

        md += "\n## Recommended Actions\n\n1. Monitor brand mentions\n2. Engage with community\n3. Address complaints promptly\n"

        return md

    # =========================================================================
    # Financial Modeling Prep Integration (Deep Financials)
    # =========================================================================

    async def _research_financial_deep_dive(
        self,
        company: CompanyProfile,
        ticker: str,
        output_dir: Path,
    ) -> Dict[str, Any]:
        """
        Deep financial analysis using Financial Modeling Prep API.

        This method provides comprehensive financial data including:
        - Company profile with market cap, employees, CEO
        - Financial ratios and metrics (50+ data points)
        - Analyst estimates and earnings forecasts
        - Company rating (buy/sell recommendation)

        Args:
            company: Company profile being researched
            ticker: Stock ticker symbol
            output_dir: Directory to write financial reports

        Returns:
            Dict with financial analysis results and statistics
        """
        # Check if FMP is enabled
        enable_fmp = os.getenv("ENABLE_FINANCIAL_DEEP_DIVE", "true").lower() == "true"
        if not enable_fmp:
            logger.info("Financial deep dive disabled via ENABLE_FINANCIAL_DEEP_DIVE=false")
            return {"enabled": False}

        try:
            from ..tools.data.financial.fmp import FinancialModelingPrepTool

            fmp = FinancialModelingPrepTool()

            if not fmp.is_available():
                logger.warning("FMP API key not configured")
                return {
                    "enabled": True,
                    "api_available": False,
                    "error": "FINANCIAL_MODELING_PREP_API_KEY not configured",
                }

            logger.info(f"Fetching financial deep dive for {ticker}...")

            # Get comprehensive analysis
            analysis = await fmp.get_full_analysis(ticker)

            # Write financial reports
            await self._write_financial_reports(
                output_dir=output_dir,
                company=company,
                ticker=ticker,
                analysis=analysis,
            )

            # Cleanup
            await fmp.close()

            profile = analysis.get("profile", {})
            metrics = analysis.get("metrics", {})
            rating = analysis.get("rating", {})

            return {
                "enabled": True,
                "api_available": True,
                "ticker": ticker,
                "market_cap": profile.get("market_cap", 0) if profile else 0,
                "sector": profile.get("sector", "") if profile else "",
                "rating": rating.get("rating", "N/A") if rating else "N/A",
                "rating_recommendation": rating.get("rating_recommendation", "") if rating else "",
                "pe_ratio": metrics.get("pe_ratio", 0) if metrics else 0,
                "roe": metrics.get("roe", 0) if metrics else 0,
                "estimates_count": len(analysis.get("estimates", [])),
            }

        except ImportError as e:
            logger.warning(f"FinancialModelingPrepTool not available: {e}")
            return {"enabled": True, "error": str(e)}
        except Exception as e:
            logger.error(f"Financial deep dive failed: {e}")
            return {"enabled": True, "error": str(e)}

    async def _write_financial_reports(
        self,
        output_dir: Path,
        company: CompanyProfile,
        ticker: str,
        analysis: Dict[str, Any],
    ) -> None:
        """
        Write financial analysis reports as markdown files.

        Creates files in the 12-Financial-Deep-Dive directory:
        - 01-Company-Profile.md
        - 02-Financial-Metrics.md
        - 03-Analyst-Estimates.md
        - 04-Company-Rating.md
        """
        fin_dir = output_dir / "12-Financial-Deep-Dive"
        fin_dir.mkdir(parents=True, exist_ok=True)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 01-Company-Profile.md
        profile_content = self._generate_fmp_profile_md(
            company, ticker, analysis.get("profile", {}), generated_at
        )
        (fin_dir / "01-Company-Profile.md").write_text(profile_content, encoding="utf-8")

        # 02-Financial-Metrics.md
        metrics_content = self._generate_fmp_metrics_md(
            company, ticker, analysis.get("metrics", {}),
            analysis.get("income_statement", []),
            analysis.get("key_metrics", []),
            generated_at
        )
        (fin_dir / "02-Financial-Metrics.md").write_text(metrics_content, encoding="utf-8")

        # 03-Analyst-Estimates.md
        estimates_content = self._generate_fmp_estimates_md(
            company, ticker, analysis.get("estimates", []), generated_at
        )
        (fin_dir / "03-Analyst-Estimates.md").write_text(estimates_content, encoding="utf-8")

        # 04-Company-Rating.md
        rating_content = self._generate_fmp_rating_md(
            company, ticker, analysis.get("rating", {}), generated_at
        )
        (fin_dir / "04-Company-Rating.md").write_text(rating_content, encoding="utf-8")

        logger.info(f"  Financial reports written to {fin_dir}")

    def _generate_fmp_profile_md(
        self,
        company: CompanyProfile,
        ticker: str,
        profile: Dict[str, Any],
        generated_at: str,
    ) -> str:
        """Generate Company Profile markdown from FMP data."""
        if not profile:
            return f"""# Company Profile

**Company:** {company.name}
**Ticker:** {ticker}
**Generated:** {generated_at}

---

*No profile data available from Financial Modeling Prep.*
"""

        market_cap = profile.get("market_cap", 0)
        market_cap_str = f"${market_cap:,.0f}" if market_cap else "N/A"

        return f"""# Company Profile

**Company:** {profile.get('company_name', company.name)}
**Ticker:** {ticker}
**Generated:** {generated_at}

---

## Overview

| Attribute | Value |
|-----------|-------|
| **Exchange** | {profile.get('exchange', 'N/A')} |
| **Sector** | {profile.get('sector', 'N/A')} |
| **Industry** | {profile.get('industry', 'N/A')} |
| **Country** | {profile.get('country', 'N/A')} |
| **Currency** | {profile.get('currency', 'USD')} |

---

## Key Figures

| Metric | Value |
|--------|-------|
| **Market Cap** | {market_cap_str} |
| **Stock Price** | ${profile.get('price', 0):.2f} |
| **Beta** | {profile.get('beta', 0):.2f} |
| **Volume (Avg)** | {profile.get('vol_avg', 0):,} |
| **Last Dividend** | ${profile.get('last_div', 0):.2f} |
| **IPO Date** | {profile.get('ipo_date', 'N/A')} |

---

## Leadership & Operations

| Attribute | Value |
|-----------|-------|
| **CEO** | {profile.get('ceo', 'N/A')} |
| **Employees** | {profile.get('employees', 0):,} |
| **Website** | [{profile.get('website', 'N/A')}]({profile.get('website', '#')}) |

---

## Company Description

{profile.get('description', '*No description available.*')}
"""

    def _generate_fmp_metrics_md(
        self,
        company: CompanyProfile,
        ticker: str,
        metrics: Dict[str, Any],
        income_statements: List[Dict],
        key_metrics: List[Dict],
        generated_at: str,
    ) -> str:
        """Generate Financial Metrics markdown from FMP data."""
        md = f"""# Financial Metrics

**Company:** {company.name}
**Ticker:** {ticker}
**Generated:** {generated_at}

---

## Key Ratios

"""
        if metrics:
            md += f"""| Metric | Value |
|--------|-------|
| **Revenue Growth** | {metrics.get('revenue_growth', 0)*100:.1f}% |
| **Gross Margin** | {metrics.get('gross_profit_margin', 0)*100:.1f}% |
| **Operating Margin** | {metrics.get('operating_margin', 0)*100:.1f}% |
| **Net Profit Margin** | {metrics.get('net_profit_margin', 0)*100:.1f}% |
| **ROE** | {metrics.get('roe', 0)*100:.1f}% |
| **ROA** | {metrics.get('roa', 0)*100:.1f}% |
| **Debt/Equity** | {metrics.get('debt_to_equity', 0):.2f} |
| **Current Ratio** | {metrics.get('current_ratio', 0):.2f} |

---

## Valuation Metrics

| Metric | Value |
|--------|-------|
| **P/E Ratio** | {metrics.get('pe_ratio', 0):.2f} |
| **P/B Ratio** | {metrics.get('pb_ratio', 0):.2f} |
| **EV/EBITDA** | {metrics.get('ev_to_ebitda', 0):.2f} |

"""
        else:
            md += "*No metrics data available.*\n\n"

        # Add income statement highlights
        if income_statements:
            md += "---\n\n## Income Statement Highlights\n\n"
            md += "| Period | Revenue | Net Income | EPS |\n"
            md += "|--------|---------|------------|-----|\n"
            for stmt in income_statements[:3]:
                period = stmt.get("date", "N/A")[:10]
                revenue = stmt.get("revenue", 0)
                net_income = stmt.get("netIncome", 0)
                eps = stmt.get("eps", 0)
                md += f"| {period} | ${revenue:,.0f} | ${net_income:,.0f} | ${eps:.2f} |\n"

        return md

    def _generate_fmp_estimates_md(
        self,
        company: CompanyProfile,
        ticker: str,
        estimates: List[Dict],
        generated_at: str,
    ) -> str:
        """Generate Analyst Estimates markdown from FMP data."""
        md = f"""# Analyst Estimates

**Company:** {company.name}
**Ticker:** {ticker}
**Generated:** {generated_at}

---

## Earnings Estimates

"""
        if estimates:
            md += "| Period | Est. EPS | Actual EPS | Est. Revenue | Analysts |\n"
            md += "|--------|----------|------------|--------------|----------|\n"
            for est in estimates:
                period = est.get("date", "N/A")[:10]
                est_eps = est.get("estimated_eps", 0)
                actual_eps = est.get("actual_eps")
                actual_str = f"${actual_eps:.2f}" if actual_eps is not None else "Pending"
                est_rev = est.get("revenue_estimated", 0)
                analysts = est.get("number_of_analysts", 0)
                md += f"| {period} | ${est_eps:.2f} | {actual_str} | ${est_rev:,.0f} | {analysts} |\n"
        else:
            md += "*No analyst estimates available.*\n"

        return md

    def _generate_fmp_rating_md(
        self,
        company: CompanyProfile,
        ticker: str,
        rating: Dict[str, Any],
        generated_at: str,
    ) -> str:
        """Generate Company Rating markdown from FMP data."""
        md = f"""# Company Rating

**Company:** {company.name}
**Ticker:** {ticker}
**Generated:** {generated_at}

---

"""
        if rating:
            rating_grade = rating.get("rating", "N/A")
            rating_score = rating.get("rating_score", 0)
            recommendation = rating.get("rating_recommendation", "N/A")

            md += f"""## Overall Rating

| Metric | Value |
|--------|-------|
| **Grade** | **{rating_grade}** |
| **Score** | {rating_score}/5 |
| **Recommendation** | **{recommendation}** |

---

## Rating Breakdown

"""
            details = rating.get("rating_details", {})
            if details:
                md += "| Factor | Score |\n"
                md += "|--------|-------|\n"
                factor_names = {
                    "dcf": "DCF Valuation",
                    "roe": "Return on Equity",
                    "roa": "Return on Assets",
                    "de": "Debt/Equity",
                    "pe": "P/E Ratio",
                    "pb": "P/B Ratio",
                }
                for key, name in factor_names.items():
                    score = details.get(key, "N/A")
                    md += f"| {name} | {score} |\n"
        else:
            md += "*No rating data available.*\n"

        return md


# =============================================================================
# Content Generation for All Files
# =============================================================================

class ContentGenerator:
    """Generates content for all 52+ output files."""

    def __init__(self, ai_client, template_dir: Optional[Path] = None):
        self.ai_client = ai_client
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"

    async def generate_all_files(
        self,
        research_result: ComprehensiveResearchResult,
    ) -> Dict[str, str]:
        """
        Generate content for all output files.

        Returns:
            Dict mapping relative file paths to content
        """
        outputs = {}
        company = research_result.company

        # Generate content for each section/file with results
        for section_name, section_results in research_result.sections.items():
            for filename, file_result in section_results.items():
                output_path = f"{file_result.section}/{filename}"

                try:
                    content = await self._generate_file_content(
                        company=company,
                        section=section_name,
                        filename=filename,
                        sources=file_result.sources,
                    )
                    outputs[output_path] = content
                except Exception as e:
                    logger.error(f"Failed to generate {output_path}: {e}")
                    # Generate placeholder
                    outputs[output_path] = self._generate_placeholder(
                        company, filename, str(e)
                    )

        # Add source tracking files
        if research_result.source_tracker:
            source_files = research_result.source_tracker.get_output_files()
            outputs.update(source_files)

        return outputs

    async def _generate_file_content(
        self,
        company: CompanyProfile,
        section: str,
        filename: str,
        sources: List[ResearchSource],
    ) -> str:
        """Generate content for a single file using AI."""
        # Build context from sources
        context_parts = []
        for source in sources[:15]:  # Limit to prevent token overflow
            if source.content:
                context_parts.append(
                    f"[Source: {source.title}]\n{source.content[:2000]}"
                )

        context_text = "\n\n---\n\n".join(context_parts)

        if not context_text:
            return self._generate_placeholder(company, filename, "No sources available")

        # Generate analysis prompt based on file type
        prompt = self._get_prompt_for_file(company, filename, context_text)

        try:
            response = await self.ai_client.generate(
                prompt,
                response_format="json",
                temperature=0.3,
            )
            data = robust_json_parse(response)

            # Render template
            return self._render_template(filename, company, data, sources)

        except Exception as e:
            logger.error(f"AI generation failed for {filename}: {e}")
            return self._generate_placeholder(company, filename, str(e))

    def _get_prompt_for_file(
        self,
        company: CompanyProfile,
        filename: str,
        context: str,
    ) -> str:
        """Get the appropriate analysis prompt for a file type."""
        # Map filenames to prompt templates
        prompts = {
            "01-Company-Overview.md": f"""Analyze the following content about {company.name} and extract company overview information.

CONTENT:
{context}

Return JSON with:
{{
    "legal_name": "Official legal name",
    "trade_name": "Trading name",
    "founded": "Year founded",
    "headquarters": "HQ location",
    "website": "Company website",
    "mission": "Mission statement if available",
    "vision": "Vision statement if available",
    "values": ["Value 1", "Value 2"],
    "history_summary": "Brief history",
    "milestones": [{{"year": "2020", "event": "Key event"}}],
    "ownership": [{{"shareholder": "Name", "percentage": "X%"}}],
    "subsidiaries": ["Sub 1", "Sub 2"],
    "employee_count": "Number of employees",
    "core_values": ["Value 1", "Value 2"]
}}""",

            "01-Market-Size-Growth.md": f"""Analyze the following content about the {company.industry} market and extract market size/growth data.

CONTENT:
{context}

Return JSON with:
{{
    "tam": "Total Addressable Market value",
    "tam_description": "TAM explanation",
    "sam": "Serviceable Available Market",
    "som": "Serviceable Obtainable Market",
    "current_market_value": "Current market value with year",
    "projected_market_value": "Projected value with year",
    "cagr": "CAGR percentage and period",
    "segments": [{{"segment": "Name", "size": "Value", "growth": "CAGR"}}],
    "growth_drivers": [{{"driver": "Name", "description": "Details", "impact": "High/Medium/Low"}}],
    "challenges": [{{"challenge": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "trends": [{{"trend": "Name", "relevance": "How it affects company"}}],
    "key_statistics": ["Stat 1 with number", "Stat 2 with number"]
}}""",

            "01-Competitor-List.md": f"""Analyze the following content and extract competitor information for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "competitors": [
        {{
            "name": "Competitor name",
            "type": "Direct/Indirect",
            "market_share": "Percentage if known",
            "threat_level": "High/Medium/Low",
            "parent_company": "Parent if applicable",
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1"],
            "description": "Brief description"
        }}
    ],
    "market_share_summary": "Overview of market share distribution",
    "competitive_dynamics": "How competitors interact"
}}""",

            "01-Financials.md": f"""Analyze the following content and extract financial information about {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "ownership": "Ownership structure",
    "subsidiaries": ["Subsidiary 1"],
    "revenue": "Latest revenue with year",
    "revenue_growth": "YoY growth percentage",
    "profit_margin": "Profit margin if known",
    "ebitda": "EBITDA if known",
    "net_income": "Net income if known",
    "arpu": "Average revenue per user",
    "subscriber_count": "Number of subscribers/users",
    "churn_rate": "Churn rate if known",
    "funding_rounds": [{{"round": "Series A", "amount": "$XM", "date": "Year", "investors": ["Investor"]}}],
    "stock_status": "Public/Private",
    "financial_outlook": "Future outlook summary",
    "industry_comparison": "How they compare to industry"
}}""",

            "05-Sales-Strategy.md": f"""Analyze the following content and extract sales intelligence for selling to/about {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "target_profile": {{
        "company_size": "Size description",
        "annual_revenue": "Revenue estimate",
        "technology_maturity": "Tech maturity level"
    }},
    "decision_makers": [{{"role": "Title", "influence": "High/Medium/Low", "priority": "What they care about"}}],
    "pain_points": [
        {{
            "pain_point": "Name",
            "severity": "High/Medium/Low",
            "urgency": "High/Medium/Low",
            "business_impact": "Description",
            "evidence": "How we know this",
            "solution_opportunity": "How to address it"
        }}
    ],
    "buying_signals": ["Signal 1", "Signal 2"],
    "recommended_approach": "Sales strategy summary",
    "objections_responses": [{{"objection": "Common objection", "response": "How to address"}}],
    "next_steps": ["Step 1", "Step 2"]
}}""",

            # SEC Filing prompts (10-SEC-Filings section)
            "01-Business-Overview.md": f"""Analyze the following SEC 10-K filing content for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "company_description": "Official business description from 10-K",
    "principal_products": ["Product/Service 1", "Product/Service 2"],
    "business_segments": [{{"segment": "Name", "description": "What it does", "revenue_contribution": "% if known"}}],
    "geographic_presence": [{{"region": "Name", "operations": "Description"}}],
    "key_customers": ["Customer type 1", "Customer type 2"],
    "competitive_position": "Market position description",
    "employees": "Employee count",
    "properties": "Key facilities/properties",
    "fiscal_year_end": "Month"
}}""",

            "02-Risk-Factors.md": f"""Analyze the following SEC filing risk factors for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "market_risks": [{{"risk": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "operational_risks": [{{"risk": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "financial_risks": [{{"risk": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "regulatory_risks": [{{"risk": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "technology_risks": [{{"risk": "Name", "description": "Details", "severity": "High/Medium/Low"}}],
    "summary": "Overall risk assessment"
}}""",

            "03-Financial-Highlights.md": f"""Analyze the following SEC filing financial data for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "revenue": {{"current": "Amount", "prior_year": "Amount", "growth": "X%"}},
    "net_income": {{"current": "Amount", "prior_year": "Amount", "growth": "X%"}},
    "gross_margin": "X%",
    "operating_margin": "X%",
    "total_assets": "Amount",
    "total_liabilities": "Amount",
    "shareholders_equity": "Amount",
    "cash_and_equivalents": "Amount",
    "debt": "Amount",
    "eps": {{"basic": "Amount", "diluted": "Amount"}},
    "key_ratios": [{{"ratio": "Name", "value": "X"}}],
    "fiscal_year": "Year"
}}""",

            "04-MDA-Summary.md": f"""Analyze the following Management Discussion & Analysis from SEC filing for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "performance_summary": "Management's view of overall performance",
    "key_factors": [{{"factor": "Name", "impact": "Description"}}],
    "segment_performance": [{{"segment": "Name", "performance": "Description"}}],
    "liquidity": "Liquidity and capital resources summary",
    "capital_expenditures": "CapEx plans and amounts",
    "outlook": "Future outlook and guidance",
    "critical_accounting": ["Policy 1", "Policy 2"],
    "management_focus": "Key priorities mentioned"
}}""",

            "05-Recent-Events.md": f"""Analyze the following SEC 8-K filings (current reports) for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "events": [
        {{
            "date": "Filing date",
            "type": "Event type (earnings, M&A, leadership, etc.)",
            "description": "Event summary",
            "significance": "High/Medium/Low",
            "market_impact": "Potential impact description"
        }}
    ],
    "patterns": "Any patterns in recent events",
    "upcoming": "Upcoming expected events if mentioned"
}}""",

            "06-Executive-Compensation.md": f"""Analyze the following executive compensation data from SEC filings for {company.name}.

CONTENT:
{context}

Return JSON with:
{{
    "ceo_compensation": {{
        "name": "CEO Name",
        "base_salary": "Amount",
        "bonus": "Amount",
        "stock_awards": "Amount",
        "total": "Amount"
    }},
    "other_executives": [
        {{
            "name": "Name",
            "title": "Title",
            "total_compensation": "Amount"
        }}
    ],
    "compensation_philosophy": "Description of pay approach",
    "performance_metrics": ["Metric 1", "Metric 2"],
    "say_on_pay": "Shareholder vote results if available"
}}""",
        }

        # Default prompt for files without specific templates
        default_prompt = f"""Analyze the following content about {company.name} ({company.industry}) and extract relevant information for {filename}.

CONTENT:
{context}

Return a JSON object with the key information extracted, including specific numbers, dates, names, and facts where available. Structure the response appropriately for the file topic."""

        return prompts.get(filename, default_prompt)

    def _render_template(
        self,
        filename: str,
        company: CompanyProfile,
        data: Dict[str, Any],
        sources: List[ResearchSource],
    ) -> str:
        """Render a template with the generated data."""
        try:
            template_path = self.template_dir / filename
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    template_str = f.read()
                template = jinja2.Template(template_str)
                return template.render(
                    company=company,
                    company_name=company.name,
                    industry=company.industry or "N/A",
                    country=company.country or "Global",
                    generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    sources=[{"title": s.title, "url": s.url} for s in sources],
                    **data,
                )
        except Exception as e:
            logger.debug(f"Template rendering failed for {filename}: {e}")

        # Fallback: generate basic markdown
        return self._generate_basic_markdown(filename, company, data, sources)

    def _generate_basic_markdown(
        self,
        filename: str,
        company: CompanyProfile,
        data: Dict[str, Any],
        sources: List[ResearchSource],
    ) -> str:
        """Generate basic markdown when template is unavailable."""
        title = filename.replace(".md", "").replace("-", " ").lstrip("0123456789-")
        md = f"# {title}\n\n"
        md += f"**Company:** {company.name}\n"
        md += f"**Industry:** {company.industry or 'N/A'}\n"
        md += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        md += "---\n\n"

        # Render data
        for key, value in data.items():
            if value and value != "N/A":
                section_title = key.replace("_", " ").title()
                md += f"## {section_title}\n\n"
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            md += f"### {item.get('name', item.get('title', 'Item'))}\n"
                            for k, v in item.items():
                                if v and k not in ('name', 'title'):
                                    md += f"- **{k.replace('_', ' ').title()}:** {v}\n"
                            md += "\n"
                        else:
                            md += f"- {item}\n"
                    md += "\n"
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if v:
                            md += f"- **{k.replace('_', ' ').title()}:** {v}\n"
                    md += "\n"
                else:
                    md += f"{value}\n\n"

        # Add sources
        md += "## Sources\n\n"
        for source in sources[:20]:
            md += f"- [{source.title}]({source.url})\n"

        return md

    def _generate_placeholder(
        self,
        company: CompanyProfile,
        filename: str,
        error: str,
    ) -> str:
        """Generate placeholder content when generation fails."""
        title = filename.replace(".md", "").replace("-", " ").lstrip("0123456789-")
        return f"""# {title}

**Company:** {company.name}
**Date:** {datetime.now().strftime('%Y-%m-%d')}

---

## Data Not Available

Unable to generate content for this section.

**Reason:** {error}

Please run additional research to populate this section.
"""


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SectionResearchResult",
    "ComprehensiveResearchResult",
    "ComprehensiveResearchService",
    "ContentGenerator",
]
