import asyncio
import argparse
from datetime import datetime
from src.pipeline.orchestrator import PipelineOrchestrator
from src.core.logger import setup_logger
from src.core.output_manager import OutputManager

logger = setup_logger("main")


async def main():
    parser = argparse.ArgumentParser(description="Company Researcher Agent")
    parser.add_argument("--name", type=str, help="Company name to research")
    parser.add_argument("--url", type=str, help="Company website URL")
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Run research phases in parallel (default: True)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run research phases sequentially (slower but uses less resources)",
    )

    args = parser.parse_args()

    # Default to a sample if no args provided (for testing)
    company_name = args.name or "Nestle"
    url = args.url or "https://www.nestle.com"

    # Sequential flag overrides parallel
    parallel = not args.sequential

    logger.info(f"Initializing research for {company_name} ({url})")
    logger.info(f"Running in {'PARALLEL' if parallel else 'SEQUENTIAL'} mode")

    orchestrator = PipelineOrchestrator(parallel=parallel)
    result = await orchestrator.conduct_research(company_name, url)
    print("\n--- RESEARCH COMPLETE ---")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Phases completed: {len(result.get('phases', []))}")

    if result.get("phases"):
        # Use OutputManager to save structured reports
        output_manager = OutputManager()
        # Convert phases to drafts format for backward compatibility
        drafts = {
            phase["phase_name"]: phase["markdown_content"]
            for phase in result["phases"]
        }
        output_manager.save_research_output(company_name, drafts)
        logger.info(f"Saved {len(drafts)} reports to output directory")
    else:
        logger.warning("No phases found in result!")
        if result.get("errors"):
            for error in result["errors"]:
                logger.error(f"Error: {error}")

    # Save to Vault (Optional / Legacy)
    try:
        from src.core.vault import VaultManager

        vault = VaultManager()
        # Construct a full report string for the vault from phases
        full_report_content = "\n\n".join(
            phase["markdown_content"]
            for phase in result.get("phases", [])
        )

        await vault.store_report(
            company_name=company_name,
            report_content=full_report_content,
            metadata={"source": "Company Researcher", "date": datetime.now().isoformat()},
        )
        logger.info("Report stored in Vault.")
    except ImportError:
        logger.warning("VaultManager not available, skipping vault storage.")
    except Exception as e:
        logger.error(f"Failed to store in Vault: {e}")


if __name__ == "__main__":
    asyncio.run(main())
