from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, TIMESTAMP, Text, SmallInteger, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime

Base = declarative_base()

class Token(BaseModel):
    userId: int
    username: str
    access_token: str
    token_type: str

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    profile_picture_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Relationship to the UserDetection model
    detections = relationship('UserDetection', back_populates='user')
    feedbacks = relationship('Feedback', back_populates='user')
    plant = relationship('Plant', back_populates='user')

class UserDetection(Base):
    __tablename__ = 'user_detection'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    plant_id = Column(Integer, ForeignKey('plant.id', ondelete='CASCADE'))
    image_url = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    symptoms = Column(Text, nullable=False)
    cause = Column(Text, nullable=False)
    treatment = Column(Text, nullable=False)
    confidence_score = Column(Float)
    detection_date = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship('User', back_populates='detections')
    feedbacks = relationship('Feedback', back_populates='detection')
    plant = relationship('Plant', back_populates='detection')


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    detection_id = Column(Integer, ForeignKey('user_detection.id', ondelete='CASCADE'))
    rating = Column(SmallInteger, nullable=False)
    comments = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship('User', back_populates='feedbacks')
    detection = relationship('UserDetection', back_populates='feedbacks')
    
class Plant(Base):
    __tablename__ = 'plant'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    nama = Column(String(255), nullable=False)


    # Relationships
    user = relationship('User', back_populates='plant')
    detection = relationship('UserDetection', back_populates='plant')