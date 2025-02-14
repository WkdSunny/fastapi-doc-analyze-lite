# # convert_v1.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.config import settings, logger
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.file_processing import save_temp_file, get_file_type
from app.services.db.insert import insert_documents, insert_task, insert_segments, insert_classification
from app.services.document_segmentation import DocumentSegmenter
from app.services.document_classification import DocumentClassifier
from app.services.rag.questions.hybrid_questions import IntegratedQuestionGeneration
from app.models.rag_model import Segment, Classification

router = APIRouter(
    prefix="/convert_v1",
    tags=["convert"]
)

document_segmenter = DocumentSegmenter()
document_classifier = DocumentClassifier()

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
            file_task = asyncio.create_task(handle_file_result(file.filename, task, content_type))
            tasks.append(file_task)
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            continue

    # Run all tasks concurrently and gather results
    document_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out successful results
    for result in document_results:
        if not isinstance(result, Exception):
            task_document_ids.append(result["document_id"])

    # Insert the Task document with all document IDs
    task_id = await insert_task(task_document_ids)

    if not document_results:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        "result": {
            "task_id": task_id,
            "document_data": [result for result in document_results if not isinstance(result, Exception)]
        }
    }

async def handle_file_result(file_name: str, task, content_type: str):
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

        # Handle segmentation and classification in parallel
        segmentation_task = handle_segmentation(document_id, result, content_type)
        classification_task = handle_classification(document_id, result)

        # Run the segmentation and classification tasks concurrently
        await asyncio.gather(segmentation_task, classification_task)

        # Step 7: Generate questions using the IntegratedQuestionGeneration service
        question_generator = IntegratedQuestionGeneration()
        questions_with_scores = await question_generator.generate_questions(result["text"], document_id)

        # Return the final result with document ID, file name, and generated questions
        final_result = {
            "document_id": document_id,
            "file_name": file_name,
            "questions": questions_with_scores
        }
        return final_result

    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
        raise


# async def handle_file_result(file_name: str, task, content_type: str):
#     """
#     Handle the result of a file processing task by waiting for the task to complete
#     and inserting the document into the database.

#     Args:
#         file_name (str): The name of the file being processed.
#         task (Task): The Celery task processing the file.
#         content_type (str): The content type of the file being processed.

#     Returns:
#         Dict[str, Any]: The response containing the document ID and other details.
#     """
#     try:
#         # Wait for the Celery task to complete
#         result = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)

#         # Insert the processed document into the database
#         document_id = await insert_documents(file_name, result)

#         # Handle segmentation and classification in parallel
#         segmentation_task = handle_segmentation(document_id, result, content_type)
#         classification_task = handle_classification(document_id, result)

#         # Run the segmentation and classification tasks concurrently
#         await asyncio.gather(segmentation_task, classification_task)

#         final_result = {"document_id": document_id, "file_name": file_name}
#         final_result.update(result)
#         return final_result
#     except Exception as e:
#         logger.error(f"Error processing file {file_name}: {e}")
#         raise

async def handle_segmentation(document_id: str, result: Dict[str, Any], content_type: str):
    """
    Handle segmentation of the document and insert the segments into the database.
    
    Args:
        document_id (str): The ID of the document.
        result (Dict[str, Any]): The result from the document processing containing the text.
        content_type (str): The content type of the document.
    """
    try:
        segments: List[Segment] = await document_segmenter.segment_document(result, content_type)
        await insert_segments(document_id, segments)
        logger.info(f"Successfully segmented and inserted segments for document ID: {document_id}")
    except Exception as e:
        logger.error(f"Failed to segment or insert segments for document ID: {document_id}: {e}")

async def handle_classification(document_id: str, result: Dict[str, Any]):
    """
    Handle classification of the document and insert the classification into the database.
    
    Args:
        document_id (str): The ID of the document.
        result (Dict[str, Any]): The result from the document processing containing the text.
    """
    try:
        classification: Classification = await document_classifier.classify_document(result["text"])
        await insert_classification(document_id, classification)
        logger.info(f"Successfully classified and inserted classification for document ID: {document_id}")
    except Exception as e:
        logger.error(f"Failed to classify or insert classification for document ID: {document_id}: {e}")


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
    
    response = client.post("/convert_v1/", files=files)
    print(response.json())
