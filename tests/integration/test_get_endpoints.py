import json
import time

import pytest

from feature_restriction.config import EVENT_STREAM_KEY
from feature_restriction.models import Event
from feature_restriction.publisher import EventPublisher
from feature_restriction.redis_user_manager import RedisUserManager


def test_can_purchase_enabled(redis_user, redis_stream, test_client):
    """
    Test the /canpurchase endpoint when the user is allowed to make purchases.
    """
    # Arrange
    user_id = "user_123"
    user_manager = RedisUserManager()
    user_data = user_manager.create_user(user_id)

    # Act: Query the /canpurchase endpoint
    response = test_client.get("/canpurchase", params={"user_id": user_id})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_purchase": True}


def test_can_message_enabled(redis_user, redis_stream, test_client):
    """
    Test the /canmessage endpoint when the user is allowed to send/receive messages.
    """
    # Arrange
    user_id = "user_789"
    user_manager = RedisUserManager()
    user_data = user_manager.create_user(user_id)

    # Act: Query the /canmessage endpoint
    response = test_client.get("/canmessage", params={"user_id": user_id})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_message": True}


def test_can_purchase_disabled(
    redis_user, redis_stream, test_client, stream_consumer_subprocess
):
    """
    Test the /canpurchase endpoint when the user is restricted from making purchases.
    """
    # Arrange
    user_id = "user_456"
    user_manager = RedisUserManager()
    user_data = user_manager.create_user(user_id)

    # Trigger a rule to disable purchase
    event_payload = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": user_id,
            "card_id": "card_001",
            "zip_code": "12345",
        },
    }
    test_client.post("/event", json=event_payload)

    # Add another unique zip code to trigger the rule
    event_payload_2 = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": user_id,
            "card_id": "card_002",
            "zip_code": "54321",
        },
    }
    test_client.post("/event", json=event_payload_2)

    # Allow time for the consumer to process
    time.sleep(1)

    # Act: Query the /canpurchase endpoint
    response = test_client.get("/canpurchase", params={"user_id": user_id})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_purchase": False}


def test_can_message_disabled(
    redis_user, redis_stream, test_client, stream_consumer_subprocess
):
    """
    Test the /canmessage endpoint when the user is restricted from sending/receiving messages.
    """
    # Arrange
    user_id = "user_101"
    user_manager = RedisUserManager()

    # Trigger the ScamMessageRule
    event_payload = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_id},
    }
    test_client.post("/event", json=event_payload)

    # Add another scam message to trigger the rule
    event_payload_2 = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_id},
    }
    test_client.post("/event", json=event_payload_2)

    # Allow time for the consumer to process
    time.sleep(1)

    # Act: Query the /canmessage endpoint
    response = test_client.get("/canmessage", params={"user_id": user_id})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_message": False}
