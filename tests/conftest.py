from queue import Queue

import pytest
from fastapi.testclient import TestClient

from app import app  # Import your FastAPI app here
from feature_restriction.event_consumer import EventConsumer
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.user_manager import UserManager

# @pytest.fixture
# def consumer_with_queue():
#     """
#     Fixture to manage the event consumer lifecycle during tests.
#     """
#     event_queue = Queue()
#     user_manager = UserManager()
#     tripwire_manager = TripWireManager()
#     consumer = EventConsumer(event_queue, user_manager, tripwire_manager)

#     # Start the consumer
#     consumer.start()

#     yield consumer  # Ensure the consumer is running during the test

#     # Stop the consumer after the test
#     consumer.stop()


@pytest.fixture
def client():
    """
    Fixture to provide a TestClient instance for testing.
    """
    return TestClient(app)


@pytest.fixture
def reset_user_manager():
    """
    Provides a fresh instance of UserManager for each test.
    """
    return UserManager()


@pytest.fixture
def reset_tripwire_manager():
    """
    Fixture to reset the tripwire manager for tests.
    """
    tripwire_manager = TripWireManager()
    tripwire_manager.clear_rules()
    return tripwire_manager
