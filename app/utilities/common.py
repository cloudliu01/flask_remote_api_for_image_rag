import tzlocal
import json
from datetime import datetime
from pytz import timezone, UTC

TZ = tzlocal.get_localzone()



def write_embedding_to_file(embedding: list, file_path: str):
    """
    Writes a list of integers (embedding) to a file in JSON format.

    :param embedding: List of integers representing the embedding.
    :param file_path: Path to the file where the embedding will be saved.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(embedding, file)
        print(f"Embedding successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing the embedding to {file_path}: {e}")


def load_embedding_from_file(file_path: str) -> list:
    """
    Loads a list of integers (embedding) from a file in JSON format.

    :param file_path: Path to the file where the embedding is stored.
    :return: List of integers representing the embedding.
    """
    try:
        with open(file_path, 'r') as file:
            embedding = json.load(file)
        print(f"Embedding successfully loaded from {file_path}")
        return embedding
    except Exception as e:
        print(f"An error occurred while loading the embedding from {file_path}: {e}")
        return []


def convert_datetime_with_timezone(local_time: str, tz_name: str = "UTC", format='%Y:%m:%d %H:%M:%S') -> datetime:
    """
    Converts EXIF Datetime string to a timezone-aware datetime object.

    :param local_time: The datetime string from EXIF (e.g., "2023:01:01 15:34:30").
    :param tz_name: The timezone name (default is UTC).
    :return: A timezone-aware datetime object.
    """
    try:
        # Convert EXIF datetime string to naive datetime object
        naive_datetime = datetime.strptime(local_time, format)

        # Apply timezone
        local_tz = timezone(tz_name)

        return local_tz.localize(naive_datetime)
    except Exception as e:
        print(f"An error occurred while converting datetime with timezone: {e}")
        return datetime.now(UTC)