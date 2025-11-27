import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.deep_research import DeepResearchAgent
from src.core.ai_client import BaseAIClient
from src.tools.browser import BrowserTool
from src.tools.search import SearchTool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockAIClient(BaseAIClient):
    async def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        if "generating search queries" in system_prompt.lower():
            return "Query: Test Query 1\nGoal: Test Goal 1\nQuery: Test Query 2\nGoal: Test Goal 2"
        if "generate targeted questions" in system_prompt.lower():
            return "Question: What is the impact of X?\nQuestion: How does Y work?"
        if "extract key learnings" in system_prompt.lower():
            return "Learning [http://example.com/1] (Score: 8): This is a test learning.\nQuestion: Follow up?"
        return "Mock response"

    def get_provider_name(self) -> str:
        return "mock"


class MockSearchTool(SearchTool):
    async def search(self, query: str, max_results: int = 5):
        return [
            {
                "url": "http://example.com/1",
                "title": "Example 1",
                "content": "Content 1",
            },
            {
                "url": "http://example.com/2",
                "title": "Example 2",
                "content": "Content 2",
            },
        ]


class MockBrowserTool(BrowserTool):
    async def fetch_page(self, url: str) -> str:
        return f"Mock content for {url}"


async def main():
    print("Starting Deep Research Agent Test...")

    # Use mocks to avoid API costs during initial test
    ai_client = MockAIClient()
    browser_tool = MockBrowserTool()
    search_tool = MockSearchTool()

    agent = DeepResearchAgent(
        ai_client=ai_client,
        browser_tool=browser_tool,
        search_tool=search_tool,
        breadth=2,
        depth=1,
    )

    query = "What is the future of AI agents?"
    print(f"Query: {query}")

    result = await agent.run(query)

    print("\nTest Complete!")
    print("Result Preview:")
    print(result[:500])


if __name__ == "__main__":
    asyncio.run(main())
