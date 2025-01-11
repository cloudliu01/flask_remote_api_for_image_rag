from sqlalchemy import BigInteger, Integer, String, Float, Column, ForeignKey, TIMESTAMP, JSON, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from geoalchemy2 import Geography

from geoalchemy2 import Geometry, Geography
from geoalchemy2.elements import WKTElement
from flask_sqlalchemy import SQLAlchemy

#from app import db
db = SQLAlchemy()

from sqlalchemy import (
    BigInteger, Integer, String, Float, Column, ForeignKey, TIMESTAMP, JSON, Text
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from geoalchemy2 import Geography
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    create_time = Column(TIMESTAMP(timezone=True), nullable=False)

    images = relationship('Image', back_populates='creator')  # Plural for many-to-one
    chat_histories = relationship('ChatHistory', back_populates='account')  # Plural for many-to-one


class Device(db.Model):
    __tablename__ = 'device'
    id = Column(Integer, primary_key=True)
    device_maker = Column(String, nullable=False)
    device_model = Column(String, nullable=False)

    images = relationship('Image', back_populates='device')  # Plural for many-to-one


class Transcript(db.Model):
    __tablename__ = 'transcript'
    id = Column(BigInteger, primary_key=True)
    text = Column(Text, nullable=False)

    embeddings = relationship('Embedding', back_populates='transcript')  # Plural for one-to-many


class Embedding(db.Model):
    __tablename__ = 'embedding'
    id = Column(BigInteger, primary_key=True)
    image_id = Column(BigInteger, ForeignKey('image.id'), nullable=False)
    transcript_id = Column(BigInteger, ForeignKey('transcript.id'), nullable=True)
    image_embedding = Column(Vector, nullable=False)
    transcript_embedding = Column(Vector, nullable=True)

    image = relationship('Image', back_populates='embeddings')  # Plural for one-to-many
    transcript = relationship('Transcript', back_populates='embeddings')  # Plural for one-to-many


class ChatSession(db.Model):
    __tablename__ = 'chat_session'
    id = Column(BigInteger, primary_key=True)
    session_id = Column(String, nullable=False)
    create_time = Column(TIMESTAMP(timezone=True), nullable=True)

    chat_histories = relationship('ChatHistory', back_populates='session')  # Plural for one-to-many


class Image(db.Model):
    __tablename__ = 'image'
    id = Column(BigInteger, primary_key=True)
    path = Column(String, nullable=True)
    md5 = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('device.id'), nullable=True)
    location = Column(Geography('POINT', srid=4326), nullable=True)
    taken_time = Column(TIMESTAMP(timezone=True), nullable=True)
    focus_35mm = Column(Integer, nullable=True)
    orientation_from_north = Column(Float, nullable=True)
    other_metadata = Column(JSON, nullable=True)

    creator = relationship('Account', back_populates='images')  # Plural for one-to-many
    device = relationship('Device', back_populates='images')  # Plural for one-to-many
    embeddings = relationship('Embedding', back_populates='image')  # Plural for one-to-many
    chat_histories = relationship('ChatHistory', back_populates='image')  # Plural for one-to-many


class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey('chat_session.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    image_id = Column(BigInteger, ForeignKey('image.id'), nullable=True)
    time = Column(TIMESTAMP(timezone=True), nullable=False)
    location = Column(Geography('POINT', srid=4326), nullable=True)
    prompt = Column(JSON, nullable=False)
    llm_reply = Column(String, nullable=True)

    session = relationship('ChatSession', back_populates='chat_histories')  # Plural for one-to-many
    account = relationship('Account', back_populates='chat_histories')  # Plural for one-to-many
    image = relationship('Image', back_populates='chat_histories', foreign_keys=[image_id])  # Plural for one-to-many
