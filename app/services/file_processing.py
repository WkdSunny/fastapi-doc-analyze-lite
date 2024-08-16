import aiofiles
import filetype
from fastapi import UploadFile, Request, HTTPException
from typing import List
from app.utils.api_utils import AsyncAPIClient
from app.config import settings, logger, get_base_url

async def save_temp_file(file: UploadFile) -> str:
    """
    Save the uploaded file to a temporary path asynchronously.
    """
    temp_path = f"/tmp/{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as temp_file:
        await temp_file.write(await file.read())
    return temp_path

async def get_file_type(file: UploadFile) -> str:
    kind = filetype.guess(await file.read(2048))
    await file.seek(0)  # Reset file pointer after reading
    return kind.mime.lower() if kind else None

async def call_question_generation_api(request: Request, document_id: str, entities: List[str], topics: List[str]):
    """
    Call the question generation API to generate questions from the text.
    """
    try:
        # Construct the base URL
        url = get_base_url(str(request.url).rstrip('/'))
        logger.debug(f"Base URL for question generation: {url}")
        
        # Initialize the API client with the constructed base URL
        api_client = AsyncAPIClient(
            base_url=url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.BEARER_TOKEN}"
            },
        )
        
        # Prepare the payload for the API call
        question_payload = {
            "document_id": str(document_id),
            "entity_words": entities,
            "topic_words": topics
        }
        logger.debug(f"Question generation payload: {question_payload}")
        
        # Make the API call to generate questions
        response = await api_client.post(settings.QUESTIONS_ENDPOINT, json=question_payload)
        logger.debug(f"Question generation API response: {response}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error during question generation API call: {e}")
        raise HTTPException(status_code=500, detail=str(e))