import asyncio
import argparse
from src.core.types import CompanyProfile
from src.agents.orchestrator import ResearchOrchestrator
from src.core.logger import setup_logger

logger = setup_logger("main")


async def main():
    parser = argparse.ArgumentParser(description="Company Researcher Agent")
    parser.add_argument("--name", type=str, help="Company name to research")
    parser.add_argument("--industry", type=str, help="Industry of the company")

    args = parser.parse_args()

    # Default to a sample if no args provided (for testing)
    company_name = args.name or "Nestle"
    industry = args.industry or "Food & Beverage"

    logger.info(f"Initializing research for {company_name} ({industry})")

    orchestrator = ResearchOrchestrator()
    await orchestrator.run_research(company_name, industry)


if __name__ == "__main__":
    asyncio.run(main())
