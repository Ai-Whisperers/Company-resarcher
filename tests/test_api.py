from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_start_research_validation():
    # Test missing required field
    response = client.post("/api/v1/research", json={})
    assert response.status_code == 422


if __name__ == "__main__":
    test_health_check()
    test_start_research_validation()
    print("API Tests Passed!")
