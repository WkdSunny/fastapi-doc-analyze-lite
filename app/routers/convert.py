#convert.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import magic
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.processors.pdf.pdf_tasks import process_pdf
from app.services.processors.pdf.textract import useTextract
from app.services.processors.excel import useOpenPyXL
from app.services.processors.word import useDocX
from app.models.pdf_model import PDFTextResponse
from app.tasks.aws_services import upload_file_to_s3, download_file_from_s3
from app.config import settings, logger
from typing import List

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

@router.post("/", response_model=List[PDFTextResponse])
async def convert_files(files: List[UploadFile] = File(...)):
    """
    Convert uploaded files to their respective processed formats.

    Args:
    files (List[UploadFile]): List of files to be uploaded and processed.

    Returns:
    List[PDFTextResponse]: List of processed file responses.
    """
    responses = []
    for file in files:
        try:
            content_type = magic.from_buffer(await file.read(2048), mime=True)
            await file.seek(0)
            temp_filename = await upload_file_to_s3(file.file, file.filename)
            s3_file_key = temp_filename  # Assuming temp_filename is the key

            # Download file from S3 for processing
            file_stream = await download_file_from_s3(settings.AWS_S3_BUCKET_NAME, s3_file_key)

            # Process file based on type
            if 'pdf' in content_type:
                response = await process_pdf.delay(file_stream)
            elif 'excel' in content_type or 'spreadsheetml' in content_type:
                response = await useOpenPyXL.delay(file_stream)
            elif 'wordprocessingml' in content_type or 'msword' in content_type:
                response = await useDocX.delay(file_stream)
            elif 'image' in content_type:
                response = await useTextract.delay(file_stream)
            else:
                raise ValueError("Unsupported file type")

            result = response.get()
            responses.append({"filename": file.filename, "response": result})
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return responses
