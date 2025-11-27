"""
Prioritization Pattern Example
------------------------------
This script demonstrates the Prioritization pattern:
Tasks -> Score -> Priority Queue -> Execute

It simulates a task queue where older tasks get a priority boost (Aging) to prevent starvation.
"""

import asyncio
import heapq
import time
from dataclasses import dataclass, field


@dataclass(order=True)
class Task:
    priority: int
    name: str = field(compare=False)
    created_at: float = field(compare=False, default_factory=time.time)


class PriorityQueue:
    def __init__(self):
        self.queue = []

    def add_task(self, name: str, priority: int):
        # Python's heapq is a min-heap, so we negate priority for max-heap behavior
        # Higher number = Higher priority
        task = Task(-priority, name)
        heapq.heappush(self.queue, task)
        print(f"📥 Added: {name} (Priority: {priority})")

    def get_next_task(self):
        if not self.queue:
            return None
        return heapq.heappop(self.queue)

    def age_tasks(self):
        # Boost priority of waiting tasks to prevent starvation
        # In a real heap, re-heapifying is O(N), so do this periodically
        print("⏳ Aging tasks (Boosting priority)...")
        new_queue = []
        while self.queue:
            task = heapq.heappop(self.queue)
            # Increase priority (make it more negative)
            task.priority -= 1
            heapq.heappush(new_queue, task)
        self.queue = new_queue


async def worker(queue: PriorityQueue):
    print("\n--- Worker Started ---")

    # Process 3 tasks
    for _ in range(3):
        task = queue.get_next_task()
        if task:
            # Remember to negate priority back for display
            print(f"⚙️  Processing: {task.name} (Effective Priority: {-task.priority})")
        else:
            print("💤 Queue empty.")
        await asyncio.sleep(0.5)

    # Simulate time passing and aging
    queue.age_tasks()

    # Process remaining
    print("\n--- Worker Resumed ---")
    while True:
        task = queue.get_next_task()
        if not task:
            break
        print(f"⚙️  Processing: {task.name} (Effective Priority: {-task.priority})")


async def main():
    pq = PriorityQueue()

    # Add tasks in random order
    pq.add_task("Low Value Task", 1)
    pq.add_task("Critical Bug Fix", 10)
    pq.add_task("Medium Feature", 5)
    pq.add_task("Another Low Task", 1)

    await worker(pq)


if __name__ == "__main__":
    asyncio.run(main())
