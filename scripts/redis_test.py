import redis
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Redis URL from environment variables
REDIS_URL = os.getenv('REDIS_URL')

# Connect to Redis
try:
    r = redis.StrictRedis.from_url(REDIS_URL)
    r.ping()
    print("Connected to Redis!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")

# Example usage:
# python -m redis_test