# /app/models/response_model.py
"""
This module defines the response models for the FastAPI application.
"""

from pydantic import BaseModel, ValidationError
from typing import List

class BoundingBox(BaseModel):
    left: float
    top: float
    width: float
    height: float

class ResponseItem(BaseModel):
    key: str
    matching_key: str
    matching_value: str
    value: str
    additional_comments: str
    page: int
    bounding_box: BoundingBox
    confidence: float

class Response(BaseModel):
    data: List[ResponseItem]

# Example Usage
if __name__ == "__main__":
    example_data = {
        "data": [
            {
                "key": "Policy Number",
                "matching_key": "Policy Number",
                "matching_value": "97-B8-5008-1",
                "value": "97-B8-5008-1",
                "additional_comments": "This is a comment.",
                "page": 1,
                "bounding_box": {
                    "left": 100.5,
                    "top": 200.5,
                    "width": 50.0,
                    "height": 20.0
                },
                "confidence": 0.98
            },
            {
                "key": "Loan Number",
                "matching_key": "Loan Number",
                "matching_value": "100001168",
                "value": "100001168",
                "additional_comments": "Another comment.",
                "page": 2,
                "bounding_box": {
                    "left": 150.5,
                    "top": 250.5,
                    "width": 60.0,
                    "height": 30.0
                },
                "confidence": 0.95
            }
        ]
    }
    try:
        Response(**example_data)
        print("Validation successful.")
    except ValidationError as e:
        print(f"Validation failed: {e}")
