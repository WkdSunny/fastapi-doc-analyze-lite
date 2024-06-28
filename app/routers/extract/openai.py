from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_clients.openai import extract_with_openai
from app.models.response_model import ExtractionResponse

router = APIRouter(
    prefix="/extract/openai",
    tags=["extract_openai"]
)

class ExtractionRequest(BaseModel):
    text: str
    prompt: str

@router.post("/", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    try:
        response = await extract_with_openai(request.text, request.prompt)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
