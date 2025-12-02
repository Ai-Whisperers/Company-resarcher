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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


@dataclass
class ComprehensiveResearchResult:
    """Result of comprehensive research across all sections."""
    company: CompanyProfile
    sections: Dict[str, Dict[str, SectionResearchResult]] = field(default_factory=dict)
    source_tracker: Optional[SourceTracker] = None
    total_sources: int = 0
    total_queries: int = 0
    duration_seconds: float = 0


# =============================================================================
# Comprehensive Research Service
# =============================================================================

class ComprehensiveResearchService:
    """
    Service for executing comprehensive research across all sections.

    This replaces the basic 5-phase research with a comprehensive
    approach that generates 52+ files with ~1000 sources.
    """

    MAX_CONCURRENT_QUERIES = 10
    MAX_RESULTS_PER_QUERY = 5

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

        Args:
            company: Company profile to research

        Returns:
            ComprehensiveResearchResult with all sections and sources
        """
        start_time = datetime.now()
        result = ComprehensiveResearchResult(company=company)

        # Reset source tracker for new research
        reset_source_tracker()
        self.source_tracker = SourceTracker()

        # Execute research for each section
        section_tasks = []
        for section_name, queries in COMPREHENSIVE_QUERIES.items():
            section_tasks.append(
                self._research_section(company, section_name, queries)
            )

        # Run all sections (can be parallelized or sequential)
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

        result.source_tracker = self.source_tracker
        result.total_queries = sum(len(q) for q in COMPREHENSIVE_QUERIES.values())
        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Comprehensive research complete: {result.total_sources} sources, "
            f"{result.total_queries} queries, {result.duration_seconds:.1f}s"
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
            )
            results[filename] = result

        return results

    async def _research_file(
        self,
        company: CompanyProfile,
        section: str,
        filename: str,
        queries: List[QueryTemplate],
    ) -> SectionResearchResult:
        """Research for a single output file."""
        result = SectionResearchResult(section=section, file=filename)

        # Format and execute queries
        # Ensure country context is added to all queries (BUG-049)
        country_name = company.country if company.country != "Global" else ""
        formatted_queries = [
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

        # Execute queries with concurrency control
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_QUERIES)

        async def search_query(query: str) -> List[ResearchSource]:
            async with semaphore:
                try:
                    search_results = await self.search_tool.search(
                        query,
                        max_results=self.MAX_RESULTS_PER_QUERY,
                    )
                    urls = [r.get("url") for r in search_results if r.get("url")]
                    if urls:
                        sources = await self.browser_tool.fetch_multiple(urls[:self.MAX_RESULTS_PER_QUERY])
                        return sources
                except Exception as e:
                    logger.debug(f"Query failed: {query[:50]}... - {e}")
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
        logger.info(f"  {section}/{filename}: {len(result.sources)} sources from {len(formatted_queries)} queries")

        return result


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
