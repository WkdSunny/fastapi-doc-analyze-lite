# /app/utils/bbox_mapping.py
"""
This module defines the bbox mapping functions for the FastAPI application.
"""

from typing import List, Dict, Any
from app.models.pdf_model import coordinates, BoundingBox, PDFTextResponse
from app.models.llm_model import ExtractionItem
from app.models.response_model import ResponseItem, BoundingBox as ResponseBoundingBox

def convert_to_bbox_models(data: List[dict]) -> List[PDFTextResponse]:
    bbox_models = []
    for item in data:
        bounding_boxes = [BoundingBox(**bbox) for bbox in item.get('bounding_boxes', [])]
        bbox_models.append(PDFTextResponse(
            file_name=item.get('file_name', 'N/A'),
            text=item.get('text', 'N/A'),
            bounding_boxes=bounding_boxes
        ))
    return bbox_models

def convert_to_llm_models(data: List[dict]) -> List[ExtractionItem]:
    return [ExtractionItem(**item) for item in data]

async def get_bbox(bbox_data: List[BoundingBox]) -> List[Dict[str, Any]]:
    """
    Extract bounding boxes from the provided PDFTextResponse data.
    
    Parameters:
        bbox_data (List[PDFTextResponse]): List of PDFTextResponse objects.
    
    Returns:
        List[Dict[str, Any]]: List of bounding box dictionaries.
    """
    bounding_boxes = []
    try:
        for item in bbox_data:
            for bbox in item.bounding_boxes:
                bounding_boxes.append({
                    "text": bbox.text,
                    "page": bbox.page,
                    "bbox": {
                        "left": bbox.bbox.left,
                        "top": bbox.bbox.top,
                        "width": bbox.bbox.width,
                        "height": bbox.bbox.height
                    },
                    "confidence": bbox.confidence
                })
    except Exception as e:
        print(f"Error extracting bounding boxes: {str(e)}")
    
    return bounding_boxes

async def map_bbox_to_data(llm_data: List[ExtractionItem], bbox_data: List[PDFTextResponse]) -> List[ResponseItem]:
    """
    Map bounding boxes to the LLM data.
    
    Parameters:
        llm_data (List[ExtractionItem]): List of ExtractionItem objects containing LLM extracted data.
        bbox_data (List[PDFTextResponse]): List of PDFTextResponse objects containing bounding box information.
    
    Returns:
        List[ResponseItem]: LLM data with mapped bounding box information.
    """
    bounding_boxes = await get_bbox(bbox_data)
    response_items = []
    
    try:
        for item in llm_data:
            for bbox in bounding_boxes:
                if item.matching_value == bbox["text"]:
                    response_item = ResponseItem(
                        key=item.key,
                        matching_key=item.matching_key,
                        matching_value=item.matching_value,
                        value=item.value,
                        additional_comments=item.additional_comments,
                        page=bbox["page"],
                        bounding_box=ResponseBoundingBox(**bbox["bbox"]),
                        confidence=bbox["confidence"]
                    )
                    response_items.append(response_item)
                    break  # Break after finding the first match to avoid redundant checks
                else:
                    response_item = ResponseItem(
                    key=item.key,
                    matching_key=item.matching_key,
                    matching_value=item.matching_value,
                    value=item.value,
                    additional_comments=item.additional_comments,
                    page=-1,  # Default value indicating no page found
                    bounding_box=ResponseBoundingBox(left=0, top=0, width=0, height=0),
                    confidence=0.0
                )
                response_items.append(response_item)
    except Exception as e:
        print(f"Error mapping bounding boxes to LLM data: {str(e)}")
    
    return response_items

# Example Usage
if __name__ == "__main__":
    import asyncio

    llm_data = [
        ExtractionItem(
            key="key1",
            matching_key="matching_key1",
            matching_value="matching_value1",
            value="value1",
            additional_comments="comments1"
        )
    ]
    bbox_data = [
        PDFTextResponse(
            file_name="example.pdf",
            text="Example text",
            bounding_boxes=[
                BoundingBox(
                    text="matching_key1",
                    page=1,
                    bbox=coordinates(left=0, top=0, width=100, height=100),
                    confidence=0.9
                )
            ]
        )
    ]
    
    mapped_data = asyncio.run(map_bbox_to_data(llm_data, bbox_data))
    for item in mapped_data:
        print(item.json(indent=2))
