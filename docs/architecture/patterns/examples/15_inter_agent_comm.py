"""
Inter-Agent Communication Pattern Example
-----------------------------------------
This script demonstrates the Inter-Agent Communication pattern:
Agent A -> Message Bus -> Agent B

It simulates a simple Pub/Sub system.
"""

import asyncio
from typing import Dict, List, Callable, Any


class MessageBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, handler: Callable):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)
        print(f"📡 Subscribed to '{topic}'")

    async def publish(self, topic: str, message: Any):
        print(f"📣 Publishing to '{topic}': {message}")
        if topic in self.subscribers:
            for handler in self.subscribers[topic]:
                await handler(message)


class Agent:
    def __init__(self, name: str, bus: MessageBus):
        self.name = name
        self.bus = bus

    async def listen(self, topic: str):
        self.bus.subscribe(topic, self.handle_message)

    async def handle_message(self, message: Any):
        print(f"🤖 {self.name} received: {message}")

    async def say(self, topic: str, content: str):
        await self.bus.publish(topic, {"sender": self.name, "content": content})


async def main():
    bus = MessageBus()

    # Create agents
    agent_a = Agent("Agent A", bus)
    agent_b = Agent("Agent B", bus)

    # Subscribe to topics
    await agent_b.listen("news")
    await agent_a.listen("alerts")

    # Send messages
    print("\n--- Interaction 1 ---")
    await agent_a.say("news", "New market data available")

    print("\n--- Interaction 2 ---")
    await agent_b.say("alerts", "System overload warning")


if __name__ == "__main__":
    asyncio.run(main())
