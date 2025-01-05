from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from typing import Dict, Any, List

from app.models_base import ImageEntry
from app.common import extract_image_metadata

api_bp = Blueprint("api", __name__)

def register_routes(app):
    app.register_blueprint(api_bp)
@api_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "API is running"}), 200

@api_bp.route("/api/data", methods=["POST"])
def handle_data():
    if not (data := request.json):
        return jsonify({"error": "No data provided"}), 400
    else:
        # Example: Process the data
        return jsonify({"message": "Data received", "data": data}), 200


# @api_bp.route("/api/upload_images", methods=["POST"])
# def upload_images():
#     """Endpoint to upload a list of images with metadata."""
#     if not request.is_json:
#         return jsonify({"error": "Request must be in JSON format"}), 400
# 
#     data = request.json
#     if not isinstance(data, list):
#         return jsonify({"error": "Request body must be a list of image objects"}), 400
# 
#     # Validate and parse each image entry
#     images = []
#     errors = []
#     for idx, entry in enumerate(data):
#         try:
#             image_entry = ImageEntry(**entry)
#             images.append(image_entry.dict())
#         except ValidationError as e:
#             errors.append({"index": idx, "error": e.errors()})
# 
#     # If any validation errors, return them
#     if errors:
#         return jsonify({"message": "Validation failed", "errors": errors}), 422
# 
#     # Example processing: return the validated data
#     return jsonify({
#         "message": "Images uploaded successfully",
#         "uploaded_images": images,
#     }), 200

    

@api_bp.route('/api/upload_image', methods=['POST'])
def upload_image():
    """
    Flask API endpoint to upload an image, store metadata, and retrieve similar images.

    Expects a JSON payload:
    {
        "image_path": "path/to/image.jpg",
        "location_desc": "location description",
        "user": "user_id",
        "chat_session_id": "session_id"
    }
    """
    # Parse the incoming JSON data
    if not request.is_json:
        return jsonify({"error": "Invalid input. Expected JSON format."}), 400

    data = request.get_json()

    # Validate required fields
    required_fields = ["image_path", "location_desc", "user", "chat_session_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    image_path = data["image_path"]
    location_desc = data["location_desc"]
    user = data["user"]
    chat_session_id = data["chat_session_id"]

    # Step 1: Extract accurate geo information from EXIF data
    image_metadata = extract_image_metadata(image_path)
    if image_metadata and image_metadata.get("WKT Point"):
        accurate_geo_exif = image_metadata["WKT Point"]

    # Step 2: Retrieve previous accurate and rough geo info from the database
    previous_geo_info = get_previous_geo_from_db(chat_session_id, user)

    # Step 3: Extract accurate and rough geo info from location description
    geo_from_location_desc = get_geo_from_location_desc(location_desc)

    # Step 4: Synthesize the determined location
    synthesized_geo = synthesize_location(
        accurate_geo_exif=accurate_geo_exif,
        geo_from_location_desc=geo_from_location_desc,
        previous_geo_info=previous_geo_info
    )

    # Step 5: Store the image and its metadata into the database
    try:
        store_image_metadata(image_path, synthesized_geo, user, chat_session_id)
    except FileNotFoundError as e:
        return jsonify({"error": f"Image file not found: {e}"}), 400

    # Step 6: Retrieve similar images based on embedding and geo info
    similar_images = retrieve_similar_images(image_path, synthesized_geo)

    # Step 7: Return the response based on whether similar images were found
    if similar_images:
        return jsonify({
            "message": "Similar images found",
            "similar_images": similar_images
        }), 200
    else:
        return jsonify({
            "message": "Not found",
            "similar_images": []
        }), 404


# Dummy sub-functions (to be implemented)
def get_accurate_geo_from_exif(exif: Dict[str, Any]) -> Dict[str, Any]:
    """Extract accurate geo information from EXIF data."""
    return {}

def get_previous_geo_from_db(chat_session_id: str, user: str) -> Dict[str, Any]:
    """Retrieve the previous accurate and rough geo info from the database."""
    return {}

def get_geo_from_location_desc(location_desc: str) -> Dict[str, Any]:
    """Extract accurate and rough geo info from the location description."""
    return {}

def synthesize_location(accurate_geo_exif: Dict[str, Any], geo_from_location_desc: Dict[str, Any], previous_geo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize the final geo location.
    Priority: 
      1. Accurate geo info from EXIF
      2. Accurate geo info from location_desc
      3. Rough geo info from location_desc
      4. Accurate geo info from database
      5. Rough geo info from database
    """
    return {}

def store_image_metadata(image_path: str, synthesized_geo: Dict[str, Any], user: str, chat_session_id: str):
    """Store the image and its metadata into the database."""
    # Validate if the file exists
    import os
    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    pass

def retrieve_similar_images(image_path: str, geo_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retrieve similar images from the database based on embeddings and geo info."""
    return []

