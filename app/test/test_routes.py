import pytest
import os
import json
from unittest.mock import patch, MagicMock

from app.utilities.image import image_to_base64
from app.app import create_app

IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# def test_upload_images_success(client):
#     """Test the upload_images endpoint with valid input."""
#     valid_data = [
#         {
#             "dir_path": os.path.join(IMAGE_DIR, "IMG_8339.JPG"),
#             "user": "user123",
#             "session": "session456"
#         },
#         {
#             "dir_path": os.path.join(IMAGE_DIR, "IMG_9018.JPG"),
#             "user": "user789",
#             "session": "session987"
#         }
#     ]
#     response = client.post(
#         "/api/upload_images",
#         json=valid_data,
#     )
#     assert response.status_code == 200
#     response_json = response.get_json()
#     assert response_json["message"] == "Images uploaded successfully"
#     assert len(response_json["uploaded_images"]) == 2
#     assert response_json["uploaded_images"][0]["URL"] == "https://example.com/image1.jpg"
# 
# def test_upload_images_invalid_url(client):
#     """Test the upload_images endpoint with an invalid URL."""
#     invalid_data = [
#         {
#             "URL": "invalid-url",
#             "create_time": "2025-01-02T12:00:00",
#             "user": "user123",
#             "session": "session456"
#         }
#     ]
#     response = client.post(
#         "/api/upload_images",
#         json=invalid_data,
#     )
#     assert response.status_code == 422
#     response_json = response.get_json()
#     assert response_json["message"] == "Validation failed"
#     assert "URL" in str(response_json["errors"][0]["error"])
# 
# def test_upload_images_missing_fields(client):
#     """Test the upload_images endpoint with missing fields."""
#     invalid_data = [
#         {
#             "URL": "https://example.com/image1.jpg",
#             "create_time": "2025-01-02T12:00:00"
#             # Missing 'user' and 'session'
#         }
#     ]
#     response = client.post(
#         "/api/upload_images",
#         json=invalid_data,
#     )
#     assert response.status_code == 422
#     response_json = response.get_json()
#     assert response_json["message"] == "Validation failed"
#     assert "user" in str(response_json["errors"][0]["error"])
# 
# def test_upload_images_non_json(client):
#     """Test the upload_images endpoint with non-JSON input."""
#     response = client.post(
#         "/api/upload_images",
#         data="Not a JSON payload",
#         content_type="text/plain",
#     )
#     assert response.status_code == 400
#     response_json = response.get_json()
#     assert response_json["error"] == "Request must be in JSON format"


# Helper function to get the path of test images
def get_test_image_path(filename):
    """
    Returns the absolute path of a test image file in the 'images' folder.
    """
    base_dir = os.path.dirname(__file__)
    images_dir = os.path.join(base_dir, "images")
    return os.path.join(images_dir, filename)

def test_upload_image_success(client):
    """
    Test the upload_image endpoint for successful image upload.
    """
    # Prepare the test payload
    image_path = get_test_image_path("IMG_8339.JPG")  # Replace with your actual test image file
    payload = {
        "image_path": image_path,  # Use the test image path
        "account_name": "test_account",
        "account_source": "test_upload_image_success",
        "chat_session_id": "test_session"
    }

    # Make the POST request
    response = client.post("/api/upload_image", json=payload)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Similar images found"
    assert isinstance(data["similar_images"], list)


#@patch("app.routes.get_chat_histories_from_db")  # Mock database function
#def test_process_chat_valid_input(mock_get_chat_histories, client):
def test_process_chat_valid_input(client):
    """
    Test process_chat with valid inputs.
    """
    # Mock response for get_chat_histories_from_db
    mock_chat_history = MagicMock()
    mock_chat_history.location = "POINT(-73.985428 40.748817)"  # Mock a valid location
    #mock_get_chat_histories.return_value = [mock_chat_history]

    # Input data
    payload = {
        "account_id": "test_account",
        "content": "Find images near Empire State Building.",
        "session_id": "test_session",
        "back_hours": 0
    }

    # Call the API
    response = client.post("/process_chat", json=payload)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert "error" not in data  # Ensure no error is returned
    assert "images" in data  # Ensure images are included in the response
    #mock_get_chat_histories.assert_called_once_with("abc123", 1, 2)  # Ensure function is called with correct params


