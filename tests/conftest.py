import os
import subprocess
import time

import pytest
import redis
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


from app import app  # Import your FastAPI app
from feature_restriction.config import (
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)


import pytest
from unittest.mock import MagicMock
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.models import UserData


# @pytest.fixture
# def mock_redis():
#     """
#     Fixture to create a mocked Redis instance.
#     """
#     mock_redis = MagicMock()
#     return mock_redis


# @pytest.fixture
# def tripwire_manager(mock_redis):
#     """
#     Fixture to initialize the TripWireManager with a mocked Redis instance.
#     """
#     manager = TripWireManager()
#     manager.redis_client = mock_redis
#     return manager

# @pytest.fixture
# def mock_redis():
#     """
#     Create a mock Redis client.
#     """
#     with patch(
#         "feature_restriction.redis_user_manager.redis.StrictRedis"
#     ) as mock_redis_cls:
#         mock_redis_instance = MagicMock()
#         mock_redis_cls.return_value = mock_redis_instance
#         yield mock_redis_instance


# @pytest.fixture
# def user_manager(mock_redis):
#     """
#     Provide an instance of RedisUserManager with a mocked Redis client.
#     """
#     return RedisUserManager()


# @pytest.fixture
# def sample_user_data():
#     """
#     Create sample user data for testing.
#     """
#     return UserData(
#         user_id="test_user",
#         scam_message_flags=1,
#         credit_cards={"card_001": "12345"},
#         total_credit_cards=1,
#         unique_zip_codes={"12345"},
#         total_spend=100.0,
#         total_chargebacks=5.0,
#         access_flags={"can_message": True, "can_purchase": True},
#     )


###### MOCKS FOR INTEGRATION TETS ######
#######################################################################################
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
def redis_tripwire():
    """
    Fixture to provide a clean Redis instance for the TripWireManager.
    """
    client = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_TRIPWIRE, decode_responses=True
    )
    client.flushdb()  # Clear the Redis database
    yield client
    client.flushdb()  # Clean up after the test


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
