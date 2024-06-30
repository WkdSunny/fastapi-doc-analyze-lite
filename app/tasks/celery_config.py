# celery_config.py

from celery import Celery
from app.config import logger, settings

# Initialize the Celery application
app = Celery('pdf_tasks',
             broker= settings.REDIS_URL,
             backend= settings.REDIS_URL,
             include=[
                 'app.services.processors.pdf.pdf_tasks',
                 'app.services.processors.excel',
                 'app.services.processors.word',
                ])  # Ensure 'pdf_tasks' is the correct name of your module containing tasks

app.autodiscover_tasks(['app.services.processors']) 

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # This configuration helps ensure that only JSON formatted messages are accepted for tasks
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Ensure the module where 'process_pdf' is defined is imported
# from app.services.processors.pdf import pdf_tasks
# from app.services.processors.pdf.pdf_tasks import simple_task

@app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')

# Function to start the Celery worker
def start_worker():
    try:
        logger.info("Starting Celery worker")
        app.start()
    except KeyboardInterrupt:
        logger.info("Worker shutdown through keyboard interruption")
    except Exception as e:
        logger.error(f"Failed to start the Celery worker: {e}")

if __name__ == '__main__':
    start_worker()
