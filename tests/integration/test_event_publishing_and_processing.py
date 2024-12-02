import json
import time

from feature_restriction.config import EVENT_STREAM_KEY
from feature_restriction.models import Event
from feature_restriction.publisher import EventPublisher
from feature_restriction.redis_user_manager import RedisUserManager


def test_scam_message_flagged_event(
    redis_stream, redis_user, stream_consumer_subprocess, redis_tripwire
):
    """
    Test that RedisStreamConsumer processes 'scam_message_flagged' events.
    """
    # Arrange
    publisher = EventPublisher()
    user_manager = RedisUserManager()

    event = Event(name="scam_message_flagged", event_properties={"user_id": "12345"})

    # Act
    publisher.add_event_to_stream(event)
    time.sleep(1)  # Wait for the consumer to process

    # Assert
    user_data = user_manager.get_user(event.event_properties["user_id"])
    assert user_data.scam_message_flags == 1
    assert user_data.user_id == "12345"


def test_event_publishing_and_consuming(
    redis_stream, redis_user, stream_consumer_subprocess, redis_tripwire
):
    """
    Test the integration between EventPublisher and RedisStreamConsumer.
    """
    # Arrange
    publisher = EventPublisher()  # Uses redis_stream via EventPublisher
    user_manager = RedisUserManager()

    # Create an Event object to mirror the API flow
    event = Event(
        name="credit_card_added",
        event_properties={
            "user_id": "12345",
            "card_id": "card_001",
            "zip_code": "54321",
        },
    )

    # Act: Publish the event using EventPublisher
    publisher.add_event_to_stream(event)

    # Allow time for the consumer to process
    time.sleep(1)  # Adjust timing based on system performance

    # Assert: Verify the user data was updated by RedisStreamConsumer
    user_id = event.event_properties["user_id"]
    user_data = user_manager.get_user(user_id)

    assert user_data.total_credit_cards == 1
    assert user_data.credit_cards["card_001"] == "54321"
    assert "54321" in user_data.unique_zip_codes


def test_event_processing_via_consumer(
    redis_stream, redis_user, stream_consumer_subprocess, redis_tripwire
):
    """
    Test that RedisStreamConsumer processes events from the stream and updates user data.
    """
    # Arrange
    publisher = EventPublisher()  # Uses redis_stream via EventPublisher
    user_manager = RedisUserManager()

    # Create an Event object to simulate a realistic API call
    event = Event(name="scam_message_flagged", event_properties={"user_id": "12345"})

    # Act: Publish the event using EventPublisher
    publisher.add_event_to_stream(event)

    # Allow time for the consumer to process
    time.sleep(1)  # Adjust timing based on system performance

    # Assert: Verify the consumer processed the event
    user_id = event.event_properties["user_id"]
    user_data = user_manager.get_user(user_id)

    # Verify the scam message flag count is incremented
    assert user_data.scam_message_flags == 1

    # Additional check for accurate user data
    assert user_data.user_id == "12345"


def test_chargeback_occurred_event(
    redis_stream, redis_user, stream_consumer_subprocess, redis_tripwire
):
    """
    Test that RedisStreamConsumer processes 'chargeback_occurred' events.
    """
    # Arrange
    publisher = EventPublisher()
    user_manager = RedisUserManager()

    event = Event(
        name="chargeback_occurred",
        event_properties={"user_id": "12345", "amount": 123.45},
    )

    # Act
    publisher.add_event_to_stream(event)
    time.sleep(1)  # Wait for the consumer to process

    # Assert
    user_data = user_manager.get_user(event.event_properties["user_id"])
    assert user_data.total_chargebacks == 123.45
    assert user_data.user_id == "12345"


