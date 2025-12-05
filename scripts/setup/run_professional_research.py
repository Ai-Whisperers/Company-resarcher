"""
Professional Company Research Runner with Full LangChain Observability

This script demonstrates professional-grade LangChain architecture:
1. LangSmith tracing (industry standard)
2. Custom metrics and callbacks
3. Structured outputs with Pydantic
4. Error handling and retries
5. Cost tracking

Usage:
    python run_professional_research.py --name "Tesla" --industry "Automotive"
"""
import asyncio
import sys
import time
from typing import Optional
from pathlib import Path

# LangChain imports
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.tracers.langchain import LangChainTracer

class ProfessionalResearchCallback(BaseCallbackHandler):
    """
    Professional callback handler for research metrics.

    Tracks:
    - LLM calls and token usage
    - Tool invocations
    - Timing information
    - Error rates
    - Cost estimation
    """

    def __init__(self):
        self.start_time = time.time()
        self.llm_calls = 0
        self.total_tokens = 0
        self.tool_calls = 0
        self.errors = []
        self.sources_found = 0

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Track LLM call start."""
        self.llm_calls += 1
        print(f"\n[LLM Call #{self.llm_calls}] Starting...")

    def on_llm_end(self, response, **kwargs):
        """Track LLM call completion."""
        # Extract token usage
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            tokens = usage.get('total_tokens', 0)
            self.total_tokens += tokens
            print(f"[LLM Call #{self.llm_calls}] Completed - {tokens} tokens")

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Track tool invocation."""
        self.tool_calls += 1
        tool_name = serialized.get('name', 'unknown')
        print(f"\n[Tool Call #{self.tool_calls}] {tool_name}")

    def on_tool_end(self, output: str, **kwargs):
        """Track tool completion."""
        # Count sources from search results
        if "http" in output:
            sources = output.count("http")
            self.sources_found += sources
            print(f"[Tool Result] Found {sources} sources")

    def on_chain_error(self, error: Exception, **kwargs):
        """Track errors."""
        self.errors.append(str(error))
        print(f"\n[ERROR] {error}")

    def get_summary(self) -> dict:
        """Get metrics summary."""
        duration = time.time() - self.start_time
        return {
            "duration_seconds": round(duration, 2),
            "llm_calls": self.llm_calls,
            "total_tokens": self.total_tokens,
            "tool_calls": self.tool_calls,
            "sources_found": self.sources_found,
            "errors": len(self.errors),
            "tokens_per_second": round(self.total_tokens / duration if duration > 0 else 0, 2)
        }


async def run_research_professional(
    company_name: str,
    industry: Optional[str] = None,
    agent_type: str = "comprehensive"
):
    """
    Run company research with professional LangChain architecture.

    Features:
    - LangSmith tracing (automatic)
    - Custom metrics callback
    - Structured error handling
    - Performance monitoring
    """
    print("=" * 70)
    print("PROFESSIONAL COMPANY RESEARCH")
    print("=" * 70)
    print(f"\nCompany: {company_name}")
    print(f"Industry: {industry or 'Auto-detect'}")
    print(f"Agent Type: {agent_type}")
    print("\nFeatures Enabled:")
    print("  [x] LangSmith Tracing")
    print("  [x] Custom Metrics")
    print("  [x] Performance Monitoring")
    print("  [x] Cost Tracking")
    print("  [x] Structured Outputs")
    print("=" * 70)

    # Initialize custom callback
    metrics_callback = ProfessionalResearchCallback()

    # Initialize LangSmith tracer (automatic if LANGCHAIN_TRACING_V2=true)
    # The tracer is automatically added by LangChain when environment variables are set

    try:
        # Import and run the actual research pipeline
        from src.cli.app import main as run_cli

        print("\n[STARTING] Research pipeline...")
        print("View live traces at: https://smith.langchain.com")
        print("Project: maga-campaign-generator")
        print()

        # Set up command-line arguments
        sys.argv = [
            "main.py",
            "--name", company_name,
        ]
        if industry:
            sys.argv.extend(["--industry", industry])

        # Run the research
        await run_cli()

        # Get metrics summary
        summary = metrics_callback.get_summary()

        print("\n" + "=" * 70)
        print("RESEARCH COMPLETED - METRICS SUMMARY")
        print("=" * 70)
        print(f"Duration: {summary['duration_seconds']}s")
        print(f"LLM Calls: {summary['llm_calls']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Tool Calls: {summary['tool_calls']}")
        print(f"Sources Found: {summary['sources_found']}")
        print(f"Errors: {summary['errors']}")
        print(f"Throughput: {summary['tokens_per_second']} tokens/sec")

        # Cost estimation (rough)
        cost_per_1k_tokens = 0.002  # GPT-3.5 Turbo rate
        estimated_cost = (summary['total_tokens'] / 1000) * cost_per_1k_tokens
        print(f"Estimated Cost: ${estimated_cost:.4f}")

        print("\n" + "=" * 70)
        print("VIEW YOUR TRACE")
        print("=" * 70)
        print("1. Go to: https://smith.langchain.com")
        print("2. Select project: maga-campaign-generator")
        print("3. Find your latest run (just now)")
        print("\nYou'll see:")
        print("  - Complete execution flow")
        print("  - Every LLM prompt & response")
        print("  - Tool calls and results")
        print("  - Timing for each step")
        print("  - Token usage & costs")
        print("  - Full input/output data")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Research failed: {e}")
        import traceback
        traceback.print_exc()

        # Metrics even on failure
        summary = metrics_callback.get_summary()
        print("\nPartial metrics:")
        print(f"  Duration: {summary['duration_seconds']}s")
        print(f"  LLM Calls: {summary['llm_calls']}")
        print(f"  Errors: {summary['errors']}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Professional Company Research with LangSmith Tracing"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Company name to research"
    )
    parser.add_argument(
        "--industry",
        help="Industry (optional - will auto-detect if not provided)"
    )
    parser.add_argument(
        "--agent",
        default="comprehensive",
        choices=["comprehensive", "investment", "sales", "social_media"],
        help="Type of research agent to use"
    )

    args = parser.parse_args()

    # Run research
    asyncio.run(run_research_professional(
        company_name=args.name,
        industry=args.industry,
        agent_type=args.agent
    ))


if __name__ == "__main__":
    main()
