from sqlalchemy.orm import Session
from contextlib import contextmanager
from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased, joinedload
from datetime import datetime, timedelta
from geoalchemy2.functions import ST_DWithin, ST_GeogFromText
from sqlalchemy.dialects.postgresql import ARRAY

from app.utilities.common import TZ, convert_datetime_with_timezone 
from app.utilities.image import convert_to_wkt
from app.models import Account, ChatSession, ChatHistory, Image, Embedding, Device


def account_to_db(db_session, account_name, account_source):
    account = db_session.query(Account).filter_by(name=account_name, source=account_source).first()
    if not account:
        account = Account(name=account_name, source=account_source, create_time=datetime.now(TZ))
        db_session.add(account)
        db_session.commit()
    return account

def device_to_db(db_session, image_metadata):
    device = None
    if 'Make' in image_metadata and 'Model' in image_metadata:
        device_maker = image_metadata['Make']
        device_model = image_metadata['Model']
        device = db_session.query(Device).filter_by(device_maker=device_maker, device_model=device_model).first()
        if not device:
            device = Device(device_maker=device_maker, device_model=device_model)
            db_session.add(device)
            db_session.commit()
    return device

def image_to_db(db_session, image_path, image_metadata, image_md5, image_embedding, account_id, device_id):
    if image_metadata.get("Datetime Taken") and image_metadata.get("Timezone"):
        taken_time = convert_datetime_with_timezone(image_metadata.get("Datetime Taken"), image_metadata.get("Timezone"))
    else:
        taken_time = datetime.now(TZ)
    image = db_session.query(Image).filter_by(md5=image_md5).first()
    if not image:
        image = Image(
            path=image_path,
            md5=image_md5,
            creator_id=account_id,
            device_id=device_id,
            location=image_metadata.get("WKT Point"),
            taken_time=taken_time,
            focus_35mm=image_metadata.get("Focal Length (35mm)"),
            orientation_from_north=image_metadata.get("Orientation (degrees)"),
            other_metadata={
                "Make": image_metadata.get("Make"),
                "Model": image_metadata.get("Model"),
                "Altitude": image_metadata.get("Altitude"),
                #"Latitude": image_metadata.get("Latitude"),
                #"Longitude": image_metadata.get("Longitude"),
            }
        )
        db_session.add(image)
        db_session.commit()

        embedding = Embedding(image_id=image.id, image_embedding=image_embedding)
        db_session.add(embedding)
        db_session.commit()

    return image



def chat_session_to_db(db_session, session_id, create_time):
    chat_session = db_session.query(ChatSession).filter_by(session_id=session_id).first()
    if not chat_session:
        chat_session = ChatSession(session_id=session_id, create_time=create_time)
        db_session.add(chat_session)
        db_session.commit()
    return chat_session


def chat_history_to_db(db_session, chat_session, account, image, prompt, location):
    chat_history = ChatHistory(
        session_id=chat_session.id,
        account_id=account.id,
        location=location,
        image_id=image.id,
        time=datetime.now(TZ),
        prompt=prompt,
        llm_reply=None  
    )
    db_session.add(chat_history)
    db_session.commit()
    return chat_history

