from pydantic import BaseModel
from typing import List

class BoundingBox(BaseModel):
    page: int
    bbox: List[int]
    text: str

    def to_dict(self):
        return {
            "page": self.page,
            "bbox": self.bbox,
            "text": self.text
    }

class ExtractionResponse(BaseModel):
    data: str
    bounding_boxes: List[BoundingBox]

    def to_dict(self):
        return {
            "data": self.data,
            "bounding_boxes": [bbox.dict() for bbox in self.bounding_boxes]
        }