def test_valid_json_with_image_1(client):
    """ Test the route with valid JSON including base64 image data """
    image_path = get_test_image_path("IMG_0643.JPG")  # Replace with your actual test image file
    image_base64 = image_to_base64(image_path)
    data = {
        "model": "gpt-4o-mini",
        "user": "671756edd40f99d73854437a",
        "session": "1234567abcd",
        "stream": True,
        "messages": [
            {"role": "system", "content": "你是一个资深导游"}, 
            {"role": "user", "content": "你好！"}, 
            {"role": "assistant", "content": "你好！有什么我可以帮助你的吗？"}, 
            {"role": "user", "content": [
                {
                    "type": "text", 
                    "content": "我想看看这张照片附近的景点"
                },
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}", 
                        "detail": "auto"
                    }
                }
            ]},
        ],
        "max_tokens": 4000
    }
    response = client.post('/process_chat_json', json=data)
    assert response.status_code == 200
    assert response.json['message'] == 'JSON data is valid'


def test_valid_json_with_image_2(client):
    """ Test the route with valid JSON including base64 image data. The image doesn't have exif data """
    image_path = get_test_image_path("IMG_1181.JPG")  
    image_base64 = image_to_base64(image_path, keep_exif=False)
    data = {
        "model": "gpt-4o-mini",
        "user": "671756edd40f99d73854437a",
        "session": "1234567abcd",
        "stream": True,
        "messages": [
            {"role": "system", "content": "你是一个资深导游"}, 
            {"role": "user", "content": "你好！"}, 
            {"role": "assistant", "content": "你好！有什么我可以帮助你的吗？"}, 
            {"role": "user", "content": [
                {
                    "type": "text", 
                    "content": "我想看看这张照片附近的景点"
                },
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}", 
                        "detail": "auto"
                    }
                }
            ]},
            {"role": "assistant", "content": "图片好像没有地理信息。请发送一个你的位置信息。"}, 
            {"role": "user", 
                "content": {
                    "type": "location",
                    "location": {
                        "longitude":    -73.985428, 
                        "latitude":     40.748817
                    }
                }
            } 
        ],
        "max_tokens": 4000
    }
    response = client.post('/process_chat_json', json=data)
    assert response.status_code == 200
    assert response.json['message'] == 'JSON data is valid'

    
import pytest
import os
from werkzeug.datastructures import FileStorage
from flask import Flask, request, jsonify

# Assuming Flask setup is correct and able to handle mixed data and file uploads


def test_upload_images(client):
    base_dir = os.path.dirname(__file__)
    images_dir = os.path.join(base_dir, "images")
    image_files = [os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.endswith('.JPG')]

    # Prepare JSON data and files according to the schema
    images_data = []
    for file in image_files:
        # Assume we simulate EXIF extraction to include type and location metadata
        images_data.append({
            'type': 'image/jpeg',
            'text': 'Sample image',
            'image_url': {
                'url': file,
                'detail': 'High detail'
            },
            'location': {
                'longitude': 0,
                'latitude': 0
            }
        })

    # Build the payload
    data = {
        'user': {
            'user': 'user123'
        },
        'images': images_data
    }

    # Convert data to JSON and add it to the request along with files
    response = client.post(
        '/upload_images',
        json=data
    )

    assert response.status_code == 200
    response_data = response.get_json()
    assert 'Images uploaded successfully' in response_data['message']
    assert len(response_data['processed_images']) == len(image_files)  # Ensure all images are processed

# Note: Adjust the actual Flask route handling logic to properly parse this mixed data format.
