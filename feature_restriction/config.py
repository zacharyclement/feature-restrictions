import os

from dotenv import load_dotenv

load_dotenv()


EVENT_STREAM_KEY = "event_stream"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
# Redis DB indices
REDIS_DB_USER = 0  # Default DB for user data
REDIS_DB_STREAM = 1  # Separate DB for the stream
REDIS_DB_TRIPWIRE = 2  # Separate DB for the tripwire data
