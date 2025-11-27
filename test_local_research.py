"""
Verification script for Local & Free Research Transition.
"""

import asyncio
import sys
import io
from src.tools.local_search import LocalSearchTool
from src.agents.factory import AgentFactory
from src.core.smart_router import SmartAIRouter
from src.core.ai_client import OllamaClient, OpenAIClient

# Force UTF-8 for stdout to avoid Windows console encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


async def test_local_search():
    print("\n--- Testing LocalSearchTool ---")
    tool = LocalSearchTool()
    results = await tool.search("OpenAI", max_results=3)
    print(f"Found {len(results)} results")
    for r in results:
        try:
            print(f"- {r['title']} ({r['url']})")
        except Exception:
            print(f"- [Encoding Error] ({r['url']})")
    assert len(results) > 0, "Local search returned no results"


def test_agent_factory_local_mode():
    print("\n--- Testing AgentFactory (Local Mode) ---")
    factory = AgentFactory(use_local_tools=True, enable_smart_routing=False)
    specialists = factory.create_specialists()

    financial_agent = specialists["financial"]
    # Check if search tool is LocalSearchTool
    assert isinstance(
        financial_agent.search_tool, LocalSearchTool
    ), "FinancialAgent not using LocalSearchTool"
    print("✓ FinancialAgent is using LocalSearchTool")


def test_smart_router_ollama():
    print("\n--- Testing SmartAIRouter (Ollama) ---")
    # Mock API key for expensive client
    router = SmartAIRouter(api_key="sk-mock", use_ollama=True)

    assert isinstance(router.cheap, OllamaClient), "Cheap client is not OllamaClient"
    assert isinstance(
        router.expensive, OpenAIClient
    ), "Expensive client is not OpenAIClient"
    print("✓ SmartAIRouter configured with Ollama as cheap client")


async def main():
    await test_local_search()
    test_agent_factory_local_mode()
    test_smart_router_ollama()
    print("\n✓ All verification tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
