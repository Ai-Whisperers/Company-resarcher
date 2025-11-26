from typing import List
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult


class MarketAnalyst(BaseAgent):
    """
    Researches industry trends, market size, and growth.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.industry} industry market size {company.country} 2024 2025",
            f"{company.industry} market trends {company.country} 2025",
            f"{company.industry} growth rate forecast {company.country}",
            f"{company.country} cultural trends affecting {company.industry}",
        ]

        sources = await self._gather_data(queries)

        # Prepare context for LLM
        context = "\n\n".join(
            [f"Source: {s.title}\nContent: {s.content[:2000]}" for s in sources]
        )

        prompt = f"""
        Analyze the following market research data for {company.name} in the {company.industry} industry ({company.country}).
        
        Return a JSON object with the following structure:
        {{
            "industry": "{company.industry}",
            "market_size": "Current market size and currency",
            "growth_rate": "CAGR or percentage growth",
            "trends": [
                {{"name": "Trend Name", "description": "Detailed description"}}
            ],
            "cultural_context": "Cultural nuances affecting the market",
            "regulatory_landscape": "Key regulations or legal considerations",
            "executive_summary": "Brief summary of the market status"
        }}

        Data:
        {context}
        """

        import json
        from ..services.json_parser_helper import robust_json_parse

        try:
            # We assume the AI client supports JSON mode or we parse it manually
            # For now, let's ask for JSON and parse it
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Add missing fields if any
            data.setdefault("industry", company.industry)
            data.setdefault("market_size", "N/A")
            data.setdefault("growth_rate", "N/A")
            data.setdefault("trends", [])
            data.setdefault("cultural_context", "N/A")
            data.setdefault("regulatory_landscape", "N/A")

            markdown_content = self._render("01-Market-Intelligence.md", data, sources)

        except Exception as e:
            logger.error(f"Error parsing JSON or rendering: {e}")
            # Fallback to raw content if JSON fails
            markdown_content = (
                f"# Error Generating Report\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name="Market Intelligence",
            markdown_content=markdown_content,
            sources=sources,
        )


class BrandAuditor(BaseAgent):
    """
    Analyzes brand voice, positioning, and values.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} brand values mission vision",
            f"{company.name} brand positioning strategy",
            f"{company.name} marketing tone of voice",
            f"{company.name} advertising slogans taglines",
        ]

        sources = await self._gather_data(queries)

        context = "\n\n".join(
            [f"Source: {s.title}\nContent: {s.content[:2000]}" for s in sources]
        )

        prompt = f"""
        Analyze the brand identity of {company.name}.
        
        Return a JSON object with the following structure:
        {{
            "positioning_statement": "Core positioning statement",
            "usp": "Unique Selling Proposition",
            "brand_archetype": "Brand Archetype (e.g., Hero, Sage)",
            "messaging_pillars": [
                {{"name": "Pillar Name", "description": "Description"}}
            ],
            "tone_of_voice": "Description of tone",
            "taglines": "List of known taglines",
            "executive_summary": "Brief summary of brand strategy"
        }}
        
        Data:
        {context}
        """

        import json
        from ..services.json_parser_helper import robust_json_parse

        try:
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Defaults
            data.setdefault("positioning_statement", "N/A")
            data.setdefault("usp", "N/A")
            data.setdefault("brand_archetype", "N/A")
            data.setdefault("messaging_pillars", [])
            data.setdefault("tone_of_voice", "N/A")
            data.setdefault("taglines", "N/A")

            markdown_content = self._render("04-Brand-Strategy.md", data, sources)

        except Exception as e:
            logger.error(f"Error parsing JSON or rendering: {e}")
            markdown_content = (
                f"# Error Generating Report\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name="Brand Strategy",
            markdown_content=markdown_content,
            sources=sources,
        )


class CompetitorScout(BaseAgent):
    """
    Identifies and analyzes competitors.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"top competitors of {company.name} {company.country}",
            f"{company.name} vs alternatives {company.industry}",
            f"{company.industry} market share leaders {company.country}",
            f"{company.name} competitor pricing comparison",
        ]

        sources = await self._gather_data(queries)

        context = "\n\n".join(
            [f"Source: {s.title}\nContent: {s.content[:2000]}" for s in sources]
        )

        prompt = f"""
        Identify and analyze the top competitors for {company.name} in {company.country}.
        
        Return a JSON object with the following structure:
        {{
            "competitors": [
                {{
                    "name": "Competitor Name",
                    "overview": "Brief overview",
                    "strengths": "Key strengths",
                    "weaknesses": "Key weaknesses",
                    "pricing": "Pricing model/tiers"
                }}
            ],
            "feature_comparison_matrix": "Markdown table comparing key features",
            "market_share_analysis": "Analysis of market share distribution",
            "executive_summary": "Brief summary of competitive landscape"
        }}
        
        Data:
        {context}
        """

        import json
        from ..services.json_parser_helper import robust_json_parse

        try:
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Defaults
            data.setdefault("competitors", [])
            data.setdefault("feature_comparison_matrix", "N/A")
            data.setdefault("market_share_analysis", "N/A")

            markdown_content = self._render(
                "03-Competitive-Landscape.md", data, sources
            )

        except Exception as e:
            logger.error(f"Error parsing JSON or rendering: {e}")
            markdown_content = (
                f"# Error Generating Report\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name="Competitive Landscape",
            markdown_content=markdown_content,
            sources=sources,
        )
