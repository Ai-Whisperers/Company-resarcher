"""
AI Query Planner - Uses AI to generate smarter, context-aware search queries.

Instead of generic template queries, this module:
1. Asks AI what it already knows about the company/topic
2. Gets AI-suggested search queries based on that knowledge
3. Provides initial context to help validate/filter results

Usage:
    from src.core.ai_query_planner import AIQueryPlanner

    planner = AIQueryPlanner()
    plan = await planner.plan_research(
        company_name="COPACO",
        section="competitive_landscape",
        industry="Telecommunications",
        country="Paraguay"
    )

    # plan.initial_context - what AI knows
    # plan.suggested_queries - optimized search queries
    # plan.known_facts - verified facts to cross-reference
    # plan.key_entities - competitors, people, products to look for
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

from .logger import setup_logger
from .ai_client import get_ai_manager

logger = setup_logger("ai_query_planner")


class ResearchSection(Enum):
    """Research sections that can be planned."""
    STRATEGIC_CONTEXT = "strategic_context"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    MARKET_INTELLIGENCE = "market_intelligence"
    DATA_ROOM = "data_room"
    TARGET_AUDIENCE = "target_audience"
    BRAND_STRATEGY = "brand_strategy"
    INVESTMENT_ANALYSIS = "investment_analysis"
    SALES_INTELLIGENCE = "sales_intelligence"


@dataclass
class QueryPlan:
    """Result of AI query planning for a section."""
    section: str
    company: str

    # What the AI already knows
    initial_context: str = ""

    # Known facts that can help validate results
    known_facts: List[str] = field(default_factory=list)

    # Key entities to look for (competitors, people, products)
    key_entities: Dict[str, List[str]] = field(default_factory=dict)

    # AI-suggested search queries (ranked by expected value)
    suggested_queries: List[str] = field(default_factory=list)

    # Questions the research should answer
    key_questions: List[str] = field(default_factory=list)

    # Confidence in AI's knowledge (0-1)
    confidence: float = 0.0


# Section-specific prompts for the AI planner
SECTION_PROMPTS = {
    ResearchSection.COMPETITIVE_LANDSCAPE: """
You are a research analyst preparing to research the competitive landscape for {company} in the {industry} industry in {country}.

BEFORE I search the web, tell me:

1. **What You Already Know**: What do you know about {company}'s main competitors? List them with brief descriptions.

2. **Key Facts**: What verified facts do you know about market positions, market share estimates, or competitive dynamics?

3. **Suggested Search Queries**: Generate 10-15 specific search queries that would find the most valuable competitive intelligence. Be specific - use competitor names, product names, and industry-specific terms you know.

4. **Key Questions**: What are the most important questions this research should answer?

5. **Entities to Track**: List specific competitors, products, and executives to look for.

Format your response as JSON:
{{
    "initial_context": "Brief overview of what you know about the competitive landscape...",
    "known_facts": ["Fact 1", "Fact 2", ...],
    "competitors": ["Competitor 1", "Competitor 2", ...],
    "key_products": ["Product 1", "Product 2", ...],
    "key_people": ["Person 1", "Person 2", ...],
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["Question 1?", "Question 2?", ...],
    "confidence": 0.7
}}
""",

    ResearchSection.DATA_ROOM: """
You are a financial analyst preparing to research financial data for {company} in the {industry} industry in {country}.

BEFORE I search the web, tell me:

1. **What You Already Know**: What do you know about {company}'s financials? Revenue, funding, ownership structure?

2. **Key Facts**: Any known revenue figures, funding rounds, valuations, or financial metrics?

3. **Suggested Search Queries**: Generate 10-15 specific search queries to find financial data. Include:
   - Parent company reports if applicable
   - Industry financial benchmarks
   - Regulatory filings
   - News about funding/acquisitions

4. **Key Questions**: What financial questions should this research answer?

Format your response as JSON:
{{
    "initial_context": "Brief overview of known financial information...",
    "known_facts": ["Revenue ~$X", "Parent company is Y", ...],
    "parent_companies": ["Parent 1", ...],
    "key_financial_events": ["Acquisition in 2020", ...],
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["What is annual revenue?", ...],
    "confidence": 0.5
}}
""",

    ResearchSection.MARKET_INTELLIGENCE: """
You are a market analyst preparing to research the {industry} market in {country}, focusing on {company}'s position.

BEFORE I search the web, tell me:

1. **What You Already Know**: What do you know about the {industry} market in {country}? Size, growth, key players?

2. **Key Facts**: Any known market statistics, growth rates, or trends?

