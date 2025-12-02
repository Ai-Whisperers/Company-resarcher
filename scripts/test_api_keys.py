#!/usr/bin/env python3
"""
API Key Tester Script - SCRIPT-005

Tests all configured API keys to verify they work:
- AI providers (OpenAI, Anthropic, Gemini, Groq)
- Search providers (Tavily, Serper)
- Data providers (NewsAPI)

Usage:
    python scripts/test_api_keys.py           # Test all API keys
    python scripts/test_api_keys.py --ai      # Test only AI providers
    python scripts/test_api_keys.py --search  # Test only search providers
    python scripts/test_api_keys.py --quick   # Quick test (smaller payloads)
"""

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Awaitable

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class TestResult:
    """Result of an API key test."""
    provider: str
    category: str
    key_var: str
    success: bool
    latency_ms: float = 0.0
    error: Optional[str] = None
    details: Optional[str] = None


async def test_openai() -> TestResult:
    """Test OpenAI API key."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return TestResult("OpenAI", "ai", "OPENAI_API_KEY", False, error="Key not configured")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=key)

        start = time.time()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful' in 3 words"}],
            max_tokens=10,
        )
        latency = (time.time() - start) * 1000

        return TestResult(
            "OpenAI", "ai", "OPENAI_API_KEY", True,
            latency_ms=latency,
            details=f"Model: gpt-3.5-turbo"
        )
    except Exception as e:
        return TestResult("OpenAI", "ai", "OPENAI_API_KEY", False, error=str(e)[:100])


async def test_anthropic() -> TestResult:
    """Test Anthropic API key."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return TestResult("Anthropic", "ai", "ANTHROPIC_API_KEY", False, error="Key not configured")

    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=key)

        start = time.time()
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test' only"}],
        )
        latency = (time.time() - start) * 1000

        return TestResult(
            "Anthropic", "ai", "ANTHROPIC_API_KEY", True,
            latency_ms=latency,
            details=f"Model: claude-3-haiku"
        )
    except Exception as e:
        return TestResult("Anthropic", "ai", "ANTHROPIC_API_KEY", False, error=str(e)[:100])


async def test_gemini() -> TestResult:
    """Test Google Gemini API key."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return TestResult("Gemini", "ai", "GEMINI_API_KEY", False, error="Key not configured")

    try:
        import google.generativeai as genai
        genai.configure(api_key=key)

        model = genai.GenerativeModel("gemini-1.5-flash")

        start = time.time()
        response = await model.generate_content_async("Say 'test' only")
        latency = (time.time() - start) * 1000

        return TestResult(
            "Gemini", "ai", "GEMINI_API_KEY", True,
            latency_ms=latency,
            details=f"Model: gemini-1.5-flash"
        )
    except Exception as e:
        return TestResult("Gemini", "ai", "GEMINI_API_KEY", False, error=str(e)[:100])


async def test_groq() -> TestResult:
    """Test Groq API key."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return TestResult("Groq", "ai", "GROQ_API_KEY", False, error="Key not configured")

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=key)

        start = time.time()
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'test' only"}],
            max_tokens=10,
        )
        latency = (time.time() - start) * 1000

        return TestResult(
            "Groq", "ai", "GROQ_API_KEY", True,
            latency_ms=latency,
            details=f"Model: llama-3.1-8b-instant"
        )
    except Exception as e:
        return TestResult("Groq", "ai", "GROQ_API_KEY", False, error=str(e)[:100])


