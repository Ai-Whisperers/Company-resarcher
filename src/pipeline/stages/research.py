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

from ..context import RequestContext
from ..stage import Stage, StageError, StageErrorCode


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
    research_types: List[str] = field(default_factory=lambda: [
        "market",
        "financial",
        "competitor",
        "brand",
        "sales",
    ])
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
        self._query_templates = {
            "market": [
                "{company} market share {industry}",
                "{company} industry trends",
                "{company} target audience demographics",
                "{industry} market size and growth",
            ],
            "financial": [
                "{company} financial performance",
                "{company} annual report",
                "{company} revenue growth",
                "{company} stock price analysis",
            ],
            "competitor": [
                "{company} top competitors",
                "{company} vs competitors comparison",
                "{company} competitive advantage",
                "{industry} key players",
            ],
            "brand": [
                "{company} brand reputation",
                "{company} customer reviews sentiment",
                "{company} brand values and mission",
                "{company} marketing campaigns",
            ],
            "sales": [
                "{company} sales strategy",
                "{company} distribution channels",
                "{company} pricing strategy",
                "{company} B2B clients",
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

        templates = self._query_templates.get(self._research_type, [])
        if not templates:
            return Err(StageError.invalid_input(
                self.name,
                f"Unknown research type: {self._research_type}",
            ))

        queries = [
            template.format(company=safe_name, industry=industry)
            for template in templates
        ]

        ctx.logger.info(f"Generated {len(queries)} queries for {self._research_type}")

        return Ok(SearchPhaseOutput(
            company=input.company,
            queries=queries,
        ))


# =============================================================================
# Search Execution Stage
# =============================================================================


class SearchExecutionStage(Stage[SearchPhaseOutput, SearchPhaseOutput]):
    """
    Executes search queries and fetches content from URLs.

    Uses bounded concurrency to prevent overwhelming external services.
    """

    MAX_CONCURRENT_QUERIES = 5

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

        async def fetch_query(query: str) -> QueryResult:
            async with semaphore:
                # Check cancellation
                if ctx.cancellation.is_cancelled:
                    return QueryResult(query=query, error="Cancelled")

                try:
                    # Search
                    search_results = await ctx.search_tool.search(
                        query,
                        max_results=self._max_results
                    )

                    # Extract URLs
                    urls = [r.get("url") for r in search_results if r.get("url")]

                    if not urls:
                        return QueryResult(query=query, sources=[])

                    # Fetch content
                    sources = await ctx.browser_tool.fetch_multiple(urls)
                    return QueryResult(query=query, sources=sources)

                except Exception as e:
                    ctx.logger.warning(f"Query failed: {query}", error=str(e))
                    return QueryResult(query=query, error=str(e))

        # Execute all queries in parallel (bounded by semaphore)
        ctx.logger.info(
            f"Executing {len(input.queries)} search queries",
            max_concurrent=self.MAX_CONCURRENT_QUERIES,
        )

        results = await asyncio.gather(
            *[fetch_query(q) for q in input.queries],
            return_exceptions=True,
        )

        # Process results
        query_results = []
        all_sources = []
        failed_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                query_results.append(QueryResult(
                    query=input.queries[i],
                    error=str(result),
                ))
                failed_count += 1
            else:
                query_results.append(result)
                all_sources.extend(result.sources)
                if result.error:
                    failed_count += 1

        ctx.logger.info(
            f"Search completed",
            total_sources=len(all_sources),
            successful_queries=len(input.queries) - failed_count,
            failed_queries=failed_count,
        )

        return Ok(SearchPhaseOutput(
            company=input.company,
            queries=input.queries,
            results=query_results,
            all_sources=all_sources,
        ))


# =============================================================================
# Analysis Stage
# =============================================================================


class AnalysisStage(Stage[SearchPhaseOutput, AnalysisOutput]):
    """
    Analyzes gathered sources using LLM.

    Loads prompt templates and generates structured analysis.
    """

    PROMPT_FILES = {
        "market": "market_intelligence.txt",
        "financial": "financial_analysis.txt",
        "competitor": "competitive_landscape.txt",
        "brand": "brand_strategy.txt",
        "sales": "sales_strategy.txt",
    }

    def __init__(self, research_type: str):
        self._research_type = research_type

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
            return Err(StageError.invalid_input(
                self.name,
                f"No prompt file for research type: {self._research_type}",
            ))

        prompt_path = Path(__file__).parent.parent.parent / "prompts" / prompt_file

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template_str = f.read()
        except FileNotFoundError:
            return Err(StageError.invalid_input(
                self.name,
                f"Prompt file not found: {prompt_file}",
            ))

        # Get context from sources
        context_text = input.get_context_text()

        if not context_text:
            ctx.logger.warning("No source content available for analysis")
            return Ok(AnalysisOutput(
                company=input.company,
                research_type=self._research_type,
                data={"warning": "No source data available"},
                sources=input.all_sources,
            ))

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

            return Ok(AnalysisOutput(
                company=input.company,
                research_type=self._research_type,
                data=data,
                sources=input.all_sources,
                raw_output=response,
            ))

        except Exception as e:
            ctx.logger.error(f"Analysis failed: {e}")
            return Err(StageError.ai_error(
                self.name,
                f"Analysis generation failed: {e}",
                retryable=True,
            ))


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
            # Prepare template context
            template_context = {
                **input.data,
                "agent_name": f"{self._research_type.title()}Analyst",
                "sources": [
                    {
                        "title": s.title,
                        "url": s.url,
                        "source_type": s.source_type,
                    }
                    for s in input.sources
                ],
            }

            markdown_content = renderer.render(template_name, **template_context)

        except Exception as e:
            ctx.logger.warning(f"Template rendering failed: {e}")
            # Fallback to basic format
            markdown_content = self._fallback_render(input)

        return Ok(ResearchPhaseResult(
            phase_name=self._research_type,
            markdown_content=markdown_content,
            sources=input.sources,
        ))

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
    """

    def __init__(self, research_type: str, max_results_per_query: int = 3):
        self._research_type = research_type
        self._max_results = max_results_per_query

        # Create sub-stages
        self._query_stage = QueryGenerationStage(research_type)
        self._search_stage = SearchExecutionStage(max_results_per_query)
        self._analysis_stage = AnalysisStage(research_type)
        self._report_stage = ReportGenerationStage(research_type)

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

        # 3. Analyze results
        analysis_result = await self._analysis_stage.run(search_output, ctx)
        if analysis_result.is_err:
            return Err(analysis_result.unwrap_err())

        analysis_output = analysis_result.unwrap().output

        # 4. Generate report
        report_result = await self._report_stage.run(analysis_output, ctx)
        if report_result.is_err:
            return Err(report_result.unwrap_err())

        return Ok(report_result.unwrap().output)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Input/Output types
    "ResearchInput",
    "QueryResult",
    "SearchPhaseOutput",
    "AnalysisOutput",
    "ResearchOutput",
    # Stages
    "QueryGenerationStage",
    "SearchExecutionStage",
    "AnalysisStage",
    "ReportGenerationStage",
    "ResearchPhaseStage",
]
