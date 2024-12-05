import os
import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest
import redis
from fastapi.testclient import TestClient

from app import app  # Import your FastAPI app
from feature_restriction.config import (
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.models import Event, UserData
from feature_restriction.publisher import EventPublisher
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.registry import EventHandlerRegistry, RuleRegistry
from feature_restriction.tripwire_manager import TripWireManager
from stream_consumer import RedisStreamConsumer


@pytest.fixture
def mock_redis():
    """
    Create separate mock Redis clients for stream, user, and tripwire databases.
    """
    with patch("redis.StrictRedis") as mock_redis_cls:
        stream_redis_mock = MagicMock()
        user_redis_mock = MagicMock()
        tripwire_redis_mock = MagicMock()

        mock_redis_cls.side_effect = [
            stream_redis_mock,
            user_redis_mock,
            tripwire_redis_mock,
        ]
        yield {
            "stream": stream_redis_mock,
            "user": user_redis_mock,
            "tripwire": tripwire_redis_mock,
        }


@pytest.fixture
def tripwire_manager(mock_redis):
    """
    Provide a TripWireManager instance with a mocked Redis client.
    """
    manager = TripWireManager(mock_redis["tripwire"])
    return manager


@pytest.fixture
def user_manager(mock_redis):
    """
    Provide a RedisUserManager instance with a mocked Redis client.
    """
    manager = RedisUserManager(mock_redis["user"])
    return manager


@pytest.fixture
def rule_registry():
    """
    Provide a mocked RuleRegistry instance.
    """
    return RuleRegistry()


@pytest.fixture
def event_registry():
    """
    Provide a mocked EventHandlerRegistry instance.
    """
    return EventHandlerRegistry()


@pytest.fixture
def stream_consumer(
    mock_redis, user_manager, tripwire_manager, rule_registry, event_registry
):
    """
    Provide an instance of RedisStreamConsumer with mocked dependencies.
    """
    return RedisStreamConsumer(
        redis_client=mock_redis["stream"],
        user_manager=user_manager,
        tripwire_manager=tripwire_manager,
        rule_registry=rule_registry,
        event_registry=event_registry,
    )


@pytest.fixture
def event_publisher(mock_redis):
    """Fixture to create an EventPublisher instance with a mock Redis client."""
    return EventPublisher(redis_client=mock_redis["stream"])


@pytest.fixture
def valid_event():
    """
    Fixture to provide a valid Event instance.
    """
    return Event(
        name="credit_card_added",
        event_properties={
            "user_id": "test_user",
            "card_id": "card_001",
            "zip_code": "12345",
        },
    )


@pytest.fixture
def sample_user_data():
    """
    Create sample UserData for testing.
    """
    return UserData(
        user_id="test_user",
        scam_message_flags=1,
        credit_cards={"card_001": "12345"},
        total_credit_cards=1,
        unique_zip_codes={"12345"},
        total_spend=100.0,
        total_chargebacks=5.0,
        access_flags={"can_message": True, "can_purchase": True},
    )


# @pytest.fixture
# def mock_redis():
#     """
#     Create a mock Redis client for testing.
#     """
#     with patch("redis.StrictRedis") as mock_redis_cls:
#         mock_redis_instance = MagicMock()
#         mock_redis_cls.return_value = mock_redis_instance
#         yield mock_redis_instance


###### MOCKS FOR INTEGRATION TETS ######
#######################################################################################
@pytest.fixture(scope="function")
def test_client():
    """
    Fixture to provide a FastAPI test client.
    """
    return TestClient(app)


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
