# /app/models/llm_model.py
"""
This module defines the llm response models for the FastAPI application.
"""

from pydantic import BaseModel
from typing import List

class ExtractionRequest(BaseModel):
    text: str
    prompt: str
    # bounding_boxes: str

class ExtractionItem(BaseModel):
    key: str
    matching_key: str
    matching_value: str
    value: str
    additional_comments: str

class ExtractionResponse(BaseModel):
    data: List[ExtractionItem]

# Example Usage
if __name__ == "__main__":
    example_data = {
        "data": [
            {
                "key": "Policy Number",
                "matching_key": "Policy Number",
                "matching_value": "97-B8-5008-1",
                "value": "97-B8-5008-1",
                "additional_comments": "This is a comment."
            },
            {
                "key": "Loan Number",
                "matching_key": "Loan Number",
                "matching_value": "100001168",
                "value": "100001168",
                "additional_comments": "Another comment."
            }
        ]
    }
    try:
        ExtractionResponse(**example_data)
        print("Validation successful.")
    except Exception as e:
        print(f"Validation failed: {e}")