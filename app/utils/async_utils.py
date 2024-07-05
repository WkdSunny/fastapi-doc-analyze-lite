# async_utils.py
"""
This module defines utility functions for running asynchronous tasks in a synchronous context.
"""

import asyncio

def run_async_task(async_func, *args):
    """
    Run an asynchronous task in a synchronous context, suitable for Celery tasks.

    Args:
    async_func (coroutine): The asynchronous function to run.
    *args: Arguments to pass to the asynchronous function.

    Returns:
    result: The result of the asynchronous function.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(async_func(*args), loop)
        return future.result()
    else:
        return loop.run_until_complete(async_func(*args))
    
# Example usage:
if __name__ == "__main__":
    async def async_task():
        await asyncio.sleep(1)
        return "Task completed"
    
    result = run_async_task(async_task)
    print(result)