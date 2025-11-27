"""
Reflection Pattern Example
--------------------------
This script demonstrates the Reflection pattern:
Generate -> Critique -> Improve

It simulates an AI writing code and then fixing it based on a critique.
"""

import asyncio
from dataclasses import dataclass


@dataclass
class CodeDraft:
    code: str
    score: int
    critique: str


# --- Mock AI ---


async def generate_code(prompt: str) -> str:
    print(f"📝 Generating code for: '{prompt}'")
    # Intentionally buggy initial code
    return "def add(a, b): return a - b  # Bug: Subtraction instead of addition"


async def critique_code(code: str) -> tuple[int, str]:
    print(f"🧐 Critiquing code:\n{code}")
    if "-" in code:
        return 2, "The function subtracts instead of adding. Replace '-' with '+'."
    return 10, "The code looks correct."


async def improve_code(code: str, critique: str) -> str:
    print(f"🔧 Improving code based on: '{critique}'")
    if "Replace '-' with '+'" in critique:
        return code.replace("-", "+").replace(
            "Bug: Subtraction instead of addition", "Fixed: Addition"
        )
    return code


# --- Reflection Loop ---


async def main():
    prompt = "Write a python function to add two numbers."

    # 1. Initial Generation
    current_code = await generate_code(prompt)

    MAX_ITERATIONS = 3
    for i in range(MAX_ITERATIONS):
        print(f"\n--- Iteration {i+1} ---")

        # 2. Critique
        score, feedback = await critique_code(current_code)
        print(f"Score: {score}/10")

        if score >= 8:
            print("✅ Quality threshold met!")
            break

        # 3. Improve
        current_code = await improve_code(current_code, feedback)

    print(f"\n🏆 Final Code:\n{current_code}")


if __name__ == "__main__":
    asyncio.run(main())
