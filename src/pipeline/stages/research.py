"""
Research Stages - Domain-specific stages for company research.

These stages replace the existing agent pattern with typed,
composable units of work that use the Pipeline architecture.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2

from ...core.result import Result, Ok, Err
from ...core.types import CompanyProfile, ResearchSource, ResearchPhaseResult
from ...services.json_parser_helper import robust_json_parse
from ...services.security import sanitize_company_name
from ...services.query_optimizer import (
    generate_fallback_queries,
    should_retry_query,
)
from ...services.source_quality_scorer import (
    rank_search_results,
    get_domain_authority_score,
)

from ..context import RequestContext
from ..stage import Stage, StageError


# =============================================================================
# Research Input/Output Types
# =============================================================================


@dataclass
class ResearchInput:
    """
    Input for the research pipeline.

    Attributes:
        company: The company profile to research
        research_types: Which types of research to perform
        max_sources_per_query: Maximum sources per search query
        extra_context: Additional context for prompts
    """

    company: CompanyProfile
    research_types: List[str] = field(
        default_factory=lambda: [
            "market",
            "financial",
            "competitor",
            "brand",
            "sales",
        ]
    )
    max_sources_per_query: int = 3
    extra_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result of a single search query."""

    query: str
    sources: List[ResearchSource] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class SearchPhaseOutput:
    """
    Output from the search phase.

    Collects all search results across all queries.
    """

    company: CompanyProfile
    queries: List[str]
    results: List[QueryResult] = field(default_factory=list)
    all_sources: List[ResearchSource] = field(default_factory=list)

    @property
    def total_sources(self) -> int:
        return len(self.all_sources)

    @property
    def successful_queries(self) -> int:
        return sum(1 for r in self.results if r.sources)

    def get_context_text(self, max_chars_per_source: int = 2000) -> str:
        """Get concatenated context from all sources."""
        parts = []
        for source in self.all_sources:
            content = source.content[:max_chars_per_source] if source.content else ""
            parts.append(f"Source: {source.title}\nContent: {content}")
        return "\n\n".join(parts)


@dataclass
class AnalysisOutput:
    """
    Output from the analysis phase.

    Contains structured analysis data from LLM.
    """

    company: CompanyProfile
    research_type: str
    data: Dict[str, Any]
    sources: List[ResearchSource]
    raw_output: str = ""

    @property
    def has_error(self) -> bool:
        return "error" in self.data


@dataclass
class ResearchOutput:
    """
    Final output from the research pipeline.

    Contains all phase results ready for report generation.
    """

    company: CompanyProfile
    phases: List[ResearchPhaseResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.phases) > 0 and not self.errors

    def get_phase(self, name: str) -> Optional[ResearchPhaseResult]:
        for phase in self.phases:
            if phase.phase_name == name:
                return phase
        return None


# =============================================================================
# Query Generation Stage
# =============================================================================


