from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.logger import setup_logger

logger = setup_logger("writer")


class ReportWriter(BaseAgent):
    """
    Drafts the final markdown sections based on the insights and gathered data.
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use write_report().
        """
        return ResearchPhaseResult(
            phase_name="Report Writer", markdown_content="", sources=[]
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

        drafts = {}

        # --- 00-Strategic-Context ---
        drafts["00-Strategic-Context/02-Executive-Summary.md"] = (
            f"# Executive Summary for {company.name}\n\n{insights.get('executive_summary', 'N/A')}\n"
        )
        drafts["00-Strategic-Context/01-Company-Overview.md"] = (
            f"# Company Overview: {company.name}\n\nWebsite: {company.url}\n"
        )

        # --- 01-Market-Intelligence ---
        drafts["01-Market-Intelligence/01-Market-Size-Growth.md"] = (
            f"# Market Size & Growth\n\nIndustry: {market_data.get('industry', 'N/A')}\n"
            f"Market Size: {market_data.get('market_size', 'N/A')}\n"
        )
        drafts["01-Market-Intelligence/02-Key-Trends.md"] = (
            f"# Key Trends\n\n{chr(10).join(['- ' + t for t in market_data.get('trends', [])])}\n"
        )

        # --- 03-Competitive-Landscape ---
        swot = insights.get("swot", {})
        drafts[
            "03-Competitive-Landscape/05-SWOT-Analysis.md"
        ] = f"""
# Strategic Analysis (SWOT)

## Strengths
{chr(10).join(['- ' + s for s in swot.get('strengths', [])])}

## Weaknesses
{chr(10).join(['- ' + w for w in swot.get('weaknesses', [])])}

## Opportunities
{chr(10).join(['- ' + o for o in swot.get('opportunities', [])])}

## Threats
{chr(10).join(['- ' + t for t in swot.get('threats', [])])}
"""
        drafts["03-Competitive-Landscape/01-Competitor-List.md"] = (
            f"# Competitor List\n\n{competitor_data.get('competitors_list', 'N/A')}\n"
        )

        # --- 04-Brand-Strategy ---
        drafts["04-Brand-Strategy/01-Positioning.md"] = (
            f"# Brand Positioning\n\n{brand_data.get('brand_positioning', 'N/A')}\n"
        )
        drafts["04-Brand-Strategy/03-Brand-Voice.md"] = (
            f"# Brand Voice\n\n{brand_data.get('brand_voice', 'N/A')}\n"
        )

        # --- 06-Data-Room ---
        fin = financial_data
        drafts[
            "06-Data-Room/01-Financials.md"
        ] = f"""
# Financial Overview

| Metric | Value |
| :--- | :--- |
| Revenue | {fin.get('revenue', 'N/A')} |
| Profit | {fin.get('profit', 'N/A')} |
| Growth | {fin.get('growth', 'N/A')} |
| Stock | {fin.get('stock_ticker', 'N/A')} |

**Key Highlights:**
{chr(10).join(['- ' + h for h in fin.get('key_highlights', [])])}
"""

        # --- Placeholders for Future Agents ---
        drafts["08-Sales-Intelligence/01-Pain-Point-Analysis.md"] = (
            "# Pain Point Analysis\n\n*Coming soon with Sales Agent upgrade.*"
        )
        drafts["09-Investment-Analysis/01-Growth-Signals.md"] = (
            "# Growth Signals\n\n*Coming soon with Investment Agent upgrade.*"
        )

        return drafts
