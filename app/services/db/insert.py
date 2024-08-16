# /app/services/db/insert.py
"""
This module defines the database insertion functions for the FastAPI application.
"""

from typing import List, Optional
from datetime import datetime, timezone
from app.models.rag_model import Segment, Entity, Topic, Classification, RAGQuestionGenerator
from app.config import settings, logger

async def insert_documents(file_name: str, result: str) -> str:
    """
    Insert the document data and its segments into the MongoDB database.

    Args:
        file_name (str): The name of the file.
        result_text (str): The text extracted from the document.

    Returns:
        str: The ID of the inserted document.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        document_data = {
            "file_name": file_name,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "text": result["text"],
            "bounding_boxes": result["bounding_boxes"],
            "status":"processed"
        }
        document_id = settings.mongo_client["Documents"].insert_one(document_data).inserted_id
        logger.info(f"Successfully inserted document with ID: {document_id}")
        return str(document_id)
    except Exception as e:
        logger.error(f"Failed to insert document: {e}")
        raise

async def insert_task(document_ids: List[str]):
    """
    Insert a Task document containing all the document IDs processed in this task.

    Args:
        document_ids (List[str]): A list of document IDs associated with this task.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        task_data = {
            "document_ids": document_ids,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        task_id = settings.mongo_client["Tasks"].insert_one(task_data).inserted_id
        logger.info(f"Successfully inserted task with ID: {task_id}")
        return str(task_id)

    except Exception as e:
        logger.error(f"Failed to insert task: {e}")
        raise

async def insert_segments(document_id: str, segments: List[Segment]):
    """
    Insert the document data and its segments into the MongoDB database.

    Args:
        document_id (str): The ID of the document to which the segments belong.
        segments (List[in_Segment]): A list of Segment model instances to be inserted.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        # Convert Segment models to dictionaries and add the document_id to each segment
        segment_dicts = [segment.dict() for segment in segments]
        for segment in segment_dicts:
            segment["document_id"] = document_id
        
        # Insert the segments into the Segments collection
        settings.mongo_client["Segments"].insert_many(segment_dicts)
        logger.info(f"Successfully inserted {len(segment_dicts)} segments for document ID: {document_id}")
    
    except Exception as e:
        logger.error(f"Failed to insert segments for document ID: {document_id}: {e}")
        raise

async def insert_entities(document_id: Optional[str], entities: List[Entity]):
    """
    Insert entity records into the MongoDB database.

    Args:
        document_id (str): The ID of the document to which the entities belong.
        entities (List[in_Entity]): A list of Entity model instances to be inserted.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        # Convert input Entity models to output Entity models and then to dictionaries
        entity_dicts = [entity.dict() for entity in entities]
        for entity in entity_dicts:
            entity["document_id"] = document_id
        
        # Insert the entities into the Entities collection
        settings.mongo_client["Entities"].insert_many(entity_dicts)
        logger.info(f"Successfully inserted {len(entity_dicts)} entities for document ID: {document_id}")
    
    except Exception as e:
        logger.error(f"Failed to insert entities for document ID: {document_id}: {e}")
        raise


async def insert_classification(document_id: str, classification: Classification):
    """
    Insert document classification record into the MongoDB database.

    Args:
        document_id (str): The ID of the document to which the classification belongs.
        classification (Classification): The classification object containing label and score.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        # Convert the Classification model to a dictionary and prepare the classification record
        classification_record = {
            "document_id": document_id,
            "label": classification.label,
            "score": float(classification.score)
        }
        
        # Insert the classification record into the DocumentClassification collection
        settings.mongo_client["DocumentClassification"].insert_one(classification_record)
        logger.info(f"Successfully inserted classification for document ID: {document_id}")
    
    except Exception as e:
        logger.error(f"Failed to insert classification for document ID: {document_id}: {e}")
        raise

async def insert_topics(document_id: Optional[str], topics: List[Topic]):
    """
    Insert the topics generated for a document into the database.

    Args:
        document_id (str): The ID of the document.
        topics (List[Topic]): A list of Topic instances representing the topics generated for the document.
    
    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        # Convert the Topic models to dictionaries and prepare the topic records
        topic_records = [topic.dict() for topic in topics]
        for topic in topic_records:
            topic["document_id"] = document_id
        
        # Insert the topic records into the Topics collection
        settings.mongo_client["Topics"].insert_many(topic_records)
        logger.info(f"Successfully inserted {len(topic_records)} topics for document ID: {document_id}")

    except Exception as e:
        logger.error(f"Failed to insert topics for document ID: {document_id}: {e}")
        raise

async def insert_tf_idf_keywords(document_id: Optional[str], keywords: List[str]):
    """
    Insert the TF-IDF keywords generated for a document into the database.
    """
    try:
        # Prepare the keyword records with the document_id
        keyword_records = [{"document_id": document_id, "keyword": keyword} for keyword in keywords]
        
        # Insert the keyword records into the TFIDFKeywords collection
        settings.mongo_client["TFIDFKeywords"].insert_many(keyword_records)
        logger.info(f"Successfully inserted {len(keyword_records)} TF-IDF keywords for document ID: {document_id}")

    except Exception as e:
        logger.error(f"Failed to insert TF-IDF keywords for document ID: {document_id}: {e}")
        raise

async def insert_questions(document_id: str, questions: List[RAGQuestionGenerator]):
    """
    Insert the generated questions into the Questions collection in the database.

    Args:
        questions (List[Dict[str, Any]]): A list of dictionaries where each dictionary contains
        a generated question and its associated score.

    Raises:
        Exception: If there's an error during the insertion process.
    """
    try:
        formatted_questions = [
            {
                "document_id": document_id,
                "serial": q["serial"],
                "question": q["question"],
                "score": float(q["score"]),
            } 
            for q in questions
        ]
        settings.mongo_client["Questions"].insert_many(formatted_questions)

        logger.info("Successfully inserted questions into the database.")

    except Exception as e:
        # Log the error and raise it again for further handling if necessary.
        logger.error(f"Failed to insert questions into the database: {e}")
        raise

