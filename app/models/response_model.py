# /app/models/response_model.py
"""
This module defines the response models for the FastAPI application.
"""

from pydantic import BaseModel
from typing import List

class ExtractionRequest(BaseModel):
    text: str
    prompt: str

# class BoundingBox(BaseModel):
#     left: float
#     top: float
#     width: float
#     height: float

class ExtractionItem(BaseModel):
    extracted_key: str
    extracted_value: str
    # page: int
    # bounding_box: BoundingBox
    # confidence: float

class ExtractionResponse(BaseModel):
    data: List[ExtractionItem]
    # bounding_boxes: List[BoundingBox]
