from typing import List, Dict, Any, Optional
import warnings
from src.core.logging import setup_logger
from src.infrastructure.security import VaultManager
from src.infrastructure.ai import get_ai_manager, AIClientManager

logger = setup_logger("sector_analyst")


class SectorAnalyst:
    """
    Analyzes a sector by aggregating data from multiple companies stored in the Vault.

    This class provides cross-company analysis capabilities by:
    1. Querying the vector vault for companies in a given sector
    2. Aggregating data across multiple company profiles
    3. Using AI to synthesize sector-level insights and trends

    Attributes:
        vault: VaultManager for retrieving stored company data
        ai: AIClientManager for generating AI-powered analysis

    Example:
        analyst = SectorAnalyst()
        report = await analyst.analyze_sector("Technology")
        print(report)  # Markdown sector analysis
    """

    def __init__(
        self,
        vault: Optional[VaultManager] = None,
        ai_manager: Optional[AIClientManager] = None,
    ) -> None:
        """
        Initialize the SectorAnalyst.

        Args:
            vault: Optional VaultManager instance (creates default if None)
            ai_manager: Optional AIClientManager (uses global manager if None)
        """
        # CQ-076: Add error handling for direct instantiation and DI warnings
        if vault is None:
            warnings.warn(
                "Creating SectorAnalyst without vault is deprecated. "
                "Provide a VaultManager instance for proper dependency injection.",
                DeprecationWarning,
                stacklevel=2,
            )
            try:
                vault = VaultManager()
            except Exception as e:
                logger.error(f"Failed to initialize VaultManager: {e}")
                raise RuntimeError(
                    f"VaultManager initialization failed: {e}. "
                    "Provide a pre-initialized vault instance."
                ) from e

        if ai_manager is None:
            warnings.warn(
                "Creating SectorAnalyst without ai_manager is deprecated. "
                "Provide an AIClientManager instance for proper dependency injection.",
                DeprecationWarning,
                stacklevel=2,
            )
            ai_manager = get_ai_manager()

        self.vault = vault
        self.ai = ai_manager

    async def analyze_sector(self, sector_name: str) -> str:
        """
        Generate a comprehensive sector analysis report.

        Fetches all companies in the specified sector from the vault,
        aggregates their data, and uses AI to identify trends, leaders,
        and opportunities.

        Args:
            sector_name: Name of the sector to analyze (e.g., "Technology", "Healthcare")

        Returns:
            Markdown-formatted sector report including:
            - Market trends and dynamics
            - Key players and market leaders
            - Investment opportunities
            - Risk factors and challenges

        Raises:
            Returns error message in markdown format if vault search or AI generation fails.
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
        Compile company data into a structured summary for AI analysis.

        Extracts company names and content snippets from vault results
        and formats them as markdown sections.

        Args:
            companies: List of company dicts from vault search, each containing
                       'company' (name) and 'content_snippet' keys

        Returns:
            Markdown-formatted string with each company as a subsection
        """
        summary = ""
        for company in companies:
            name = company.get("company", "Unknown")
            snippet = company.get("content_snippet", "")
            summary += f"### {name}\n{snippet}\n\n"
        return summary

    async def _generate_sector_report(self, sector_name: str, data: str) -> str:
        """
        Use AI to synthesize aggregated company data into a sector report.

        Args:
            sector_name: Name of the sector being analyzed
            data: Aggregated company data in markdown format

        Returns:
            AI-generated markdown report with sector analysis
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
