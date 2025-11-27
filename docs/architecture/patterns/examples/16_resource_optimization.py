"""
Resource Optimization Pattern Example
-------------------------------------
This script demonstrates the Resource Optimization pattern:
Task -> Router -> (Cheap Model | Expensive Model)

It simulates routing tasks based on complexity to save costs.
"""

import asyncio
import random
from typing import Protocol


class Model(Protocol):
    async def generate(self, prompt: str) -> str: ...
    @property
    def cost_per_token(self) -> float: ...


class CheapModel:
    cost_per_token = 0.0001

    async def generate(self, prompt: str) -> str:
        return f"[Cheap] Quick answer to: {prompt}"


class ExpensiveModel:
    cost_per_token = 0.03

    async def generate(self, prompt: str) -> str:
        return f"[Expensive] Detailed, nuanced analysis of: {prompt}"


class Router:
    def __init__(self):
        self.cheap = CheapModel()
        self.expensive = ExpensiveModel()
        self.total_cost = 0.0

    def estimate_complexity(self, prompt: str) -> str:
        # Simple heuristic: Length or keywords
        if len(prompt) > 20 or "analyze" in prompt.lower():
            return "high"
        return "low"

    async def route(self, prompt: str) -> str:
        complexity = self.estimate_complexity(prompt)

        if complexity == "low":
            model = self.cheap
            print(f"📉 Routing to Cheap Model (Complexity: Low)")
        else:
            model = self.expensive
            print(f"📈 Routing to Expensive Model (Complexity: High)")

        response = await model.generate(prompt)

        # Track cost (simulated 100 tokens)
        self.total_cost += model.cost_per_token * 100
        return response


async def main():
    router = Router()

    tasks = [
        "Hi there",
        "What is 2+2?",
        "Analyze the geopolitical implications of quantum computing",
        "Summarize this short text",
        "Write a complex sonnet about entropy",
    ]

    print("--- Processing Tasks ---")
    for task in tasks:
        print(f"\nTask: '{task}'")
        response = await router.route(task)
        print(f"Response: {response}")

    print(f"\n💰 Total Cost: ${router.total_cost:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
