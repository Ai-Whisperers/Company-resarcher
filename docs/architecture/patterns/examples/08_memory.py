"""
Memory Pattern Example
----------------------
This script demonstrates the Memory pattern:
Short-term (Session) vs Long-term (Persistent)

It simulates a chat agent that remembers user details.
"""

import asyncio
from typing import Dict, List


class MemorySystem:
    def __init__(self):
        self.short_term: List[str] = []  # Current conversation
        self.long_term: Dict[str, str] = {}  # Persistent facts

    def add_message(self, role: str, content: str):
        self.short_term.append(f"{role}: {content}")

    def store_fact(self, key: str, value: str):
        print(f"💾 Storing Long-Term Fact: {key} = {value}")
        self.long_term[key] = value

    def retrieve_context(self) -> str:
        # Combine recent messages + relevant facts
        context = "--- Long Term Memory ---\n"
        for k, v in self.long_term.items():
            context += f"{k}: {v}\n"

        context += "\n--- Short Term History ---\n"
        context += "\n".join(self.short_term[-5:])  # Last 5 messages
        return context


# --- Mock Agent ---


async def chat(user_input: str, memory: MemorySystem):
    # 1. Add to short-term
    memory.add_message("User", user_input)

    # 2. Check for facts to store (Simulated extraction)
    if "my name is" in user_input.lower():
        name = user_input.split("is")[-1].strip()
        memory.store_fact("User Name", name)

    # 3. Retrieve context
    context = memory.retrieve_context()

    # 4. Generate response (Simulated)
    print(f"\n🤖 AI Context:\n{context}")
    response = "I understand."
    if "User Name" in memory.long_term:
        response = f"Hello, {memory.long_term['User Name']}!"

    memory.add_message("AI", response)
    print(f"👉 AI Response: {response}")


async def main():
    mem = MemorySystem()

    await chat("Hi, my name is Alice.", mem)
    await chat("What is the weather?", mem)
    await chat("Do you remember who I am?", mem)


if __name__ == "__main__":
    asyncio.run(main())
