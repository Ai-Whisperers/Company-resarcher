"""
Test LangFuse integration after setup is complete.

Prerequisites:
1. LangFuse containers running (docker ps)
2. Account created at http://localhost:3000
3. API keys added to .env file

Run: python test_langfuse_integration.py
"""
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(".env"), override=True)

async def test_langfuse():
    """Test LangFuse tracing."""

    print("="*60)
    print("LangFuse Integration Test")
    print("="*60)

    # Check configuration
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    print(f"\nConfiguration:")
    print(f"  LANGFUSE_HOST: {host}")
    print(f"  LANGFUSE_PUBLIC_KEY: {'[SET]' if public_key else '[MISSING]'}")
    print(f"  LANGFUSE_SECRET_KEY: {'[SET]' if secret_key else '[MISSING]'}")

    if not public_key or not secret_key:
        print("\n ERROR: LangFuse credentials not configured!")
        print("\nSetup steps:")
        print("1. Open http://localhost:3000")
        print("2. Create account and project")
        print("3. Go to Settings -> API Keys")
        print("4. Create new secret key")
        print("5. Add to .env:")
        print("   LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("   LANGFUSE_SECRET_KEY=sk-lf-...")
        print("   LANGFUSE_HOST=http://localhost:3000")
        return

    print("\n" + "="*60)
    print("Testing LangChain with LangFuse Tracing")
    print("="*60)

    try:
        from langfuse.callback import CallbackHandler
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        # Create LangFuse callback
        langfuse_handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )

        print("\n1. Creating LLM with LangFuse callback...")
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

        print("2. Sending test message...")
        response = await llm.ainvoke(
            [HumanMessage(content="Say 'LangFuse tracing works!' and explain what you do")],
            config={"callbacks": [langfuse_handler]}
        )

        print(f"\n3. Response received:")
        print(f"   {response.content}")

        # Flush traces
        print("\n4. Flushing traces to LangFuse...")
        langfuse_handler.langfuse.flush()

        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nView your trace:")
        print(f"  1. Go to: {host}")
        print(f"  2. Select your project")
        print(f"  3. You should see this test run!")
        print("\nThe trace shows:")
        print("  - Complete execution tree")
        print("  - LLM prompts & responses")
        print("  - Token usage & costs")
        print("  - Execution time")
        print("  - All metadata")

    except ImportError as e:
        print(f"\n ERROR: Missing dependency: {e}")
        print("\nInstall: pip install langfuse langchain-openai")
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()

        print("\n\nTroubleshooting:")
        print("1. Is LangFuse running? Check: docker ps")
        print("2. Can you access the UI? Try: http://localhost:3000")
        print("3. Are API keys correct? Check Settings -> API Keys")

if __name__ == "__main__":
    asyncio.run(test_langfuse())
