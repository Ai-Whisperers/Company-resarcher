import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8001"


def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("[SUCCESS] Health check passed")
        else:
            print(f"[FAILURE] Health check failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAILURE] Could not connect to API: {e}")
        sys.exit(1)


def test_research_flow():
    # 1. Start Research
    payload = {
        "company_name": "Test Company",
        "url": "https://example.com",
        "industry": "Technology",
        "country": "USA",
    }
    print("Starting research task...")
    response = requests.post(f"{BASE_URL}/api/v1/research", json=payload)

    if response.status_code != 200:
        print(f"[FAILURE] Start research failed: {response.text}")
        sys.exit(1)

    data = response.json()
    task_id = data["task_id"]
    print(f"[SUCCESS] Task started with ID: {task_id}")

    # 2. Poll Status
    print("Polling status...")
    for _ in range(10):
        response = requests.get(f"{BASE_URL}/api/v1/research/{task_id}")
        if response.status_code != 200:
            print(f"[FAILURE] Get status failed: {response.text}")
            break

        status_data = response.json()
        status = status_data["status"]
        print(f"Current status: {status}")

        if status in ["completed", "failed"]:
            print(f"[SUCCESS] Task finished with status: {status}")
            if status == "completed":
                print(f"Result: {status_data.get('result')}")
            else:
                print(f"Error: {status_data.get('error')}")
            return

        time.sleep(2)

    print("[WARNING] Task timed out or is still running")


if __name__ == "__main__":
    # Wait for server to start
    time.sleep(5)
    test_health()
    test_research_flow()
