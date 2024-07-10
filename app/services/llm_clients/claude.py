from app.config import settings
from app.models.llm_model import ExtractionResponse
import requests

async def extract_with_claude(text: str, prompt: str) -> ExtractionResponse:
    response = requests.post(
        "https://api.anthropic.com/v1/claude/completion",
        headers={"Authorization": f"Bearer {settings.CLAUDE_API_KEY}"},
        json={"prompt": f"{prompt}\n\n{text}"}
    )
    # Placeholder for actual extraction and bounding box determination logic
    return ExtractionResponse(data="extracted data", bounding_boxes=[{"page": 1, "bbox": [0, 0, 100, 100], "text": "sample"}])
