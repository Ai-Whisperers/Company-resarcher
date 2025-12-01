"""
Deep Research Service - Implements iterative research with learnings extraction.

Based on patterns from professional research tools like GPT-Researcher and Deep Research.
This module provides:
1. Learnings extraction from sources
2. Source quality curation
3. Dynamic query generation based on gaps
4. Iterative refinement
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.types import ResearchSource, CompanyProfile
from ..core.logger import setup_logger

from ..core.logger import setup_logger
from .query_expander import QueryExpander
from .source_quality_scorer import score_source
from .fact_verifier import FactVerifier
from .contradiction_detector import ContradictionDetector

logger = setup_logger("deep_research")


# =============================================================================
# Prompts for Deep Research
# =============================================================================

EXTRACTION_PROMPTS = {
    "market": """You are an expert market research analyst. Extract key market intelligence from the content about {company_name} ({industry}).

CONTENT:
{content}

Focus on extracting:
1. **Market Size & Growth**: TAM, SAM, SOM, CAGR, projected growth
2. **Market Trends**: Emerging trends, shifts in consumer behavior, regulatory changes
3. **Market Drivers**: Key factors driving adoption or growth
4. **Market Challenges**: Barriers to entry, saturation, economic headwinds

Return JSON:
{{
    "learnings": ["Specific fact 1", "Specific fact 2", ...],
    "metrics": {{
        "tam": "Total Addressable Market",
        "sam": "Serviceable Available Market",
        "som": "Serviceable Obtainable Market",
        "cagr": "Growth rate",
        "market_share": "Company's share"
    }},
    "entities": {{
        "competitors": ["Competitor 1", ...],
        "customer_segments": ["Segment 1", ...]
    }},
    "gaps": ["Missing market data"]
}}
""",
    "financial": """You are an expert financial analyst. Extract key financial data from the content about {company_name} ({industry}).

CONTENT:
{content}

Focus on extracting:
1. **Revenue & Profit**: Annual/quarterly revenue, EBITDA, net income, margins
2. **Growth Metrics**: YoY growth, QoQ growth
3. **Balance Sheet**: Cash reserves, debt levels, assets
4. **Funding & Valuation**: Recent rounds, investors, valuation, stock performance

Return JSON:
{{
    "learnings": ["Specific fact 1", "Specific fact 2", ...],
    "metrics": {{
        "revenue": "Latest revenue",
        "revenue_growth": "YoY growth %",
        "gross_margin": "Gross margin %",
        "net_margin": "Net margin %",
        "ebitda": "EBITDA",
        "valuation": "Current valuation/market cap"
    }},
    "entities": {{
        "investors": ["Investor 1", ...],
        "acquisitions": ["Acquired Company 1", ...]
    }},
    "gaps": ["Missing financial data"]
}}
""",
    "competitor": """You are an expert competitive intelligence analyst. Extract competitor insights from the content about {company_name} ({industry}).

CONTENT:
{content}

Focus on extracting:
1. **Direct Competitors**: Companies offering similar products/services
2. **Indirect Competitors**: Alternatives or substitutes
3. **Competitive Advantage**: Moats, USPs, strengths vs competitors
4. **Market Position**: Leader, challenger, niche player

Return JSON:
{{
    "learnings": ["Specific fact 1", "Specific fact 2", ...],
    "metrics": {{
        "market_share": "Company's share",
        "competitor_share": "Competitor's share (if mentioned)"
    }},
    "entities": {{
        "direct_competitors": ["Competitor A", "Competitor B"],
        "indirect_competitors": ["Alternative C", "Substitute D"],
        "partners": ["Partner X", "Partner Y"]
    }},
    "gaps": ["Missing competitor info"]
}}
""",
    "brand": """You are an expert brand strategist. Extract brand insights from the content about {company_name} ({industry}).

CONTENT:
{content}

Focus on extracting:
1. **Brand Sentiment**: Customer perception, reviews, reputation
2. **Value Proposition**: Core promise, USP, mission/vision
3. **Brand Values**: Sustainability, diversity, innovation focus
4. **Target Audience**: Demographics, psychographics

