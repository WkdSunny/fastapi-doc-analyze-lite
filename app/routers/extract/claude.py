from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_clients.claude import extract_with_claude
from app.models.response_model import ExtractionResponse
from app.config import logger

router = APIRouter(
    prefix="/extract/claude",
    tags=["extract_claude"]
)

class ExtractionRequest(BaseModel):
    text: str
    prompt: str

@router.post("/", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    """
    Extract data from text using Claude LLM.

    Args:
    request (ExtractionRequest): Request object containing text and prompt.

    Returns:
    ExtractionResponse: Contains extracted data and bounding boxes.
    """
    try:
        response = await extract_with_claude(request.text, request.prompt)
        return response
    except Exception as e:
        logger.error(f"Failed to extract data with Claude: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
