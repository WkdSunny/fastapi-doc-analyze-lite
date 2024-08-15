# /app/tasks/debug_tasks.py
from celery import shared_task
from app.config import logger

@shared_task(bind=True)
def debug_task(self, message="Debug Task Executed"):
    """
    A simple Celery task for debugging purposes.

    Args:
        message (str): A custom message to log when the task is executed.

    Returns:
        str: The message that was logged.
    """
    logger.info(f'Debug Task - Request: {self.request!r}')
    logger.info(f'Debug Task - Message: {message}')
    return message

# Example usage when running this file directly
if __name__ == "__main__":
    debug_task.apply_async(args=["Running Debug Task in development..."])
