from src.services.research.incremental import IncrementalResearchService
from src.cli.handlers.profiles import load_batch_profiles, load_company_profile


def run_status_command(
    batch_path: str | None = None,
    profile_path: str | None = None,
    company_name: str | None = None,
) -> None:
    """Show research status for a company or batch."""
    if batch_path:
        # Show status for all companies in batch
        profiles = load_batch_profiles(batch_path)
        print(f"\n{'='*70}")
        print("RESEARCH STATUS - ALL COMPANIES")
        print(f"{'='*70}\n")
        service = IncrementalResearchService()
        for profile in profiles:
            status = service.get_research_status(profile["name"])
            print(f"{profile['name']}:")
            print(f"  Completeness: {status['completeness']}")
            print(f"  Data gaps: {status['gaps_count']}")
            print(
                f"  Sources: {status['sources_count']} ({status['stale_sources']} stale)"
            )
            if status["priority_gaps"]:
                print(f"  Priority gaps: {', '.join(status['priority_gaps'][:3])}")
            print()
        return

    # Determine company name
    target_name = company_name
    if profile_path:
        profile = load_company_profile(profile_path)
        target_name = profile["name"]

    if not target_name:
        print("Error: --status requires --profile, --name, or --batch")
        return

    # Show status for single company
    service = IncrementalResearchService()
    status = service.get_research_status(target_name)
    print(f"\n{'='*60}")
    print(f"RESEARCH STATUS: {target_name}")
    print(f"{'='*60}")
    print(f"Completeness: {status['completeness']}")
    print(f"Data gaps: {status['gaps_count']}")
    print(f"Sources tracked: {status['sources_count']}")
    print(f"Stale sources: {status['stale_sources']}")
    if status["last_research"]:
        print(f"Last research: {status['last_research']}")
    if status["priority_gaps"]:
        print(f"\nPriority gaps to fill:")
        for gap in status["priority_gaps"]:
            print(f"  - {gap}")
    if status["data_types_found"]:
        print(f"\nData types found: {', '.join(status['data_types_found'][:5])}")
    print(f"{'='*60}\n")
