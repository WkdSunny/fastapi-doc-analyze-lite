# /app/config.py

import os
import logging
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse

# Load environment variables
load_dotenv()

class Settings:
    """Class to store application settings."""
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")

    # External API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    BEARER_TOKEN = os.getenv("API_TOKEN")
    REDIS_URL = os.getenv("REDIS_URL")
    PDF_PROCESSING_TIMEOUT = int(os.getenv("PDF_PROCESSING_TIMEOUT", 180))  # Default to 180 seconds

    # Define the path for log files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the directory where the script resides
    LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")
    LOG_FILE = "api.log"

    # Define DB settings
    MONGO_URI = os.getenv("MONGO_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME")

    # Initialize MongoDB client
    mongo_client = MongoClient(MONGO_URI)
    database = mongo_client[DATABASE_NAME]

    # Define the URL for the question generation API
    QUESTIONS_ENDPOINT = os.getenv("SELF_QUESTIONS_URI")

    # Configuration for PDF Processor Prioritization
    PDF_PROCESSOR_PRIORITIZATION = [
        {
            'name': 'muPDF',
            'processor': 'app.services.processors.pdf.muPDF.usePyMuPDF',
            'parallel': True,  # Run in parallel with others
            'success_rate': 0.95,  # Assumed success rate
            'speed': 'fast',  # Assumed processing speed
        },
        {
            'name': 'pdf_miner',
            'processor': 'app.services.processors.pdf.pdf_miner.usePDFMiner',
            'parallel': True,
            'success_rate': 0.85,
            'speed': 'medium',
        },
        {
            'name': 'textract',
            'processor': 'app.services.processors.pdf.textract.useTextract',
            'parallel': False,  # Sequential fallback
            'success_rate': 0.70,
            'speed': 'slow',
        },
        {
            'name': 'tesseract',
            'processor': 'app.services.processors.pdf.tesseract.useTesseract',
            'parallel': True,
            'success_rate': 0.60,
            'speed': 'slow',
        },
    ]

    IMG_PROCESSOR_PRIORITIZATION = [
        {
            'name': 'textract',
            'processor': 'app.services.processors.pdf.textract.useTextract',
            'parallel': False,  # Sequential fallback
            'success_rate': 0.70,
            'speed': 'slow',
        },
        {
            'name': 'tesseract',
            'processor': 'app.services.processors.pdf.tesseract.useTesseract',
            'parallel': True,
            'success_rate': 0.60,
            'speed': 'slow',
        },
    ]

    EXCEL_PROCESSOR_PRIORITIZATION = [
        {
            'name': 'openpyxl',
            'processor': 'app.services.processors.excel.openpyxl.useOpenpyxl',
            'parallel': True,
        },
    ]

    WORD_PROCESSOR_PRIORITIZATION = [
        {
            'name': 'python-docx',
            'processor': 'app.services.processors.word.python_docx.usePythonDocx',
            'parallel': True,
        },
    ]



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
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("mongo").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("BertForSequenceClassification").setLevel(logging.CRITICAL)
    logging.getLogger("transformers").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("gunicorn").setLevel(logging.WARNING)
    logging.getLogger("spacy").setLevel(logging.WARNING)


    return logger

def init_db():
    """Initialize the database and collections."""
    try:
        required_collections = ["Documents", "Segments", "Entities", "DocumentClassification", "Topics", "TFIDFKeywords", "Questions", "Answers", "Labels"]
        database = Settings.database

        # Check if collections exist, if not, create them
        existing_collections = database.list_collection_names()
        for collection in required_collections:
            if collection not in existing_collections:
                database.create_collection(collection)
                logger.info(f"Created collection: {collection}")

        logger.info("Database initialized successfully")
    except ConnectionError as e:
        logger.error(f"Failed to connect to the database: {e}")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")

def get_base_url(url: str) -> str:
    """
    Extracts the base URL from a full URL, removing the path.
    :param url: The full URL.
    :return: The base URL without the path.
    """
    parsed_url = urlparse(url)
    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return base_url

# Initialize the logger
logger = setup_logging()
settings = Settings()