3. **Suggested Search Queries**: Generate 10-15 specific queries to find market data. Include:
   - Market research report sources (Statista, Mordor, etc.)
   - Government telecom regulators
   - Industry associations
   - Recent news about market developments

4. **Key Questions**: What market questions should this research answer?

Format your response as JSON:
{{
    "initial_context": "Brief overview of the market...",
    "known_facts": ["Market size ~$X billion", "Growth rate ~X%", ...],
    "key_players": ["Player 1", "Player 2", ...],
    "regulatory_bodies": ["Regulator 1", ...],
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["What is total market size?", ...],
    "confidence": 0.6
}}
""",

    ResearchSection.STRATEGIC_CONTEXT: """
You are a business analyst preparing to research {company} in the {industry} industry in {country}.

BEFORE I search the web, tell me:

1. **What You Already Know**: What do you know about {company}? History, ownership, key facts?

2. **Key Facts**: Any known founding date, headquarters, parent company, key executives?

3. **Suggested Search Queries**: Generate 10-15 specific queries to find company information. Include:
   - Official company pages
   - LinkedIn/business profiles
   - News articles
   - Wikipedia entries

4. **Key Questions**: What company questions should this research answer?

Format your response as JSON:
{{
    "initial_context": "Brief overview of the company...",
    "known_facts": ["Founded in XXXX", "Part of X group", ...],
    "key_executives": ["CEO Name", ...],
    "parent_companies": ["Parent", ...],
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["When was it founded?", ...],
    "confidence": 0.7
}}
""",

    ResearchSection.INVESTMENT_ANALYSIS: """
You are an investment analyst preparing to research {company} in the {industry} industry in {country}.

BEFORE I search the web, tell me:

1. **What You Already Know**: What do you know about {company}'s investment potential? Growth signals, risks?

2. **Key Facts**: Any known funding history, growth metrics, or risk factors?

3. **Suggested Search Queries**: Generate 10-15 specific queries focusing on:
   - Growth indicators (new products, expansion, hiring)
   - Risk factors (regulatory, competition, technology)
   - Recent news and announcements

4. **Key Questions**: What investment questions should this research answer?

Format your response as JSON:
{{
    "initial_context": "Brief investment overview...",
    "known_facts": ["Recent expansion into X", ...],
    "growth_signals": ["Signal 1", ...],
    "risk_factors": ["Risk 1", ...],
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["What are growth drivers?", ...],
    "confidence": 0.5
}}
""",
}

# Default prompt for sections without specific prompts
DEFAULT_SECTION_PROMPT = """
You are a research analyst preparing to research {section} for {company} in the {industry} industry in {country}.

BEFORE I search the web, tell me:

1. **What You Already Know**: What relevant information do you know about {company} for this topic?

2. **Key Facts**: Any verified facts relevant to {section}?

3. **Suggested Search Queries**: Generate 10-15 specific search queries that would find the most valuable information for {section}.

4. **Key Questions**: What questions should this research answer?

