"""
Prompt Chaining Example
-----------------------
This script demonstrates the Prompt Chaining pattern:
Input -> Generator -> Critique -> Refine -> Output

It uses a Mock AI Client to be runnable without API keys.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, Any


# --- Mock AI Client ---
class MockAI:
    async def generate(self, prompt: str) -> str:
        print(f"\n🤖 AI received prompt:\n{prompt[:50]}...")
        if "Write a haiku" in prompt:
            return "Code flows like a stream,\nBugs vanish in the morning,\nDeploy with a smile."
        elif "Critique this haiku" in prompt:
            return "The last line has 6 syllables, not 5. 'Smile' is 1, but 'morning' makes it tricky."
        elif "Fix the haiku" in prompt:
            return "Code flows like a stream,\nBugs vanish in the morning,\nShip it with a grin."
        return "I don't know."


# --- The Chain Steps ---


async def step_1_generate(topic: str, ai: MockAI) -> str:
    print(f"\n--- Step 1: Generate ({topic}) ---")
    prompt = f"Write a haiku about {topic}."
    result = await ai.generate(prompt)
    print(f"Output: {result}")
    return result


async def step_2_critique(haiku: str, ai: MockAI) -> str:
    print("\n--- Step 2: Critique ---")
    prompt = f"Critique this haiku for syllable count (5-7-5):\n{haiku}"
    result = await ai.generate(prompt)
    print(f"Output: {result}")
    return result


async def step_3_refine(haiku: str, critique: str, ai: MockAI) -> str:
    print("\n--- Step 3: Refine ---")
    prompt = f"Fix the haiku based on this critique:\nOriginal: {haiku}\nCritique: {critique}"
    result = await ai.generate(prompt)
    print(f"Output: {result}")
    return result


# --- Orchestrator ---


async def run_chain(topic: str):
    ai = MockAI()

    # Execute Chain
    draft = await step_1_generate(topic, ai)
    critique = await step_2_critique(draft, ai)
    final = await step_3_refine(draft, critique, ai)

    print(f"\n✅ Final Result:\n{final}")


if __name__ == "__main__":
    asyncio.run(run_chain("Software Engineering"))
