# pdf_tasks.py
"""
This module defines the PDF processing tasks for the FastAPI application.
"""

import pdb
import asyncio
from celery import shared_task
from remote_pdb import RemotePdb
from app.services.processors.pdf import textract, tesseract, pdf_miner, pyPDF2, muPDF
from app.models.pdf_model import PDFTextResponse
from app.config import settings, logger
from app.tasks.aws_services import download_file_from_s3
from app.tasks.celery_config import app
import fitz  # PyMuPDF
import time

def is_pdf_scanned(file_stream):
    """
    Check if any page in a PDF is scanned using an in-memory file-like object.

    Args:
    file_stream (BytesIO): The in-memory file-like object containing the PDF.

    Returns:
    bool: True if any page is scanned, False otherwise.
    """
    try:
        file_stream.seek(0)  # Reset the stream position
        doc = fitz.open(stream=file_stream, filetype="pdf")
        for page in doc:
            text = page.get_text().strip()
            img_blocks = page.get_images(full=True)
            if len(text) < 50 and img_blocks:
                return True
        return False
    except Exception as e:
        logger.error(f"Error determining if any page is scanned: {e}")
        return False

@shared_task()
def simple_task():
    logger.info("Simple task executed")
    return "Simple task result"

@shared_task
async def process_pdf(s3_file_key):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    s3_file_key (str): The S3 key of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        pdb.set_trace()
        logger.info(f"Starting process_pdf task for {s3_file_key}")

        # Start remote debugger
        RemotePdb('127.0.0.1', 5555).set_trace()  # Use a different port if necessary

        # Download the file from S3
        file_stream = await download_file_from_s3(settings.AWS_S3_BUCKET_NAME, s3_file_key)
        logger.info(f"Downloaded from S3 with key: {s3_file_key}")
        file_path = f"/tmp/{s3_file_key}"  # Temporary path to use with libraries that need a file path
        logger.info(f"Processing PDF - {s3_file_key} with updated file path: {file_path}")

        # Check if the PDF is scanned
        scanned = is_pdf_scanned(file_stream)
        if scanned:
            logger.info(f"Scanned file detected: {s3_file_key}")
            response = asyncio.run(textract.useTextract([{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}]))
            if not response.bounding_boxes:
                file_stream.seek(0)  # Reset the stream position
                with open(file_path, 'wb') as f:
                    f.write(file_stream.getbuffer())
                response = asyncio.run(tesseract.useTesseract(file_path))
        else:
            logger.info(f"Text-based file detected: {s3_file_key}")
            file_stream.seek(0)  # Reset the stream position
            with open(file_path, 'wb') as f:
                f.write(file_stream.getbuffer())
            response = asyncio.run(pdf_miner.usePDFMiner(file_path))
            if not response.bounding_boxes:
                response = asyncio.run(pyPDF2.usePyPDF2(file_path))
                if not response.bounding_boxes:
                    response = asyncio.run(muPDF.usePyMuPDF(file_path))

        return response
    except Exception as e:
        logger.error(f"Failed to process PDF {s3_file_key} with error: {e}")
        return PDFTextResponse(file_name=s3_file_key, text="", bounding_boxes=[])

# Example usage:
if __name__ == "__main__":
    s3_key = "your-document-key.pdf"
    results = asyncio.run(process_pdf(s3_key))
    print(results)
