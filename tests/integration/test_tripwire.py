import time

from feature_restriction.redis_user_manager import RedisUserManager


def test_tripwire_not_triggered_below_threshold(
    redis_user, redis_stream, test_client, stream_consumer_subprocess
):
    """
    Test that the tripwire does not disable rules when the affected user percentage is below the threshold.
    """
    # Arrange
    user_manager = RedisUserManager()
    num_users = 5  # Below the threshold (e.g., threshold = 5%)
    users = [f"user_{i}" for i in range(1, num_users + 1)]

    for user_id in users:

        # Send events that would trigger the rule but stay below the threshold
        event_payload = {
            "name": "scam_message_flagged",
            "event_properties": {"user_id": user_id},
        }
        test_client.post("/event", json=event_payload)

    # Allow time for the consumer to process
    time.sleep(2)

    # Assert
    for user_id in users:
        user_data = user_manager.get_user(user_id)
        print("user_data.scam_message_flags", user_data.scam_message_flags)
        assert user_data.scam_message_flags == 1  # Rule applied
    assert (
        "scam_message_rule" not in user_manager.tripwire_manager.tripwire_disabled_rules
    )
