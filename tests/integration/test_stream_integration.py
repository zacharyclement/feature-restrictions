import json

import pytest

from feature_restriction.config import EVENT_STREAM_KEY
from feature_restriction.redis_user_manager import RedisUserManager


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
