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
from ..services.source_tracker import SourceTracker, reset_source_tracker
from ..services.json_parser_helper import robust_json_parse
from ..core.logger import setup_logger
from ..utils.url_utils import add_country_context_to_query
from ..core.relevance_filter import RelevanceFilter
from ..core.adaptive_timeout import get_adaptive_timeout_manager
from ..core.company_probe import probe_company_presence, CompanyPresence, RESEARCH_PROFILES
from ..core.url_cache import reset_url_cache
from ..services.html_cache import get_html_cache
from ..core.ai_query_planner import get_query_planner, QueryPlan
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
from ..core.cross_company_cache import (
    get_cross_company_cache,
    reset_cross_company_cache,
)
from ..core.domain_timeout import (
    get_timeout_manager,
    is_domain_circuit_open,
)
from ..core.search_fallback import (
    SearchFallbackManager,
    get_fallback_queries,
)

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

        return result

    async def _research_section(
        self,
        company: CompanyProfile,
        section_name: str,
        queries: List[QueryTemplate],
    ) -> Dict[str, SectionResearchResult]:
        """Research a single section with all its queries."""
        logger.info(f"Researching section: {section_name} ({len(queries)} queries)")

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
