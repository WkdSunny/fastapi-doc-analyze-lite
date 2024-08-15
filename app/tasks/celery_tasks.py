# /app/tasks/celery_tasks.py
"""
This module defines utility functions for celery to be used in the FastAPI application.
"""

import asyncio
from celery import shared_task
from celery.result import AsyncResult
from app.config import logger

@shared_task
async def wait_for_celery_task(task_id: str, timeout: int):
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
    start_time = asyncio.get_event_loop().time()
    
    try:
        while not task.ready():
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError(f"Celery task {task_id} timed out after {timeout} seconds")
            await asyncio.sleep(1)
        
        result = task.result
        if task.failed():
            raise task.result
        logger.info(f"Task {task_id} completed successfully with result: {result}")
        return result
    
    except TimeoutError as te:
        logger.error(te)
        raise

    except Exception as e:
        logger.error(f"Error occurred while waiting for Celery task {task_id}: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    task_id = "task_id"
    timeout = 60
    try:
        asyncio.run(wait_for_celery_task(task_id, timeout))
    except Exception as e:
        logger.error(f"Failed to complete task {task_id}: {e}")

if __name__ == "__main__":
    # Example usage of the wait_for_celery_task function
    task_id = "task_id"
    timeout = 60
    try:
        asyncio.run(wait_for_celery_task(task_id, timeout))
    except Exception as e:
        logger.error(f"Failed to complete task {task_id}: {e}")