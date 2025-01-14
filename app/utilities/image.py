import pprint
import io
import os
import hashlib
import piexif
import base64
from typing import Optional, Tuple, Dict, Union
from PIL import Image, ExifTags
from timezonefinder import TimezoneFinder
from pytz import timezone


def image_to_binary(path):
    """
    Loads an image from the specified path and returns a binary stream.

    :param path: Path to the image file.
    :return: BytesIO object containing the binary data of the image.
    """
    # Open the image file
    with Image.open(path) as img:
        # Create a BytesIO object
        img_byte_arr = io.BytesIO()
        # Save the image to the BytesIO object in JPEG format
        img.save(img_byte_arr, format='JPEG')
        # Seek to the beginning of the stream
        img_byte_arr.seek(0)
        return img_byte_arr

def resize_image(input_path, output_path=None, max_side_length=1024):
    """
    Resize an image to a maximum side length while preserving EXIF data.
    
    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the resized image. If None, return as binary.
        max_side_length (int): Maximum size of the longer side of the image.
    
    Returns:
        Tuple: (None, exif_data) if saved to a file, or (image_binary, exif_data) if returned as binary.
    """
    # Open the image file
    with Image.open(input_path) as img:
        # Get the original EXIF data (structured)
        exif_data = img._getexif()

        # Get original dimensions
        width, height = img.size

        # Determine new dimensions
        if width > height and width > max_side_length:
            # Landscape orientation
            scale_factor = max_side_length / float(width)
            new_width = max_side_length
            new_height = int(float(height) * scale_factor)
        elif height > width and height > max_side_length:
            # Portrait orientation
            scale_factor = max_side_length / float(height)
            new_height = max_side_length
            new_width = int(float(width) * scale_factor)
        else:
            # No resize needed
            new_width, new_height = width, height

        # Resize the image
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        if output_path:
            # Save to the specified path
            img_resized.save(output_path, format=img.format, exif=img.info.get("exif"))
            return (None, exif_data)
        else:
            # Save to a binary stream
            img_binary = io.BytesIO()
            img_resized.save(img_binary, format=img.format, exif=img.info.get("exif"))
            img_binary.seek(0)  # Reset stream position
            return (img_binary.read(), exif_data)

def _resize_image(input_path, output_path=None, max_side_length=1024):
    '''
    Give an input image, resize it to 1024 for it's longer side
    
    return:
        output_path is a file path => (None, exif_data)
                                    otherwise (image_binary, exif_data)
    '''
    # Open the image file
    with Image.open(input_path) as img:
        # Get the original EXIF data
        exif_data = img.info.get('exif')

        # Get original dimensions
        width, height = img.size

        # Determine if width or height is the longer side
        if width > height and width > max_side_length:
            # Landscape orientation (resize based on width)
            scale_factor = max_side_length / float(width)
            new_width = max_side_length
            new_height = int(float(height) * scale_factor)
        elif height > width and height > max_side_length:
            # Portrait orientation (resize based on height)
            scale_factor = max_side_length / float(height)
            new_height = max_side_length
            new_width = int(float(width) * scale_factor)

        # Resize the image
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        if output_path:
            if exif_data:
                img_resized.save(output_path, exif=exif_data)
                return (None, exif_data)
            else:
                img_resized.save(output_path)  # Save without EXIF if it's None
                return (None, None)
        else:
            # Otherwise, return the image in binary format
            img_binary = io.BytesIO()
            if exif_data:
                img_resized.save(img_binary, format=img.format, exif=exif_data)
            else:
                img_resized.save(img_binary, format=img.format)  
            img_binary.seek(0)  # Go back to the beginning of the BytesIO object
            return (img_binary.read(), exif_data)



def pretty_print_exif(exif_dict):
    # Use pprint to pretty print the EXIF data
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(exif_dict)


