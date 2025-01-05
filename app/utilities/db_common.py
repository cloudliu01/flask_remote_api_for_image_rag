from sqlalchemy.orm import Session
from datetime import datetime
from contextlib import contextmanager
from app.utilities.common import TZ, convert_datetime_with_timezone
from app.models import Account, ChatSession, ChatHistory, Image, Embedding, Device

def image_data_to_db(
    db_session: Session,
    image_metadata: dict,
    image_embedding: list,
    account_name: str,
    account_source: str,
    session_id: str,
    image_path: str,
):
    """
    Stores image metadata, embedding, and related data into the database.

    :param db_session: SQLAlchemy session object.
    :param image_path: Path to the uploaded image file.
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
            time=datetime.now(TZ),
            content="Image uploaded with metadata and embedding."
        )
        db_session.add(chat_history)
        db_session.commit()

        return image

    except Exception as e:
        db_session.rollback()
        print(f"An error occurred while storing image data: {e}")
        return None
