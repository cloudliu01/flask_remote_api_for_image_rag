from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from app.models_base import ImageEntry

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


@api_bp.route("/api/upload_images", methods=["POST"])
def upload_images():
    """Endpoint to upload a list of images with metadata."""
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    data = request.json
    if not isinstance(data, list):
        return jsonify({"error": "Request body must be a list of image objects"}), 400

    # Validate and parse each image entry
    images = []
    errors = []
    for idx, entry in enumerate(data):
        try:
            image_entry = ImageEntry(**entry)
            images.append(image_entry.dict())
        except ValidationError as e:
            errors.append({"index": idx, "error": e.errors()})

    # If any validation errors, return them
    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 422

    # Example processing: return the validated data
    return jsonify({
        "message": "Images uploaded successfully",
        "uploaded_images": images,
    }), 200