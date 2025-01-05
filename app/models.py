from sqlalchemy import (
    BigInteger, Integer, String, Float, Column, ForeignKey, TIMESTAMP, JSON, Text, DateTime
)
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Integer, String, Float, Column, ForeignKey, TIMESTAMP, JSON, Text
from geoalchemy2 import Geography

from geoalchemy2 import Geometry, Geography
from geoalchemy2.elements import WKTElement

try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = "session"

    id = Column(BigInteger, primary_key=True)
    session_id = Column(String, nullable=False)
    create_time = Column(TIMESTAMP, nullable=False)

    def __repr__(self):
        return f"<Session(id={self.id}, session_id={self.session_id})>"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    source = Column(String, nullable=False)
    create_time = Column(TIMESTAMP, nullable=False)

    images = relationship("Image", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Device(Base):
    __tablename__ = "device"

    id = Column(Integer, primary_key=True)
    device_maker = Column(String, nullable=False)
    device_model = Column(String, nullable=False)

    images = relationship("Image", back_populates="device")

    def __repr__(self):
        return f"<Device(id={self.id}, device_maker={self.device_maker}, device_model={self.device_model})>"


class Image(Base):
    __tablename__ = "image"

    id = Column(BigInteger, primary_key=True)
    path = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("device.id"), nullable=True)
    location = Column(Geography("POINT", srid=4326), nullable=True)  # Use Geography for location
    taken_time = Column(TIMESTAMP, nullable=True)
    focus_35mm = Column(Integer, nullable=True)
    orientation_from_north = Column(Float, nullable=True)
    other_metadata = Column(JSON, nullable=True)

    creator = relationship("User", back_populates="images")
    device = relationship("Device", back_populates="images")
    embeddings = relationship("Embedding", back_populates="image")

    def __repr__(self):
        return f"<Image(id={self.id}, path={self.path})>"


class Embedding(Base):
    __tablename__ = "embedding"

    id = Column(BigInteger, primary_key=True)
    image_id = Column(BigInteger, ForeignKey("image.id"), nullable=False)
    transcript_id = Column(BigInteger, ForeignKey("transcript.id"), nullable=True)
    image_embedding = Column(Vector, nullable=False)  
    text_embedding = Column(Vector, nullable=True)

    image = relationship("Image", back_populates="embeddings")
    transcript = relationship("Transcript", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, image_id={self.image_id})>"
