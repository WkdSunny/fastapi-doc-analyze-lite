# /app/routers/extract/openai.py
"""
This module defines the extraction routes for the FastAPI application using OpenAI.
"""

from fastapi import APIRouter, HTTPException
from app.config import logger
from app.utils.model_utils import csv_to_json
from app.services.llm_clients.openai import send_openai_request
from app.models.llm_model import ExtractionResponse, ExtractionItem, ExtractionRequest
from app.utils.llm_utils import default_system_prompt, default_user_prompt
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
    
def prepare_prompt(text: str, prompt: str) -> str:
    """
    Prepare the final prompt to be sent to the OpenAI API.
    """
    if not prompt:
        prompt = default_user_prompt()

    return f"{prompt}\n<Content>\n{text}\n</Content>"

def prepare_messages(system_prompt, user_prompt: str) -> list:
    """
    Prepare the messages for the OpenAI API request.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

async def extract_with_openai(text: str, prompt: str) -> dict:
    """
    Main function to get the response from OpenAI API.
    """
    if not text:
        raise ValueError('Data is required')

    final_prompt = prepare_prompt(text, prompt)
    logger.debug(f'Final prompt is: {final_prompt}')

    messages = prepare_messages(default_system_prompt(), final_prompt)

    try:
        result = await send_openai_request(messages)
        if not result['success']:
            raise ValueError(result['message'])

        raw_response = result['response']['choices'][0]['message']['content']
        return raw_response.strip()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise ValueError(str(e))

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
