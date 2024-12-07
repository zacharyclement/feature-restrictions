import os

from dotenv import load_dotenv

load_dotenv()


# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_DB_USER = 0  # Default DB for user data
REDIS_DB_STREAM = 1  # Separate DB for the stream
REDIS_DB_TRIPWIRE = 2  # Separate DB for the tripwire data
REDIS_DB_LOCUST = 3  # Separate DB for Locust load test

# Stream configuration
EVENT_STREAM_KEY = "event_stream"
CONSUMER_GROUP = "group1"
CONSUMER_NAME = "consumer1"

# Tripwire configuration
TIIME_WINDOW = 300  # Time window in seconds (e.g., 5 minutes)
THRESHOLD = 0.05  # 5% of total users