class QueryGenerationStage(Stage[ResearchInput, SearchPhaseOutput]):
    """
    Generates search queries based on company and research type.

    This stage creates optimized search queries for each research type,
    considering the company profile and industry context.
    """

    def __init__(self, research_type: str):
        self._research_type = research_type
        # Issue #5: Improved query templates with better disambiguation
        # Using quotes around company name and explicit industry terms
        self._query_templates = {
            "market": [
                '"{company}" {industry} market share',
                '"{company}" {industry} company overview',
                "{industry} market size growth {country}",
                "{industry} market trends analysis",
            ],
            "financial": [
                '"{company}" {industry} financial performance',
                '"{company}" {industry} revenue annual report',
                '"{company}" company financials {industry}',
                "{company} investor relations {industry}",
                # Parent company queries for better financial data
                '"{company}" parent company owner financials',
                '"{company}" {industry} holding company annual report',
                '"{company}" owner group financial results revenue',
                "{company} {country} telecom parent company financial",
            ],
            "competitor": [
                '"{company}" competitors {industry}',
                "{company} vs competitors comparison {industry}",
                "{industry} companies market leaders {country}",
                "{industry} top players market share {country}",
                '"{company}" competitive landscape analysis',
                # Additional queries for better competitor discovery (BUG-042)
                "{company} alternatives {industry}",
                'site:crunchbase.com "{company}" {industry}',
            ],
            "brand": [
                '"{company}" {industry} brand reputation',
                '"{company}" customer reviews {industry}',
                '"{company}" brand mission values {industry}',
                '"{company}" marketing campaigns {industry}',
            ],
            "sales": [
                '"{company}" {industry} sales strategy',
                '"{company}" distribution channels {industry}',
                '"{company}" pricing plans {industry}',
                '"{company}" B2B enterprise clients {industry}',
            ],
        }

    @property
    def name(self) -> str:
        return f"query_generation_{self._research_type}"

    async def execute(
        self,
        input: ResearchInput,
        ctx: RequestContext,
    ) -> Result[SearchPhaseOutput, StageError]:
        safe_name = sanitize_company_name(input.company.name)
        industry = input.company.industry or "industry"
        country = input.company.country if input.company.country != "Global" else ""

        templates = self._query_templates.get(self._research_type, [])
        if not templates:
            return Err(
                StageError.invalid_input(
                    self.name,
                    f"Unknown research type: {self._research_type}",
                )
            )

        # Generate queries with country context (BUG-049)
        # Issue #5: Templates now include {country} placeholder
        queries = []
        for template in templates:
            # Format with all available placeholders
            query = template.format(
                company=safe_name,
                industry=industry,
                country=country,
            )
            # Clean up double spaces from empty country
            query = " ".join(query.split())
            queries.append(query)

        ctx.logger.info(f"Generated {len(queries)} queries for {self._research_type}")

        return Ok(
            SearchPhaseOutput(
                company=input.company,
                queries=queries,
            )
        )


# =============================================================================
# Search Execution Stage
# =============================================================================


