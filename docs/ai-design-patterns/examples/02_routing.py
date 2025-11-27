"""
Routing Pattern Example
-----------------------
This script demonstrates the Routing pattern:
Query -> Router -> Specific Handler

It simulates a semantic router that classifies user intent.
"""

import asyncio
from typing import Callable, Dict

# --- Mock Handlers ---


async def handle_financial(query: str):
    print(f"💰 Financial Agent processing: '{query}'")
    return "Financial Report Generated"


async def handle_creative(query: str):
    print(f"🎨 Creative Agent processing: '{query}'")
    return "Creative Assets Generated"


async def handle_support(query: str):
    print(f"🛡️ Support Agent processing: '{query}'")
    return "Support Ticket Created"


async def handle_fallback(query: str):
    print(f"❓ Fallback Agent processing: '{query}'")
    return "I'm not sure how to help with that."


# --- The Router ---


class Router:
    def __init__(self):
        # In a real app, this would be an LLM or Embedding-based classifier
        self.routes: Dict[str, Callable] = {
            "price": handle_financial,
            "cost": handle_financial,
            "revenue": handle_financial,
            "design": handle_creative,
            "logo": handle_creative,
            "write": handle_creative,
            "help": handle_support,
            "issue": handle_support,
        }

    async def route_and_execute(self, query: str):
        print(f"\nIncoming Query: '{query}'")

        # Simple keyword matching for demonstration
        handler = handle_fallback
        for keyword, route_handler in self.routes.items():
            if keyword in query.lower():
                handler = route_handler
                break

        # Execute the selected handler
        result = await handler(query)
        print(f"✅ Result: {result}")


# --- Main Execution ---


async def main():
    router = Router()

    queries = [
        "What is the revenue for Q3?",
        "Design a new logo for the product",
        "I need help with my account issue",
        "Tell me a joke",  # Fallback
    ]

    for q in queries:
        await router.route_and_execute(q)


if __name__ == "__main__":
    asyncio.run(main())
