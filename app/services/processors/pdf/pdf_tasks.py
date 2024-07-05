# pdf_tasks.py
"""
This module defines the PDF processing tasks for the FastAPI application.
"""

import fitz
import asyncio
from celery import shared_task
from celery.result import AsyncResult
from app.services.processors.pdf import textract, tesseract, pdf_miner, pyPDF2, muPDF
from app.config import settings, logger

PDF_PROCESSING_TIMEOUT = 180  # seconds

@shared_task
def process_pdf(temp_path):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    temp_path (str): The temporary path of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_process_pdf(temp_path), loop)
        return future.result()
    else:
        return loop.run_until_complete(_process_pdf(temp_path))

async def wait_for_celery_task(task_id, timeout):
    """
    Wait for a Celery task to complete within a given timeout.

    Args:
    task_id (str): The ID of the Celery task.
    timeout (int): The maximum time to wait in seconds.

    Returns:
    result: The result of the Celery task.

    Raises:
    TimeoutError: If the task does not complete within the timeout.
    """
    task = AsyncResult(task_id)
    try:
        result = await asyncio.to_thread(task.get, timeout=timeout)
        logger.info(f"Task result: {result}")
        return result
    except TimeoutError:
        logger.error("Celery task timed out")
        raise
    except Exception as e:
        logger.error(f"Error waiting for Celery task: {e}")
        raise

async def process_with_fallbacks(file_path, processors):
    """
    Process the PDF file using a list of processors with fallback.

    Args:
    file_path (str): The path to the PDF file.
    processors (list): A list of processor tasks to try in order.

    Returns:
    PDFTextResponse: The response from the first successful processor.
    """
    for processor in processors:
        try:
            logger.info(f"Trying processor {processor.__name__} for {file_path}")
            task = processor.delay(file_path)
            response = await wait_for_celery_task(task.id, PDF_PROCESSING_TIMEOUT)
            if response.bounding_boxes:
                return response
        except Exception as e:
            logger.error(f"Processor {processor.__name__} failed for {file_path} with error: {e}")
    return {"file_name": "", "text": "", "bounding_boxes": []}

async def _process_pdf(temp_path):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    temp_path (str): The temporary path of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        logger.info(f"Starting process_pdf task for {temp_path}")

        # Processors in the order of preference
        processors = [muPDF.usePyMuPDF, pdf_miner.usePDFMiner, textract.useTextract, tesseract.useTesseract]

        response = await process_with_fallbacks(temp_path, processors)
        return response

    except Exception as e:
        logger.error(f"Failed to process PDF {temp_path} with error: {e}")
        return {
            "file_name": "",
            "text": "",
            "bounding_boxes": []
        }

# Example usage:
if __name__ == "__main__":
    temp_path = "/tmp/sample.pdf"
    results = asyncio.run(process_pdf(temp_path))
    print(results)