def convert_to_postgis_point(latitude: Optional[float], longitude: Optional[float], altitude: Optional[float] = None) -> Optional[str]:
    """
    Converts latitude, longitude, and altitude into a WKT POINT format suitable for PostGIS.

    :param latitude: Latitude in decimal degrees.
    :param longitude: Longitude in decimal degrees.
    :param altitude: Altitude in meters (optional).
    :return: WKT POINT as a string (e.g., "POINT(-74.0060 40.7128 10.5)").
    """
    if latitude is None or longitude is None:
        return None

    if altitude is not None:
        return f"POINT({longitude} {latitude} {altitude})"
    return f"POINT({longitude} {latitude})"


def convert_to_wkt(location_info: dict) -> str:
    """
    Converts location information to WKT format.
    
    :param location_info: A dictionary with 'latitude', 'longitude', and optionally 'altitude'.
                          Example: {"latitude": 40.785091, "longitude": -73.968285, "altitude": 30.5}
    :return: A WKT POINT or POINTZ string.
    :raises ValueError: If latitude or longitude is missing or invalid.
    """
    try:
        latitude = location_info.get("latitude")
        longitude = location_info.get("longitude")
        altitude = location_info.get("altitude")

        if latitude is None or longitude is None:
            raise ValueError("Latitude and longitude are required for WKT conversion.")

        # Validate that latitude and longitude are floats
        latitude = float(latitude)
        longitude = float(longitude)

        # Ensure valid latitude/longitude ranges
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude value: {latitude}. Must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude value: {longitude}. Must be between -180 and 180.")

        # Construct POINT or POINTZ based on altitude availability
        if altitude is not None:
            altitude = float(altitude)
            return f"POINTZ({longitude} {latitude} {altitude})"
        return f"POINT({longitude} {latitude})"

    except (ValueError, TypeError) as e:
        raise ValueError(f"Error converting location to WKT: {e}")


def get_decimal_coordinates(gps_info: Dict) -> Tuple[Optional[float], Optional[float]]:
    """
    Converts GPSInfo to decimal coordinates.

    :param gps_info: The GPSInfo dictionary extracted from EXIF data.
    :return: A tuple containing latitude and longitude in decimal degrees.
    """
    def to_decimal(coord, ref):
        degrees, minutes, seconds = coord
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal *= -1
        return decimal

    latitude = gps_info.get(2)
    latitude_ref = gps_info.get(1)
    longitude = gps_info.get(4)
    longitude_ref = gps_info.get(3)

    if latitude and longitude and latitude_ref and longitude_ref:
        return (
            to_decimal(latitude, latitude_ref),
            to_decimal(longitude, longitude_ref),
        )
    return None, None



def get_timezone_from_gps(gps_info):
    if gps_info is None:
        return None

    # Extract latitude and longitude
    latitude, longitude = get_decimal_coordinates(gps_info)  # Implement this function to parse GPSInfo

    # Infer timezone
    tz_finder = TimezoneFinder()
    tz_name = tz_finder.timezone_at(lat=latitude, lng=longitude)

    if tz_name:
        #return timezone(tz_name)
        return tz_name
    return None


def get_altitude(gps_info: Dict) -> Optional[float]:
    """
    Extracts altitude information from GPSInfo.

    :param gps_info: The GPSInfo dictionary extracted from EXIF data.
    :return: Altitude in meters or None if unavailable.
    """
    altitude = gps_info.get(6)  # Altitude
    altitude_ref = gps_info.get(5)  # Altitude reference (b'\x00' = above sea level)

    if altitude is None:
        return None

    # Convert IFDRational to float if necessary
    if hasattr(altitude, "numerator") and hasattr(altitude, "denominator"):
        altitude = float(altitude)

    return altitude if altitude_ref == b'\x00' else -altitude

def get_orientation(gps_info: Dict) -> Optional[float]:
    """
    Extracts orientation information from GPSInfo.

    :param gps_info: The GPSInfo dictionary extracted from EXIF data.
    :return: Orientation in degrees as a float or None if unavailable.
    """
    orientation = gps_info.get(17)  # Orientation in degrees relative to true north

    if orientation is None:
        return None

    # Convert IFDRational or tuple to float
    if hasattr(orientation, "numerator") and hasattr(orientation, "denominator"):
        orientation = float(orientation)
    elif isinstance(orientation, tuple) and len(orientation) == 2:
        orientation = orientation[0] / orientation[1]

    return orientation


