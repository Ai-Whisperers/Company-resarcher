"""
Multi-Agent Pattern Example
---------------------------
This script demonstrates the Multi-Agent pattern:
Orchestrator -> Agent A -> Agent B -> Result

It simulates a Researcher and a Writer working together.
"""

import asyncio
from dataclasses import dataclass

# --- Agents ---


async def researcher_agent(topic: str) -> str:
    print(f"🔎 [Researcher] Gathering info on '{topic}'...")
    await asyncio.sleep(0.5)
    return f"Key facts about {topic}: 1. Popular, 2. Versatile, 3. Powerful."


async def writer_agent(facts: str) -> str:
    print(f"✍️ [Writer] Writing article based on facts...")
    await asyncio.sleep(0.5)
    return f"Title: The Power of Python\n\nSummary: {facts}\n\nConclusion: It's great!"


# --- Orchestrator ---


async def orchestrator(topic: str):
    print(f"\n--- Orchestrating Task: Write about {topic} ---")

    # 1. Call Researcher
    facts = await researcher_agent(topic)
    print(f"   -> Info gathered: {facts}")

    # 2. Call Writer
    article = await writer_agent(facts)

    print("\n✅ Final Output:")
    print(article)


async def main():
    await orchestrator("Python")


if __name__ == "__main__":
    asyncio.run(main())
