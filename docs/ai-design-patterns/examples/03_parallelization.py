"""
Parallelization Pattern Example
-------------------------------
This script demonstrates the Parallelization pattern:
Split -> Parallel Exec -> Merge

It uses asyncio.gather with a Semaphore to control concurrency.
"""

import asyncio
import time
import random

# --- Mock Task ---


async def fetch_data(id: int, semaphore: asyncio.Semaphore):
    async with semaphore:
        print(f"🚀 Task {id} started (Active: {max_active(semaphore)})")

        # Simulate network latency (0.5 to 2.0 seconds)
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

        # Simulate occasional failure
        if random.random() < 0.1:
            print(f"❌ Task {id} failed!")
            raise Exception(f"Network Error on Task {id}")

        print(f"✅ Task {id} completed in {delay:.2f}s")
        return f"Data {id}"


def max_active(sem: asyncio.Semaphore):
    # Helper to see how many slots are used (approximate)
    return sem._value


# --- Orchestrator ---


async def main():
    # Configuration
    TOTAL_TASKS = 10
    MAX_CONCURRENT = 3

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    print(f"--- Starting {TOTAL_TASKS} tasks (Max Parallel: {MAX_CONCURRENT}) ---")
    start_time = time.time()

    # Create tasks
    tasks = [fetch_data(i, semaphore) for i in range(TOTAL_TASKS)]

    # Execute with error handling (return_exceptions=True)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    # Process Results
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    print("\n--- Summary ---")
    print(f"Total Time: {duration:.2f}s")
    print(f"Successes: {len(successes)}")
    print(f"Failures:  {len(failures)}")
    print(f"Results:   {successes}")


if __name__ == "__main__":
    asyncio.run(main())
