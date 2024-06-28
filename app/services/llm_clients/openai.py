from app.config import settings
from app.models.response_model import ExtractionResponse
import openai
import requests

async def extract_with_openai(text: str, prompt: str) -> ExtractionResponse:
    openai.api_key = settings.OPENAI_API_KEY
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=f"{prompt}\n\n{text}",
        max_tokens=1500
    )
    # Placeholder for actual extraction and bounding box determination logic
    return ExtractionResponse(data="extracted data", bounding_boxes=[{"page": 1, "bbox": [0, 0, 100, 100], "text": "sample"}])