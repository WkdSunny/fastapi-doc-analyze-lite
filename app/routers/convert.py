# # convert_v1.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.config import settings, logger
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.file_processing import save_temp_file, get_file_type
from app.services.db.insert import (
    insert_documents, 
    insert_task, 
    insert_segments, 
    insert_classification, 
    insert_entities, 
    insert_token_consumption, 
    insert_topics, 
    insert_tf_idf_keywords
)
# from app.services.document_segmentation import DocumentSegmenter
from app.services.prompt_engine.document_segmentation import DocumentSegmenter
from app.services.prompt_engine.document_classification import classify_documents
from app.services.prompt_engine.entity_recognition import get_entities
from app.services.topic_modeling.pipeline import TopicModelingPipeline
from app.services.tfidf_extraction import TFIDFExtractor
from app.services.prompt_engine.question_generator import generate_questions
# from app.services.document_classification import DocumentClassifier
# from app.services.rag.questions.hybrid_questions import IntegratedQuestionGeneration
from app.models.rag_model import Segment, Classification, Entity
from app.utils.csv_utils import parse_csv_content

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

document_segmenter = DocumentSegmenter()
topic_modeling_pipeline = TopicModelingPipeline(num_topics=5, passes=10)
tfidf_extractor = TFIDFExtractor()
# document_classifier = DocumentClassifier()

@router.post("/", response_model=Dict[str, Any])
async def convert_files(files: List[UploadFile] = File(...)):
    tasks = []
    document_results = []
    task_document_ids = []

    for file in files:
        try:
            logger.info(f'Processing file: {file.filename}')
            content_type = await get_file_type(file)
            if content_type is None:
                raise ValueError("Cannot determine file type")
            logger.info(f"File type: {content_type}")

            # Save the file to a temporary path
            temp_path = await save_temp_file(file)
            logger.info(f"Saved file to temporary path: {temp_path}")

            # Process file based on type
            if 'pdf' in content_type:
                logger.info(f"PDF file detected...")
                task = process_pdf.delay(temp_path)
            elif 'excel' in content_type or 'spreadsheetml' in content_type:
                task = process_excel.delay(temp_path)
            elif 'wordprocessingml' in content_type or 'msword' in content_type:
                task = process_word.delay(temp_path)
            elif 'image' in content_type:
                task = process_img.delay(temp_path)
            else:
                logger.error(f"Unsupported file type: {file.filename}")
                continue

            # Wait for the Celery task to complete and handle the result
            file_task = asyncio.create_task(handle_file_result(file.filename, task))
            tasks.append(file_task)
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            continue

    # Run all tasks concurrently and gather results
    document_results = await asyncio.gather(*tasks, return_exceptions=True)

    if not document_results:
        raise HTTPException(status_code=500, detail="No files processed successfully")
    
    # Filter out successful results
    successful_results = []
    for result in document_results:
        if not isinstance(result, Exception):
            task_document_ids.append(result["document_id"])
            successful_results.append(result)

    # Insert the Task document with all document IDs
    task_id = await insert_task(task_document_ids)

    prompt_generation = await combined_tasks(task_id, document_results)

    result = {
        "task_id": task_id,
        "document_data": successful_results,
        "other_tasks": prompt_generation
    }

    return {
        "status": 200,
        "success": True,
        "result": {
            "task_id": task_id,
            "document_data": [result for result in document_results if not isinstance(result, Exception)]
        }
    }