def extract_image_metadata(image_input: Union[str, io.BytesIO]) -> Dict[str, Optional[str]]:
    """
    Extracts metadata from an image file or binary image data, including location, focal length, orientation,
    altitude, device details, and capture datetime. GPSInfo is formatted for PostGIS.

    :param image_input: Path to the image file or binary image data (io.BytesIO).
    :return: A dictionary with extracted metadata.
    """
    try:
        # Open the image (handle both file path and binary data)
        if isinstance(image_input, str) and os.path.exists(image_input):
            image = Image.open(image_input)
        elif isinstance(image_input, io.BytesIO):
            image = Image.open(image_input)
        else:
            return {"Error": "Unsupported input type. Provide a file path or binary data."}

        #image.show()
        # Extract EXIF data
        exif = image._getexif()
        if not exif:
            return {}

        # Map EXIF tags to human-readable names
        exif_data = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}

        # Extract GPSInfo
        gps_info = exif_data.get("GPSInfo")
        if gps_info:
            # Convert GPS tags to human-readable names
            gps_data = {}
            for key, value in gps_info.items():
                tag_name = ExifTags.GPSTAGS.get(key, key)
                gps_data[tag_name] = value
            exif_data["GPSInfo"] = gps_data
            latitude, longitude = get_decimal_coordinates(gps_info)
            altitude = get_altitude(gps_info)
            wkt_point = convert_to_postgis_point(latitude, longitude )
        else:
            wkt_point, latitude, longitude, altitude = None, None, None, None

        # Extract other metadata
        make = exif_data.get("Make", None)  # Device make
        model = exif_data.get("Model", None)  # Device model
        datetime_taken = exif_data.get("DateTimeOriginal", None)  # Datetime the image was taken
        focal_length_35mm = exif_data.get("FocalLengthIn35mmFilm", None)  # Focal length (35mm equivalent)
        orientation = get_orientation(gps_info)  # Orientation in degrees

        return {
            "WKT Point": wkt_point,
            "Latitude": latitude,
            "Longitude": longitude,
            "Altitude": altitude,
            "Make": make,
            "Model": model,
            "Datetime Taken": datetime_taken,
            "Timezone": get_timezone_from_gps(gps_info), 
            "Focal Length (35mm)": focal_length_35mm,
            "Orientation (degrees)": orientation,
        }

    except Exception as e:
        return {"Error": str(e)}


def image_to_base64(filepath, keep_exif=True):
    """Converts an image to base64 string."""
    if keep_exif:   
        with open(filepath, "rb") as image:
            return base64.b64encode(image.read()).decode('utf-8')
    else:
        with Image.open(filepath) as image:
            buffer = io.BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(buffer, format='JPEG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

def base64_to_image(base64_string):
    """Converts a base64-encoded string back to an image and displays it."""
    image_bytes = base64.b64decode(base64_string)
    image_data = io.BytesIO(image_bytes)
    #image = Image.open(image_data)
    #image.show()
    return image_data



def get_md5_of_image(input_data):
    """
    Computes the MD5 hash of an image given directly as bytes, from a file path, or from a base64-encoded string.

    :param input_data: Either the bytes of the image, a string path to an image file, or a base64-encoded string.
    :return: The hexadecimal MD5 hash of the image.
    """
    hash_md5 = hashlib.md5()
    
    if isinstance(input_data, bytes):
        # If input is bytes, directly update MD5 hash
        hash_md5.update(input_data)
    elif isinstance(input_data, str):
        if os.path.isfile(input_data):
            # If input is a file path, open the file and update MD5 hash
            with open(input_data, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hash_md5.update(chunk)
        else:
            # Assume input is a base64 string, decode and update MD5 hash
            try:
                image_bytes = base64.b64decode(input_data)
                hash_md5.update(image_bytes)
            except base64.binascii.Error:
                raise ValueError("Input string is neither a valid file path nor a valid base64 string")
    else:
        raise ValueError("Input must be either image bytes, a valid file path to an image, or a base64-encoded string")

    return hash_md5.hexdigest()
