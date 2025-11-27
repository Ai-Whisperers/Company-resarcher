from typing import Dict, Any
from .base_agent import BaseAgent
from ..core.logger import setup_logger
from ..core.ai_client import BaseAIClient
from ..core.types import CompanyProfile, ResearchPhaseResult
from src.core.constants import (
    AGENT_FINANCIAL,
    AGENT_MARKET,
    AGENT_COMPETITOR,
    AGENT_BRAND,
    AGENT_SALES,
)

logger = setup_logger("specialists")


class FinancialAgent(BaseAgent):
    """Specialist for financial analysis."""

    def __init__(self, client: BaseAIClient = None, sec_tool=None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_FINANCIAL,
            prompt_template="financial_analysis.txt",
            **kwargs,
        )
        self.sec_tool = sec_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} financial performance",
            f"{company.name} annual report",
            f"{company.name} revenue growth",
            f"{company.name} stock price analysis",
        ]
        # Fetch SEC data if available
        sec_data = ""
        if self.sec_tool:
            try:
                # Try to get 10-K content
                sec_content = self.sec_tool.get_latest_10k_content(
                    company.name
                )  # Naive ticker usage, might need search
                if sec_content:
                    sec_data = f"SEC 10-K Excerpt:\n{sec_content[:5000]}..."
            except Exception as e:
                logger.error(f"Error fetching SEC data: {e}")

        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Financials.md",
            extra_context={"sec_data": sec_data},
        )


class MarketAnalyst(BaseAgent):
    """Specialist for market research."""

    def __init__(
        self,
        client: BaseAIClient = None,
        youtube_tool=None,
        app_store_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name=AGENT_MARKET,
            prompt_template="market_intelligence.txt",
            **kwargs,
        )
        self.youtube_tool = youtube_tool
        self.app_store_tool = app_store_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} market share {company.industry}",
            f"{company.name} industry trends",
            f"{company.name} target audience demographics",
            f"{company.industry} market size and growth",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Market-Size-Growth.md",
        )


class CompetitorScout(BaseAgent):
    """Specialist for competitor analysis."""

    def __init__(self, client: BaseAIClient = None, tech_stack_tool=None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_COMPETITOR,
            prompt_template="competitive_landscape.txt",
            **kwargs,
        )
        self.tech_stack_tool = tech_stack_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} top competitors",
            f"{company.name} vs competitors comparison",
            f"{company.name} competitive advantage",
            f"{company.industry} key players",
        ]
        # Analyze Tech Stack
        tech_stack_data = {}
        if self.tech_stack_tool and company.website:
            tech_stack_data = self.tech_stack_tool.analyze_url(company.website)

        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Competitor-List.md",
            extra_context={"tech_stack": tech_stack_data},
        )


class BrandAuditor(BaseAgent):
    """Specialist for brand analysis."""

    def __init__(
        self,
        client: BaseAIClient = None,
        youtube_tool=None,
        app_store_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name=AGENT_BRAND,
            prompt_template="brand_strategy.txt",
            **kwargs,
        )
        self.youtube_tool = youtube_tool
        self.app_store_tool = app_store_tool

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} brand reputation",
            f"{company.name} customer reviews sentiment",
            f"{company.name} brand values and mission",
            f"{company.name} marketing campaigns",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Positioning.md",
        )


class SalesAgent(BaseAgent):
    """Specialist for sales strategy."""

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_SALES,
            prompt_template="sales_strategy.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} sales strategy",
            f"{company.name} distribution channels",
            f"{company.name} pricing strategy",
            f"{company.name} B2B clients",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="05-Sales-Strategy.md",
        )
