"""
Quick test to verify LangSmith tracing is working.
Run this and then check https://smith.langchain.com
"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
load_dotenv(Path(".env"), override=True)

# Import LangSmith setup
from src.infrastructure.ai.langsmith_setup import configure_langsmith, is_langsmith_configured

async def test_langsmith_tracing():
    """Test LangSmith tracing with a simple LLM call."""

    # Configure LangSmith
    configured = configure_langsmith()
    print(f"LangSmith Configured: {configured}")
    print(f"LangSmith Active: {is_langsmith_configured()}")

    if not configured:
        print("❌ LangSmith not configured. Check your .env file.")
        return

    print("\n" + "="*60)
    print("Testing LangSmith Tracing...")
    print("="*60)

    # Test 1: Simple LangChain call
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        print("\n📡 Sending test message to OpenAI...")

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
        )

        response = await llm.ainvoke([
            HumanMessage(content="Say 'LangSmith tracing is working!' in a creative way")
        ])

        print(f"✅ Response: {response.content}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")

    # Test 2: Check environment
    print("\n" + "="*60)
    print("Environment Check:")
    print("="*60)
    print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
    print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
    print(f"LANGCHAIN_API_KEY: {'SET (hidden)' if os.getenv('LANGCHAIN_API_KEY') else 'MISSING'}")
    print(f"LANGCHAIN_ENDPOINT: {os.getenv('LANGCHAIN_ENDPOINT')}")

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Go to: https://smith.langchain.com")
    print(f"2. Open project: {os.getenv('LANGCHAIN_PROJECT', 'company-researcher')}")
    print("3. You should see a trace from this test!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_langsmith_tracing())
