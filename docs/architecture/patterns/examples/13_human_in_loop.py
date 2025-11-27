"""
Human-in-the-Loop Pattern Example
---------------------------------
This script demonstrates the HITL pattern:
Execute -> Pause -> Human Review -> Resume

It simulates a critical action (Deploy) requiring approval.
"""

import asyncio


async def critical_action():
    print("🚀 Initiating Deployment Sequence...")
    await asyncio.sleep(0.5)
    print("⚠️  PAUSED: Waiting for Human Approval.")

    # Simulate waiting for user input
    # In a real app, this would be an API endpoint or UI callback
    user_input = input("\n>> Do you authorize deployment? (yes/no): ").strip().lower()

    if user_input == "yes":
        print("✅ Approval Received.")
        print("🚀 Deploying to Production...")
        await asyncio.sleep(1)
        print("🎉 Deployment Complete!")
    else:
        print("❌ Approval Denied.")
        print("🛑 Deployment Aborted.")


async def main():
    print("--- Workflow Started ---")
    await critical_action()
    print("--- Workflow Ended ---")


if __name__ == "__main__":
    # Note: input() is blocking, but fine for this simple CLI demo
    asyncio.run(main())
