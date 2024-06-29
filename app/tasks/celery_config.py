# celery_config.py

from celery import Celery
from app.config import logger, settings

# Initialize the Celery application
app = Celery('pdf_tasks',
             broker= settings.REDIS_URL,
             backend= settings.REDIS_URL,
            #  broker='redis://localhost:6379/0',
            #  backend='redis://localhost:6379/0',
             include=['app.services.processors.pdf.pdf_tasks'])  # Ensure 'pdf_tasks' is the correct name of your module containing tasks


# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # This configuration helps ensure that only JSON formatted messages are accepted for tasks
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
)

# Function to start the Celery worker
def start_worker():
    try:
        app.start()
    except KeyboardInterrupt:
        logger.info("Worker shutdown through keyboard interruption")
    except Exception as e:
        logger.error(f"Failed to start the Celery worker: {e}")

if __name__ == '__main__':
    start_worker()
