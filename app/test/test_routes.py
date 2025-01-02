import pytest
import os
from app.app import create_app

IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_upload_images_success(client):
    """Test the upload_images endpoint with valid input."""
    valid_data = [
        {
            "file_path": os.path.join(IMAGE_DIR, "IMG_8339.JPG"),
            "user": "user123",
            "session": "session456"
        },
        {
            "file_path": os.path.join(IMAGE_DIR, "IMG_9018.JPG"),
            "user": "user789",
            "session": "session987"
        }
    ]
    response = client.post(
        "/api/upload_images",
        json=valid_data,
    )
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["message"] == "Images uploaded successfully"
    assert len(response_json["uploaded_images"]) == 2
    assert response_json["uploaded_images"][0]["URL"] == "https://example.com/image1.jpg"

def test_upload_images_invalid_url(client):
    """Test the upload_images endpoint with an invalid URL."""
    invalid_data = [
        {
            "URL": "invalid-url",
            "create_time": "2025-01-02T12:00:00",
            "user": "user123",
            "session": "session456"
        }
    ]
    response = client.post(
        "/api/upload_images",
        json=invalid_data,
    )
    assert response.status_code == 422
    response_json = response.get_json()
    assert response_json["message"] == "Validation failed"
    assert "URL" in str(response_json["errors"][0]["error"])

def test_upload_images_missing_fields(client):
    """Test the upload_images endpoint with missing fields."""
    invalid_data = [
        {
            "URL": "https://example.com/image1.jpg",
            "create_time": "2025-01-02T12:00:00"
            # Missing 'user' and 'session'
        }
    ]
    response = client.post(
        "/api/upload_images",
        json=invalid_data,
    )
    assert response.status_code == 422
    response_json = response.get_json()
    assert response_json["message"] == "Validation failed"
    assert "user" in str(response_json["errors"][0]["error"])

def test_upload_images_non_json(client):
    """Test the upload_images endpoint with non-JSON input."""
    response = client.post(
        "/api/upload_images",
        data="Not a JSON payload",
        content_type="text/plain",
    )
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json["error"] == "Request must be in JSON format"