async def handle_file_result(file_name: str, task):
    """
    Handle the result of a file processing task by waiting for the task to complete,
    inserting the document into the database, segmenting, classifying, and generating questions.

    Args:
        file_name (str): The name of the file being processed.
        task (Task): The Celery task processing the file.
        content_type (str): The content type of the file being processed.

    Returns:
        Dict[str, Any]: The response containing the document ID, file name, and generated questions.
    """
    try:
        # Wait for the Celery task to complete
        result = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)

        # Insert the processed document into the database
        document_id = await insert_documents(file_name, result)

        # # Handle segmentation and classification in parallel
        # segmentation_task = handle_segmentation(document_id, result, content_type)
        # # classification_task = handle_classification(document_id, result)
        # classification_task = handle_classification(document_id, result, content_type)
        # topic_modeling_task = topic_modeling(document_id, result["text"])

        # # Run the segmentation and classification tasks concurrently
        # segments, classification, topics = await asyncio.gather(segmentation_task, classification_task, topic_modeling_task)
        # logger.info(f"Segments: {segments}")
        # logger.info(f"Classification: {classification}")
        # logger.info(f"Topics: {topics}")

        # entities_task = handle_entity(document_id, segments)
        # tfidf_extraction_task = tfidf_extraction(document_id, segments)

        # # Run the entity recognition and TF-IDF extraction tasks concurrently
        # entities_result, tfidf_keywords = await asyncio.gather(entities_task, tfidf_extraction_task)
        # logger.info(f"Entities: {entities_result}")
        # logger.info(f"TF-IDF Keywords: {tfidf_keywords}")

        # questions = await generate_questions(segments, classification, entities_result["entities"], topics, tfidf_keywords, content_type)
        # logger.info(f"Generated Questions: {questions}")

        # Step 7: Generate questions using the IntegratedQuestionGeneration service
        # question_generator = IntegratedQuestionGeneration()
        # questions_with_scores = await question_generator.generate_questions(result["text"], document_id)

        # Return the final result with document ID, file name, and generated questions
        final_result = {
            "document_id": document_id,
            "file_name": file_name,
            "text": result["text"],
            "bounding_boxes": result["bounding_boxes"],
            # "segments": segments,
            # "classification": classification,
            # "entity_list": entities_result,
            # "topics": topics,
            # "tfidf_keywords": tfidf_keywords,
            # "questions": questions
        }
        return final_result

    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
        raise

async def combined_tasks(task_id: str, result: List[Dict[str, Any]]):
    try:
        # Handle segmentation and classification in parallel
        segmentation_task = handle_segmentation(task_id, result)
        classification_task = handle_classification(task_id, result)
        topic_modeling_task = topic_modeling(task_id, result)

        # Run the segmentation and classification tasks concurrently
        segments, classification, topics = await asyncio.gather(segmentation_task, classification_task, topic_modeling_task)
        logger.info(f"Segments: {segments}")
        logger.info(f"Classification: {classification}")
        logger.info(f"Topics: {topics}")

        entities_task = handle_entity(task_id, segments)
        tfidf_extraction_task = tfidf_extraction(task_id, segments)

        # # Run the entity recognition and TF-IDF extraction tasks concurrently
        entities_result, tfidf_keywords = await asyncio.gather(entities_task, tfidf_extraction_task)
        logger.info(f"Entities: {entities_result}")
        logger.info(f"TF-IDF Keywords: {tfidf_keywords}")

        questions = await generate_questions(segments, classification, entities_result["entities"], topics, tfidf_keywords)
        logger.info(f"Generated Questions: {questions}")

        return {
            "segments": segments,
            # "classification": classification,
        }
    
    except Exception as e:
        logger.error(f"Error processing file {task_id}: {e}")
        raise

async def handle_segmentation(task_id: str, result: Dict[str, Any]):
    """
    Handle segmentation of the document and insert the segments into the database.
    
    Args:
        task_id (str): The ID of the document.
        result (Dict[str, Any]): The result from the document processing containing the text.
        content_type (str): The content type of the document.
    """
    try:
        segments: List[Segment] = await document_segmenter.segment_document(result)
        # await insert_segments(task_id, segments)
        logger.info(f"Successfully segmented and inserted segments for document ID: {task_id}")
        return segments
    except Exception as e:
        logger.error(f"Failed to segment or insert segments for document ID: {task_id}: {e}")

async def handle_classification(task_id: str, result: Dict[str, Any]):
    try:
        classification_result = await classify_documents(result)
        # classification = classification_result["classification"][0]
        # logger.debug(f"Classification: {classification}")
        token_usage = classification_result["token_usage"]

        # formatted_classification = Classification(
        #     label=classification["classification"],
        #     description=classification["description"]
        # )
        
        # Run the database insertion tasks concurrently
        # await asyncio.gather(
        #     insert_classification(task_id, formatted_classification),
        #     insert_token_consumption(task_id, "OpenAI", "Document Classification", token_usage)
        # )

        await insert_token_consumption(task_id, "OpenAI", "Document Classification", token_usage)

        # return formatted_classification
        return classification_result
    except Exception as e:
        logger.error(f"Failed to classify document ID: {task_id}: {e}")
        raise

