"""
Planning Pattern Example
------------------------
This script demonstrates the Planning pattern:
Goal -> Generate Plan -> Execute Steps

It simulates an agent creating a travel itinerary.
"""

import asyncio
from typing import List, Dict

# --- Mock AI Planner ---


async def generate_plan(goal: str) -> List[str]:
    print(f"🧠 Generating plan for: '{goal}'")
    # Simulating LLM output
    if "Tokyo" in goal:
        return [
            "Book flight to Narita",
            "Reserve hotel in Shinjuku",
            "Buy JR Pass",
            "Pack luggage",
        ]
    return ["Research destination", "Book travel", "Pack"]


# --- Executor ---


async def execute_step(step: str):
    print(f"   ▶️ Executing: {step}...")
    await asyncio.sleep(0.5)  # Simulate work
    print(f"   ✅ Completed: {step}")


# --- Orchestrator ---


async def run_planner(goal: str):
    print(f"\n--- Goal: {goal} ---")

    # 1. Plan
    plan = await generate_plan(goal)
    print(f"📋 Plan Created: {len(plan)} steps")

    # 2. Execute
    for i, step in enumerate(plan):
        print(f"Step {i+1}/{len(plan)}")
        await execute_step(step)

    print("🎉 Goal Achieved!")


async def main():
    await run_planner("Trip to Tokyo for 5 days")


if __name__ == "__main__":
    asyncio.run(main())
