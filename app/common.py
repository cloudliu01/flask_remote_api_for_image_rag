from PIL import Image, ExifTags
from typing import Optional, Tuple, Dict


from PIL import Image, ExifTags
from typing import Dict, Optional, Tuple


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


def get_altitude(gps_info: Dict) -> Optional[float]:
    """
    Extracts altitude information from GPSInfo.

    :param gps_info: The GPSInfo dictionary extracted from EXIF data.
    :return: Altitude in meters or None if unavailable.
    """
    altitude = gps_info.get(6)  # Altitude
    altitude_ref = gps_info.get(5)  # Altitude reference (b'\x00' = above sea level)
    return altitude if altitude_ref == b'\x00' else -altitude


def extract_image_metadata(image_path: str) -> Dict[str, Optional[str]]:
    """
    Extracts metadata from an image file, including location, focal length, orientation,
    altitude, device details, and capture datetime. GPSInfo is formatted for PostGIS.

    :param image_path: Path to the image file.
    :return: A dictionary with extracted metadata.
    """
    try:
        # Open the image and get its EXIF data
        image = Image.open(image_path)

        exif= image._getexif()
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
            wkt_point = convert_to_postgis_point(latitude, longitude, altitude)
        else:
            wkt_point, latitude, longitude, altitude = None, None, None, None

        # Extract other metadata
        make = exif_data.get("Make", None)  # Device make
        model = exif_data.get("Model", None)  # Device model
        datetime_taken = exif_data.get("DateTimeOriginal", None)  # Datetime the image was taken
        focal_length_35mm = exif_data.get("FocalLengthIn35mmFilm", None)  # Focal length (35mm equivalent)
        orientation = gps_info.get(17) if gps_info else None  # Direction in degrees relative to true north

        return {
            "WKT Point": wkt_point,
            "Latitude": latitude,
            "Longitude": longitude,
            "Altitude": altitude,
            "Make": make,
            "Model": model,
            "Datetime Taken": datetime_taken,
            "Focal Length (35mm)": focal_length_35mm,
            "Orientation (degrees)": orientation,
        }

    except Exception as e:
        return {"Error": str(e)}

