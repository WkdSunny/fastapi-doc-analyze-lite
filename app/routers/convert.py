# convert.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
import filetype
from celery.result import AsyncResult
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.services.processors.pdf.pdf_tasks import process_pdf, simple_task
# from app.services.processors.pdf.pdf_tasks import simple_task
from app.services.processors.pdf.textract import useTextract
from app.services.processors.excel import useOpenPyXL
from app.services.processors.word import useDocX
from app.tasks.aws_services import upload_file_to_s3
from app.config import settings, logger

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

async def wait_for_celery_task(task_id, timeout):
    start_time = asyncio.get_event_loop().time()
    while True:
        result = AsyncResult(task_id)
        print(f'result: {result}')
        print(f'result.ready(): {result.ready()}')
        logger.info(f"Task state: {result.state}")  # Log task state
        if result.ready():
            task_result = result.result
            logger.info(f"Raw Task result: {task_result}")  # Log raw result
            return task_result
        elif (asyncio.get_event_loop().time() - start_time) > timeout:
            raise TimeoutError("Celery task timed out")
        await asyncio.sleep(1)  # Sleep for a short period to avoid busy waiting

@router.post("/", response_model=Dict[str, Any])
# async def convert_files():
#     try:
#         task = simple_task.delay()
#         logger.info(f"Queued task: {task.id}")  # Log task ID
#         result = await wait_for_celery_task(task.id, 15)
#         logger.info(f"Task result: {result}")
#         return {"status": "success", "result": result}
#     except Exception as e:
#         logger.error(f"Failed to execute task: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

async def convert_files(files: List[UploadFile] = File(...)):
    responses = []
    unsupported_files = []
    failed_files = []
    success_files = []

    for file in files:
        try:
            logger.info(f'Processing file: {file.filename}')
            kind = filetype.guess(await file.read(2048))
            if kind is None:
                raise ValueError("Cannot determine file type")
            content_type = kind.mime
            await file.seek(0)
            logger.info(f"File type: {content_type}")

            # Upload the file to S3
            temp_filename = await upload_file_to_s3(file)
            logger.info(f"Uploaded to S3 with temp filename: {temp_filename}")
            s3_file_key = temp_filename  # Assuming temp_filename is the key

            # Process file based on type
            if 'pdf' in content_type:
                task = process_pdf.delay(s3_file_key)
            elif 'excel' in content_type or 'spreadsheetml' in content_type:
                task = useOpenPyXL.delay(s3_file_key)
            elif 'wordprocessingml' in content_type or 'msword' in content_type:
                task = useDocX.delay(s3_file_key)
            elif 'image' in content_type:
                documents = [{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}]
                task = useTextract.delay(documents)
            else:
                unsupported_files.append(file.filename)
                logger.error(f"Unsupported file type: {file.filename}")
                continue

            result = await wait_for_celery_task(task, 180)
            success_files.append(file.filename)
            responses.append({"filename": file.filename, "response": result})
        except Exception as e:
            failed_files.append(file.filename)
            logger.error(f"Failed to process file {file.filename}: {e}")

    if not responses:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        "unsupported_files": unsupported_files,
        "conversion_failed": failed_files,
        "result": responses
    }
