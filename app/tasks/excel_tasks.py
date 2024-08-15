# /app/tasks/excel_tasks.py
"""
This module defines the Excel processing tasks for the FastAPI application.
"""

import asyncio
import functools
import importlib
from celery import shared_task, Task
from app.config import settings, logger
from app.tasks.async_tasks import run_async_task
from app.tasks.celery_tasks import wait_for_celery_task
from app.config import settings

class ExcelTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 5}
    retry_backoff = True

@shared_task(base=ExcelTask)
def process_excel(file_path):
    """
    Process Excel files based on type and handle fallbacks.

    Args:
    file_path (str): The path to the Excel file.

    Returns:
    ExcelTextResponse: Contains the file name and converted JSON data.
    """
    try:
        results = run_async_task(_process_excel, file_path)
        return results
    except Exception as e:
        logger.error(f"Failed to process Excel {file_path} with error: {e}")
        return {"file_name":file_path, "data": []}

async def process_with_fallbacks(file_path, processors):
    """
    Process the Excel file using a list of processors with fallback.

    Args:
    file_path (str): The path to the Excel file.
    processors (list): A list of processor tasks to try in order.

    Returns:
    ExcelTextResponse: The response from the first successful processor.
    """
    for processor in processors:
        try:
            processor_func = processor['processor']
            logger.info(f"Trying processor {processor['name']} for {file_path}")
            
            # Safely execute the Celery task with delay
            if callable(processor_func):
                task = processor_func.delay(file_path)
                logger.debug(f"Task queued: {task.id}")
            else:
                logger.error(f"Processor function {processor_func} is not callable")
                continue

            response = await wait_for_celery_task(task.id, settings.EXCEL_PROCESSING_TIMEOUT)
            if response['data']:
                return response
        except asyncio.TimeoutError:
            logger.error(f"Processor {processor['name']} timed out for {file_path}")
        except Exception as e:
            logger.error(f"Processor {processor['name']} failed for {file_path} with error: {e}")
    
    return {"file_name":file_path, "data": []}

async def _process_excel(file_path):
    """
    Process Excel files based on type and handle fallbacks.

    Args:
    file_path (str): The path to the Excel file.

    Returns:
    ExcelTextResponse: Contains the file name and converted JSON data.
    """
    try:
        logger.info(f"Starting process_excel task for {file_path}")

        # Dynamic processor loading based on configuration
        processors = []
        parallel_processors = []

        for proc in settings.EXCEL_PROCESSOR_PRIORITIZATION:  # Use the imported PROCESSOR_PRIORITIZATION
            module_name, func_name = proc['processor'].rsplit('.', 1)
            module = importlib.import_module(module_name)
            processor_func = functools.partial(getattr(module, func_name))
            proc['processor'] = processor_func

            if proc['parallel']:
                parallel_processors.append(proc)
            else:
                processors.append(proc)

        # Parallel processing for prioritized processors
        if parallel_processors:
            tasks = [process_with_fallbacks(file_path, [processor]) for processor in parallel_processors]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            response = done.pop().result()

            if not response['data']:
                response = await process_with_fallbacks(file_path, processors)
        else:
            response = await process_with_fallbacks(file_path, processors)

        logger.info(f"Processing result: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to process Excel {file_path} with error: {e}")
        return {"file_name":file_path, "data": []}