class SearchExecutionStage(Stage[SearchPhaseOutput, SearchPhaseOutput]):
    """
    Executes search queries and fetches content from URLs.

    Uses bounded concurrency to prevent overwhelming external services.
    Enhanced with:
    - Smart fallback queries when searches return no results
    - Source quality ranking to prioritize high-authority sources
    """

    MAX_CONCURRENT_QUERIES = 5
    MAX_FALLBACK_ATTEMPTS = 2  # Max fallback queries per empty result

    def __init__(self, max_results_per_query: int = 3):
        self._max_results = max_results_per_query

    @property
    def name(self) -> str:
        return "search_execution"

    async def execute(
        self,
        input: SearchPhaseOutput,
        ctx: RequestContext,
    ) -> Result[SearchPhaseOutput, StageError]:
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_QUERIES)
        target_country_tld = input.company.get_country_tld()

        async def fetch_query(query: str) -> QueryResult:
            async with semaphore:
                # Check cancellation
                if ctx.cancellation.is_cancelled:
                    return QueryResult(query=query, error="Cancelled")

                try:
                    # Search
                    search_results = await ctx.search_tool.search(
                        query, max_results=self._max_results
                    )

                    # Rank search results by quality before fetching (pre-fetch scoring)
                    if search_results:
                        search_results = rank_search_results(
                            search_results,
                            target_country_tld=target_country_tld,
                        )

                    # Extract URLs (now ranked by quality)
                    urls = [r.get("url") for r in search_results if r.get("url")]

                    if not urls:
                        return QueryResult(query=query, sources=[])

                    # Fetch content
                    sources = await ctx.browser_tool.fetch_multiple(urls)
                    return QueryResult(query=query, sources=sources)

                except Exception as e:
                    ctx.logger.warning(f"Query failed: {query}", error=str(e))
                    return QueryResult(query=query, error=str(e))

        async def fetch_with_fallbacks(query: str) -> List[QueryResult]:
            """Execute query with smart fallbacks if no results."""
            results = []

            # Try original query first
            result = await fetch_query(query)
            results.append(result)

            # Check if we need fallbacks (no sources and no error)
            if should_retry_query(query, len(result.sources)) and not result.error:
                # Generate fallback queries
                fallbacks = generate_fallback_queries(
                    original_query=query,
                    company_name=input.company.name,
                    country=input.company.country,
                    industry=input.company.industry,
                    max_fallbacks=self.MAX_FALLBACK_ATTEMPTS,
                )

                # Try fallbacks until we get results
                for fallback_query in fallbacks:
                    if ctx.cancellation.is_cancelled:
                        break

                    ctx.logger.info(f"Trying fallback query: {fallback_query[:50]}...")
                    fallback_result = await fetch_query(fallback_query)
                    results.append(fallback_result)

                    # Stop if we got results
                    if fallback_result.sources:
                        ctx.logger.info(
                            f"Fallback succeeded with {len(fallback_result.sources)} sources"
                        )
                        break

            return results

        # Execute all queries in parallel (bounded by semaphore)
        ctx.logger.info(
            f"Executing {len(input.queries)} search queries",
            max_concurrent=self.MAX_CONCURRENT_QUERIES,
        )

        # Use fetch_with_fallbacks for each query
        all_query_results = await asyncio.gather(
            *[fetch_with_fallbacks(q) for q in input.queries],
            return_exceptions=True,
        )

        # Process results with deduplication (BUG-044)
        query_results = []
        all_sources = []
        seen_urls = set()  # Track URLs for deduplication
        failed_count = 0
        duplicate_count = 0
        empty_count = 0
        fallback_success_count = 0

        for i, result_list in enumerate(all_query_results):
            if isinstance(result_list, Exception):
                query_results.append(
                    QueryResult(
                        query=input.queries[i],
                        error=str(result_list),
                    )
                )
                failed_count += 1
            else:
                # result_list is a list of QueryResults (original + fallbacks)
                got_sources = False
                for result in result_list:
                    query_results.append(result)
                    # Deduplicate sources by URL (BUG-044, BUG-052)
                    for source in result.sources:
                        # Normalize URL: lowercase, strip trailing slash, remove www prefix
                        normalized_url = source.url.lower().rstrip("/")
                        # Remove www. prefix for deduplication (BUG-052)
                        if "://www." in normalized_url:
                            normalized_url = normalized_url.replace("://www.", "://")
                        if normalized_url not in seen_urls:
                            seen_urls.add(normalized_url)
                            all_sources.append(source)
                            got_sources = True
                        else:
                            duplicate_count += 1
                    if result.error:
                        failed_count += 1

                # Track if fallbacks helped
                if len(result_list) > 1 and got_sources:
                    fallback_success_count += 1
                elif not got_sources:
                    empty_count += 1  # Track empty results (TECH-033)

        # Sort all_sources by domain authority (highest first)
        all_sources.sort(key=lambda s: get_domain_authority_score(s.url), reverse=True)

        # Accurate logging with empty count (TECH-033)
        ctx.logger.info(
            f"Search completed",
            total_sources=len(all_sources),
            successful_queries=len(input.queries) - failed_count - empty_count,
            empty_queries=empty_count,
            failed_queries=failed_count,
            duplicates_removed=duplicate_count,
            fallback_successes=fallback_success_count,
        )

        return Ok(
            SearchPhaseOutput(
                company=input.company,
                queries=input.queries,
                results=query_results,
                all_sources=all_sources,
            )
        )


# =============================================================================
# Analysis Stage
# =============================================================================


