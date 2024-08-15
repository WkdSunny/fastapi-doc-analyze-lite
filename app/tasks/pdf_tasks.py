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
            logger.debug(f"Loading {processor['name']} for {file_path}")
            print(f"Loading {processor['name']} for {file_path}")
            processor_func = processor['processor']

            # Safely execute the Celery task with delay
            if callable(processor_func):
                task = processor_func.delay(file_path)
                logger.debug(f"Task queued: {task.id}")
            else:
                logger.error(f"Processor function {processor_func} is not callable.")
                continue

            response = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)
            if response['bounding_boxes']:
                return response
        except asyncio.TimeoutError:
            logger.error(f"Processor {processor['name']} timed out for {file_path}")
        except Exception as e:
            logger.error(f"Processor {processor['name']} failed for {file_path} with error: {e}")

    # for processor in processors:
    #     try:
    #         logger.info(f"Trying processor {processor.__name__} for {file_path}")
    #         task = processor.delay(file_path)
    #         response = await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT)
    #         if response['bounding_boxes']:
    #             return response
    #     except Exception as e:
    #         logger.error(f"Processor {processor.__name__} failed for {file_path} with error: {e}")
            
    return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

# async def _process_pdf(temp_path):
#     """
#     Process PDF files based on type and handle fallbacks.

#     Args:
#     temp_path (str): The temporary path of the PDF file.

#     Returns:
#     PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
#     """
#     try:
#         logger.info(f"Starting process_pdf task for {temp_path}")

#         # Processors in the order of preference
#         processors = [usePyMuPDF, usePDFMiner, useTextract, useTesseract]

#         response = await process_with_fallbacks(temp_path, processors)
#         logger.info(f"Processing result: {response}")
#         return response

#     except Exception as e:
#         logger.error(f"Failed to process PDF {temp_path} with error: {e}")
#         return PDFTextResponse(file_name="", text="", bounding_boxes=[]).to_dict()

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

        # Dynamic processor loading based on configuration
        processors = []
        parallel_processors = []

        for proc in settings.PDF_PROCESSOR_PRIORITIZATION:  # Use the imported PROCESSOR_PRIORITIZATION
            # Dynamically import processor functions based on the configuration
            try:
                print(f"Loading processor: {proc}")
                logger.debug(f"Loading processor: {proc['processor']}")
                module_name, func_name = proc['processor'].rsplit('.', 1)
                
                # Add debug logging here
                logger.debug(f"Importing processor: module_name='{module_name}', func_name='{func_name}'")

                module = importlib.import_module(module_name)
                processor_func = getattr(module, func_name)
                logger.debug(f"Imported function: {processor_func}, Type: {type(processor_func)}")

                # Validate the imported object
                if not callable(processor_func):
                    logger.error(f"{func_name} in module {module_name} is not callable.")
                    continue

                logger.debug(f"Successfully imported {func_name} from {module_name}.")

                proc['processor'] = processor_func

                if proc['parallel']:
                    parallel_processors.append(proc)
                else:
                    processors.append(proc)

            except (ImportError, AttributeError) as e:
                logger.error(f"Error importing {proc['name']} processor: {e}")
                continue

        # Parallel processing for prioritized processors
        if parallel_processors:
            logger.debug(f"Starting parallel processing for {temp_path} with processors: {parallel_processors}")
            [await process_with_fallbacks(temp_path, [processor]) for processor in parallel_processors]
            # done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # for task in pending:
            #     task.cancel()

            # # Use the first successful result from parallel tasks
            # response = done.pop().result()

            # # If no response from parallel tasks, proceed with remaining processors
            # if not response['bounding_boxes']:
            #     logger.warning("No response from parallel processors, proceeding with remaining processors.")
            #     response = await process_with_fallbacks(temp_path, processors)
        if processors:
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
