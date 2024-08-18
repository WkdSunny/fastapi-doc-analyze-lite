# /app/configs/celery_config.py

import time
import threading
from celery import Celery
from app.config import logger, settings

# Initialize the Celery application
app = Celery('doc_analyse_lite_tasks',
             broker= settings.REDIS_URL,
             backend= settings.REDIS_URL,
             include=[
                'app.tasks.pdf_tasks',
                'app.tasks.word_tasks',
                'app.tasks.excel_tasks',
                'app.tasks.img_tasks',
             ]
            )

app.autodiscover_tasks(['app.tasks'])

# Configure Celery settings
app.conf.update(
    task_serializer='json',                         # Use JSON to serialize task arguments and results.
    accept_content=['json'],                        # Accept only JSON format for content.
    result_serializer='json',                       # Serialize task results as JSON.
    timezone='America/New_York',                    # Set timezone to US Eastern Time (ET).
    enable_utc=True,                                # Enable UTC, ensuring consistency across different regions.
    broker_connection_retry_on_startup=True,        # Retry connecting to the broker if it fails at startup.
    worker_log_level='INFO',                        # Set logging level to INFO for detailed logs.
    task_acks_late=True,                            # Acknowledge tasks after execution to prevent data loss if a worker crashes.
    worker_max_tasks_per_child=100,                 # Recycle workers after 100 tasks to prevent memory leaks.
    worker_prefetch_multiplier=1                    # Prevent overloading a single worker by balancing task distribution.
)

stop_event = threading.Event()

# Function to start the Celery worker
def start_worker(max_retries=3, delay=5):
    """
    Start the Celery worker.

    Args:
        max_retries (int): The maximum number of retries to attempt.
        delay (int): The delay between retries in seconds.
    """
    retries = 0
    while retries < max_retries:
        if stop_event.is_set():
            logger.info("Stop event detected. Shutting down worker before start.")
            break
        try:
            logger.info("Starting Celery worker")
            app.start()
            break
        except KeyboardInterrupt:
            logger.info("Worker shutdown through keyboard interruption")
            break
        except Exception as e:
            retries += 1
            logger.error(f"Failed to start the Celery worker: {e}. Retry {retries}/{max_retries}")
            if retries < max_retries:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Max retries reached. Exiting.")
                break

def run_worker_in_thread():
    """
    Runs the Celery worker in a separate thread.

    Returns:
        Tuple[threading.Event, threading.Thread]: The stop event and the worker thread.
    """
    worker_thread = threading.Thread(target=start_worker)
    worker_thread.start()
    return stop_event, worker_thread

def stop_worker():
    """
    Signals the Celery worker to shut down gracefully.
    """
    stop_event.set()
    logger.info("Stop event set. Worker will finish current tasks and then shut down.")

if __name__ == '__main__':
    # Start the worker in a separate thread
    stop_event, worker_thread = run_worker_in_thread()

    # Simulate performing other tasks
    try:
        logger.info("Main thread is running other tasks...")
        for i in range(10):
            logger.info(f"Main thread working... {i}")
            time.sleep(2)  # Simulate work
    except KeyboardInterrupt:
        logger.info("Main thread interrupted. Initiating shutdown.")

    # Programmatically stop the worker
    logger.info("Stopping the worker programmatically.")
    stop_worker()
    worker_thread.join()  # Wait for the worker thread to finish
    logger.info("Worker has been shut down gracefully.")