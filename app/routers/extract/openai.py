# /app/routers/extract/openai.py
"""
This module defines the extraction routes for the FastAPI application using OpenAI.
"""

import json
from fastapi import APIRouter, HTTPException
from app.config import logger
from app.utils.model_utils import csv_to_json
from app.services.llm_clients.openai import extract_with_openai
from app.models.pdf_model import BoundingBox, PDFTextResponse
from app.models.llm_model import ExtractionResponse, ExtractionItem, ExtractionRequest
from app.utils.bbox_mapping import map_bbox_to_data

router = APIRouter(
    prefix="/extract/openai",
    tags=["extract_openai"]
)

@router.post("/", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    try:
        # Parse bounding_boxes JSON string into a list of BoundingBox models
        # bbox_data = json.loads(request.bounding_boxes)
        # bounding_boxes = [BoundingBox(**bbox) for bbox in bbox_data]

        # Create PDFTextResponse with parsed bounding_boxes
        # pdf_text_response = PDFTextResponse(
        #     file_name="",
        #     text="",
        #     bounding_boxes=bounding_boxes
        # )

        # Call the function to extract data using OpenAI API
        response = await extract_with_openai(request.text, request.prompt)
        logger.debug(f"Response from OpenAI API: {response}, Data type: {type(response)}")

        response = csv_to_json(response)
        logger.debug(f"Response after conversion: {response.dict()}, Data type: {type(response.dict())}")

        # final_response = await map_bbox_to_data(response.data, [pdf_text_response])
        # logger.debug(f"Final response after mapping: {final_response}, Data type: {type(final_response)}")
        # final_response = ExtractionResponse(data=final_response)

        # return final_response
        return response
    
    except ValueError as ve:
        logger.error(f'ValueError occurred: {str(ve)}')
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f'Unexpected error occurred: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

# Example Usage:
if __name__ == "__main__":
    import asyncio

    async def test_extraction():
        request = ExtractionRequest(
            text="This is a test document.",
            prompt="Extract the following information: Name, Address, Phone Number."
        )
        response = await extract_data(request)
        print(response)

    asyncio.run(test_extraction())
