"""
This module defines the conversion routes for the FastAPI application.
"""

import time
import asyncio
import aiofiles
import filetype
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.services.processors.pdf.pdf_tasks import process_pdf
from app.services.processors.pdf.textract import useTextract
from app.services.processors.excel import useOpenPyXL
from app.services.processors.word import useDocX
# from app.tasks.aws_services import upload_file_to_s3
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
        elif (time.time() - start_time) > timeout:
            raise TimeoutError("Celery task timed out")
        time.sleep(1)

async def save_temp_file(file: UploadFile) -> str:
    """
    Save the uploaded file to a temporary path asynchronously.

    Args:
    file (UploadFile): The uploaded file.

    Returns:
    str: The path to the temporary file.
    """
    temp_path = f"/tmp/{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as temp_file:
        await temp_file.write(await file.read())
    return temp_path

@router.post("/", response_model=Dict[str, Any])
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

            # Save the file to a temporary path
            temp_path = await save_temp_file(file)
            logger.info(f"Saved file to temporary path: {temp_path}")

            # Process file based on type
            if 'pdf' in content_type:
                logger.info(f"PDF file detected...")
                task = process_pdf.delay(temp_path)
            elif 'excel' in content_type or 'spreadsheetml' in content_type:
                task = useOpenPyXL.delay(temp_path)
            elif 'wordprocessingml' in content_type or 'msword' in content_type:
                task = useDocX.delay(temp_path)
            elif 'image' in content_type:
                task = useTextract.delay(temp_path)
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
