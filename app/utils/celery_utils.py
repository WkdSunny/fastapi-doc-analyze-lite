# utils.py
"""
This module defines utility functions for celery to be used in the FastAPI application.
"""

import asyncio
from celery.result import AsyncResult
from app.config import logger

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

# Example usage:
if __name__ == "__main__":
    task_id = "task_id"
    timeout = 60
    asyncio.run(wait_for_celery_task(task_id, timeout))