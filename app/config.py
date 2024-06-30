import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    BEARER_TOKEN = os.getenv("API_TOKEN")
    REDIS_URL = os.getenv("REDIS_URL")

    # Define the path for log files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the directory where the script resides
    LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")
    LOG_FILE = "api.log"

def setup_logging():
    """Set up the logging configuration."""
    os.makedirs(Settings.LOG_DIRECTORY, exist_ok=True)  # Ensure the log directory exists
    log_file_path = os.path.join(Settings.LOG_DIRECTORY, Settings.LOG_FILE)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set global level to DEBUG to capture all logs

    # Create handlers
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
    file_handler.setLevel(logging.DEBUG)  # Set file handler level to DEBUG

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set console handler level to DEBUG

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

     # Set logging levels for specific modules
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("aiobotocore").setLevel(logging.WARNING)

    return logger

# Initialize the logger
logger = setup_logging()

settings = Settings()
