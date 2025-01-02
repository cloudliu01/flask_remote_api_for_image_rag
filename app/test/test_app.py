import pytest
from app import create_app

@pytest.fixture
def client():
    """Fixture to set up a test client for the app."""
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "OK"
    assert response.json["message"] == "API is running"

def test_handle_data(client):
    """Test the /api/data endpoint with valid POST data."""
    payload = {"key": "value"}
    response = client.post("/api/data", json=payload)
    assert response.status_code == 200
    assert response.json["message"] == "Data received"
    assert response.json["data"] == payload

def test_handle_data_no_payload(client):
    """Test the /api/data endpoint with no payload."""
    response = client.post("/api/data", json={})
    assert response.status_code == 400
    assert response.json["error"] == "No data provided"
