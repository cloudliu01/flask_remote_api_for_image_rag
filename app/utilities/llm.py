import os
import requests
import json

from app.config import Config
from app.utilities.image import image_to_binary, resize_image, extract_image_metadata, pretty_print_exif


def get_embedding(input_data, mode="image"):
    """
    Generates a vector embedding for an image or text using Azure AI Vision 4.0 APIs.

    :param input_data: Filepath to the image (for "image" mode) or a text string (for "text" mode).
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
        # Process image input for "image" mode
        if mode == "image":
            data, _ = resize_image(input_data, output_path=None, max_side_length=1024)  # Resize image
            image_metadata = extract_image_metadata(data)  # Optionally extract metadata (not used here)
        # Prepare text input for "text" mode
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


def _get_image_embedding(image):
    '''
    Generates a vector embedding for an image using Azure AI Vision 4.0
    (Vectorize Image API).

    :param image: The image filepath.
    :return: The vector embedding of the image.
    '''
    endpoint = f"{Config.AZURE_VISION_ENDPOINT}computervision/"
    key = Config.AZURE_VISION_KEY
    version = Config.AZURE_VISION_VERSION
    vectorize_img_url = f"{endpoint}retrieval:vectorizeImage{version}"
    vectorize_text_url = f"{endpoint}retrieval:vectorizeText{version}"


    #with open(image, "rb") as img:
    #    data = img.read()

    headers = {
        "Content-type": "application/octet-stream",
        "Ocp-Apim-Subscription-Key": key
    }

    #headers = {
    #    "Content-Type": "application/json",
    #    "Ocp-Apim-Subscription-Key": key
    #}
    #data = {
    #    "url": "https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png"
    #}

    try:
        data, _ = resize_image(image, output_path=None, max_side_length=1024)
        image_metadata = extract_image_metadata(data)
        #r = requests.post(vectorize_img_url, json=data, headers=headers)
        r = requests.post(vectorize_img_url, data=data, headers=headers)

        if r.status_code == 200:
            return r.json()["vector"]
        else:
            print(f"An error occurred while processing {image}. Error code: {r.status_code}.")

    except Exception as e:
        print(f"An error occurred while processing {image}: {e}")

    return None
