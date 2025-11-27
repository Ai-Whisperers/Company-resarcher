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

    if "drafts" in result:
        print("\n--- DRAFTS ---")
        import os

        output_dir = f"outputs/{company_name}"
        os.makedirs(output_dir, exist_ok=True)

        full_report = ""
        for section, content in result["drafts"].items():
            print(f"\n=== {section.upper()} ===\n")
            print(content[:500] + "..." if len(content) > 500 else content)
            full_report += content + "\n\n"

        with open(f"{output_dir}/full_report.md", "w", encoding="utf-8") as f:
            f.write(full_report)
        logger.info(f"Report saved to {output_dir}/full_report.md")

        # Save to Vault
        from src.core.vault import VaultManager

        vault = VaultManager()
        # We need to be in an async context to await
        # Since we are in main() which is async, we can await.
        # But wait, the printing logic above is synchronous inside main().
        # Let's verify main() structure.

        await vault.store_report(
            company_name=company_name,
            report_content=full_report,
            metadata={"source": "Company Researcher", "date": "2024-05-22"},
        )
        logger.info("Report stored in Vault.")


if __name__ == "__main__":
    asyncio.run(main())
