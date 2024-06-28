from pydantic import BaseModel
from typing import List

class BoundingBox(BaseModel):
    page: int
    bbox: List[int]
    text: str

class ExtractionResponse(BaseModel):
    data: str
    bounding_boxes: List[BoundingBox]
