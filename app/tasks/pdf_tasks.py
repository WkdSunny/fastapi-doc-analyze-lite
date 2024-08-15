# /app/tasks/pdf_tasks.py
"""
This module defines the PDF processing tasks for the FastAPI application.
"""

import asyncio
import importlib
from celery import shared_task, Task
from app.config import settings, logger
from app.models.pdf_model import PDFTextResponse
from app.tasks.async_tasks import run_async_task
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.document_processors.pdf.muPDF import usePyMuPDF
from app.services.document_processors.pdf.pdf_miner import usePDFMiner
from app.services.document_processors.pdf.textract import useTextract
from app.services.document_processors.pdf.tesseract import useTesseract
from app.config import settings

# class PDFTask(Task):
#     autoretry_for = (Exception,)
#     retry_kwargs = {'max_retries': 3, 'countdown': 5}
#     retry_backoff = True

# @shared_task(Base=PDFTask)
@shared_task()
def process_pdf(temp_path):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    temp_path (str): The temporary path of the PDF file.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        results = run_async_task(_process_pdf, temp_path)
        if not results['bounding_boxes']:
            logger.warning(f"No text extracted from {temp_path}")
            raise Exception(f"PDF processing failed...")
        return results
    except Exception as e:
        logger.error(f"Failed to process PDF {temp_path} with error: {e}")
        return PDFTextResponse(file_name=temp_path, text="", bounding_boxes=[]).to_dict()

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
            response = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)
            if response['bounding_boxes']:
                return response
        except Exception as e:
            logger.error(f"Processor {processor.__name__} failed for {file_path} with error: {e}")
            
    return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

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
        processors = [usePyMuPDF, usePDFMiner, useTextract, useTesseract]

        response = await process_with_fallbacks(temp_path, processors)
        logger.info(f"Processing result: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to process PDF {temp_path} with error: {e}")
        return PDFTextResponse(file_name="", text="", bounding_boxes=[]).to_dict()

# Example usage:
if __name__ == "__main__":
    temp_path = "/tmp/sample.pdf"
    results = asyncio.run(process_pdf(temp_path))
    print(results)
