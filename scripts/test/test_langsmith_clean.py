"""
LangSmith tracing test - Windows compatible (no emojis)
"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment FIRST
load_dotenv(Path(".env"), override=True)

async def test_langsmith():
    """Test LangSmith tracing."""

    print("="*60)
    print("LangSmith Configuration Test")
    print("="*60)

    # Check environment
    tracing = os.getenv("LANGCHAIN_TRACING_V2")
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "company-researcher")

    print(f"\nLANGCHAIN_TRACING_V2: {tracing}")
    print(f"LANGCHAIN_API_KEY: [SET]" if api_key else "LANGCHAIN_API_KEY: [MISSING]")
    print(f"LANGCHAIN_PROJECT: {project}")

    if not tracing or tracing.lower() != "true":
        print("\nERROR: Tracing not enabled!")
        return

    if not api_key:
        print("\nERROR: API key missing!")
        return

    print("\n" + "="*60)
    print("Testing LangChain with OpenAI...")
    print("="*60)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

        print("\nSending test message...")

        response = await llm.ainvoke([
            HumanMessage(content="Say 'LangSmith tracing works!' and explain what you do in one sentence.")
        ])

        print(f"\nResponse received:")
        print(f"  {response.content}")

        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print("\nView your trace:")
        print(f"  1. Go to: https://smith.langchain.com")
        print(f"  2. Select project: {project}")
        print("  3. You should see this test run!")
        print("\nThe trace will show:")
        print("  - Your prompt (input)")
        print("  - Model response (output)")
        print("  - Token usage & cost")
        print("  - Execution time")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langsmith())
