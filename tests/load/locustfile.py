"""
Locust load testing configuration for Company Researcher API.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
"""

from locust import HttpUser, task, between, events
import json
import random
import string


# =============================================================================
# Test Data Generators
# =============================================================================


def random_company_name():
    """Generate a random company name."""
    prefixes = ["Tech", "Global", "Advanced", "Premier", "Elite", "Smart", "Digital"]
    suffixes = ["Corp", "Inc", "Solutions", "Systems", "Industries", "Group", "Labs"]
    return f"{random.choice(prefixes)} {random_string(5)} {random.choice(suffixes)}"


def random_string(length=8):
    """Generate a random string."""
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_url():
    """Generate a random company URL."""
    domain = random_string(10).lower()
    return f"https://{domain}.com"


# =============================================================================
# Load Test User Classes
# =============================================================================


class APIUser(HttpUser):
    """
    Simulates a typical API user making research requests.
    """

    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a simulated user starts."""
        self.created_tasks = []

    @task(10)
    def health_check(self):
        """
        High-frequency health check requests.
        Weight: 10 (most common operation)
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(5)
    def detailed_health_check(self):
        """
        Detailed health check including dependency checks.
        Weight: 5
        """
        with self.client.get("/health/detailed", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def start_research(self):
        """
        Start a new research task.
        Weight: 3
        """
        payload = {
            "company_name": random_company_name(),
            "url": random_url(),
            "industry": random.choice(["Technology", "Finance", "Healthcare", "Retail"]),
            "country": random.choice(["USA", "UK", "Germany", "Japan"]),
        }

        with self.client.post(
            "/api/v1/research",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    self.created_tasks.append(data["task_id"])
                    response.success()
                else:
                    response.failure("No task_id in response")
            elif response.status_code == 429:
                # Rate limited - expected under load
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(8)
    def check_task_status(self):
        """
        Check status of a previously created task.
        Weight: 8 (common polling operation)
        """
        if not self.created_tasks:
            return

        task_id = random.choice(self.created_tasks)

        with self.client.get(
            f"/api/v1/research/{task_id}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Task may have been cleaned up
                self.created_tasks.remove(task_id)
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def check_nonexistent_task(self):
        """
        Check status of a non-existent task (404 scenario).
        Weight: 1
        """
        fake_task_id = f"fake-{random_string(32)}"

        with self.client.get(
            f"/api/v1/research/{fake_task_id}",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")


class AggressiveUser(HttpUser):
    """
    Simulates an aggressive user making rapid requests.
    Used for stress testing and rate limit validation.
    """

    wait_time = between(0.1, 0.5)

    @task
    def rapid_health_check(self):
        """Rapid health check requests."""
        self.client.get("/health")

    @task
    def rapid_research_requests(self):
        """Rapid research requests to test rate limiting."""
        payload = {
            "company_name": random_company_name(),
        }

        with self.client.post(
            "/api/v1/research",
            json=payload,
            catch_response=True,
        ) as response:
            # Both 200 and 429 are acceptable
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class ValidationUser(HttpUser):
    """
    Tests validation and error handling under load.
    """

    wait_time = between(0.5, 2)

    @task(3)
    def empty_company_name(self):
        """Test empty company name validation."""
        with self.client.post(
            "/api/v1/research",
            json={"company_name": ""},
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Expected 422, got {response.status_code}")

    @task(3)
    def invalid_url(self):
        """Test invalid URL validation."""
        with self.client.post(
            "/api/v1/research",
            json={"company_name": "Test Corp", "url": "not-a-url"},
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Expected 422, got {response.status_code}")

    @task(2)
    def missing_required_field(self):
        """Test missing required field."""
        with self.client.post(
            "/api/v1/research",
            json={},
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Expected 422, got {response.status_code}")

    @task(2)
    def long_company_name(self):
        """Test excessively long company name."""
        with self.client.post(
            "/api/v1/research",
            json={"company_name": "A" * 500},
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Expected 422, got {response.status_code}")


# =============================================================================
# Event Handlers
# =============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("Load test completed.")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