class AnalysisStage(Stage[SearchPhaseOutput, AnalysisOutput]):
    """
    Analyzes gathered sources using LLM with deep research.

    Enhanced with:
    - Learnings extraction from sources
    - Source curation and ranking
    - Enriched context with extracted facts/metrics
    """

    PROMPT_FILES = {
        "market": "market_intelligence.txt",
        "financial": "financial_analysis.txt",
        "competitor": "competitive_landscape.txt",
        "brand": "brand_strategy.txt",
        "sales": "sales_strategy.txt",
    }

    def __init__(self, research_type: str, enable_deep_research: bool = True):
        self._research_type = research_type
        self._enable_deep_research = enable_deep_research

    @property
    def name(self) -> str:
        return f"analysis_{self._research_type}"

    async def execute(
        self,
        input: SearchPhaseOutput,
        ctx: RequestContext,
    ) -> Result[AnalysisOutput, StageError]:
        # Load prompt template
        prompt_file = self.PROMPT_FILES.get(self._research_type)
        if not prompt_file:
            return Err(
                StageError.invalid_input(
                    self.name,
                    f"No prompt file for research type: {self._research_type}",
                )
            )

        prompt_path = Path(__file__).parent.parent.parent / "prompts" / prompt_file

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template_str = f.read()
        except FileNotFoundError:
            return Err(
                StageError.invalid_input(
                    self.name,
                    f"Prompt file not found: {prompt_file}",
                )
            )

        # Get context - enhanced with deep research if enabled
        if self._enable_deep_research and input.all_sources:
            context_text = await self._get_enriched_context(input, ctx)
        else:
            context_text = input.get_context_text()

        if not context_text:
            ctx.logger.warning("No source content available for analysis")
            return Ok(
                AnalysisOutput(
                    company=input.company,
                    research_type=self._research_type,
                    data={"warning": "No source data available"},
                    sources=input.all_sources,
                )
            )

        # Render prompt
        template = jinja2.Template(prompt_template_str)
        prompt = template.render(
            company=input.company,
            context=context_text,
        )

        # Generate analysis
        ctx.logger.info(f"Generating {self._research_type} analysis")

        try:
            response = await ctx.ai_client.generate(
                prompt,
                response_format="json",
            )

            # Parse JSON response
            data = robust_json_parse(response)

            return Ok(
                AnalysisOutput(
                    company=input.company,
                    research_type=self._research_type,
                    data=data,
                    sources=input.all_sources,
                    raw_output=response,
                )
            )

        except Exception as e:
            ctx.logger.error(f"Analysis failed: {e}")
            return Err(
                StageError.ai_error(
                    self.name,
                    f"Analysis generation failed: {e}",
                    retryable=True,
                )
            )

    async def _get_enriched_context(
        self,
        input: SearchPhaseOutput,
        ctx: RequestContext,
    ) -> str:
        """
        Get enriched context using deep research service.

        This extracts learnings, curates sources, and builds
        a richer context than raw source content.
        """
        try:
            from ...services.deep_research import DeepResearchService

            deep_research = DeepResearchService(
                ai_client=ctx.ai_client,
                max_iterations=1,  # Single pass for now (faster)
            )

            ctx.logger.info(f"Running deep research for {self._research_type}")

            # Run deep research (without followup queries for now)
            state = await deep_research.run_deep_research(
                initial_sources=input.all_sources,
                company=input.company,
                research_type=self._research_type,
                search_callback=None,  # Disable followup queries for speed
            )

            # Build enriched context
            enriched = deep_research.build_enriched_context(state)

            if enriched:
                ctx.logger.info(
                    f"Deep research complete: {len(state.learnings)} learnings extracted"
                )
                return enriched
            else:
                # Fallback to raw context
                ctx.logger.warning("Deep research returned empty, using raw context")
                return input.get_context_text()

        except Exception as e:
            ctx.logger.warning(f"Deep research failed, using raw context: {e}")
            return input.get_context_text()


# =============================================================================
# Report Generation Stage
# =============================================================================


