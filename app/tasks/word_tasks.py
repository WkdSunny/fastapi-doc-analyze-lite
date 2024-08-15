# /app/tasks/word_tasks.py
"""
This module defines the Word processing tasks for the FastAPI application.
"""

import asyncio
import functools
import importlib
from celery import shared_task, Task
from app.config import settings, logger
from app.tasks.async_tasks import run_async_task
from app.tasks.celery_tasks import wait_for_celery_task
from app.services.document_processors.word import useDocX
from app.config import settings

# class WordTask(Task):
#     autoretry_for = (Exception,)
#     retry_kwargs = {'max_retries': 3, 'countdown': 5}
#     retry_backoff = True

# @shared_task(base=WordTask)
@shared_task
def process_word(file_path):
    """
    Process Word documents based on type and handle fallbacks.

    Args:
    file_path (str): The path to the Word document.

    Returns:
    WordTextResponse: Contains the file name and converted JSON data.
    """
    try:
        results = run_async_task(_process_word, file_path)
        return results
    except Exception as e:
        logger.error(f"Failed to process Word document {file_path} with error: {e}")
        return {"file_name":file_path, "data": []}

async def process_with_fallbacks(file_path, processors):
    """
    Process the Word document using a list of processors with fallback.

    Args:
    file_path (str): The path to the Word document.
    processors (list): A list of processor tasks to try in order.

    Returns:
    WordTextResponse: The response from the first successful processor.
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

            response = await wait_for_celery_task(task.id, settings.WORD_PROCESSING_TIMEOUT)
            if response['data']:
                return response
        except asyncio.TimeoutError:
            logger.error(f"Processor {processor['name']} timed out for {file_path}")
        except Exception as e:
            logger.error(f"Processor {processor['name']} failed for {file_path} with error: {e}")
    
    return {"file_name":file_path, "data": []}

async def _process_word(file_path):
    """
    Process Word documents based on type and handle fallbacks.

    Args:
    file_path (str): The path to the Word document.

    Returns:
    WordTextResponse: Contains the file name and converted JSON data.
    """
    try:
        logger.info(f"Starting process_word task for {file_path}")

        # processors = []
        # parallel_processors = []

        # for proc in settings.WORD_PROCESSOR_PRIORITIZATION:
        #     module_name, func_name = proc['processor'].rsplit('.', 1)
        #     module = importlib.import_module(module_name)
        #     processor_func = functools.partial(getattr(module, func_name))
        #     proc['processor'] = processor_func

        #     if proc['parallel']:
        #         parallel_processors.append(proc)
        #     else:
        #         processors.append(proc)

        # if parallel_processors:
        #     tasks = [process_with_fallbacks(file_path, [processor]) for processor in parallel_processors]
        #     done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        #     for task in pending:
        #         task.cancel()

        #     response = done.pop().result()

        #     if not response['data']:
        #         response = await process_with_fallbacks(file_path, processors)
        # else:
        #     response = await process_with_fallbacks(file_path, processors)

        response = await process_with_fallbacks(file_path, useDocX)
        logger.info(f"Processing result: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to process Word document {file_path} with error: {e}")
        return {"file_name":file_path, "data": []}
