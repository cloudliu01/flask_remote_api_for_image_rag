from flask import Blueprint, jsonify, request, current_app
from pydantic import ValidationError
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from jsonschema import validate, ValidationError
from PIL import Image
import re
import os

#from app import app
from app.utilities.image import extract_image_metadata, convert_to_wkt, base64_to_image, image_to_base64, get_md5_of_image
from app.utilities.llm import get_embedding
from app.utilities.db_common import account_to_db, device_to_db, image_to_db, chat_session_to_db, chat_history_to_db, \
    search_images, get_chat_histories_from_db
from app.utilities.common import write_embedding_to_file, load_embedding_from_file, TZ
from app.models_base import ChatJsonSchema

from datetime import timezone
api_bp = Blueprint("api", __name__)


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
        "account_name": "account_name",
        "account_source": "account_source",
        "chat_session_id": "session_id"
    }
    """
    try:
        # Parse the incoming JSON data
        if not request.is_json:
            return jsonify({"error": "Invalid input. Expected JSON format."}), 400

        data = request.get_json()

        # Validate required fields
        required_fields = ["image_path", "account_name", "account_source",  "chat_session_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        image_path = data["image_path"]
        account_name = data["account_name"]
        account_source = data["account_source"]
        chat_session_id = data["chat_session_id"]

        db_session = current_app.extensions["sqlalchemy"].session

        # Step 1: Extract accurate geo information from EXIF data
        image_metadata = extract_image_metadata(image_path)
        if image_metadata:
            if image_metadata.get("WKT Point"):
                accurate_geo_exif = image_metadata["WKT Point"]
    
        #image_embedding = get_embedding(image_path, mode="image")
        image_embedding = load_embedding_from_file('./test_embedding.txt')

        #sample_text = "This is a sample text for testing."
        #text_embedding = get_embedding(image_path, mode="text")

        # Step 2: Store the image and its metadata into the database
        image_data_to_db( db_session=db_session, image_path=image_path,
            image_metadata=image_metadata, image_embedding=image_embedding, account_name=account_name, 
            account_source=account_source, session_id=chat_session_id) 
        print('Image data stored in the database')
    
    except Exception as e:
        print(e)
        raise e


@api_bp.route('/process_chat', methods=['POST'])
def process_chat():
    """
    Process chat content, find associated location and embeddings, and return similar images.
    """
    try:
        # Parse input arguments
        data = request.json
        account_id = data.get("account_id")
        content = data.get("content")
        session_id = data.get("session_id")
        back_hours = data.get("back_hours", 0)  # Default 0 hour means all chat history

        db_session = current_app.extensions["sqlalchemy"].session

        # Validate input
        if not account_id or not content or not session_id:
            return jsonify({"error": "Missing required parameters: account_id, content, session_id"}), 400

        # Step 1: Find previous chat history (memory)
        chat_histories = get_chat_histories_from_db(db_session, session_id, account_id, back_hours)

        # Step 2: Check if the last chat history has been replied 
        
        
        # Step 2: Check if any chat history has location info
        found_location = None
        for chat in chat_histories:
            if chat.location:
                found_location = chat.location
                break

        # # Step 3: Store new chat history
        # new_chat_history = ChatHistory(
        #     session_id=session_id,
        #     account_id=account_id,
        #     content=content,
        #     time=datetime.utcnow(),
        #     location=found_location  # Placeholder for location
        # )
        # db.session.add(new_chat_history)
        # db.session.flush()  # Ensure the record gets an ID

        # # Step 4: If no location found, call LLM to extract location
        # if not found_location:
        #     location_info = extract_location_info(content)  # Replace with your LangChain/OpenAI implementation
        #     if location_info:
        #         found_location = convert_to_wkt(location_info)
        #         new_chat_history.location = found_location
        #     else:
        #         return jsonify({"error": "Unable to determine location from previous chat history or content."}), 400

        # # Step 5: Use the location to find similar images
        # embedding = [0.1, 0.2, 0.3, 0.4]  # Placeholder: Replace with embedding generation function
        # similar_images = search_images(location_wkt=found_location, embedding=embedding, radius=1000, threshold=0.5, limit=10)

        # # Commit the new chat history record to the database
        # db.session.commit()

        # # Step 6: Return similar images
        # return jsonify({"images": similar_images}), 200
        return None

    except Exception as e:
        return None
        # db_session.rollback()  # Roll back any uncommitted transactions
        # return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    

def find_last_image_url_chat(messages):
    """
    Finds the last chat message containing an 'image_url' item in the 'content'.

    :param messages: list of messages coming from the JSON data.
    :return: The last chat message containing an 'image_url', or None if not found.
    """
    # Iterate over the messages in reverse order to find the last 'image_url'
    seen_messages = []
    for message in reversed(messages):
        # Check if 'content' is a list (it could be a string or a list)
        if isinstance(message.get('content'), list):
            # Iterate over the items in 'content'
            for item in message['content']:
                if item.get('type') == 'image_url':
                    #chat_item_content = message.get('content')
                    #for i in chat_item_content:
                    #    if i.get('type') == 'image_url':
                    #        return i.get('image_url').get('url')
                    seen_messages.append(message)
                    return list(reversed(seen_messages))
        seen_messages.append(message)
    del seen_messages
    return messages

def get_header_info(request):
    user_agent = request.headers.get('User-Agent')
    referer = request.headers.get('Referer')
    x_forwarded_for = request.headers.get('X-Forwarded-For')  # Could contain multiple IPs if routed through multiple proxies.
    return f"User-Agent: {user_agent}, Referer: {referer}, X-Forwarded-For: {x_forwarded_for}"


def get_location_from_db(db_session, chat_session, account, back_hours=1):
    """
    Extracts geographic information from messages using different modes.

    :param db_session: database connection session.
    :param chat_session: chat_session database item.
    :param account: account database item.
    :return: A WKT Point string representing the location.
    """
    try:
        chat_history_items = get_chat_histories_from_db(db_session, chat_session, account, back_hours) 
        for item in reversed(chat_history_items):
            if item.location:
                return item.location
            elif item.image and item.image.location:
                return item.image.location
        return {}
    except ValueError as e:
        print(f"An error occurred while extracting location from database: {e}")
        return {}




@api_bp.route('/process_chat_json', methods=['POST'])
def handle_json():
    try:
        # header 
        header = get_header_info(request)

        # Parse JSON data
        data = request.get_json()
        # Validate JSON data
        validate(instance=data, schema=ChatJsonSchema)

        db_session = current_app.extensions["sqlalchemy"].session

        user = data.get("user")     
        chat_session = data.get("session")     
        model = data.get("model")     
        max_tokens = data.get("max_tokens") 
        messages = data.get("messages")

        current_time = datetime.now(TZ)

        account_item = account_to_db(db_session, user, header)
        chat_session_item = chat_session_to_db(db_session, chat_session, current_time)

        device_item = None
        image_item = None

        chat_history_item = None

        # Try to get geo info from the database
        location = get_location_from_db(db_session, chat_session, user)

        ## TODO: Need LibreChat to pass image path instead of base64 string in the future
        #image_path = '/Users/liulizhuang/GitHubProjects/flask_remote_api_for_image_rag/app/test/images/IMG_8339.JPG'
        #base64_str_from_image = image_to_base64(image_path)  
        image_path = 'Dummy path'
        image_md5 = 'Dummy md5'
        image_metadata = {}

        messages_with_latest_image = find_last_image_url_chat(messages)
        if messages_with_latest_image:
            # extract exif from the image base64 string
            image_url = messages_with_latest_image[0].get('content')[1].get('image_url').get('url')
            ## ====== It's also working when image_url is a path ======
            #image_url = '/Users/liulizhuang/GitHubProjects/flask_remote_api_for_image_rag/app/test/images/IMG_8339.JPG'
            if re.match(r'^data:image/jpeg;base64,', image_url):
                base64_str_no_header = re.sub(r'^data:image/jpeg;base64,', '', image_url)
            elif os.path.isfile(image_url):
                base64_str_no_header = image_to_base64(image_url)
                image_path = image_url

            image_md5 = get_md5_of_image(base64_str_no_header)
            image_data = base64_to_image(base64_str_no_header)
            image_metadata = extract_image_metadata(image_data)

            #image_embedding = get_embedding(image_data, mode="image")
            image_embedding = load_embedding_from_file('./test_embedding.txt')

            image_item = image_to_db(db_session, image_url, image_metadata, image_md5, image_embedding, account_item, device_item)


            if image_metadata:
                device_item = device_to_db(db_session, image_metadata)

                # Overwrite the location if the latest image has geo info
                if image_metadata.get("WKT Point"):
                    location = image_metadata["WKT Point"]

    
        if messages_with_latest_image and messages_with_latest_image[-1].get('role') == 'user' \
                and messages_with_latest_image[-1].get('content').get('type') == 'location':    
            location = messages_with_latest_image[-1].get('content').get('location') 
            location = convert_to_wkt(location)

        if not location:
            return jsonify({"assistant": "请发送定位确定你的位置，以便给你个性化的体验！"}), 200

        prompt = messages[-1]
        chat_history_item = chat_history_to_db(db_session, chat_session_item, account_item, image_item, prompt, location)

        #sample_text = "This is a sample text for testing."
        #text_embedding = get_embedding(image_path, mode="text")

        print('Image data stored in the database')

        # If validation passes
        return jsonify({"message": "JSON data is valid"}), 200
    except ValidationError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Handle other exceptions
        db_session.rollback()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

