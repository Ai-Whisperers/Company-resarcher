"""
Test research with LangSmith tracing enabled.
This will show the full execution flow in LangSmith.
"""
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(".env"), override=True)

async def main():
    """Run a quick company research test."""

    # Import after env is loaded
    from src.pipeline.orchestrator import PipelineOrchestrator
    from src.infrastructure.ai.langsmith_setup import configure_langsmith

    print("="*60)
    print("Company Research Test with LangSmith Tracing")
    print("="*60)

    # Configure LangSmith
    langsmith_enabled = configure_langsmith()
    print(f"\nLangSmith Tracing: {'ENABLED' if langsmith_enabled else 'DISABLED'}")

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        research_types=["market"],  # Just market research for speed
        parallel=False,
        timeout_seconds=300,
    )

    print("\nStarting research for: Tesla")
    print("This will take 1-2 minutes...")
    print("-"*60)

    try:
        # Run research
        result = await orchestrator.conduct_research(
            company_name="Tesla",
            url="https://tesla.com",
            industry="Automotive",
        )

        print("\n" + "="*60)
        print("Research Complete!")
        print("="*60)
        print(f"\nStatus: {result.get('status')}")
        print(f"Phases completed: {len(result.get('phases', []))}")

        if langsmith_enabled:
            print("\n" + "="*60)
            print("VIEW YOUR TRACE IN LANGSMITH:")
            print("="*60)
            print("1. Go to: https://smith.langchain.com")
            print("2. Open project: maga-campaign-generator")
            print("3. Look for the latest 'Tesla' research run")
            print("\nYou'll see:")
            print("  - Complete execution graph")
            print("  - All LLM calls with prompts/responses")
            print("  - Tool invocations (search, browser)")
            print("  - Timing and cost breakdown")
            print("  - Any errors or warnings")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
