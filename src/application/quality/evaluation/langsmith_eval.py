import asyncio
import os
from typing import Dict, Any, List
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_openai import ChatOpenAI
from src.agents.factory import AgentFactory
from src.core.types import CompanyProfile
from src.core.config import get_settings

# Initialize LangSmith client
client = Client()


async def run_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Target function for evaluation."""
    company_name = inputs.get("company_name")
    industry = inputs.get("industry")
    agent_type = inputs.get("agent_type", "financial")

    agent = AgentFactory.create_agent(agent_type)
    company = CompanyProfile(name=company_name, industry=industry)

    result = await agent.research(company)

    return {
        "output": result.markdown_content,
        "sources": [s.url for s in result.sources],
    }


async def main():
    """Run evaluation."""
    settings = get_settings()
    if not settings.telemetry.langsmith_api_key:
        print("LangSmith API key not found. Skipping evaluation.")
        return

    # Define dataset
    dataset_name = "Company Research Benchmark"

    # Create dataset if it doesn't exist
    if not client.has_dataset(dataset_name=dataset_name):
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Benchmark for company research agents",
        )

        # Add examples
        client.create_examples(
            inputs=[
                {
                    "company_name": "Tesla",
                    "industry": "Automotive",
                    "agent_type": "financial",
                },
                {
                    "company_name": "Apple",
                    "industry": "Technology",
                    "agent_type": "market",
                },
            ],
            outputs=[
                {"must_contain": ["revenue", "profit", "margin"]},
                {"must_contain": ["market share", "growth", "competitors"]},
            ],
            dataset_id=dataset.id,
        )

    # Define evaluators
    evaluators = [
        LangChainStringEvaluator("criteria", config={"criteria": "relevance"}),
        LangChainStringEvaluator("criteria", config={"criteria": "coherence"}),
    ]

    # Run evaluation
    results = await evaluate(
        run_agent,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix="agent-eval",
        max_concurrency=2,
    )

    print(f"Evaluation complete. View results at: {results.run_url}")


if __name__ == "__main__":
    asyncio.run(main())
