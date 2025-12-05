"""
Simple LangSmith tracing test without complex imports.
"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment FIRST
load_dotenv(Path(".env"), override=True)

async def test_langsmith():
    """Test LangSmith tracing with a simple call."""

    print("="*60)
    print("LangSmith Configuration Test")
    print("="*60)

    # Check environment
    tracing = os.getenv("LANGCHAIN_TRACING_V2")
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "company-researcher")
    endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

    print(f"\nLANGCHAIN_TRACING_V2: {tracing}")
    print(f"LANGCHAIN_API_KEY: {'[SET]' if api_key else '[MISSING]'}")
    print(f"LANGCHAIN_PROJECT: {project}")
    print(f"LANGCHAIN_ENDPOINT: {endpoint}")

    if not tracing or tracing.lower() != "true":
        print("\n❌ Tracing not enabled! Set LANGCHAIN_TRACING_V2=true")
        return

    if not api_key:
        print("\n❌ API key missing! Set LANGCHAIN_API_KEY in .env")
        return

    print("\n" + "="*60)
    print("Testing LangChain with OpenAI...")
    print("="*60)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        # Create LLM
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
        )

        print("\n📡 Sending test message...")

        # Send a simple message
        messages = [
            SystemMessage(content="You are a helpful assistant testing LangSmith tracing."),
            HumanMessage(content="Say 'Hello from LangSmith!' and explain in one sentence what LangSmith does.")
        ]

        response = await llm.ainvoke(messages)

        print(f"\n✅ Response received:")
        print(f"   {response.content}")

        print("\n" + "="*60)
        print("SUCCESS! 🎉")
        print("="*60)
        print("\n📊 View your trace:")
        print(f"   1. Go to: https://smith.langchain.com")
        print(f"   2. Select project: '{project}'")
        print(f"   3. You should see this test run in the traces!")
        print("\nThe trace will show:")
        print("   - Your prompt (input)")
        print("   - The model's response (output)")
        print("   - Token usage")
        print("   - Latency")
        print("   - Cost estimate")

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Run: pip install langchain-openai langchain-core")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langsmith())
