# /src/app/models/rag_model.py
"""
This module defines the Pydantic models for the question generation routes.
"""

from pydantic import BaseModel
from typing import List, Optional
from app.models.pdf_model import coordinates

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
    left: Optional[float] = 0.0
    top: Optional[float] = 0.0
    width: Optional[float] = 0.0
    height: Optional[float] = 0.0

class Segment(BaseModel):
    """
    Represents a segment of a document, including optional page and bounding box information.
    Used for both PDF/image documents (with bounding boxes) and text/Excel documents.
    """
    serial: int
    page: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    text: str
    confidence: float

class Entity(BaseModel):
    """
    Represents an entity extracted from a document.
    """
    serial: int
    word: str
    entity: str
    score: float
    start: Optional[int] = 0
    end: Optional[int] = 0

class Classification(BaseModel):
    """
    Represents a classification result for a document.
    """
    label: str
    score: float

class Topic(BaseModel):
    serial: int
    words: List[str]

class RAGQuestionRequest(BaseModel):
    """
    Represents a request to generate questions from a document segment.
    """
    document_id: Optional[str] = None
    document_text: str
    # entities: List[str]
    # topics: List[str]

class RAGQuestionGenerator(BaseModel):
    """
    Represents a question generated from a document segment.
    """
    serial: int
    entities: List[str]
    topics: List[str]