"""
Learning Pattern Example
------------------------
This script demonstrates the Learning & Adaptation pattern:
Execute -> Feedback -> Update Rules -> Execute

It simulates an agent that learns formatting rules from user feedback.
"""

import asyncio
from typing import List


class LearningAgent:
    def __init__(self):
        self.rules: List[str] = []

    def add_rule(self, rule: str):
        print(f"🧠 Learning new rule: '{rule}'")
        self.rules.append(rule)

    def generate(self, prompt: str) -> str:
        response = f"Response to '{prompt}'"

        # Apply learned rules
        for rule in self.rules:
            if "uppercase" in rule.lower():
                response = response.upper()
            if "exclamation" in rule.lower():
                response += "!"
            if "emoji" in rule.lower():
                response = "🤖 " + response

        return response


async def main():
    agent = LearningAgent()

    # 1. Initial State
    print("--- Round 1 (No Rules) ---")
    print(f"Output: {agent.generate('Hello')}\n")

    # 2. Feedback & Learning
    print("--- Feedback Received: 'Please use uppercase.' ---")
    agent.add_rule("Always use uppercase")

    # 3. Adapted State
    print("--- Round 2 (After Learning) ---")
    print(f"Output: {agent.generate('Hello')}\n")

    # 4. More Learning
    print("--- Feedback Received: 'Add an emoji at the start.' ---")
    agent.add_rule("Start with robot emoji")

    # 5. Final State
    print("--- Round 3 (Cumulative Learning) ---")
    print(f"Output: {agent.generate('Hello')}\n")


if __name__ == "__main__":
    asyncio.run(main())
