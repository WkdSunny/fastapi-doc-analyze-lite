# /app/services/retrieve.py
"""
This module defines the data retrieval service for the FastAPI application.
"""

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.retrieve import db_retrieve_data
from app.config import logger

class RetrieveRequest(BaseModel):
    document_id: str
    retrieve_data: List[str]
    linked: Optional[bool] = False

router = APIRouter(
    prefix="/retrieve",
    tags=["retrieve"]
)

VALID_RETRIEVE_OPTIONS = ["document", "segment", "entity", "classification", "topics", "tfidf", "questions"]

@router.post("/")
async def retrieve_endpoint(payload: RetrieveRequest):
    """
    Retrieve data from the database based on document_id and requested data types.

    Args:
        document_id (str): The ID of the document to retrieve data for.
        retrieve_data (List[str]): A list of data types to retrieve (e.g., ["document", "segment"]).
        linked (bool): Whether to return the data in a linked (nested) structure. Default is False.

    Returns:
        Dict[str, Any]: A dictionary containing the retrieved data.

    Raises:
        HTTPException: If an error occurs during data retrieval or if input is invalid.
    """
    document_id = payload.document_id
    retrieve_data = payload.retrieve_data
    linked = payload.linked
    
    # Input validation
    if not document_id:
        raise HTTPException(status_code=400, detail="Document ID must be provided.")
    
    if not all(data_type in VALID_RETRIEVE_OPTIONS for data_type in retrieve_data):
        raise HTTPException(status_code=400, detail=f"Invalid retrieve_data options. Valid options are: {VALID_RETRIEVE_OPTIONS}")

    try:
        logger.info(f"Starting data retrieval for document_id: {document_id} with retrieve_data: {retrieve_data}, linked: {linked}")

        # Perform the data retrieval
        result = await db_retrieve_data(document_id, retrieve_data, linked)

        logger.info(f"Data retrieval successful for document_id: {document_id}")
        
        return {
            "status": 200,
            "success": True,
            "result": result
        }

    except ValueError as ve:
        logger.error(f"ValueError in retrieve_endpoint: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        logger.error(f"Unexpected error in retrieve_endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during data retrieval.")

# Example usage:
if __name__ == "__main__":
    import asyncio
    from app.services.db import retrieve as db_retrieve

    async def test_retrieve():
        document_id = "test_document_id"
        retrieve_data = ["document", "segment", "entity", "classification", "topics", "tfidf", "questions"]
        linked = True

        result = await db_retrieve_data(document_id, retrieve_data, linked)
        print(result)

    asyncio.run(test_retrieve())