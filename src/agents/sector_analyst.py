from typing import List, Dict, Any
from ..core.logging import setup_logger
from ..core.vault import VaultManager
from ..core.ai import get_ai_manager

logger = setup_logger("sector_analyst")


class SectorAnalyst:
    """
    Analyzes a sector by aggregating data from multiple companies stored in the Vault.
    """

    def __init__(self):
        self.vault = VaultManager()
        self.ai = get_ai_manager()

    async def analyze_sector(self, sector_name: str) -> str:
        """
        Generates a sector report by analyzing all companies in the given sector.
        """
        logger.info(f"Starting analysis for sector: {sector_name}")

        # 1. Fetch companies from Vault
        # In a real implementation, we would query Pinecone/Neo4j for companies with industry=sector_name
        # For now, we'll search for the sector name in the local vault
        try:
            companies = await self.vault.search_similar_companies(sector_name)
        except Exception as e:
            logger.error(f"Failed to search vault for sector '{sector_name}': {e}")
            return f"# Error\n\nFailed to retrieve sector data: {e}"

        if not companies:
            logger.warning(f"No companies found for sector: {sector_name}")
            return f"No data found for sector: {sector_name}"

        logger.info(f"Found {len(companies)} companies in sector.")

        # 2. Aggregate Data
        aggregated_data = self._aggregate_data(companies)

        # 3. Generate Insights using AI
        try:
            report = await self._generate_sector_report(sector_name, aggregated_data)
        except Exception as e:
            logger.error(f"Failed to generate sector report for '{sector_name}': {e}")
            return f"# Error\n\nFailed to generate report: {e}\n\n## Raw Data\n\n{aggregated_data}"

        return report

    def _aggregate_data(self, companies: List[Dict[str, Any]]) -> str:
        """
        Compiles a summary string of all found companies.
        """
        summary = ""
        for company in companies:
            name = company.get("company", "Unknown")
            snippet = company.get("content_snippet", "")
            summary += f"### {name}\n{snippet}\n\n"
        return summary

    async def _generate_sector_report(self, sector_name: str, data: str) -> str:
        """
        Uses LLM to synthesize a sector report.
        """
        prompt = f"""
        You are a Sector Analyst.
        Analyze the following data for the '{sector_name}' sector.
        Identify common trends, market leaders, and opportunities.
        
        Data:
        {data}
        
        Output a Markdown report.
        """

        response = await self.ai.generate(prompt)
        return response
