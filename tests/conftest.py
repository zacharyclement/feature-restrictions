import subprocess
import threading
import time

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


import os
import subprocess
import time

import pytest
import redis

from feature_restriction.config import (
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_HOST,
    REDIS_PORT,
)


@pytest.fixture(scope="function")
def stream_consumer_subprocess():
    """
    Fixture to run the Redis stream consumer as a subprocess.
    """
    # Calculate the path to the consumer script
    script_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )  # Navigate up from ./tests
    script_path = os.path.join(script_dir, "stream_consumer.py")

    # Verify the script exists
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Consumer script not found at {script_path}")

    # Start the consumer as a subprocess
    process = subprocess.Popen(
        ["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print("consumer running as subprocess")
    # Wait for the consumer to initialize
    time.sleep(1)  # Adjust based on startup time

    yield process  # Yield the subprocess for testing

    # Terminate the subprocess
    process.terminate()
    process.wait(timeout=5)  # Wait for the process to exit
    if process.poll() is None:  # Check if still running
        process.kill()  # Force kill if it hasn't exited

    # Optionally log any captured output for debugging
    stdout, stderr = process.communicate()
    print("Consumer STDOUT:", stdout.decode())
    print("Consumer STDERR:", stderr.decode())
