import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.specialists import FinancialAgent
from src.core.types import CompanyProfile
from src.tools.financial_data import FinancialDataTool
from src.core.ai_client import BaseAIClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("src").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class MockAIClient(BaseAIClient):
    async def generate(self, prompt: str, system: str = None, **kwargs) -> str:
        return '{"analysis": "The company shows strong growth.", "key_metrics": {"revenue": "100B"}}'

    def get_provider_name(self) -> str:
        return "mock"


async def main():
    logger.info("Starting FinancialAgent Manual Test")

    # Initialize tools
    financial_tool = FinancialDataTool()

    # Initialize Agent
    agent = FinancialAgent(client=MockAIClient(), financial_tool=financial_tool)

    # Define Company
    company = CompanyProfile(
        name="Apple Inc.",
        industry="Technology",
        description="Tech giant",
        website="https://www.apple.com",
    )

    # Run Research
    logger.info(f"Researching {company.name}...")

    # Verify data fetching directly first
    logger.info("Verifying yfinance data fetch...")
    ticker = financial_tool.guess_ticker_from_name(company.name)
    logger.info(f"Guessed ticker: {ticker}")
    if ticker:
        data = await financial_tool.get_historical_data(ticker)
        if data is not None and not data.empty:
            logger.info(f"Successfully fetched {len(data)} rows for {ticker}")
        else:
            logger.error(f"Failed to fetch data for {ticker}")

    result = await agent.research(company)

    # Verify Results
    logger.info("\n--- Research Result ---")
    # Check if quant analysis is in the extra_context or output (mock output won't show it, but we can check the object)
    # The agent passes extra_context to execute_research_cycle, which uses it to format the prompt.
    # Since we mock the AI, we won't see it in the final text, but we can check logs or step through if we could.
    # For this test, we rely on the logs from AlphaFactorMiner and QuantEngine.

    print("Test Complete. Check logs for 'Backtest complete' messages.")


if __name__ == "__main__":
    asyncio.run(main())
