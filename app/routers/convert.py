# convert.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
import aiofiles
import filetype
from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.config import settings, logger
from app.services.processors.word import useDocX
from app.services.processors.excel import useOpenPyXL
from app.utils.celery_utils import wait_for_celery_task
from app.services.processors.pdf.textract import useTextract
from app.services.processors.pdf.pdf_tasks import process_pdf

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

database = settings.database

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

async def insert_document_and_segments(document_data: Dict[str, Any], segments: List[Dict[str, Any]]) -> str:
    """
    Insert the document data and its segments into the MongoDB database.
    """
    # Insert the document data into the Documents collection
    document_id = database["Documents"].insert_one(document_data).inserted_id
    
    # Prepare segment data with document_id reference
    for segment in segments:
        segment["document_id"] = document_id
    
    # Insert the segments into the Segments collection
    database["Segments"].insert_many(segments)
    
    return str(document_id)

@router.post("/", response_model=Dict[str, Any])
async def convert_files(files: List[UploadFile] = File(...)):
    responses = []
    # unsupported_files = []
    # failed_files = []
    # success_files = []

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
                # unsupported_files.append(file.filename)
                logger.error(f"Unsupported file type: {file.filename}")
                continue

            result = {"document_id": None}
            result.update(await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT))
            # success_files.append(file.filename)

            # Prepare document data and segments
            document_data = {
                "file_name": file.filename,
                "uploaded_at": datetime.now(timezone.utc),
                "text": result["text"],  # Extracted text
                "status": "processed"
            }

            segments = []
            for bbox in result["bounding_boxes"]:
                segment = {
                    "page": bbox["page"],
                    "bbox": bbox["bbox"],
                    "text": bbox["text"],
                    "confidence": bbox["confidence"]
                }
                segments.append(segment)
            
            # Insert data into MongoDB
            document_id = await insert_document_and_segments(document_data, segments)
            logger.info(f"Inserted document with ID: {document_id} into the database")

            result["document_id"] = document_id
            responses.append(result)
        except Exception as e:
            # failed_files.append(file.filename)
            logger.error(f"Failed to process file {file.filename}: {e}")

    if not responses:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        # "unsupported_files": unsupported_files,
        # "conversion_failed": failed_files,
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
