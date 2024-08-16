from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from app.models.pdf_model import coordinates, BoundingBox

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return str(v)

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {
            ObjectId: str,
        }
class Document(MongoBaseModel):
    file_name: str
    uploaded_at: str
    text: str
    bounding_boxes: Optional[List[BoundingBox]] = None
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
    entities: List[str]
    topics: List[str]
    tfidf_keywords: List[str]
    