async def handle_entity(task_id: str, segments: List[Segment]) -> Dict[str, Optional[str]]:
    """
    Perform entity recognition on all segments at once while preserving relationships.

    Args:
        task_id (str): The ID of the document being processed.
        segments (List[Segment]): A list of Segment objects.

    Returns:
        Dict[str, Optional[str]]: A dictionary containing the entities and token usage.
    """
    try:
        # Create a structured input for the LLM
        # Combine all segments into one structured text block
        structured_text = []
        # for segment_list in segments:
        #     for segment in segment_list:
        #         segment_text = (
        #             f"<segment id='{segment.serial}' relates_to='{segment.relates_to}' "
        #             f"relationship_type='{segment.relationship_type}'>"
        #             f"{segment.text}</segment>"
        #         )
        #         structured_text.append(segment_text)
        for segment in segments:
            segment_text = (
                f"<segment id='{segment.serial}' relates_to='{segment.relates_to}' "
                f"relationship_type='{segment.relationship_type}'>"
                f"{segment.text}</segment>"
            )
            structured_text.append(segment_text)

        combined_text = "\n".join(structured_text)
        logger.info(f"Document ID: {task_id}, Structured Combined Text: {combined_text}")

        # Send the combined structured text for entity extraction
        raw_entities = await get_entities(combined_text)
        entities_csv = raw_entities["entities"]
        token_usage = raw_entities["token_usage"]

        # Parse the entities CSV content
        parsed_entities = await parse_csv_content(entities_csv)
        logger.info(f"Document ID: {task_id}, Parsed Entities: {parsed_entities}")

        # Convert parsed entities into Entity objects and attach the segment serial
        entity_list = []
        for i, entity_data in enumerate(parsed_entities):
            try:
                entity = Entity(
                    serial=i+1,
                    entity=entity_data.get("category"),
                    text=entity_data.get("entity"),
                    description=entity_data.get("entity_description"),
                    segment_serial=int(entity_data.get("segment_serial", 0))
                )
                entity_list.append(entity)
            except Exception as e:
                logger.error(f"Failed to create entity object: {e}")
                continue
        
        # Insert all entities and token usage into the database
        await asyncio.gather(
            insert_entities(task_id, entity_list),
            insert_token_consumption(task_id, "OpenAI", "Entity Recognition", token_usage)
        )

        return {
            "entities": entity_list,
            "token_usage": token_usage
        }

    except Exception as e:
        logger.error(f"Failed to extract entities for document ID: {task_id}: {e}")
        raise

async def topic_modeling(task_id: str, result: List[Dict[str, Any]]):
    """
    Perform topic modeling on the document text and insert the topics into the database.

    Args:
        document_text (str): The text of the document to perform topic modeling on.

    Returns:
        List[str]: A list of topics extracted from the document.
    """
    try:
        text = ""
        for segment in result:
            text += segment["text"]

        topics = topic_modeling_pipeline.run([text])
        if not topics:
            raise ValueError("No topics found in the document.")
        await insert_topics(task_id, topics)
        return topics
    except Exception as e:
        logger.error(f"Failed to perform topic modeling for document ID: {task_id}: {e}")
        raise

async def tfidf_extraction(task_id: str, segments: List[Segment]):
    """
    Perform TF-IDF keyword extraction on the document segments and insert the keywords into the database.

    Args:
        document_id (str): The ID of the document being processed.
        segments (List[Segment]): A list of Segment objects.

    Returns:
        List[str]: A list of TF-IDF keywords extracted from the document.
    """
    try:
        document_text = "\n".join([segment.text for segment in segments])
        tfidf_keywords = await tfidf_extractor.extract_keywords(document_text)
        if not tfidf_keywords:
            raise ValueError("No TF-IDF keywords found in the document.")
        await insert_tf_idf_keywords(task_id, tfidf_keywords)
        return tfidf_keywords
    except Exception as e:
        logger.error(f"Failed to extract TF-IDF keywords for Task ID: {task_id}: {e}")
        raise

if __name__ == "__main__":
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
    files = [
        UploadFile(filename="sample.pdf", content_type="application/pdf"),
        UploadFile(filename="sample.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        UploadFile(filename="sample.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        UploadFile(filename="sample.jpg", content_type="image/jpeg"),
    ]
    
    response = client.post("/convert", files=files)
    print(response.json())