Return JSON:
{{
    "learnings": ["Specific fact 1", "Specific fact 2", ...],
    "metrics": {{
        "sentiment_score": "Positive/Negative/Neutral (or specific score)",
        "nps": "Net Promoter Score (if found)",
        "social_following": "Follower counts (if found)"
    }},
    "entities": {{
        "key_opinion_leaders": ["Influencer A", ...],
        "brand_ambassadors": ["Person B", ...]
    }},
    "gaps": ["Missing brand info"]
}}
""",
    "sales": """You are an expert sales strategist. Extract sales intelligence from the content about {company_name} ({industry}).

CONTENT:
{content}

Focus on extracting:
1. **Pricing Strategy**: Models (subscription, one-time), tiers, discounts
2. **Sales Channels**: Direct, retail, partners, online
3. **Customer Segments**: B2B vs B2C, enterprise vs SMB, key accounts
4. **Pain Points**: Customer problems the product solves

Return JSON:
{{
    "learnings": ["Specific fact 1", "Specific fact 2", ...],
    "metrics": {{
        "arpu": "Average Revenue Per User",
        "cac": "Customer Acquisition Cost",
        "ltv": "Lifetime Value",
        "churn_rate": "Churn %"
    }},
    "entities": {{
        "key_customers": ["Customer A", "Customer B"],
        "channel_partners": ["Distributor X", ...]
    }},
    "gaps": ["Missing sales info"]
}}
""",
    "default": """You are an expert research analyst. Extract key learnings from the following content about {company_name} ({industry}).

CONTENT:
{content}

Extract specific, factual learnings. Focus on:
1. **Exact numbers**: Revenue figures, market share percentages, subscriber counts, growth rates
2. **Dates and timelines**: When things happened, fiscal years, quarters
3. **Key entities**: Parent companies, subsidiaries, executives, competitors
4. **Strategic information**: Acquisitions, partnerships, product launches
5. **Financial metrics**: ARPU, EBITDA, profit margins, debt levels

Return JSON:
{{
    "learnings": [
        "Specific factual learning 1 with numbers/dates if available",
        "Specific factual learning 2 with numbers/dates if available"
    ],
    "entities": {{
        "parent_company": "Name if found or null",
        "executives": ["Name - Title", ...],
        "competitors": ["Competitor 1", ...],
        "subsidiaries": ["Subsidiary 1", ...]
    }},
    "metrics": {{
        "revenue": "Amount with currency and year if found",
        "market_share": "Percentage if found",
        "subscribers": "Count if found",
        "growth_rate": "Percentage if found"
    }},
    "gaps": [
        "Information still missing that should be researched"
    ]
}}

Be precise. Only include facts explicitly stated in the content. Mark unavailable data as null.
""",
}

SOURCE_CURATION_PROMPT = """Evaluate these research sources for relevance to: {research_goal}

SOURCES:
{sources_json}

Rate each source and return a JSON object:
{{
    "curated_sources": [
        {{
            "url": "source url",
            "relevance_score": 0-10,
            "has_quantitative_data": true/false,
            "key_value": "What useful info this source provides",
            "include": true/false
        }}
    ],
    "reasoning": "Why these sources were selected/rejected"
}}

PRIORITIZE sources that contain:
- Specific numbers, statistics, financial data
- Recent information (2023-2024)
- Official company information
- Industry reports with market data

DEPRIORITIZE sources that are:
- Generic Wikipedia articles without specifics
- Dictionary/translation pages
- Outdated information (before 2020)
- Irrelevant industries
"""

DYNAMIC_QUERY_PROMPT = """Based on the research gaps identified, generate targeted search queries.

COMPANY: {company_name}
INDUSTRY: {industry}
COUNTRY: {country}

CURRENT LEARNINGS:
{learnings}

IDENTIFIED GAPS:
{gaps}

Generate 3-5 specific search queries to fill these gaps. Be very specific:
- Include company name in quotes
- Add year qualifiers (2023, 2024)
- Target specific data types (revenue, market share, etc.)
- Search for parent company/holding group if subsidiary