async def test_tavily() -> TestResult:
    """Test Tavily search API key."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return TestResult("Tavily", "search", "TAVILY_API_KEY", False, error="Key not configured")

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=key)

        start = time.time()
        response = client.search("test query", max_results=1)
        latency = (time.time() - start) * 1000

        return TestResult(
            "Tavily", "search", "TAVILY_API_KEY", True,
            latency_ms=latency,
            details=f"Results: {len(response.get('results', []))}"
        )
    except Exception as e:
        return TestResult("Tavily", "search", "TAVILY_API_KEY", False, error=str(e)[:100])


async def test_serper() -> TestResult:
    """Test Serper search API key."""
    key = os.getenv("SERPER_API_KEY")
    if not key:
        return TestResult("Serper", "search", "SERPER_API_KEY", False, error="Key not configured")

    try:
        import httpx

        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": "test", "num": 1},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        latency = (time.time() - start) * 1000

        return TestResult(
            "Serper", "search", "SERPER_API_KEY", True,
            latency_ms=latency,
            details=f"Results: {len(data.get('organic', []))}"
        )
    except Exception as e:
        return TestResult("Serper", "search", "SERPER_API_KEY", False, error=str(e)[:100])


async def test_newsapi() -> TestResult:
    """Test NewsAPI key."""
    key = os.getenv("NEWS_API_KEY")
    if not key:
        return TestResult("NewsAPI", "data", "NEWS_API_KEY", False, error="Key not configured")

    try:
        import httpx

        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://newsapi.org/v2/top-headlines",
                params={"apiKey": key, "country": "us", "pageSize": 1},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        latency = (time.time() - start) * 1000

        if data.get("status") == "ok":
            return TestResult(
                "NewsAPI", "data", "NEWS_API_KEY", True,
                latency_ms=latency,
                details=f"Total: {data.get('totalResults', 0)}"
            )
        else:
            return TestResult(
                "NewsAPI", "data", "NEWS_API_KEY", False,
                error=data.get("message", "Unknown error")
            )
    except Exception as e:
        return TestResult("NewsAPI", "data", "NEWS_API_KEY", False, error=str(e)[:100])


# Registry of test functions
TEST_FUNCTIONS: dict[str, list[Callable[[], Awaitable[TestResult]]]] = {
    "ai": [test_openai, test_anthropic, test_gemini, test_groq],
    "search": [test_tavily, test_serper],
    "data": [test_newsapi],
}


async def run_tests(categories: list[str]) -> list[TestResult]:
    """Run tests for specified categories."""
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for category in categories:
            if category not in TEST_FUNCTIONS:
                continue

            for test_func in TEST_FUNCTIONS[category]:
                # Get provider name from function name
                provider = test_func.__name__.replace("test_", "").title()
                task = progress.add_task(f"Testing {provider}...", total=None)

                try:
                    result = await asyncio.wait_for(test_func(), timeout=60.0)
                except asyncio.TimeoutError:
                    result = TestResult(
                        provider, category, "",
                        success=False,
                        error="Timeout (60s)"
                    )

                results.append(result)
                progress.remove_task(task)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test Company Researcher API keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--ai", action="store_true",
        help="Test AI providers only (OpenAI, Anthropic, Gemini, Groq)"
    )
    parser.add_argument(
        "--search", action="store_true",
        help="Test search providers only (Tavily, Serper)"
    )
    parser.add_argument(
        "--data", action="store_true",
        help="Test data providers only (NewsAPI)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=60,
        help="Timeout per test in seconds (default: 60)"
    )

    args = parser.parse_args()

    # Determine which categories to test
    if args.ai or args.search or args.data:
        categories = []
        if args.ai:
            categories.append("ai")
        if args.search:
            categories.append("search")
        if args.data:
            categories.append("data")
    else:
        categories = ["ai", "search", "data"]

    console.print("\n[bold]API Key Tester[/bold]")
    console.print(f"Testing categories: {', '.join(categories)}\n")

    # Run tests
    results = asyncio.run(run_tests(categories))

    # Build results table
    table = Table(title="API Key Test Results")
    table.add_column("Provider", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Details/Error")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for result in results:
        if result.success:
            status = "[green]PASS[/green]"
            latency = f"{result.latency_ms:.0f}ms"
            details = result.details or ""
            success_count += 1
        elif result.error and "not configured" in result.error.lower():
            status = "[yellow]SKIP[/yellow]"
            latency = "-"
            details = result.error
            skip_count += 1
        else:
            status = "[red]FAIL[/red]"
            latency = "-"
            details = f"[red]{result.error}[/red]"
            fail_count += 1

        table.add_row(
            result.provider,
            result.category,
            status,
            latency,
            details
        )

    console.print(table)
    console.print()

    # Summary
    total = len(results)
    console.print(f"[bold]Summary:[/bold] {success_count}/{total} passed, {fail_count} failed, {skip_count} skipped")

    if fail_count > 0:
        console.print("\n[yellow]Some API keys failed validation. Check your .env configuration.[/yellow]")
        sys.exit(1)
    elif success_count == 0:
        console.print("\n[yellow]No API keys configured. Run 'python scripts/validate_config.py --example' for a template.[/yellow]")
    else:
        console.print("\n[green]All configured API keys are working![/green]")


if __name__ == "__main__":
    main()
