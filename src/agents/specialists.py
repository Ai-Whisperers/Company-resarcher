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

    def __init__(self, client: BaseAIClient = None):
        super().__init__(
            client=client,
            name=AGENT_FINANCIAL,
            prompt_template="financial_analysis.txt",
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} financial performance",
            f"{company.name} annual report",
            f"{company.name} revenue growth",
            f"{company.name} stock price analysis",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="financial_report.md",
        )


class MarketAnalyst(BaseAgent):
    """Specialist for market research."""

    def __init__(self, client: BaseAIClient = None):
        super().__init__(
            client=client, name=AGENT_MARKET, prompt_template="market_intelligence.txt"
        )

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
            output_template="market_report.md",
        )


class CompetitorScout(BaseAgent):
    """Specialist for competitor analysis."""

    def __init__(self, client: BaseAIClient = None):
        super().__init__(
            client=client,
            name=AGENT_COMPETITOR,
            prompt_template="competitive_landscape.txt",
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} top competitors",
            f"{company.name} vs competitors comparison",
            f"{company.name} competitive advantage",
            f"{company.industry} key players",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="competitor_report.md",
        )


class BrandAuditor(BaseAgent):
    """Specialist for brand analysis."""

    def __init__(self, client: BaseAIClient = None):
        super().__init__(
            client=client, name=AGENT_BRAND, prompt_template="brand_strategy.txt"
        )

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
            output_template="brand_report.md",
        )


class SalesAgent(BaseAgent):
    """Specialist for sales strategy."""

    def __init__(self, client: BaseAIClient = None):
        super().__init__(
            client=client, name=AGENT_SALES, prompt_template="sales_strategy.txt"
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
            output_template="sales_report.md",
        )
