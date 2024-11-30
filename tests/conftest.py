import threading

import pytest
import redis
from fastapi.testclient import TestClient

from app import app  # Import your FastAPI app
from feature_restriction.config import (
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from stream_consumer import RedisStreamConsumer


@pytest.fixture(scope="function")
def redis_stream():
    """
    Fixture to provide a clean Redis instance for stream testing.
    """
    client = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STREAM, decode_responses=True
    )
    client.flushdb()  # Clear the Redis database
    yield client
    client.flushdb()  # Clean up after the test


@pytest.fixture(scope="function")
def redis_user():
    """
    Fixture to provide a clean Redis instance for user management testing.
    """
    client = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_USER, decode_responses=True
    )
    client.flushdb()  # Clear the Redis database
    yield client
    client.flushdb()  # Clean up after the test


@pytest.fixture(scope="function")
def test_client():
    """
    Fixture to provide a FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def stream_consumer(redis_client):
    """
    Fixture for the RedisStreamConsumer.
    """
    consumer_group = "test_group"
    consumer_name = "test_consumer"
    consumer = RedisStreamConsumer(
        redis_client=redis_client,
        stream_key=EVENT_STREAM_KEY,
        consumer_group=consumer_group,
        consumer_name=consumer_name,
    )

    # Run the consumer in a separate thread
    consumer_thread = threading.Thread(target=consumer.start, daemon=True)
    consumer_thread.start()

    # Yield control to the test
    yield consumer

    # Stop the consumer and wait for the thread to finish
    consumer.redis_client.xgroup_destroy(
        EVENT_STREAM_KEY, consumer_group
    )  # Clean up group
    consumer_thread.join(timeout=5)  # Ensure the thread stops within 5 seconds
