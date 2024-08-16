"""
This module defines the Pydantic models for the database operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

class MongoBaseModel(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")

    class Config:
        json_encoders = {
            ObjectId: str,
        }
        orm_mode = True

class Document(MongoBaseModel):
    file_name: str
    uploaded_at: str
    text: str
    status: str

class Segment(MongoBaseModel):
    document_id: str
    serial: int
    page: Optional[int] = None
    bbox: Optional[dict] = None  # Assuming bounding boxes are dictionaries
    text: str
    confidence: float

class Entity(MongoBaseModel):
    document_id: str
    serial: int
    word: str
    entity: str
    score: float
    start: Optional[int] = None
    end: Optional[int] = None

class Classification(MongoBaseModel):
    document_id: str
    label: str
    score: float

class Topic(MongoBaseModel):
    document_id: str
    serial: int
    words: List[str]

class TFIDF(MongoBaseModel):
    document_id: str
    keyword: str

class Question(MongoBaseModel):
    document_id: str
    serial: int
    question: str
    score: float