Return JSON:
{{
    "queries": [
        {{
            "query": "The specific search query",
            "target_gap": "Which gap this aims to fill",
            "expected_source": "Type of source expected (annual report, news, etc.)"
        }}
    ]
}}
"""


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Learning:
    """A specific factual learning extracted from a source."""

    content: str
    source_url: str
    confidence: float = 1.0
    category: str = "general"  # financial, market, competitor, etc.


@dataclass
class ResearchState:
    """Tracks the state of iterative research."""

    company: CompanyProfile
    research_type: str
    learnings: List[Learning] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    curated_sources: List[ResearchSource] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 2

    def get_learnings_text(self) -> str:
        """Get learnings as formatted text."""
        if not self.learnings:
            return "No learnings yet."
        return "\n".join(f"- {l.content}" for l in self.learnings)

    def get_gaps_text(self) -> str:
        """Get gaps as formatted text."""
        if not self.gaps:
            return "No gaps identified."
        return "\n".join(f"- {g}" for g in self.gaps)

    def merge_learnings(self, new_learnings: List[Learning]):
        """Merge new learnings, avoiding duplicates."""
        existing = {l.content.lower() for l in self.learnings}
        for learning in new_learnings:
            if learning.content.lower() not in existing:
                self.learnings.append(learning)
                existing.add(learning.content.lower())

    def merge_entities(self, new_entities: Dict[str, Any]):
        """Merge new entities, preferring non-null values."""
        for key, value in new_entities.items():
            if value and (key not in self.entities or not self.entities[key]):
                self.entities[key] = value
            elif isinstance(value, list) and isinstance(self.entities.get(key), list):
                # Merge lists
                existing = set(self.entities[key])
                for item in value:
                    if item and item not in existing:
                        self.entities[key].append(item)

    def merge_metrics(self, new_metrics: Dict[str, Any]):
        """Merge new metrics, preferring non-null values."""
        for key, value in new_metrics.items():
            if (
                value
                and value != "null"
                and (key not in self.metrics or not self.metrics[key])
            ):
                self.metrics[key] = value


# =============================================================================
# Deep Research Service
# =============================================================================


class DeepResearchService:
    """
    Implements deep, iterative research with learnings extraction.

    Flow:
    1. Initial search with base queries
    2. Extract learnings from sources (facts, numbers, entities)
    3. Identify gaps in knowledge
    4. Generate targeted queries to fill gaps
    5. Repeat until max_iterations or gaps filled
    6. Return enriched context for analysis
    """

    def __init__(self, ai_client, max_iterations: int = 2):
        self.ai_client = ai_client
        self.max_iterations = max_iterations
        self.query_expander = QueryExpander(ai_client)
        self.fact_verifier = FactVerifier(ai_client)
        self.contradiction_detector = ContradictionDetector(ai_client)

    async def extract_learnings(
        self,
        sources: List[ResearchSource],
        company: CompanyProfile,
        research_type: str,
    ) -> Dict[str, Any]:
        """
        Extract structured learnings from a list of sources.

        Returns:
            Dict with learnings, entities, metrics, and gaps
        """
        if not sources:
            return {"learnings": [], "entities": {}, "metrics": {}, "gaps": []}

        # Combine source content (limit to avoid token overflow)
        combined_content = []
        for source in sources[:10]:  # Limit sources
            if source.content and len(source.content) > 100:
                # Trim each source to 3000 chars
                content = source.content[:3000]
                combined_content.append(f"[Source: {source.title}]\n{content}")

        if not combined_content:
            return {"learnings": [], "entities": {}, "metrics": {}, "gaps": []}

        content_text = "\n\n---\n\n".join(combined_content)

        # Select prompt based on research type
        prompt_template = EXTRACTION_PROMPTS.get(
            research_type, EXTRACTION_PROMPTS["default"]
        )

        prompt = prompt_template.format(
            company_name=company.name,
            industry=company.industry or "unknown industry",
            content=content_text[:15000],  # Limit total content
        )

        try:
            response = await self.ai_client.generate(
                prompt,
                response_format="json",
                temperature=0.3,
            )

            from ..services.json_parser_helper import robust_json_parse

            result = robust_json_parse(response)

            logger.info(
                f"Extracted {len(result.get('learnings', []))} learnings, "
                f"{len(result.get('gaps', []))} gaps identified"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to extract learnings: {e}")
            return {"learnings": [], "entities": {}, "metrics": {}, "gaps": []}

    async def curate_sources(
        self,
        sources: List[ResearchSource],
        research_goal: str,
        max_sources: int = 10,
    ) -> List[ResearchSource]:
        """
        Curate and rank sources by relevance and quality.
        """
        if not sources:
            return []

        # 1. Score sources using enhanced SourceQualityScorer
        scored_sources = []
        for source in sources:
            if not source.content or len(source.content) < 200:
                continue

            quality_score = score_source(
                url=source.url, title=source.title, content=source.content
            )

            # Filter low quality sources
            if quality_score.is_low_quality:
                logger.debug(
                    f"Skipping low quality source {source.url}: {quality_score.skip_reason}"
                )
                continue

            scored_sources.append((quality_score.overall_score, source))

        # Sort by quality score
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        valid_sources = [s for _, s in scored_sources]

        if len(valid_sources) <= max_sources:
            return valid_sources

        # 2. Use AI to rank top candidates for relevance
        sources_json = []
        for i, source in enumerate(valid_sources[:20]):  # Limit for API
            sources_json.append(
                {
                    "index": i,
                    "url": source.url,
                    "title": source.title,
                    "content_preview": source.content[:500] if source.content else "",
                }
            )

        import json

        prompt = SOURCE_CURATION_PROMPT.format(
            research_goal=research_goal,
            sources_json=json.dumps(sources_json, indent=2),
        )

        try:
            response = await self.ai_client.generate(
                prompt,
                response_format="json",
                temperature=0.2,
            )

            from ..services.json_parser_helper import robust_json_parse

            result = robust_json_parse(response)

            curated = result.get("curated_sources", [])

            # Sort by relevance score and filter
            curated = sorted(
                [c for c in curated if c.get("include", True)],
                key=lambda x: x.get("relevance_score", 0),
                reverse=True,
            )

            # Map back to original sources
            selected_indices = {c.get("url"): c for c in curated[:max_sources]}
            selected_sources = [s for s in valid_sources if s.url in selected_indices]

            logger.info(
                f"Curated {len(selected_sources)} sources from {len(valid_sources)}"
            )
            return selected_sources

        except Exception as e:
            logger.error(f"Failed to curate sources: {e}")
            return valid_sources[:max_sources]

    async def generate_followup_queries(
        self,
        state: ResearchState,
    ) -> List[Dict[str, str]]:
        """
        Generate targeted queries to fill identified gaps.
        """
        if not state.gaps:
            logger.info("No gaps to fill, skipping followup queries")
            return []

        prompt = DYNAMIC_QUERY_PROMPT.format(
            company_name=state.company.name,
            industry=state.company.industry or "unknown",
            country=state.company.country or "Global",
            learnings=state.get_learnings_text(),
            gaps=state.get_gaps_text(),
        )

        try:
            response = await self.ai_client.generate(
                prompt,
                response_format="json",
                temperature=0.5,
            )

            from ..services.json_parser_helper import robust_json_parse

            result = robust_json_parse(response)

            queries = result.get("queries", [])
            logger.info(f"Generated {len(queries)} followup queries for gaps")

            # Expand queries using QueryExpander
            expanded_queries = []
            for q in queries:
                original_query = q.get("query", "")
                if original_query:
                    # Get variations
                    variations = await self.query_expander.expand_query(
                        original_query, num_variations=2
                    )
                    # Add original
                    expanded_queries.append(q)
                    # Add variations as new query objects
                    for v in variations:
                        if v != original_query:
                            new_q = q.copy()
                            new_q["query"] = v
                            expanded_queries.append(new_q)

            return expanded_queries


    async def run_deep_research(
        self,
        initial_sources: list[ResearchSource],
        company: CompanyProfile,
        research_type: str,
        search_callback=None,
    ) -> ResearchState:
        """
        Run the full deep research loop.

        Args:
            initial_sources: Sources from initial search
            company: Company profile
            research_type: Type of research (market, financial, etc.)
            search_callback: Async function to execute additional searches

        Returns:
            ResearchState with all accumulated learnings
        """
        state = ResearchState(
            company=company,
            research_type=research_type,
            max_iterations=self.max_iterations,
        )

        # Curate initial sources
        state.curated_sources = await self.curate_sources(
            initial_sources,
            f"{company.name} {research_type} analysis",
        )

        # Extract learnings from initial sources
        extraction = await self.extract_learnings(
            state.curated_sources,
            company,
            research_type,
        )

        # Update state with extracted data
        for learning_text in extraction.get("learnings", []):
            state.learnings.append(
                Learning(
                    content=learning_text,
                    source_url="initial_search",
                    category=research_type,
                )
            )

        state.merge_entities(extraction.get("entities", {}))
        state.merge_metrics(extraction.get("metrics", {}))
        state.gaps = extraction.get("gaps", [])

        # Iterative refinement
        while state.iteration < state.max_iterations and state.gaps and search_callback:
            state.iteration += 1
            logger.info(
                f"Deep research iteration {state.iteration}/{state.max_iterations}"
            )

            # Generate targeted queries for gaps
            followup_queries = await self.generate_followup_queries(state)

            if not followup_queries:
                break

            # Execute followup searches
            for query_info in followup_queries[:3]:  # Limit queries per iteration
                query = query_info.get("query", "")
                if not query:
                    continue

                logger.info(f"Executing followup query: {query[:50]}...")

                try:
                    new_sources = await search_callback(query)
                    if new_sources:
                        # Curate new sources
                        curated_new = await self.curate_sources(
                            new_sources,
                            query_info.get("target_gap", query),
                            max_sources=5,
                        )

                        # Extract learnings from new sources
                        new_extraction = await self.extract_learnings(
                            curated_new,
                            company,
                            research_type,
                        )

                        # Merge new learnings
                        for learning_text in new_extraction.get("learnings", []):
                            state.learnings.append(
                                Learning(
                                    content=learning_text,
                                    source_url=query,
                                    category=research_type,
                                )
                            )

                        state.merge_entities(new_extraction.get("entities", {}))
                        state.merge_metrics(new_extraction.get("metrics", {}))

                        # Update gaps (remove filled ones, add new ones)
                        new_gaps = new_extraction.get("gaps", [])
                        state.gaps = [
                            g for g in new_gaps if g not in state.get_learnings_text()
                        ]

                        # Add new curated sources
                        state.curated_sources.extend(curated_new)

                except Exception as e:
                    logger.error(f"Followup search failed: {e}")

        logger.info(
            f"Deep research complete: {len(state.learnings)} learnings, "
            f"{len(state.curated_sources)} sources"
        )

        return state

    def build_enriched_context(self, state: ResearchState) -> str:
        """
        Build an enriched context string from the research state.

        This context is richer than raw source content because it includes
        extracted learnings, entities, and metrics.
        """
        parts = []

        # Add extracted metrics if available
        if state.metrics:
            metrics_lines = []
            for key, value in state.metrics.items():
                if value and value != "null":
                    metrics_lines.append(f"- {key.replace('_', ' ').title()}: {value}")
            if metrics_lines:
                parts.append("## Key Metrics\n" + "\n".join(metrics_lines))

        # Add extracted entities
        if state.entities:
            entity_lines = []
            for key, value in state.entities.items():
                if value:
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value if v)
                    if value:
                        entity_lines.append(
                            f"- {key.replace('_', ' ').title()}: {value}"
                        )
            if entity_lines:
                parts.append("## Key Entities\n" + "\n".join(entity_lines))

        # Add learnings grouped by category
        if state.learnings:
            learnings_text = "\n".join(f"- {l.content}" for l in state.learnings)
            parts.append(f"## Research Learnings\n{learnings_text}")

        # Add source content (abbreviated)
        if state.curated_sources:
            source_parts = []
            for source in state.curated_sources[:8]:
                content = source.content[:2000] if source.content else ""
                source_parts.append(
                    f"### {source.title}\nSource: {source.url}\n{content}"
                )
            parts.append("## Source Content\n" + "\n\n".join(source_parts))

        return "\n\n".join(parts)