def _image_data_to_db(
    db_session: Session,
    image_metadata: dict,
    image_embedding: list,
    account_name: str,
    account_source: str,
    session_id: str,
    image_path: str,
    image_md5: str,
):
    """
    Stores image metadata, embedding, and related data into the database.

    :param db_session: SQLAlchemy session object.
    :param image_path: Path to the uploaded image file.
    :param image_md5: md5 of the image file or data.
    :param account_name: Name of the account who uploaded the image.
    :param account_source: Source of the account (e.g., "mobile", "web").
    :param image_metadata: Metadata extracted from the image.
    :param image_embedding: Vector embedding of the image.
    :param session_id: Session ID associated with the upload.
    :return: The newly created Image object.
    """
    try:
        # Ensure the account exists or create a new one
        account = db_session.query(Account).filter_by(name=account_name, source=account_source).first()
        if not account:
            account = Account(
                name=account_name,
                source=account_source,
                create_time=datetime.now(TZ)
            )
            db_session.add(account)
            db_session.commit()

        # Ensure the chat session exists or create a new one
        chat_session = db_session.query(ChatSession).filter_by(session_id=session_id).first()
        if not chat_session:
            chat_session = ChatSession(
                session_id=session_id,
                create_time= datetime.now(TZ)
            )
            db_session.add(chat_session)
            db_session.commit()

        image = db_session.query(Image).filter_by(md5=image_md5).first()

        if not image:
            # Ensure the device exists or create a new one
            if image_metadata.get('Make') and image_metadata.get('Model'):
                device_maker = image_metadata.get('Make') 
                device_model = image_metadata.get('Model') 
                device = db_session.query(Device).filter_by(device_maker=device_maker, device_model=device_model).first()
                if not device:
                    device = Device(
                        device_maker=device_maker,
                        device_model=device_model
                    )
                    db_session.add(device)
                    db_session.commit()
            else:
                device = None


            if image_metadata.get("Datetime Taken") and image_metadata.get("Timezone"):
                taken_time = convert_datetime_with_timezone(image_metadata.get("Datetime Taken"), image_metadata.get("Timezone"))
            else:
                taken_time = datetime.now(TZ)

            # Create a new Image record
            image = Image(
                path=image_path,
                md5=image_md5,
                creator_id=account.id,
                device_id=device.id if device else None,
                location=image_metadata.get("WKT Point"),
                taken_time=taken_time,
                focus_35mm=image_metadata.get("Focal Length (35mm)"),
                orientation_from_north=image_metadata.get("Orientation (degrees)"),
                other_metadata={
                    "Make": image_metadata.get("Make"),
                    "Model": image_metadata.get("Model"),
                    "Altitude": image_metadata.get("Altitude"),
                    #"Latitude": image_metadata.get("Latitude"),
                    #"Longitude": image_metadata.get("Longitude"),
                }
            )
            db_session.add(image)
            db_session.commit()

            # Create a new Embedding record
            embedding = Embedding(
                image_id=image.id,
                image_embedding=image_embedding
            )
            db_session.add(embedding)
            db_session.commit()

        # Optionally add to chat_history (if applicable)
        chat_history = ChatHistory(
            session_id=chat_session.id,
            account_id=account.id,
            image_id=image.id,
            location=image_metadata.get("WKT Point"),
            time=datetime.now(TZ),
            prompt="Image uploaded with metadata and embedding.",
            llm_reply=None
        )
        db_session.add(chat_history)
        db_session.commit()

        return image

    except Exception as e:
        db_session.rollback()
        print(f"An error occurred while storing image data: {e}")
        return None
 



def find_images_by_location(db_session: Session, location_wkt: str, radius: float = 1000) -> list:
    """
    Finds images within a specified radius of a location.

    :param location_wkt: The WKT string representing the location (POINT or POINTZ).
    :param radius: The radius in meters for the location search (default: 1 km).
    :return: A list of Image records within the radius.
    """
    try:
        return (
            db_session.query(Image)
            .filter(
                ST_DWithin(
                    func.Geography(Image.location),  # Geography type for location
                    func.Geography(ST_GeogFromText(location_wkt)),  # Convert WKT to Geography
                    radius
                )
            )
            .all()
        )
    except Exception as e:
        raise ValueError(f"Error performing location-based search: {e}")



