import asyncio
import os
from src.tools.search.tool import SearchTool
from langchain_core.tools import Tool


async def verify_search_tool():
    print("1. Initializing SearchTool...")
    # Use DuckDuckGo as it doesn't require API keys
    tool = SearchTool(preferred_provider="duckduckgo")

    print("2. Converting to LangChain Tool...")
    lc_tool = tool.to_langchain_tool()

    assert isinstance(lc_tool, Tool)
    assert lc_tool.name == "web_search"
    print("   Conversion successful.")

    print("3. Testing Async Invocation...")
    try:
        # Simple query that should return results
        result = await lc_tool.ainvoke("Python programming language")
        print(f"   Result type: {type(result)}")
        print(f"   Result length: {len(result)}")
        assert len(result) > 0
        assert "Python" in result
        print("   Async invocation successful.")
    except Exception as e:
        print(f"   Async invocation failed: {e}")
        # Don't fail the script if it's just a network issue, but report it

    print("\nVerification Complete!")


if __name__ == "__main__":
    asyncio.run(verify_search_tool())
