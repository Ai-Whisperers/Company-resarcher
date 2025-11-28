import json

from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult, ResearchContext
from ..core.models import TypedResearchContext, StrategicInsights
from ..core.logger import setup_logger
from ..services.json_parser_helper import robust_json_parse
from ..services.security import sanitize_company_name

logger = setup_logger("insight_generator")


class InsightGenerator(BaseAgent):
    """
    Synthesizes raw data from all specialists into strategic insights (SWOT, PESTLE).
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use analyze() or analyze_typed() which accepts full context.
        """
        return await self.analyze(company, ResearchContext())

    async def analyze_typed(
        self,
        company: CompanyProfile,
        context: TypedResearchContext,
    ) -> tuple[ResearchPhaseResult, StrategicInsights]:
        """
        Synthesize research data into strategic insights using typed models (recommended).

        This method provides type safety and returns both the markdown result
        and the structured StrategicInsights model.

        Args:
            company: The company profile being analyzed.
            context: Typed research context from specialist agents.

        Returns:
            Tuple of (ResearchPhaseResult, StrategicInsights)
        """
        # Convert typed context to legacy ResearchContext for internal processing
        legacy_context = ResearchContext(
            financial_data=context.financial_data.to_legacy_dict(),
            market_data=context.market_data.to_legacy_dict(),
            competitor_data=context.competitor_data.to_legacy_dict(),
            brand_data=context.brand_data.to_legacy_dict(),
        )

        result = await self.analyze(company, legacy_context)

        # Parse the insights from the result (re-generate for typed output)
        insights = await self._generate_insights_model(company, context)

        return result, insights

    async def _generate_insights_model(
        self,
        company: CompanyProfile,
        context: TypedResearchContext,
    ) -> StrategicInsights:
        """Generate StrategicInsights model from typed context."""
        safe_name = sanitize_company_name(company.name)

        context_str = f"""
        Financial Data:
        - Revenue: {context.financial_data.revenue or 'N/A'}
        - Profit: {context.financial_data.profit or 'N/A'}
        - Growth: {context.financial_data.growth or 'N/A'}
        - Key Highlights: {', '.join(context.financial_data.key_highlights) or 'None'}

        Market Data:
        - Industry: {context.market_data.industry or 'N/A'}
        - Market Size: {context.market_data.market_size or 'N/A'}
        - Trends: {', '.join(context.market_data.trends) or 'None'}

        Competitor Data:
        - Competitors: {context.competitor_data.competitors_list or 'N/A'}
        - Competitive Advantages: {', '.join(context.competitor_data.competitive_advantages) or 'None'}

        Brand Data:
        - Positioning: {context.brand_data.brand_positioning or 'N/A'}
        - Brand Voice: {context.brand_data.brand_voice or 'N/A'}
        """

        prompt = f"""
        You are a Chief Strategy Officer. Synthesize the provided research data for {safe_name} into a strategic analysis.

        Return a JSON object with the following structure:
        {{
            "swot": {{
                "strengths": ["List of strengths"],
                "weaknesses": ["List of weaknesses"],
                "opportunities": ["List of opportunities"],
                "threats": ["List of threats"]
            }},
            "strategic_takeaways": [
                "Key strategic insight 1",
                "Key strategic insight 2"
            ],
            "executive_summary": "A high-level executive summary of the company's position."
        }}

        Data:
        {context_str}
        """

        try:
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)
            return StrategicInsights.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to generate insights model: {e}", exc_info=True)
            return StrategicInsights()

    async def analyze(
        self,
        company: CompanyProfile,
        context: ResearchContext,
    ) -> ResearchPhaseResult:
        """
        Synthesize research data into strategic insights (legacy Dict[str, Any] version).

        For new code, prefer analyze_typed() which provides type safety.

        Args:
            company: The company profile being analyzed.
            context: Aggregated research data from specialist agents.

        Returns:
            ResearchPhaseResult with SWOT analysis and strategic insights.
        """
        # Combine all data into a context string
        context_str = f"""
        Financial Data:
        {context.financial_data}

        Market Data:
        {context.market_data}

        Competitor Data:
        {context.competitor_data}

        Brand Data:
        {context.brand_data}
        """

        safe_name = sanitize_company_name(company.name)
        prompt = f"""
        You are a Chief Strategy Officer. Synthesize the provided research data for {safe_name} into a strategic analysis.

        Return a JSON object with the following structure:
        {{
            "swot": {{
                "strengths": ["List of strengths"],
                "weaknesses": ["List of weaknesses"],
                "opportunities": ["List of opportunities"],
                "threats": ["List of threats"]
            }},
            "strategic_takeaways": [
                "Key strategic insight 1",
                "Key strategic insight 2"
            ],
            "executive_summary": "A high-level executive summary of the company's position."
        }}

        Data:
        {context_str}
        """

        content_json_str = ""
        try:
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Defaults
            data.setdefault(
                "swot",
                {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            )
            data.setdefault("strategic_takeaways", [])
            data.setdefault("executive_summary", "N/A")

            # Render the insights markdown
            markdown_content = self._render("02-Strategic-Analysis.md", data, [])

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"JSON parsing failed in insight generator: {e}", exc_info=True
            )
            markdown_content = (
                f"# Error Generating Insights\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )
        except AttributeError as e:
            logger.error(f"Missing method or attribute in insight generator: {e}", exc_info=True)
            markdown_content = (
                f"# Error Generating Insights\n\nAttributeError: {e}\n\nRaw Output:\n{content_json_str}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in insight generator: {e}", exc_info=True)
            markdown_content = (
                f"# Error Generating Insights\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name="Strategic Analysis",
            markdown_content=markdown_content,
            sources=[],
        )
