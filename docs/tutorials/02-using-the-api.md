# Tutorial: Using the REST API

**Time:** 20-30 minutes
**Level:** Intermediate
**Prerequisites:** Completed [Your First Research](./01-your-first-research.md), basic HTTP/REST knowledge

## What You'll Learn

- How to start the API server
- How to initiate research via HTTP requests
- How to poll for results
- How to build a simple client application

---

## Before You Start

Ensure you have:
- Company Researcher installed and configured
- API keys set up in `.env`
- A tool for HTTP requests (curl, Postman, or Python requests)

---

## Step 1: Start the API Server

Open a terminal in the project directory:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start the server
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

> **Note:** Keep this terminal running. Open a new terminal for the next steps.

---

## Step 2: Verify the Server

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

For detailed health:
```bash
curl http://localhost:8000/health/detailed
```

**Expected Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "config": {"status": "ok"},
    "ai_provider": {"status": "ok"}
  }
}
```

---

## Step 3: Explore the API Documentation

Open your browser and visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These pages show all available endpoints and let you try them interactively.

---

## Step 4: Start a Research Task

Send a POST request to start research:

```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Stripe",
    "url": "https://stripe.com",
    "industry": "Fintech",
    "country": "USA"
  }'
```

**Expected Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Research task started successfully."
}
```

**Save the `task_id`** - you'll need it to check results!

---

## Step 5: Check Task Status

Poll the status endpoint with your task ID:

```bash
curl http://localhost:8000/api/v1/research/550e8400-e29b-41d4-a716-446655440000
```

**Response (In Progress):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "result": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "company_name": "Stripe",
    "output_path": "output/Stripe/",
    "reports_generated": 15,
    "sources_count": 42
  },
  "error": null
}
```

---

## Step 6: Build a Polling Script

Create a file `poll_research.py`:

```python
#!/usr/bin/env python3
"""
Poll a research task until completion.
Usage: python poll_research.py <task_id>
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000"

def poll_task(task_id: str, interval: int = 10, timeout: int = 1800):
    """Poll until task completes or times out."""
    start = time.time()

    while True:
        # Check timeout
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"❌ Timeout after {timeout} seconds")
            return None

        # Get status
        response = requests.get(f"{BASE_URL}/api/v1/research/{task_id}")

        if response.status_code == 404:
            print(f"❌ Task not found: {task_id}")
            return None

        data = response.json()
        status = data["status"]

        # Handle completion
        if status == "completed":
            print(f"✅ Research completed!")
            print(f"   Output: {data['result'].get('output_path')}")
            return data["result"]

        elif status == "failed":
            print(f"❌ Research failed: {data.get('error')}")
            return None

        # Still running
        print(f"⏳ Status: {status} ({int(elapsed)}s elapsed)")
        time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python poll_research.py <task_id>")
        sys.exit(1)

    task_id = sys.argv[1]
    result = poll_task(task_id)

    if result:
        print(f"\n📊 Results:")
        for key, value in result.items():
            print(f"   {key}: {value}")
```

Run it:
```bash
python poll_research.py 550e8400-e29b-41d4-a716-446655440000
```

---

## Step 7: Build a Complete Client

Create `research_client.py`:

```python
#!/usr/bin/env python3
"""
Complete research client with start and poll.
Usage: python research_client.py "Company Name" [--url URL]
"""
import argparse
import time
import requests

BASE_URL = "http://localhost:8000"

def start_research(company_name: str, url: str = None, industry: str = None):
    """Start a research task."""
    payload = {"company_name": company_name}
    if url:
        payload["url"] = url
    if industry:
        payload["industry"] = industry

    response = requests.post(
        f"{BASE_URL}/api/v1/research",
        json=payload
    )

    if response.status_code != 200:
        error = response.json().get("detail", "Unknown error")
        raise Exception(f"Failed to start: {error}")

    return response.json()["task_id"]

def wait_for_result(task_id: str, interval: int = 10):
    """Poll until complete."""
    print(f"📋 Task ID: {task_id}")

    while True:
        response = requests.get(f"{BASE_URL}/api/v1/research/{task_id}")
        data = response.json()

        if data["status"] == "completed":
            return data["result"]
        elif data["status"] == "failed":
            raise Exception(data.get("error", "Unknown error"))

        print(f"   Status: {data['status']}...")
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Research a company")
    parser.add_argument("company", help="Company name")
    parser.add_argument("--url", help="Company website URL")
    parser.add_argument("--industry", help="Industry sector")
    args = parser.parse_args()

    print(f"🔍 Starting research for: {args.company}")

    try:
        # Start research
        task_id = start_research(args.company, args.url, args.industry)

        # Wait for result
        result = wait_for_result(task_id)

        print(f"\n✅ Research completed!")
        print(f"📁 Output: {result.get('output_path')}")
        print(f"📄 Reports: {result.get('reports_generated')}")
        print(f"🔗 Sources: {result.get('sources_count')}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

Run it:
```bash
python research_client.py "Zoom" --url "https://zoom.us" --industry "Video Conferencing"
```

---

## Step 8: Handle Errors

Common errors and handling:

### Rate Limiting (429)

```python
def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 429:
            wait = 10 * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### Invalid Input (400/422)

```python
response = requests.post(url, json=payload)

if response.status_code in (400, 422):
    error = response.json()
    print(f"Invalid input: {error['detail']}")
```

---

## Verification Checklist

After completing this tutorial:

- [ ] API server starts successfully
- [ ] Health endpoint returns healthy
- [ ] Can start a research task via API
- [ ] Can poll for task status
- [ ] Completed task returns results
- [ ] Built a working client script

---

## Next Steps

- **Add authentication** - See [Security Guide](../guides/SECURITY.md)
- **Deploy to production** - See [Deployment Guide](../deployment/README.md)
- **Optimize performance** - See [Performance Guide](../guides/PERFORMANCE.md)

---

## Summary

You've learned how to:
- ✅ Start and verify the API server
- ✅ Explore API documentation
- ✅ Start research via HTTP
- ✅ Poll for results
- ✅ Handle errors gracefully
- ✅ Build a complete client

**Well done!** You can now integrate Company Researcher into any application.
