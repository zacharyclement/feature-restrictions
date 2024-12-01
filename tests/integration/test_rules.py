import time

from feature_restriction.redis_user_manager import RedisUserManager


def test_unique_zip_code_rule(
    redis_user, redis_stream, test_client, stream_consumer_subprocess, redis_tripwire
):
    """
    Test if the UniqueZipCodeRule disables 'can_purchase' when the threshold is exceeded.
    """
    # Arrange
    user_id = "user_123"
    user_manager = RedisUserManager()

    # Add an initial credit card
    event_payload_1 = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": user_id,
            "card_id": "card_001",
            "zip_code": "12345",
        },
    }
    test_client.post("/event", json=event_payload_1)

    # Add a second credit card with a unique zip code to trigger the rule
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

    # Assert
    updated_user_data = user_manager.get_user(user_id)
    assert updated_user_data.access_flags["can_purchase"] is False


def test_scam_message_rule(
    redis_user, redis_stream, test_client, stream_consumer_subprocess, redis_tripwire
):
    """
    Test if the ScamMessageRule disables 'can_message' after the scam message flag threshold is reached.
    """
    # Arrange
    user_id = "user_456"
    user_manager = RedisUserManager()

    # Flag the first scam message
    event_payload_1 = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_id},
    }
    test_client.post("/event", json=event_payload_1)

    # Flag the second scam message to trigger the rule
    event_payload_2 = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_id},
    }
    test_client.post("/event", json=event_payload_2)

    # Allow time for the consumer to process
    time.sleep(1)

    # Assert
    updated_user_data = user_manager.get_user(user_id)
    assert updated_user_data.access_flags["can_message"] is False


def test_chargeback_ratio_rule(
    redis_user, redis_stream, test_client, stream_consumer_subprocess, redis_tripwire
):
    """
    Test if the ChargebackRatioRule disables 'can_purchase' when the chargeback-to-spend ratio exceeds the limit.
    """
    # Arrange
    user_id = "user_789"
    user_manager = RedisUserManager()

    # Add a purchase event to set the spend amount
    purchase_event = {
        "name": "purchase_made",
        "event_properties": {"user_id": user_id, "amount": 100.00},
    }
    test_client.post("/event", json=purchase_event)

    # Add a chargeback event to exceed the chargeback ratio threshold
    chargeback_event = {
        "name": "chargeback_occurred",
        "event_properties": {"user_id": user_id, "amount": 15.00},
    }
    test_client.post("/event", json=chargeback_event)

    # Allow time for the consumer to process
    time.sleep(1)

    # Assert
    updated_user_data = user_manager.get_user(user_id)
    assert updated_user_data.access_flags["can_purchase"] is False
