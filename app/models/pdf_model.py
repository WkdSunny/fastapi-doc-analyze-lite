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

class PDFTextResponse(BaseModel):
    file_name: str
    text: str
    bounding_boxes: List[BoundingBox]

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "text": self.text,
            "bounding_boxes": [bbox.dict() for bbox in self.bounding_boxes]
        }
