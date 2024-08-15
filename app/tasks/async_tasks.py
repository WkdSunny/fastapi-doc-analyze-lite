# /app/tasks/async_tasks.py
"""
This module defines a Celery task for running asynchronous tasks in a synchronous context.
"""

import asyncio
from celery import shared_task
from app.config import logger

@shared_task
def run_async_task(async_func, *args, **kwargs):
    """
    Run an asynchronous task in a synchronous context, suitable for Celery tasks.

    Args:
    async_func (coroutine): The asynchronous function to run.
    *args: Arguments to pass to the asynchronous function.
    **kwargs: Keyword arguments to pass to the asynchronous function.

    Returns:
    result: The result of the asynchronous function.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If there's an existing running loop, use it to run the async function
        future = asyncio.run_coroutine_threadsafe(async_func(*args, **kwargs), loop)
        return future.result()
    else:
        try:
            # If no running loop, create and run a new loop
            result = loop.run_until_complete(async_func(*args, **kwargs))
            logger.info(f"Successfully executed async task: {async_func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing async task {async_func.__name__}: {e}")
            raise
