import os
import requests
import json

from app.config import Config
from app.utilities.image import image_to_binary, resize_image, extract_image_metadata, pretty_print_exif

import base64
import io
import requests
from PIL import Image


def get_embedding(input_data, mode="image"):
    """
    Generates a vector embedding for an image or text using Azure AI Vision 4.0 APIs.

    :param input_data: Filepath, base64 string, or BytesIO to the image (for "image" mode) or a text string (for "text" mode).
    :param mode: Either "image" for image embeddings or "text" for text embeddings.
    :return: The vector embedding of the image or text.
    """
    endpoint = f"{Config.AZURE_VISION_ENDPOINT}computervision/"
    key = Config.AZURE_VISION_KEY
    version = Config.AZURE_VISION_VERSION

    # Determine the correct API URL
    if mode == "image":
        vectorize_url = f"{endpoint}retrieval:vectorizeImage{version}"
        headers = {
            "Content-type": "application/octet-stream",
            "Ocp-Apim-Subscription-Key": key
        }
    elif mode == "text":
        vectorize_url = f"{endpoint}retrieval:vectorizeText{version}"
        headers = {
            "Content-type": "application/json",
            "Ocp-Apim-Subscription-Key": key
        }
    else:
        raise ValueError(f"Invalid mode: {mode}. Supported modes are 'image' and 'text'.")

    try:
        # Process input based on mode
        if mode == "image":
            if isinstance(input_data, str):
                if os.path.isfile(input_data):
                    with open(input_data, "rb") as image_file:
                        data = image_file.read()
                else: 
                    data = base64.b64decode(input_data)
            elif isinstance(input_data, io.BytesIO):
                input_data.seek(0)
                data = input_data.read()
            else:
                raise ValueError("Unsupported image input type. Must be filepath, Base64 string, or BytesIO.")
            
            #data = resize_image(data, output_path=None, max_side_length=1024)  # Adjust if necessary
        elif mode == "text":
            data = {"text": input_data}

        # Send the request to the Azure API
        r = requests.post(vectorize_url, data=data if mode == "image" else json.dumps(data), headers=headers)

        # Check the response
        if r.status_code == 200:
            return r.json()["vector"]
        else:
            print(f"An error occurred. Mode: {mode}. Error code: {r.status_code}, Response: {r.text}")

    except Exception as e:
        print(f"An error occurred while processing {input_data}: {e}")

    return None
