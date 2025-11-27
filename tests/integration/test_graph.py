import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph.graph_builder import build_graph
from src.graph.state import ResearchState


async def test_graph():
    print("Building Graph...")
    graph = build_graph()

    print("Initializing State...")
    initial_state = ResearchState(company_name="Test Corp", website="https://test.com")

    print("Running Graph...")
    # LangGraph invoke returns the final state
    result = await graph.ainvoke(initial_state.model_dump())

    print("\n--- FINAL STATE ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(test_graph())
