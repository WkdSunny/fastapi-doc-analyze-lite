from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from app.models.pdf_model import BoundingBox

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
    text: str
    confidence: float

class Entity(MongoBaseModel):
    document_id: str
    entity: str
    text: str

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
    
class TokenUsage(MongoBaseModel):
    document_id: str
    llm: str
    consumer: str
    token: str
    count: int