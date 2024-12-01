import json
import time

from feature_restriction.config import EVENT_STREAM_KEY
from feature_restriction.publisher import EventPublisher
from feature_restriction.redis_user_manager import RedisUserManager


def test_event_publishing_to_stream(test_client, redis_stream):
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
    assert response.json() == {"status": "Event added to the stream."}

    # Check Redis stream for the event
    events = redis_stream.xrange(EVENT_STREAM_KEY)
    assert len(events) == 1  # Ensure exactly one event was added

    # Validate the event content
    event_id, event_data = events[0]
    assert event_data["name"] == "credit_card_added"
    assert (
        json.loads(event_data["event_properties"]) == event_payload["event_properties"]
    )


def test_stream_integration_with_user_manager(redis_stream, redis_user):
    """
    Test if the Redis stream integration correctly processes events and updates user data.
    """
    # Arrange
    user_manager = RedisUserManager()
    event_payload = {
        "name": "scam_message_flagged",
        "event_properties": {
            "user_id": "12345",
        },
    }

    # Add the event to the Redis stream
    redis_stream.xadd(
        EVENT_STREAM_KEY,
        {
            "name": event_payload["name"],
            "event_properties": json.dumps(event_payload["event_properties"]),
        },
    )

    # Simulate processing the event by the consumer
    event = redis_stream.xrange(EVENT_STREAM_KEY)[0]  # Retrieve the first event
    event_id, event_data = event

    # Convert the event_data into an Event-compatible structure
    event_data["event_properties"] = json.loads(
        event_data["event_properties"]
    )  # Deserialize event_properties

    # Process the event
    user_id = event_data["event_properties"]["user_id"]
    try:
        user_data = user_manager.get_user(user_id)
    except KeyError:
        user_data = user_manager.create_user(user_id)

    # Simulate flagging the scam message
    user_data.scam_message_flags += 1
    user_manager.save_user(user_data)

    # Assert the user data was updated
    updated_user_data = user_manager.get_user(user_id)
    assert updated_user_data.scam_message_flags == 1


def test_event_publishing_and_consuming(
    redis_stream, redis_user, stream_consumer_subprocess
):
    """
    Test the integration between EventPublisher and RedisStreamConsumer.
    """
    # Arrange
    publisher = EventPublisher()  # Uses redis_stream via EventPublisher
    user_manager = RedisUserManager()
    event_payload = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "12345",
            "card_id": "card_001",
            "zip_code": "54321",
        },
    }

    # Act: Publish the event using EventPublisher
    publisher.add_event_to_stream(event_payload)

    # Allow time for the consumer to process
    time.sleep(2)  # Adjust timing based on system speed

    # Assert: Verify the user data was updated by RedisStreamConsumer
    user_id = event_payload["event_properties"]["user_id"]
    user_data = user_manager.get_user(user_id)

    assert user_data.total_credit_cards == 1
    assert user_data.credit_cards["card_001"] == "54321"
    assert "54321" in user_data.unique_zip_codes
