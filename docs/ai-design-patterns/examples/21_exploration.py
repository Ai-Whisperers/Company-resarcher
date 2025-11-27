"""
Exploration Pattern Example
---------------------------
This script demonstrates the Exploration & Discovery pattern:
Topic -> Expand -> Map -> Explore

It simulates a Breadth-First Search (BFS) to map out related concepts from a starting topic.
"""

import asyncio
from typing import List, Set


class ExplorerAgent:
    async def expand(self, topic: str) -> List[str]:
        # Simulate generating related topics (Mock LLM)
        print(f"🔍 Exploring: '{topic}'")
        await asyncio.sleep(0.5)

        related_map = {
            "Coffee": ["Caffeine", "Farming", "Culture"],
            "Caffeine": ["Energy", "Sleep", "Chemistry"],
            "Farming": ["Sustainability", "Climate", "Trade"],
            "Culture": ["Rituals", "History", "Art"],
            "Energy": ["Work", "Sports"],
            "Sleep": ["Dreams", "Health"],
        }

        return related_map.get(topic, [])


async def map_topic_space(start_topic: str, max_depth: int = 2):
    explorer = ExplorerAgent()
    visited: Set[str] = set()
    queue = [(start_topic, 0)]

    print(f"🚀 Starting exploration of '{start_topic}' (Depth: {max_depth})\n")

    while queue:
        current_topic, depth = queue.pop(0)

        if current_topic in visited:
            continue
        visited.add(current_topic)

        indent = "  " * depth
        print(f"{indent}📍 Node: {current_topic}")

        if depth < max_depth:
            related = await explorer.expand(current_topic)
            for topic in related:
                if topic not in visited:
                    queue.append((topic, depth + 1))

    print(f"\n✅ Exploration Complete. Discovered {len(visited)} concepts.")


async def main():
    await map_topic_space("Coffee", max_depth=2)


if __name__ == "__main__":
    asyncio.run(main())
