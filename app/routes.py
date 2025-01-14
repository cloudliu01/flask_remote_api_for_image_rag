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
from app.models_base import ChatJsonSchema, ImageUploadJsonSchema

from datetime import timezone
api_bp = Blueprint("api", __name__)


@api_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "API is running"}), 200


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


@api_bp.route('/upload_images', methods=['POST'])
def upload_images():
    db_session = current_app.extensions["sqlalchemy"].session

    try:
        # header 
        header = get_header_info(request)

        # Parse and validate JSON data
        data = request.get_json()
        validate(instance=data, schema=ImageUploadJsonSchema)

        account_info = data.get("user")  
        account_name = account_info.get("user")
        current_time = datetime.now(TZ)  

        processed_images = []

        account_item = account_to_db(db_session, account_name, header)

        for image in data['images']:
            image_type = image.get('type')
            image_url = image.get('image_url', {}).get('url')
            image_detail = image.get('image_url', {}).get('detail')
            location = image.get('location')

            if not image_url or not image_type:
                continue  # Skip images without required URL or type

            if os.path.isfile(image_url):
                base64_str_no_header = image_to_base64(image_url)
                image_md5 = get_md5_of_image(base64_str_no_header)
                image_data = base64_to_image(base64_str_no_header)
                image_metadata = extract_image_metadata(image_data)

                image_embedding = get_embedding(image_data, mode="image")
                #image_embedding = load_embedding_from_file('./test_embedding.txt')

                image_item = image_to_db(db_session, image_url, image_metadata, image_md5, image_embedding, account_item.id, None)

                # Update location from JSON if metadata does not have it
                if location and not image_metadata.get("WKT Point"):
                    image_item.location = f"POINT({location['longitude']} {location['latitude']})"

                processed_images.append(image_item)

        db_session.commit()
        return jsonify({"message": "Images processed successfully", "processed_images": len(processed_images)}), 200

    except ValidationError as e:
        db_session.rollback()
        return jsonify({"error": "Invalid data", "details": str(e)}), 400
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500



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

            image_embedding = get_embedding(image_data, mode="image")
            #image_embedding = load_embedding_from_file('./test_embedding.txt')

            account_id = account_item.id if account_item else None
            device_id = device_item.id if device_item else None
            image_item = image_to_db(db_session, image_url, image_metadata, image_md5, image_embedding, account_id, device_id)


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

        # TODO: 
        #   1. To implement the functions to associate transcripts to existing image data
        #   2. To return transcript or mp3 
        #   3. if none similar image found, return a instruction to Libre to query GPT instead
        images = search_images(db_session=db_session, location_wkt=location, embedding=image_embedding, radius= 1000, threshold=0.5, limit=3)

        if images[0] == 'IMG_1181.JPG':
            return 'aaaa'
        # If validation passes
        return jsonify({"message": "JSON data is valid"}), 200
    except ValidationError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Handle other exceptions
        db_session.rollback()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

