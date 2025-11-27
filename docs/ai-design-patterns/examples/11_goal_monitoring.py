"""
Goal Monitoring Pattern Example
-------------------------------
This script demonstrates the Goal Setting & Monitoring pattern:
Set Goals -> Execute -> Monitor -> Adjust

It simulates an agent trying to complete a checklist of tasks.
"""

import asyncio
from typing import List, Dict


class GoalMonitor:
    def __init__(self, goals: List[str]):
        self.goals = {g: False for g in goals}

    def mark_done(self, goal: str):
        if goal in self.goals:
            self.goals[goal] = True
            print(f"✅ Goal Completed: {goal}")

    def check_status(self):
        pending = [g for g, done in self.goals.items() if not done]
        if not pending:
            print("🎉 All goals achieved!")
            return True
        print(f"⚠️ Pending Goals: {pending}")
        return False


async def agent_work(monitor: GoalMonitor):
    # Simulating work steps
    steps = [
        ("Research", "Research market trends"),
        ("Draft", "Draft content"),
        ("Review", "Review draft"),  # Oops, missed one goal initially
        ("Publish", "Publish post"),
    ]

    for action, goal_desc in steps:
        print(f"\n🤖 Agent Action: {action}")
        await asyncio.sleep(0.5)

        # Check if action completed a goal (Simulated logic)
        if action == "Research":
            monitor.mark_done("Gather Data")
        elif action == "Draft":
            monitor.mark_done("Write Draft")
        elif action == "Publish":
            monitor.mark_done("Publish")

        # Monitor checks status
        if monitor.check_status():
            break


async def main():
    goals = ["Gather Data", "Write Draft", "Publish"]
    monitor = GoalMonitor(goals)

    print("--- Starting Task ---")
    await agent_work(monitor)


if __name__ == "__main__":
    asyncio.run(main())
