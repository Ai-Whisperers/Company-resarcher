"""
Evaluation Pattern Example
--------------------------
This script demonstrates the Evaluation & Monitoring pattern:
Output -> LLM Judge -> Score

It simulates an LLM grading the quality of text summaries.
"""

import asyncio
import random


class LLMJudge:
    async def evaluate(self, input_text: str, output_text: str, criteria: str) -> dict:
        # Simulate LLM evaluation logic
        print(f"⚖️  Judging output based on: {criteria}")

        # Simple heuristic simulation
        score = 0
        reasoning = ""

        if "concise" in criteria.lower():
            if len(output_text) < 50:
                score = 5
                reasoning = "Excellent conciseness."
            elif len(output_text) < 100:
                score = 3
                reasoning = "Acceptable length."
            else:
                score = 1
                reasoning = "Too verbose."
        else:
            score = random.randint(1, 5)
            reasoning = "General quality assessment."

        return {"score": score, "reasoning": reasoning}


async def main():
    judge = LLMJudge()

    input_text = "The quick brown fox jumps over the lazy dog."

    # Candidate 1
    output_1 = "Fox jumps dog."
    print(f"\n📝 Candidate 1: '{output_1}'")
    eval_1 = await judge.evaluate(input_text, output_1, "Be concise")
    print(f"   -> Score: {eval_1['score']}/5 ({eval_1['reasoning']})")

    # Candidate 2
    output_2 = "The quick brown fox, which is a type of animal, jumped over the lazy dog, which is another animal."
    print(f"\n📝 Candidate 2: '{output_2}'")
    eval_2 = await judge.evaluate(input_text, output_2, "Be concise")
    print(f"   -> Score: {eval_2['score']}/5 ({eval_2['reasoning']})")


if __name__ == "__main__":
    asyncio.run(main())
