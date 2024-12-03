from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from feature_restriction.models import Event


@pytest.fixture
def mock_redis():
    """
    Fixture to create a mock Redis instance.
    """
    with patch("feature_restriction.publisher.redis.StrictRedis") as mock_redis_cls:
        mock_redis_instance = MagicMock()
        mock_redis_cls.return_value = mock_redis_instance
        yield mock_redis_instance


def test_add_event_to_stream_success(event_publisher, mock_redis, valid_event):
    """
    Test adding a valid event to the Redis stream successfully.
    """
    # Call the method
    response = event_publisher.add_event_to_stream(valid_event)

    # Assert the Redis xadd method was called correctly
    mock_redis.xadd.assert_called_once()
    assert "status" in response
    assert response["status"] == f"Event '{valid_event.name}' added to the stream."


def test_add_event_to_stream_missing_fields(event_publisher):
    """
    Test adding an event with missing fields raises a ValueError.
    """
    invalid_event = Event(name="", event_properties={})
    with pytest.raises(HTTPException) as exc_info:
        event_publisher.add_event_to_stream(invalid_event)

    assert exc_info.value.status_code == 400
    assert "Event is missing required fields" in str(exc_info.value.detail)


def test_add_event_to_stream_invalid_user_id(event_publisher):
    """
    Test adding an event with an invalid user_id raises a validation error.
    """
    invalid_event = Event(
        name="credit_card_added", event_properties={"card_id": "card_001"}
    )
    with pytest.raises(HTTPException) as exc_info:
        event_publisher.add_event_to_stream(invalid_event)

    assert exc_info.value.status_code == 400
    assert "Validation error" in str(exc_info.value.detail)


def test_add_event_to_stream_redis_error(event_publisher, mock_redis, valid_event):
    """
    Test handling a Redis error when adding an event to the stream.
    """
    # Simulate a Redis error
    mock_redis.xadd.side_effect = Exception("Redis connection error")

    with pytest.raises(HTTPException) as exc_info:
        event_publisher.add_event_to_stream(valid_event)

    assert exc_info.value.status_code == 500
    assert "Unexpected error occurred while adding event" in str(exc_info.value.detail)


def test_add_event_to_stream_logs_event(
    event_publisher, mock_redis, valid_event, caplog
):
    """
    Test that the event is logged when added successfully.
    """
    event_publisher.add_event_to_stream(valid_event)

    assert f"Received event: {valid_event}" in caplog.text
    assert "Added event to Redis stream" in caplog.text
