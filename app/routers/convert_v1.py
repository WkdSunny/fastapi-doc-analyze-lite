# # convert_v1.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
from typing import List, Dict, Any
from transformers import pipeline
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.config import settings, logger
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.file_processing import save_temp_file, get_file_type
from app.services.db.insert import insert_documents, insert_task

router = APIRouter(
    prefix="/convert_v1",
    tags=["convert"]
)

database = settings.database

@router.post("/", response_model=Dict[str, Any])
async def convert_files(files: List[UploadFile] = File(...)):
    tasks = []

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
                # unsupported_files.append(file.filename)
                logger.error(f"Unsupported file type: {file.filename}")
                continue

            # Wait for the Celery task to complete and handle the result
            tasks.append(asyncio.create_task(handle_file_result(file.filename, task)))
            # tasks.append(wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT))
        except Exception as e:
            # failed_files.append(file.filename)
            logger.error(f"Failed to process file {file.filename}: {e}")
            continue

    # Run all tasks concurrently and gather results
    document_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out successful results
    document_results = [result for result in document_results if not isinstance(result, Exception)]

    # Extract document IDs from the results and store them
    task_document_ids = [doc["document_id"] for doc in document_results]

    # Insert the Task document with all document IDs
    task_id = await insert_task(task_document_ids)

    if not document_results:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        "result": {
            "task_id": task_id,
            "document_data": document_results
        }
    }

async def handle_file_result(file_name: str, task):
    """
    Handle the result of a file processing task by waiting for the task to complete
    and inserting the document into the database.

    Args:
        file_name (str): The name of the file being processed.
        task (Task): The Celery task processing the file.

    Returns:
        Dict[str, Any]: The response containing the document ID and other details.
    """
    try:
        # Wait for the Celery task to complete
        result = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)

        # Insert the processed document into the database
        document_id = await insert_documents(file_name, result["text"])

        return {
            "document_id": document_id,
            "file_name": file_name,
            "status": "processed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
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
    
    response = client.post("/convert/", files=files)
    print(response.json())