class ReportGenerationStage(Stage[AnalysisOutput, ResearchPhaseResult]):
    """
    Generates markdown report from analysis output.

    Uses Jinja2 templates for consistent formatting.
    """

    TEMPLATE_FILES = {
        "market": "01-Market-Size-Growth.md",
        "financial": "01-Financials.md",
        "competitor": "01-Competitor-List.md",
        "brand": "01-Positioning.md",
        "sales": "05-Sales-Strategy.md",
    }

    def __init__(self, research_type: str):
        self._research_type = research_type

    @property
    def name(self) -> str:
        return f"report_{self._research_type}"

    async def execute(
        self,
        input: AnalysisOutput,
        ctx: RequestContext,
    ) -> Result[ResearchPhaseResult, StageError]:
        template_name = self.TEMPLATE_FILES.get(self._research_type)
        if not template_name:
            template_name = f"{self._research_type}.md"

        # Import template renderer
        from ...core.template_renderer import get_template_renderer

        renderer = get_template_renderer()

        try:
            # Filter out error/dictionary/irrelevant/foreign sources (BUG-039, BUG-045)
            target_industry = input.company.industry
            target_country_tld = input.company.get_country_tld()
            usable_sources = [
                s
                for s in input.sources
                if s.is_usable(target_industry, target_country_tld)
            ]

            filtered_count = len(input.sources) - len(usable_sources)
            if filtered_count > 0:
                ctx.logger.info(
                    f"Filtered {filtered_count} unusable sources from report"
                )

            # Prepare template context with all required variables (BUG-040, BUG-054)
            # Issue #2: Filter out empty/None values from AI data to prevent overwriting
            # our explicit template variables with empty strings
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            # Filter AI response data - remove empty strings, None values, and "N/A"
            ai_data = {
                k: v
                for k, v in input.data.items()
                if v is not None
                and v != ""
                and v != "N/A"
                and k
                not in (
                    "industry",
                    "country",
                    "region",
                    "company",
                    "company_name",
                    "company_url",
                    "timestamp",
                    "generated_at",
                    "date",
                    "sources",
                )
            }

            template_context = {
                # AI-generated data first (filtered)
                **ai_data,
                # Explicit company data (takes precedence)
                "company": input.company,
                "company_name": input.company.name,
                "company_url": input.company.website,
                # Template variables - both original names and aliases for compatibility
                "industry": input.company.industry or "N/A",
                "company_industry": input.company.industry or "N/A",
                "country": input.company.country or "Global",
                "company_country": input.company.country or "Global",
                "region": input.company.country or "Global",
                # Timestamp variables - multiple formats for template compatibility
                "timestamp": now.isoformat(),
                "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "agent_name": f"{self._research_type.title()}Analyst",
                "research_type": self._research_type,
                "sources": [
                    {
                        "title": s.title,
                        "url": s.url,
                        "source_type": s.source_type,
                    }
                    for s in usable_sources
                ],
            }

            markdown_content = renderer.render(template_name, **template_context)

        except Exception as e:
            ctx.logger.warning(f"Template rendering failed: {e}")
            # Fallback to basic format
            markdown_content = self._fallback_render(input)

        return Ok(
            ResearchPhaseResult(
                phase_name=self._research_type,
                markdown_content=markdown_content,
                sources=input.sources,
            )
        )

    def _fallback_render(self, input: AnalysisOutput) -> str:
        """Fallback rendering when template fails."""
        md = f"# {self._research_type.title()} Analysis\n\n"
        md += f"**Company:** {input.company.name}\n"
        md += "---\n\n"

        if input.has_error:
            md += f"**Error:** {input.data.get('error')}\n\n"
        else:
            for key, value in input.data.items():
                if key not in ("error", "raw_output"):
                    md += f"## {key.replace('_', ' ').title()}\n\n"
                    md += f"{value}\n\n"

        md += "## Sources\n\n"
        for source in input.sources:
            md += f"- [{source.title}]({source.url})\n"

        return md


# =============================================================================
# Research Phase Stage (Combines Query -> Search -> Analysis -> Report)
# =============================================================================


