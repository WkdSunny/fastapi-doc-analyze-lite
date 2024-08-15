# # convert_v1.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import torch
import asyncio
import aiofiles
import filetype
from typing import List, Dict, Any
from datetime import datetime, timezone
from transformers import pipeline
from transformers import BertTokenizer, BertForTokenClassification, BertForSequenceClassification
from fastapi import APIRouter, File, UploadFile, HTTPException
from concurrent.futures import ThreadPoolExecutor
from app.config import settings, logger
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.file_processing import save_temp_file, get_file_type

router = APIRouter(
    prefix="/convert_v1",
    tags=["convert"]
)

database = settings.database

@router.post("/", response_model=Dict[str, Any])
async def convert_files(files: List[UploadFile] = File(...)):
    tasks = []
    responses = []

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

            tasks.append(wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT))
        except Exception as e:
            # failed_files.append(file.filename)
            logger.error(f"Failed to process file {file.filename}: {e}")
            continue

        # Run all tasks in parallel and gather the results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect responses and filter out errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with error: {result}")
            else:
                responses.append(result)
                
    if not responses:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        "result": responses
    }

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