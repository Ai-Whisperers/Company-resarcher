import os
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_missing_api_key_returns_401(monkeypatch):
    """Test that missing API key returns 401 when auth is enabled."""
    # Enable API key authentication
    monkeypatch.setenv("API_KEY", "test-api-key-12345")

    # Request without API key should return 401
    response = client.post("/api/v1/research", json={"company_name": "Test"})
    assert response.status_code == 401


def test_start_research_validation_with_auth(monkeypatch):
    """Test validation errors return 422 after authentication (BUG-002)."""
    # Set and use API key for authentication
    test_api_key = "test-api-key-12345"
    monkeypatch.setenv("API_KEY", test_api_key)

    # Test missing required field - should get 422 validation error
    response = client.post(
        "/api/v1/research",
        json={},
        headers={"X-API-Key": test_api_key}
    )
    assert response.status_code == 422


def test_start_research_validation_no_auth_configured():
    """Test validation errors when auth is disabled (no API_KEY env)."""
    # When API_KEY is not set, auth is disabled and we should get 422 for validation
    # Note: This depends on the test environment not having API_KEY set
    if os.getenv("API_KEY"):
        pytest.skip("API_KEY is set, cannot test no-auth mode")

    response = client.post("/api/v1/research", json={})
    assert response.status_code == 422


if __name__ == "__main__":
    test_health_check()
    print("API Tests Passed!")
