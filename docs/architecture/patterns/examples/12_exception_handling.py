"""
Exception Handling Pattern Example
----------------------------------
This script demonstrates the Exception Handling pattern:
Try -> Catch -> Retry (with Backoff) -> Fallback

It simulates an unstable API call.
"""

import asyncio
import random
from typing import Callable, Any


class ServiceError(Exception):
    pass


# --- Unstable Service ---


async def unstable_api():
    """Simulates an API that fails 70% of the time."""
    if random.random() < 0.7:
        print("   ❌ API Failed!")
        raise ServiceError("Connection timeout")
    print("   ✅ API Success!")
    return "Data Payload"


# --- Resilience Logic ---


async def retry_with_backoff(func: Callable, max_retries: int = 3) -> Any:
    for i in range(max_retries):
        try:
            print(f"Attempt {i+1}...")
            return await func()
        except ServiceError:
            if i == max_retries - 1:
                raise  # Re-raise if last attempt

            wait_time = 0.5 * (2**i)  # Exponential backoff
            print(f"   ⚠️ Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)


async def execute_safe():
    print("--- calling Unstable API ---")
    try:
        result = await retry_with_backoff(unstable_api)
        print(f"🎉 Final Result: {result}")
    except ServiceError:
        print("💀 All retries failed. Using Fallback.")
        print("🛡️ Fallback Result: Cached Data")


async def main():
    # Run it a few times to see different outcomes
    for _ in range(3):
        await execute_safe()
        print("-" * 20)


if __name__ == "__main__":
    asyncio.run(main())
