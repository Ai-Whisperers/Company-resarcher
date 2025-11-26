import asyncio
import argparse
from src.core.types import CompanyProfile
from src.agents.orchestrator import ResearchOrchestrator
from src.core.logger import setup_logger

logger = setup_logger("main")


async def main():
    parser = argparse.ArgumentParser(description="Company Researcher Agent")
    parser.add_argument("--name", type=str, help="Company name to research")
    parser.add_argument("--url", type=str, help="Company website URL")

    args = parser.parse_args()

    # Default to a sample if no args provided (for testing)
    company_name = args.name or "Nestle"
    url = args.url or "https://www.nestle.com"

    logger.info(f"Initializing research for {company_name} ({url})")

    orchestrator = ResearchOrchestrator()
    result = await orchestrator.conduct_research(company_name, url)
    print("\n--- RESEARCH COMPLETE ---")
    print(f"Final State Keys: {result.keys()}")


if __name__ == "__main__":
    asyncio.run(main())