class ResearchPhaseStage(Stage[ResearchInput, ResearchPhaseResult]):
    """
    Complete research phase for a single research type.

    Combines query generation, search, analysis, and report generation
    into a single cohesive stage.

    Enhanced with:
    - Iterative query refinement based on gaps
    - Deep research for learnings extraction
    - Dynamic followup queries for missing data
    """

    def __init__(
        self,
        research_type: str,
        max_results_per_query: int = 3,
        enable_iterative_search: bool = True,
        max_iterations: int = 2,
    ):
        self._research_type = research_type
        self._max_results = max_results_per_query
        self._enable_iterative = enable_iterative_search
        self._max_iterations = max_iterations

        # Create sub-stages
        self._query_stage = QueryGenerationStage(research_type)
        self._search_stage = SearchExecutionStage(max_results_per_query)
        self._analysis_stage = AnalysisStage(research_type, enable_deep_research=True)
        self._report_stage = ReportGenerationStage(research_type)
        self._evaluation_stage = EvaluationStage(research_type)

    @property
    def name(self) -> str:
        return f"research_{self._research_type}"

    async def execute(
        self,
        input: ResearchInput,
        ctx: RequestContext,
    ) -> Result[ResearchPhaseResult, StageError]:
        # 1. Generate queries
        query_result = await self._query_stage.run(input, ctx)
        if query_result.is_err:
            return Err(query_result.unwrap_err())

        search_input = query_result.unwrap().output

        # 2. Execute searches
        search_result = await self._search_stage.run(search_input, ctx)
        if search_result.is_err:
            return Err(search_result.unwrap_err())

        search_output = search_result.unwrap().output

        # 2b. Iterative refinement if enabled
        if self._enable_iterative and search_output.all_sources:
            search_output = await self._iterative_refinement(input, search_output, ctx)

        # 3. Analyze results (with deep research / learnings extraction)
        analysis_result = await self._analysis_stage.run(search_output, ctx)
        if analysis_result.is_err:
            return Err(analysis_result.unwrap_err())

        analysis_output = analysis_result.unwrap().output

        # 4. Generate report
        report_result = await self._report_stage.run(analysis_output, ctx)
        if report_result.is_err:
            return Err(report_result.unwrap_err())

        report_output = report_result.unwrap().output

        # 5. Evaluate result
        eval_result = await self._evaluation_stage.run(report_output, ctx)
        if eval_result.is_err:
            # If evaluation fails, just return report output (non-critical)
            return Ok(report_output)

        return Ok(eval_result.unwrap().output)

    async def _iterative_refinement(
        self,
        input: ResearchInput,
        initial_output: SearchPhaseOutput,
        ctx: RequestContext,
    ) -> SearchPhaseOutput:
        """
        Perform iterative query refinement based on gaps in data.

        Uses the deep research service to identify missing information
        and generates targeted followup queries.
        """
        try:
            from ...services.deep_research import DeepResearchService

            deep_research = DeepResearchService(
                ai_client=ctx.ai_client,
                max_iterations=1,
            )

            # Quick extraction to find gaps
            extraction = await deep_research.extract_learnings(
                sources=initial_output.all_sources,
                company=input.company,
                research_type=self._research_type,
            )

            gaps = extraction.get("gaps", [])

            if not gaps:
                ctx.logger.info("No gaps identified, skipping iterative search")
                return initial_output

            ctx.logger.info(f"Identified {len(gaps)} gaps, generating followup queries")

            # Create a temporary state for followup query generation
            from ...services.deep_research import ResearchState, Learning

            state = ResearchState(
                company=input.company,
                research_type=self._research_type,
                gaps=gaps,
            )

            # Add learnings to state
            for learning_text in extraction.get("learnings", []):
                state.learnings.append(
                    Learning(
                        content=learning_text,
                        source_url="initial_search",
                        category=self._research_type,
                    )
                )

            # Generate followup queries
            followup_queries = await deep_research.generate_followup_queries(state)

            if not followup_queries:
                return initial_output

            # Execute followup searches (limit to 3)
            additional_sources = []
            for query_info in followup_queries[:3]:
                query = query_info.get("query", "")
                if not query:
                    continue

                ctx.logger.info(f"Followup search: {query[:50]}...")

                try:
                    # Create a mini search input for this query
                    followup_input = SearchPhaseOutput(
                        company=input.company,
                        queries=[query],
                    )

                    followup_result = await self._search_stage.run(followup_input, ctx)
                    if followup_result.is_ok:
                        followup_output = followup_result.unwrap().output
                        additional_sources.extend(followup_output.all_sources)
                except Exception as e:
                    ctx.logger.warning(f"Followup search failed: {e}")

            # Merge additional sources with original
            if additional_sources:
                ctx.logger.info(
                    f"Added {len(additional_sources)} sources from followup searches"
                )
                # Deduplicate
                seen_urls = {
                    s.url.lower().rstrip("/") for s in initial_output.all_sources
                }
                for source in additional_sources:
                    normalized = source.url.lower().rstrip("/")
                    if normalized not in seen_urls:
                        initial_output.all_sources.append(source)
                        seen_urls.add(normalized)

            return initial_output

        except Exception as e:
            ctx.logger.warning(f"Iterative refinement failed: {e}")
            return initial_output


# =============================================================================
# Exports
# =============================================================================

from .evaluation import EvaluationStage

__all__ = [
    # Input/Output types
    "ResearchInput",
    "ResearchOutput",
    # Stages
    "QueryGenerationStage",
    "SearchExecutionStage",
    "AnalysisStage",
    "ReportGenerationStage",
    "ResearchPhaseStage",
]
