# /app/models/db.model.py
"""
This module defines the Pydantic models for the database operations.
"""

from pydantic import BaseModel
from typing import List, Dict, Optional

class Document(BaseModel):
    """
    Represents a document with metadata and text content.
    """
    file_name: str
    uploaded_at: str
    text: str
    status: str

class BoundingBox(BaseModel):
    """
    Represents the bounding box coordinates for a segment of a document.
    Used for PDFs or image-based documents.
    """
    left: Optional[float]
    top: Optional[float]
    width: Optional[float]
    height: Optional[float]

class Segment(BaseModel):
    """
    Represents a segment of a document, including optional page and bounding box information.
    Used for both PDF/image documents (with bounding boxes) and text/Excel documents.
    """
    document_id: str
    page: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    text: str
    confidence: float

class Entity(BaseModel):
    """
    Represents an entity extracted from a document.
    """
    document_id: str
    word: str
    entity: str
    score: float
    start: int
    end: int

class Topic(BaseModel):
    """
    Represents a topic generated from a document.
    """
    document_id: str
    key: int
    terms: List[str]

class Classification(BaseModel):
    """
    Represents a classification result for a document.
    """
    document_id: str
    label: str
    score: float

class Question(BaseModel):
    """
    Pydantic model for the question generation request.
    """
    document_id: str
    entities: List[str]
    topics: Dict[int, List[str]]