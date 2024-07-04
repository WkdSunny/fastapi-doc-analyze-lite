"""
This module defines the PDF processing tasks for the FastAPI application.
"""

import io
import fitz
import time
import asyncio
import functools
from celery import shared_task
from app.tasks.aws_services import download_file_from_s3
from app.services.processors.pdf import textract, tesseract, pdf_miner, pyPDF2, muPDF
from app.config import settings, logger

async def has_images(file_stream):
    """
    Check if any page in a PDF has images using an in-memory file-like object.

    Args:
    file_stream (BytesIO): The in-memory file-like object containing the PDF.

    Returns:
    bool: True if any page has images, False otherwise.
    """
    try:
        file_stream.seek(0)  # Reset the stream position
        doc = await asyncio.to_thread(functools.partial(fitz.open, stream=file_stream, filetype="pdf"))
        for page_num in range(len(doc)):
            page = await asyncio.to_thread(functools.partial(doc.load_page, page_num))
            img_list = await asyncio.to_thread(functools.partial(page.get_images, full=True))
            if img_list:
                return True
        return False
    except Exception as e:
        logger.error(f"Error determining if the PDF has images: {e}")
        return False

@shared_task
def process_pdf(s3_file_key):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    s3_file_key (str): The S3 key of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_process_pdf(s3_file_key), loop)
        return future.result()
    else:
        return loop.run_until_complete(_process_pdf(s3_file_key))

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

async def _process_pdf(s3_file_key):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    s3_file_key (str): The S3 key of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        logger.info(f"Starting process_pdf task for {s3_file_key}")

        file_stream = io.BytesIO(await download_file_from_s3(settings.AWS_S3_BUCKET_NAME, s3_file_key))
        logger.info(f"Downloaded from S3 with key: {s3_file_key}")
        file_path = f"/tmp/{s3_file_key}"  # Temporary path to use with libraries that need a file path
        logger.info(f"Processing PDF - {s3_file_key} with updated file path: {file_path}")

        # Check if the PDF has images
        has_img = await has_images(file_stream)
        # if has_img:
        print(f"Pdf has images: {has_img}")
        # logger.info(f"PDF with images detected: {s3_file_key}")
        # response = await asyncio.to_thread(functools.partial(textract.useTextract, [{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}]))
        task = textract.useTextract.delay([{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}])
            # response = await textract.useTextract([{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}])
        #     if not response.bounding_boxes:
        #         file_stream.seek(0)  # Reset the stream position
        #         async with aiofiles.open(file_path, 'wb') as f:
        #             await f.write(file_stream.getbuffer())
        #         response = await tesseract.useTesseract(file_path)
        # else:
        #     logger.info(f"Text-based PDF detected: {s3_file_key}")
        #     file_stream.seek(0)  # Reset the stream position
        #     async with aiofiles.open(file_path, 'wb') as f:
        #         await f.write(file_stream.getbuffer())
        #     response = await pdf_miner.usePDFMiner(file_path)
        #     if not response.bounding_boxes:
        #         response = await pyPDF2.usePyPDF2(file_path)
        #         if not response.bounding_boxes:
        #             response = await muPDF.usePyMuPDF(file_path)

        response = wait_for_celery_task(task, 180)

        return response
    except Exception as e:
        logger.error(f"Failed to process PDF {s3_file_key} with error: {e}")
        return {
            "file_name": "",
            "text": "",
            "bounding_boxes": []
        }

# Example usage:
if __name__ == "__main__":
    s3_key = "your-document-key.pdf"
    results = asyncio.run(process_pdf(s3_key))
    print(results)