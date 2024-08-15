# /app/configs/celery_config.py

from celery import Celery
from datetime import time
from app.config import logger, settings

# Initialize the Celery application
app = Celery('doc_analyse_tasks',
             broker= settings.REDIS_URL,
             backend= settings.REDIS_URL,
             include=[
                'app.tasks.pdf_tasks',
                'app.tasks.word_tasks',
                'app.tasks.excel_tasks',
                'app.services.document_processors.pdf.muPDF',
                'app.services.document_processors.pdf.pdf_miner',
                'app.services.document_processors.pdf.tesseract',
                'app.services.document_processors.pdf.textract',
             ]
            )

app.autodiscover_tasks(['app.tasks'])

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_log_level='INFO',
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)

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

if __name__ == '__main__':
    start_worker()
