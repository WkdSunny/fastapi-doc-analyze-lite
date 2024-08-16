# /app/services/db/retrieve.py
"""
This module defines the database retrieval services for the FastAPI application.
"""

from bson import ObjectId
from typing import List, Type, Any
from pymongo.errors import PyMongoError
from pydantic import BaseModel
from app.utils.db_utils import find_many_documents
from app.models.db_model import Document, Segment, Entity, Classification, Topic, TFIDF, Question
from app.config import logger

async def retrieve_data(collection_name: str, field_name: str, document_id: str, model: Type[BaseModel]) -> List[Any]:
    """
    Generic function to retrieve data from a specified MongoDB collection.

    Args:
        collection_name (str): The name of the MongoDB collection.
        document_id (str): The document ID to query.
        model (Type[BaseModel]): The Pydantic model to use for the data.

    Returns:
        List[Any]: A list of Pydantic models representing the retrieved data.
    
    Raises:
        RuntimeError: If there is an error during retrieval.
    """
    try:
        if field_name == "_id":
            document_id = ObjectId(document_id)
        data = list(find_many_documents(collection_name, {str(field_name): document_id}))
        logger.info(f"Retrieved {len(data)} documents from {collection_name} for document_id {document_id}")

        if collection_name == "Documents":
            for item in data:
                item['document_id'] = str(item['_id']) 
                
        return [model(**item) for item in data]
    except PyMongoError as e:
        logger.error(f"Error retrieving data from {collection_name} for document_id {document_id}: {e}")
        raise RuntimeError(f"Error retrieving data from {collection_name} for document_id {document_id}: {e}")

async def retrieve_documents(document_id: str) -> List[Any]:
    return await retrieve_data("Documents", "_id", document_id, Document)

async def retrieve_segments(document_id: str) -> List[Any]:
    return await retrieve_data("Segments", "document_id", document_id, Segment)

async def retrieve_entities(document_id: str) -> List[Any]:
    return await retrieve_data("Entities", "document_id", document_id, Entity)

async def retrieve_classifications(document_id: str) -> List[Any]:
    return await retrieve_data("DocumentClassification", "document_id", document_id, Classification)

async def retrieve_topics(document_id: str) -> List[Any]:
    return await retrieve_data("Topics", "document_id", document_id, Topic)

async def retrieve_tfidf(document_id: str) -> List[Any]:
    return await retrieve_data("TFIDFKeywords", "document_id", document_id, TFIDF)

async def retrieve_questions(document_id: str) -> List[Any]:
    return await retrieve_data("Questions", "document_id", document_id, Question)
