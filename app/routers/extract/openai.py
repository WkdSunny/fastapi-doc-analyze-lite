# /app/routers/extract/openai.py
"""
This module defines the extraction routes for the FastAPI application using OpenAI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_clients.openai import extract_with_openai
from app.models.response_model import ExtractionResponse, ExtractionItem, ExtractionRequest
import logging

router = APIRouter(
    prefix="/extract/openai",
    tags=["extract_openai"]
)

logger = logging.getLogger(__name__)

@router.post("/", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    try:
        # Call the function to extract data using OpenAI API
        response = await extract_with_openai(request.text, request.prompt)
        
        # Ensure the response is in the expected format
        if not response or not isinstance(response, list):
            logger.error("Invalid response format from OpenAI API")
            raise HTTPException(status_code=500, detail="Invalid response format from OpenAI API")

        # Map the response to the expected format
        extraction_items = []
        for item in response:
            extraction_item = ExtractionItem(
                extracted_key=item.get("Information Key", "N/A"),
                extracted_value=item.get("Value", "N/A"),
            )
            extraction_items.append(extraction_item)
        
        return ExtractionResponse(data=extraction_items)
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
