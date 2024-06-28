from pydantic import BaseModel
from typing import List

class BoundingBox(BaseModel):
    page: int
    bbox: List[int]
    text: str

class PDFTextResponse(BaseModel):
    file_name: str
    text: str
    bounding_boxes: List[BoundingBox]
