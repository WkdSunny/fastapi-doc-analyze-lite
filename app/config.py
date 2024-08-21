# /app/config.py
"""
This module defines the configuration settings for the application.
"""

import os
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse
from pymongo.errors import PyMongoError
from logging.handlers import RotatingFileHandler
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

class MongoClientSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
        return cls._instance

    def get_database(self, db_name):
        return self._instance.client[db_name]

    def close(self):
        logger.info("MongoDB client connection closed.")
        self._instance.client.close()

class AWSSettings:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")

class DBSettings:
    mongo_client = MongoClientSingleton().get_database(os.getenv("DATABASE_NAME"))

class LoggingSettings:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")
    LOG_FILE = "api.log"
    os.makedirs(LOG_DIRECTORY, exist_ok=True)       # Ensure the log directory exists

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if os.getenv("ENV") == "production":
    logger.setLevel(logging.WARNING)

file_handler = RotatingFileHandler(
    os.path.join(LoggingSettings.LOG_DIRECTORY, LoggingSettings.LOG_FILE),
    maxBytes=5 * 1024 * 1024, 
    backupCount=10
)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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

class Settings(AWSSettings, DBSettings, LoggingSettings):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL")
    PDF_PROCESSING_TIMEOUT = int(os.getenv("PDF_PROCESSING_TIMEOUT", 600))
    BEARER_TOKEN = os.getenv("API_TOKEN")

# Helper function to get the base URL
def get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return base_url

async def init_db():
    """Initialize the database and collections."""
    try:
        required_collections = [
            "Tasks", 
            "Documents", 
            "Segments", 
            "Entities", 
            "DocumentClassification", 
            "Topics", 
            "TFIDFKeywords", 
            "Questions", 
            "Answers", 
            "Labels",
            "TokenUsage"
        ]
        database = settings.mongo_client

        # Check if collections exist, if not, create them
        existing_collections = await database.list_collection_names()
        for collection in required_collections:
            if collection not in existing_collections:
                await database.create_collection(collection)
                logger.info(f"Created collection: {collection}")

        logger.info("Database initialized successfully")
    except PyMongoError as e:
        logger.error(f"Failed to connect to the database: {e}")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")

settings = Settings()
