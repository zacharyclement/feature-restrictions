import json

from feature_restriction.config import EVENT_STREAM_KEY


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
