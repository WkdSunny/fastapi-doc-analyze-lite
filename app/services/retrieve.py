# /app/services/retrieve.py
"""
This module defines the data retrieval service for the FastAPI application.
"""

from typing import List, Dict, Any
from app.services.db import retrieve as db_retrieve
from app.config import logger

async def db_retrieve_data(document_id: str, retrieve_data: List[str], linked: bool = False) -> Dict[str, Any]:
    """
    Retrieve data from the database based on the document ID and requested data types.

    Args:
        document_id (str): The ID of the document to retrieve data for.
        retrieve_data (List[str]): A list of data types to retrieve (e.g., ["document", "segment"]).
        linked (bool): Whether to return the data in a linked (nested) structure. Default is False.

    Returns:
        Dict[str, Any]: A dictionary containing the retrieved data.
    """
    data = {}
    
    try:
        documents = await db_retrieve.retrieve_documents(document_id)
        if not documents:
            raise ValueError(f"No document found for ID: {document_id}")
        
        data["document"] = documents
        data["segment"] = await db_retrieve.retrieve_segments(document_id)
        data["entity"] = await db_retrieve.retrieve_entities(document_id)    
        data["classification"] = await db_retrieve.retrieve_classifications(document_id)
        data["topics"] = await db_retrieve.retrieve_topics(document_id)
        data["tfidf"] = await db_retrieve.retrieve_tfidf(document_id)
        data["questions"] = await db_retrieve.retrieve_questions(document_id)

        if linked:
            data = create_linked_response(data)
        
        return data

    except Exception as e:
        logger.error(f"Error in db_retrieve_data: {e}")
        raise

def create_linked_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a linked (nested) JSON structure from the retrieved data.

    Args:
        data (Dict[str, Any]): The dictionary of retrieved data.

    Returns:
        Dict[str, Any]: The nested structure.
    """
    # Example of a simple linked structure
    linked_data = {}
    
    # Assume documents are always present if linked is True
    if "document" in data and data["document"]:
        linked_data["document"] = data["document"][0]  # Assume one document per ID

        if "segment" in data and data["segment"]:
            linked_data["document"]["segments"] = data["segment"]

        if "entity" in data and data["entity"]:
            linked_data["document"]["entities"] = data["entity"]

        if "classification" in data and data["classification"]:
            linked_data["document"]["classification"] = data["classification"]

        if "topics" in data and data["topics"]:
            linked_data["document"]["topics"] = data["topics"]

        if "tfidf" in data and data["tfidf"]:
            linked_data["document"]["tfidf"] = data["tfidf"]

        if "questions" in data and data["questions"]:
            linked_data["document"]["questions"] = data["questions"]

    return linked_data
