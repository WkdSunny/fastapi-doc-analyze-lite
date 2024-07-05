# utils.py
"""
This module defines utility functions for celery to be used in the FastAPI application.
"""

import asyncio
from celery import shared_task
from celery.result import AsyncResult
from app.config import logger

@shared_task
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
    start_time = asyncio.get_event_loop().time()
    while not task.ready():
        if (asyncio.get_event_loop().time() - start_time) > timeout:
            raise TimeoutError("Celery task timed out")
        await asyncio.sleep(1)
    logger.info(f"Task result: {task.result}")
    return task.result

# Example usage:
if __name__ == "__main__":
    task_id = "task_id"
    timeout = 60
    asyncio.run(wait_for_celery_task(task_id, timeout))