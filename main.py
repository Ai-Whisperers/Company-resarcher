import asyncio
import argparse
import os
from src.agents.orchestrator import ResearchOrchestrator
from src.core.logger import setup_logger
from src.core.output_manager import OutputManager

logger = setup_logger("main")


async def main():
    parser = argparse.ArgumentParser(description="Company Researcher Agent")
    parser.add_argument("--name", type=str, help="Company name to research")
    parser.add_argument("--url", type=str, help="Company website URL")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use free local tools (DuckDuckGo + Ollama) instead of paid APIs",
    )

    args = parser.parse_args()

    # Default to a sample if no args provided (for testing)
    company_name = args.name or "Nestle"
    url = args.url or "https://www.nestle.com"

    logger.info(f"Initializing research for {company_name} ({url})")
    if args.local:
        logger.info("Running in LOCAL mode (Free Tools)")

    orchestrator = ResearchOrchestrator(use_local_tools=args.local)
    result = await orchestrator.conduct_research(company_name, url)
    print("\n--- RESEARCH COMPLETE ---")
    print(f"Final State Keys: {result.keys()}")

    if "drafts" in result:
        # Use OutputManager to save structured reports
        output_manager = OutputManager()
        output_manager.save_research_output(company_name, result["drafts"])

        # Also save the full report for backward compatibility or easy reading
        # We can reconstruct it from the drafts if needed, or just rely on the structured files.
        # For now, let's just log success.
    else:
        logger.warning("No drafts found in result!")

    # Save to Vault (Optional / Legacy)
    try:
        from src.core.vault import VaultManager

        vault = VaultManager()
        # Construct a full report string for the vault
        full_report_content = "\n\n".join(result.get("drafts", {}).values())

        await vault.store_report(
            company_name=company_name,
            report_content=full_report_content,
            metadata={"source": "Company Researcher", "date": "2024-05-22"},
        )
        logger.info("Report stored in Vault.")
    except ImportError:
        logger.warning("VaultManager not available, skipping vault storage.")
    except Exception as e:
        logger.error(f"Failed to store in Vault: {e}")


if __name__ == "__main__":
    asyncio.run(main())
