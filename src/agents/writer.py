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

        # Section 1: Executive Summary
        drafts["executive_summary"] = (
            f"# Executive Summary for {company.name}\n\n{insights.get('executive_summary', 'N/A')}\n"
        )

        # Section 2: Financial Overview
        fin = financial_data
        drafts[
            "financials"
        ] = f"""
## Financial Overview
| Metric | Value |
| :--- | :--- |
| Revenue | {fin.get('revenue', 'N/A')} |
| Profit | {fin.get('profit', 'N/A')} |
| Growth | {fin.get('growth', 'N/A')} |
| Stock | {fin.get('stock_ticker', 'N/A')} |

**Key Highlights:**
{chr(10).join(['- ' + h for h in fin.get('key_highlights', [])])}
"""

        # Section 3: Strategic Analysis (SWOT)
        swot = insights.get("swot", {})
        drafts[
            "strategy"
        ] = f"""
## Strategic Analysis (SWOT)

### Strengths
{chr(10).join(['- ' + s for s in swot.get('strengths', [])])}

### Weaknesses
{chr(10).join(['- ' + w for w in swot.get('weaknesses', [])])}

### Opportunities
{chr(10).join(['- ' + o for o in swot.get('opportunities', [])])}

### Threats
{chr(10).join(['- ' + t for t in swot.get('threats', [])])}
"""

        # Section 4: Market & Competitors
        drafts["market"] = (
            f"## Market Intelligence\n\nIndustry: {market_data.get('industry', 'N/A')}\nMarket Size: {market_data.get('market_size', 'N/A')}\n"
        )

        return drafts
