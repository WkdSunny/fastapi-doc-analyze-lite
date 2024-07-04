# convert.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import time
import asyncio
import filetype
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.services.processors.pdf.pdf_tasks import process_pdf
from app.services.processors.pdf.textract import useTextract
from app.services.processors.excel import useOpenPyXL
from app.services.processors.word import useDocX
from app.tasks.aws_services import upload_file_to_s3
from app.config import settings, logger

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

def wait_for_celery_task(task, timeout):
    logger.info(f"Waiting for Celery task with ID: {task.id}, Type of task_id: {type(task.id)}")
    start_time = time.time()
    while True:
        if task.ready():
            result = task.result
            logger.info(f"Task result: {result}")
            return result
        elif (asyncio.get_event_loop().time() - start_time) > timeout:
            raise TimeoutError("Celery task timed out")
        time.sleep(1)

@router.post("/", response_model=Dict[str, Any])
async def convert_files(files: List[UploadFile] = File(...)):
    # pdb.set_trace()
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
            s3_file_key = temp_filename

            # Process file based on type
            if 'pdf' in content_type:
                logger.info(f"PDF file detected...")
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

            result = wait_for_celery_task(task, 180)
            success_files.append(file.filename)
            responses.append(result)
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

# Example usage:
if __name__ == "__main__":
    files = [
        UploadFile(filename="sample.pdf", content_type="application/pdf"),
        UploadFile(filename="sample.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        UploadFile(filename="sample.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        UploadFile(filename="sample.jpg", content_type="image/jpeg"),
        UploadFile(filename="sample.txt", content_type="text/plain")
    ]
    results = asyncio.run(convert_files(files))
    print(results)