from pydantic import BaseModel
from typing import List

class coordinates(BaseModel):
    left: float
    top: float
    width: float
    height: float

    def to_dict(self):
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height
        }

class BoundingBox(BaseModel):
    page: int
    bbox: coordinates
    text: str
    confidence: float

    def to_dict(self):
        return {
            "page": self.page,
            "bbox": self.bbox.to_dict(),
            "text": self.text,
            "confidence": self.confidence
        }

class PDFTextResponse(BaseModel):
    file_name: str
    text: str
    bounding_boxes: List[BoundingBox]

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "text": self.text,
            "bounding_boxes": [bbox.to_dict() for bbox in self.bounding_boxes]
        }