Format your response as JSON:
{{
    "initial_context": "Brief overview...",
    "known_facts": ["Fact 1", ...],
    "key_entities": {{"type": ["entity1", ...]}},
    "suggested_queries": ["query 1", "query 2", ...],
    "key_questions": ["Question 1?", ...],
    "confidence": 0.5
}}
"""


class AIQueryPlanner:
    """
    Uses AI to plan research queries before web searching.

    This leverages the AI's existing knowledge to:
    1. Provide initial context about the company/topic
    2. Generate more targeted, specific search queries
    3. Identify key entities to look for in results
    4. Frame key questions the research should answer
    """

    def __init__(self):
        self._ai_client = None
        self._cache: Dict[str, QueryPlan] = {}

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    def _get_cache_key(self, company: str, section: str) -> str:
        """Generate cache key for a query plan."""
        return f"{company.lower()}:{section}"

    async def plan_research(
        self,
        company_name: str,
        section: str,
        industry: str = "Technology",
        country: str = "Global",
        use_cache: bool = True,
    ) -> QueryPlan:
        """
        Generate an AI-powered research plan for a section.

        Args:
            company_name: Name of the company to research
            section: Section to research (e.g., "competitive_landscape")
            industry: Industry context
            country: Geographic context
            use_cache: Whether to use cached plans

        Returns:
            QueryPlan with AI-generated queries and context
        """
        cache_key = self._get_cache_key(company_name, section)

        # Check cache
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached plan for {company_name}:{section}")
            return self._cache[cache_key]

        # Get section-specific prompt
        try:
            section_enum = ResearchSection(section)
            prompt_template = SECTION_PROMPTS.get(section_enum, DEFAULT_SECTION_PROMPT)
        except ValueError:
            prompt_template = DEFAULT_SECTION_PROMPT

        # Format prompt
        prompt = prompt_template.format(
            company=company_name,
            industry=industry,
            country=country,
            section=section.replace("_", " ").title(),
        )

        # Call AI
        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a knowledgeable research analyst. Provide accurate information you know, and generate targeted search queries. Always respond with valid JSON.",
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more factual responses
            )

            # Parse response
            plan = self._parse_response(response, company_name, section)

            # Cache result
            self._cache[cache_key] = plan

            logger.info(
                f"Generated query plan for {company_name}:{section} - "
                f"{len(plan.suggested_queries)} queries, confidence={plan.confidence:.0%}"
            )

            return plan

        except Exception as e:
            logger.warning(f"AI query planning failed: {e}")
            # Return empty plan on failure
            return QueryPlan(section=section, company=company_name)

    def _parse_response(self, response: str, company: str, section: str) -> QueryPlan:
        """Parse AI response into QueryPlan."""
        import json

        try:
            # Try to extract JSON from response
            # Handle case where response has text before/after JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Build QueryPlan from parsed data
            plan = QueryPlan(
                section=section,
                company=company,
                initial_context=data.get("initial_context", ""),
                known_facts=data.get("known_facts", []),
                suggested_queries=data.get("suggested_queries", []),
                key_questions=data.get("key_questions", []),
                confidence=data.get("confidence", 0.5),
            )

            # Extract key entities from various possible fields
            entities: Dict[str, List[str]] = {}

            for entity_type in ["competitors", "key_players", "key_executives",
                               "key_people", "parent_companies", "key_products",
                               "regulatory_bodies", "growth_signals", "risk_factors"]:
                if entity_type in data and data[entity_type]:
                    entities[entity_type] = data[entity_type]

            # Also check for nested key_entities
            if "key_entities" in data:
                entities.update(data["key_entities"])

            plan.key_entities = entities

            return plan

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            # Return plan with raw response as context
            return QueryPlan(
                section=section,
                company=company,
                initial_context=response[:500] if response else "",
            )

    async def plan_all_sections(
        self,
        company_name: str,
        industry: str = "Technology",
        country: str = "Global",
        sections: Optional[List[str]] = None,
    ) -> Dict[str, QueryPlan]:
        """
        Generate query plans for multiple sections in parallel.

        Args:
            company_name: Name of the company
            industry: Industry context
            country: Geographic context
            sections: List of sections to plan (defaults to all)

        Returns:
            Dict mapping section name to QueryPlan
        """
        if sections is None:
            sections = [s.value for s in ResearchSection]

        # Plan all sections concurrently
        tasks = [
            self.plan_research(company_name, section, industry, country)
            for section in sections
        ]

        plans = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dict
        result = {}
        for section, plan in zip(sections, plans):
            if isinstance(plan, Exception):
                logger.warning(f"Failed to plan {section}: {plan}")
                result[section] = QueryPlan(section=section, company=company_name)
            else:
                result[section] = plan

        return result

    def get_combined_queries(
        self,
        plan: QueryPlan,
        template_queries: List[str],
        max_queries: int = 35,
    ) -> List[str]:
        """
        Combine AI-suggested queries with template queries.

        AI queries are prioritized, then template queries fill remaining slots.
        Duplicates and near-duplicates are removed.

        Args:
            plan: The query plan with AI suggestions
            template_queries: Template-generated queries
            max_queries: Maximum total queries

        Returns:
            Combined, deduplicated list of queries
        """
        combined = []
        seen_normalized = set()

        def normalize(q: str) -> str:
            """Normalize query for duplicate detection."""
            return q.lower().strip().replace('"', '').replace("'", "")

        # Add AI queries first (they're usually better)
        for query in plan.suggested_queries:
            norm = normalize(query)
            if norm not in seen_normalized and len(combined) < max_queries:
                combined.append(query)
                seen_normalized.add(norm)

        # Fill with template queries
        for query in template_queries:
            norm = normalize(query)
            if norm not in seen_normalized and len(combined) < max_queries:
                combined.append(query)
                seen_normalized.add(norm)

        return combined


# Module-level instance
_planner: Optional[AIQueryPlanner] = None


def get_query_planner() -> AIQueryPlanner:
    """Get the global AIQueryPlanner instance."""
    global _planner
    if _planner is None:
        _planner = AIQueryPlanner()
    return _planner


__all__ = [
    "AIQueryPlanner",
    "QueryPlan",
    "ResearchSection",
    "get_query_planner",
]