def test_e2e_concurrent_events(
    test_client, redis_stream, redis_user, stream_consumer_subprocess, redis_tripwire
):
    """
    Test the end-to-end flow for concurrent events affecting multiple users.
    """
    # Arrange
    user_manager = RedisUserManager()
    users = [
        {"user_id": "12345", "card_id": "card_001", "zip_code": "54321"},
        {"user_id": "67890", "card_id": "card_002", "zip_code": "98765"},
    ]

    # Act: Send events concurrently for multiple users
    for user in users:
        event_payload = {
            "name": "credit_card_added",
            "event_properties": user,
        }
        response = test_client.post("/event", json=event_payload)
        assert response.status_code == 200

    # Allow time for the consumer to process the events
    time.sleep(1)

    # Assert: Validate user data for each user
    for user in users:
        user_data = user_manager.get_user(user["user_id"])
        assert user_data.total_credit_cards == 1
        assert user_data.credit_cards[user["card_id"]] == user["zip_code"]
        assert user["zip_code"] in user_data.unique_zip_codes


import json
import time

from feature_restriction.config import EVENT_STREAM_KEY
from feature_restriction.redis_user_manager import RedisUserManager


def test_event_publishing_to_stream(
    test_client, redis_stream, redis_tripwire, redis_user, stream_consumer_subprocess
):
    """
    Test if events are successfully added to the Redis stream.
    """
    # Arrange
    event_payload = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "12345",
            "card_id": "card_678",
            "zip_code": "12345",
        },
    }

    # Act
    response = test_client.post("/event", json=event_payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "status": "Event 'credit_card_added' added to the stream."
    }

    # Check Redis stream for the event
    events = redis_stream.xrange(EVENT_STREAM_KEY)
    assert len(events) == 1  # Ensure exactly one event was added

    # Validate the event content
    event_id, event_data = events[0]
    assert event_data["name"] == "credit_card_added"
    assert (
        json.loads(event_data["event_properties"]) == event_payload["event_properties"]
    )


def test_multiple_event_handling_via_endpoint(
    test_client, redis_stream, redis_user, stream_consumer_subprocess
):
    """
    Test the processing of multiple events in sequence via the endpoint.
    """
    # Arrange
    user_manager = RedisUserManager()
    user_id = "12345"

    events = [
        {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": user_id,
                "card_id": "card_001",
                "zip_code": "54321",
            },
        },
        {
            "name": "scam_message_flagged",
            "event_properties": {"user_id": user_id},
        },
        {
            "name": "purchase_made",
            "event_properties": {"user_id": user_id, "amount": 100.50},
        },
    ]

    # Act: Send events to the endpoint
    for event in events:
        response = test_client.post("/event", json=event)
        assert response.status_code == 200
        assert response.json() == {
            "status": f"Event '{event['name']}' added to the stream."
        }

    # Allow time for the consumer to process
    time.sleep(3)

    # Assert: Validate user data
    user_data = user_manager.get_user(user_id)

    # Validate updates from all events
    assert user_data.total_credit_cards == 1
    assert user_data.credit_cards["card_001"] == "54321"
    assert "54321" in user_data.unique_zip_codes
    assert user_data.scam_message_flags == 1
    assert user_data.total_spend == 100.50


def test_event_with_missing_data_via_endpoint(
    test_client, redis_stream, redis_user, stream_consumer_subprocess, caplog
):
    """
    Test the behavior of the system when processing an event with missing data via the endpoint.
    """
    # Arrange
    # Invalid event: missing user_id in event_properties
    invalid_event = {
        "name": "credit_card_added",
        "event_properties": {"card_id": "card_001", "zip_code": "54321"},  # No user_id
    }

    # Act: Send the invalid event to the endpoint
    response = test_client.post("/event", json=invalid_event)

    # Assert: Verify response indicates failure
    assert response.status_code == 400  # Bad Request
    assert "Validation error" in response.json()["detail"]

    # Allow time for the consumer to process
    time.sleep(1)

    # Assert: Verify that no user data was created or updated
    all_keys = redis_user.keys("*")
    assert len(all_keys) == 0  # Ensure no user was added

    # Check logs for error handling
    assert "Validation error" in caplog.text
    assert "Event is missing" in caplog.text
