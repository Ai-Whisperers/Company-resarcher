import logging
import yaml
from pathlib import Path
from src.services.research.incremental import (
    IncrementalResearchService,
    run_incremental_research,
    run_incremental_batch,
    print_incremental_report,
)
from src.cli.handlers.profiles import load_batch_profiles, load_company_profile

logger = logging.getLogger("cli.commands.incremental")


async def run_incremental_batch_mode(
    batch_path: str,
    max_queries: int = 30,
) -> None:
    """Run incremental research for a batch of companies."""
    logger.info(f"Running INCREMENTAL research for batch: {batch_path}")
    profiles = load_batch_profiles(batch_path)
    company_names = [p["name"] for p in profiles]

    # Load market config for industry
    industry = "telecommunications"
    market_yaml = Path(batch_path) / "_market.yaml"
    if market_yaml.exists():
        with open(market_yaml, "r", encoding="utf-8") as f:
            market_config = yaml.safe_load(f)
            industry = market_config.get("market", {}).get("industry", industry)
            country = market_config.get("market", {}).get("country", "Paraguay")
    else:
        country = profiles[0].get("country", "Paraguay") if profiles else "Paraguay"

    print(f"\n{'='*70}")
    print("INCREMENTAL RESEARCH MODE")
    print(f"{'='*70}")
    print(f"Companies: {len(profiles)}")
    print(f"Industry: {industry}")
    print(f"Max queries per company: {max_queries}")
    print(f"{'='*70}\n")

    results = await run_incremental_batch(
        company_names=company_names,
        industry=industry,
        country=country,
    )

    # Print summary
    print(f"\n{'='*70}")
    print("INCREMENTAL RESEARCH COMPLETE")
    print(f"{'='*70}")
    total_skipped_seen = sum(r.stats.urls_skipped_seen for r in results.values())
    total_skipped_similar = sum(r.stats.urls_skipped_similar for r in results.values())
    total_fetched = sum(r.stats.urls_fetched_new for r in results.values())
    total_filled = sum(r.stats.gaps_filled for r in results.values())
    print(f"URLs skipped (already seen): {total_skipped_seen}")
    print(f"URLs skipped (similar content): {total_skipped_similar}")
    print(f"New URLs fetched: {total_fetched}")
    print(f"Gaps filled: {total_filled}")
    print(f"\nPer-company results:")
    for company, result in results.items():
        efficiency = result.stats.to_dict()["efficiency_rate"]
        print(f"  {company}: {result.stats.gaps_filled} gaps filled, {efficiency}")
    print(f"{'='*70}\n")


async def run_incremental_profile_mode(
    profile_path: str,
    max_queries: int = 30,
) -> None:
    """Run incremental research for a single company profile."""
    profile = load_company_profile(profile_path)
    company_name = profile["name"]
    industry = profile.get("industry", "telecommunications")
    country = profile.get("country", "Paraguay")

    print(f"\n{'='*70}")
    print(f"INCREMENTAL RESEARCH: {company_name}")
    print(f"{'='*70}")
    print(f"Industry: {industry}")
    print(f"Country: {country}")
    print(f"Max queries: {max_queries}")
    print(f"{'='*70}\n")

    result = await run_incremental_research(
        company_name=company_name,
        industry=industry,
        country=country,
        max_queries=max_queries,
    )

    print_incremental_report(result)


async def run_incremental_name_mode(
    company_name: str,
    industry: str | None,
    max_queries: int = 30,
) -> None:
    """Run incremental research for a company name."""
    print(f"\n{'='*70}")
    print(f"INCREMENTAL RESEARCH: {company_name}")
    print(f"{'='*70}")
    print(f"Industry: {industry or 'telecommunications'}")
    print(f"Max queries: {max_queries}")
    print(f"{'='*70}\n")

    result = await run_incremental_research(
        company_name=company_name,
        industry=industry or "telecommunications",
        max_queries=max_queries,
    )

    print_incremental_report(result)