def find_images_by_similarity(db_session: Session, image_ids: list, embedding: list, threshold: float = 0.5, limit: int = 10) -> list:
    """
    Finds images based on cosine similarity of embeddings.

    :param image_ids: A list of image IDs to filter by (e.g., results of location-based search).
    :param embedding: The vector embedding for cosine similarity search.
    :param threshold: The similarity threshold for filtering results (default: 0.5).
    :param limit: Maximum number of similar images to return (default: 10).
    :return: A list of dictionaries containing similar images and their metadata.
    """
    try:
        if not image_ids:
            return []  # No images to process

        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Embedding must be a non-empty list.")

        return (
            db_session.query(
                Image.id,
                Image.path,
                Image.location,
                Image.other_metadata,
                func.cosine_similarity(Embedding.image_embedding, ARRAY(embedding)).label("similarity")
            )
            .join(Embedding, Embedding.image_id == Image.id)
            .filter(
                Image.id.in_(image_ids),  # Filter by image IDs
                func.cosine_similarity(Embedding.image_embedding, ARRAY(embedding)) >= threshold  # Cosine similarity filter
            )
            .order_by(func.cosine_similarity(Embedding.image_embedding, ARRAY(embedding)).desc())  # Order by similarity
            .limit(limit)
            .all()
        )
    except Exception as e:
        raise ValueError(f"Error performing cosine similarity search: {e}")


def search_images(location_wkt: str, embedding: list, radius: float = 1000, threshold: float = 0.5, limit: int = 10) -> list:
    """
    Combines location-based and cosine similarity searches to find relevant images.

    :param location_wkt: The WKT string representing the location (POINT or POINTZ).
    :param embedding: The vector embedding for cosine similarity search.
    :param radius: The radius in meters for the location search (default: 1 km).
    :param threshold: The similarity threshold for cosine similarity search (default: 0.5).
    :param limit: Maximum number of similar images to return (default: 10).
    :return: A list of dictionaries containing the final filtered images.
    """
    try:
        # Step 1: Find images by location
        location_results = find_images_by_location(location_wkt, radius)
        if not location_results:
            return []

        # Extract image IDs from location-based search results
        image_ids = [image.id for image in location_results]

        # Step 2: Find images by cosine similarity within the location results
        similarity_results = find_images_by_similarity(image_ids, embedding, threshold, limit)

        # Step 3: Format and return the results
        return [
            {
                "id": result.id,
                "path": result.path,
                "location": result.location,
                "metadata": result.other_metadata,
                "similarity": result.similarity
            }
            for result in similarity_results
        ]
    except Exception as e:
        raise ValueError(f"Error performing combined search: {e}")


def get_chat_histories_from_db(db_session: Session, session_id: str, account_id: str, back_hours: int = 0) -> list:
    """
    Fetch previous chat histories based on session_id and account_id within the last 'back_hours',
    including related images and devices if available.

    :param session_id: The session ID to filter by.
    :param account_id: The account ID to filter by.
    :param back_hours: The time range to filter (default: 0 hour, means all).
    :return: A list of ChatHistory objects with loaded relationships.
    """
    try:
        if back_hours > 0:
            cutoff_time = datetime.now(TZ) - timedelta(hours=back_hours)
            filter_condition = and_(
                ChatSession.session_id == session_id,
                Account.name == account_id,
                ChatHistory.time >= cutoff_time
            )
        else:
            filter_condition = and_(
                ChatSession.session_id == session_id,
                Account.name == account_id
            )
        query = (
            db_session.query(ChatHistory)
            .join(ChatSession, ChatHistory.session_id == ChatSession.id)
            .join(Account, ChatHistory.account_id == Account.id)
            .outerjoin(Image, ChatHistory.image_id == Image.id)  
            .outerjoin(Device, Image.device_id == Device.id)  
            .filter(*filter_condition)
            .order_by(ChatHistory.time.desc())
            .limit(10)
        )

        # Execute and return the query
        results = query.all()
        data = [
            {
                "id": result.id,
                "session_id": result.session_id,
                "account_id": result.account_id,
                "time": result.time,
                "location": str(result.location) if result.location else None,
                "prompt": result.prompt,
                "llm_reply": result.llm_reply,
                "image_path": result.image.path if result.image else None,
                "device_maker": result.image.device.device_maker if result.image and result.image.device else None
            } for result in results ]
        print(data)
        return results

    except Exception as e:
        raise ValueError(f"Error fetching chat histories: {e}")

