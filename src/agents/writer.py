from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.models import (
    FinancialData,
    MarketData,
    CompetitorData,
    BrandData,
    StrategicInsights,
    TypedResearchContext,
)
from ..core.logging import setup_logger
from ..services.security import sanitize_company_name
from ..services.quality import GroundingService
from ..core.ai import AIClientManager

logger = setup_logger("writer")

# Constants for placeholder text
_NONE_IDENTIFIED = "*None identified*"
_NO_DATA = "N/A"


class ReportWriter(BaseAgent):
    """
    Drafts the final markdown sections based on the insights and gathered data.
    """

    def __init__(self, ai_client: AIClientManager):
        super().__init__(ai_client)
        self.grounding_service = GroundingService(ai_client)

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use write_report() or write_report_typed().
        """
        return ResearchPhaseResult(
            phase_name="Report Writer", markdown_content="", sources=[]
        )

    async def write_report_typed(
        self,
        company: CompanyProfile,
        context: TypedResearchContext,
        insights: StrategicInsights,
    ) -> Dict[str, str]:
        """
        Write report using typed models (recommended).

        This method provides type safety and IDE autocompletion.

        Args:
            company: Company profile
            context: Typed research context with all data
            insights: Strategic insights from insight generator

        Returns:
            Dict mapping file paths to markdown content
        """
        return await self._generate_drafts(
            company=company,
            financial=context.financial_data,
            market=context.market_data,
            competitor=context.competitor_data,
            brand=context.brand_data,
            insights=insights,
            sources=context.sources,
        )

    async def write_report(
        self,
        company: CompanyProfile,
        financial_data: Dict[str, Any],
        market_data: Dict[str, Any],
        competitor_data: Dict[str, Any],
        brand_data: Dict[str, Any],
        insights: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Write report using Dict[str, Any] (legacy, for backward compatibility).

        For new code, prefer write_report_typed() which provides type safety.
        """
        # Convert to typed models
        financial = FinancialData.from_dict(financial_data)
        market = MarketData.from_dict(market_data)
        competitor = CompetitorData.from_dict(competitor_data)
        brand = BrandData.from_dict(brand_data)
        insights_typed = StrategicInsights.from_dict(insights)

        return await self._generate_drafts(
            company=company,
            financial=financial,
            market=market,
            competitor=competitor,
            brand=brand,
            insights=insights_typed,
            sources=[],  # Legacy path has no sources
        )

    async def _generate_drafts(
        self,
        company: CompanyProfile,
        financial: FinancialData,
        market: MarketData,
        competitor: CompetitorData,
        brand: BrandData,
        insights: StrategicInsights,
        sources: List[Any] = None,
    ) -> Dict[str, str]:
        """
        Internal method that generates drafts using typed models.

        All public methods delegate to this for consistent behavior.
        """
        drafts = {}
        safe_name = sanitize_company_name(company.name)

        # --- 00-Strategic-Context ---
        drafts["00-Strategic-Context/02-Executive-Summary.md"] = (
            f"# Executive Summary for {safe_name}\n\n{insights.executive_summary}\n"
        )

        # Ground Executive Summary if sources available
        if sources:
            try:
                grounded = await self.grounding_service.ground_response(
                    insights.executive_summary, sources
                )
                if grounded and grounded.get("grounded_text"):
                    drafts["00-Strategic-Context/02-Executive-Summary.md"] = (
                        f"# Executive Summary for {safe_name}\n\n{grounded['grounded_text']}\n"
                    )
            except Exception as e:
                logger.warning(f"Failed to ground executive summary: {e}")
        drafts["00-Strategic-Context/01-Company-Overview.md"] = (
            f"# Company Overview: {safe_name}\n\nWebsite: {company.website}\n"
        )

        # --- 01-Market-Intelligence ---
        drafts["01-Market-Intelligence/01-Market-Size-Growth.md"] = (
            f"# Market Size & Growth\n\nIndustry: {market.industry or 'N/A'}\n"
            f"Market Size: {market.market_size or 'N/A'}\n"
        )
        trends_list = (
            "\n".join([f"- {t}" for t in market.trends])
            if market.trends
            else "*No trends identified*"
        )
        drafts["01-Market-Intelligence/02-Key-Trends.md"] = (
            f"# Key Trends\n\n{trends_list}\n"
        )

        # --- 03-Competitive-Landscape ---
        swot = insights.swot
        strengths = (
            "\n".join([f"- {s}" for s in swot.strengths])
            if swot.strengths
            else _NONE_IDENTIFIED
        )
        weaknesses = (
            "\n".join([f"- {w}" for w in swot.weaknesses])
            if swot.weaknesses
            else _NONE_IDENTIFIED
        )
        opportunities = (
            "\n".join([f"- {o}" for o in swot.opportunities])
            if swot.opportunities
            else _NONE_IDENTIFIED
        )
        threats = (
            "\n".join([f"- {t}" for t in swot.threats])
            if swot.threats
            else _NONE_IDENTIFIED
        )

        drafts[
            "03-Competitive-Landscape/05-SWOT-Analysis.md"
        ] = f"""# Strategic Analysis (SWOT)

## Strengths
{strengths}

## Weaknesses
{weaknesses}

## Opportunities
{opportunities}

## Threats
{threats}
"""
        drafts["03-Competitive-Landscape/01-Competitor-List.md"] = (
            f"# Competitor List\n\n{competitor.competitors_list or 'N/A'}\n"
        )

        # --- 04-Brand-Strategy ---
        drafts["04-Brand-Strategy/01-Positioning.md"] = (
            f"# Brand Positioning\n\n{brand.brand_positioning or 'N/A'}\n"
        )
        drafts["04-Brand-Strategy/03-Brand-Voice.md"] = (
            f"# Brand Voice\n\n{brand.brand_voice or 'N/A'}\n"
        )

        # --- 06-Data-Room ---
        highlights = (
            "\n".join([f"- {h}" for h in financial.key_highlights])
            if financial.key_highlights
            else "*No highlights available*"
        )
        drafts[
            "06-Data-Room/01-Financials.md"
        ] = f"""# Financial Overview

| Metric | Value |
| :--- | :--- |
| Revenue | {financial.revenue or 'N/A'} |
| Profit | {financial.profit or 'N/A'} |
| Growth | {financial.growth or 'N/A'} |
| Stock | {financial.stock_ticker or 'N/A'} |

**Key Highlights:**
{highlights}
"""

        # --- Placeholders for Future Agents ---
        drafts["08-Sales-Intelligence/01-Pain-Point-Analysis.md"] = (
            "# Pain Point Analysis\n\n*Coming soon with Sales Agent upgrade.*"
        )
        drafts["09-Investment-Analysis/01-Growth-Signals.md"] = (
            "# Growth Signals\n\n*Coming soon with Investment Agent upgrade.*"
        )

        return drafts
