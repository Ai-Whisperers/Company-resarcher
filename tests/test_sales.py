import asyncio
from src.agents.specialists import SalesAgent
from src.core.types import CompanyProfile


async def main():
    print("Testing Sales Agent with Product Matching...")
    agent = SalesAgent()

    profile = CompanyProfile(
        name="Acme Corp",
        website="https://acme.com",
        country="USA",
        industry="Logistics",
    )

    # We expect the agent to match "Data Analytics Dashboard" or "AI Automation Suite"
    # given the industry "Logistics".

    result = await agent.research(profile)
    print("\n--- SALES STRATEGY ---")
    print(result.markdown_content)


if __name__ == "__main__":
    asyncio.run(main())
