from datetime import time
import os
import platform
from celery import Celery, signals
from app.config import logger, settings

# Initialize the Celery application
app = Celery(
    'doc_analyse_tasks',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.pdf_tasks',
        'app.tasks.excel_tasks',
        'app.tasks.word_tasks',
        'app.services.processors.pdf.muPDF',
        'app.services.processors.pdf.pdf_miner',
        'app.services.processors.pdf.textract',
        'app.services.processors.pdf.tesseract',
    ]
)

# Automatically discover tasks in specified modules
app.autodiscover_tasks(['app.tasks'])

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ensure only JSON formatted messages are accepted for tasks
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_log_level='INFO',
    task_acks_late=True,  # Ensures tasks are not marked as completed until fully executed
    worker_max_tasks_per_child=100,  # Replace worker after 100 tasks to manage memory usage
    worker_hijack_root_logger=False,  # Ensure Celery doesn't override root logger
)

# Check if running on macOS and set environment variable to avoid fork safety issues
if platform.system() == 'Darwin':
    logger.info("Running on macOS. Setting OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES")
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

    # Use Celery's worker_process_init signal to handle reinitialization
    @signals.worker_process_init.connect
    def reinitialize_resources_after_fork(**kwargs):
        logger.info("Reinitializing resources after fork")

# Function to start the Celery worker with improved error handling and retry mechanism
# def start_worker(max_retries=3, delay=5):
def start_worker():
#     retries = 0
#     while retries < max_retries:
    try:
        logger.info("Starting Celery worker")
        app.start()
        # break
    except KeyboardInterrupt:
        logger.info("Worker shutdown through keyboard interruption")
        # break
    # except Exception as e:
    #     retries += 1
    #     logger.error(f"Failed to start the Celery worker: {e}. Retry {retries}/{max_retries}")
    #     if retries < max_retries:
    #         logger.info(f"Retrying in {delay} seconds...")
    #         time.sleep(delay)
    #     else:
    #         logger.error("Max retries reached. Exiting.")
    #         break

if __name__ == '__main__':
    start_worker()
