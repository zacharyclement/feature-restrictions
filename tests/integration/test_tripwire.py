import time

from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.tripwire_manager import TripWireManager


def test_tripwire_disables_rule_when_threshold_exceeded(redis_tripwire):
    """
    Test that a rule is disabled via the tripwire when the affected user percentage exceeds the threshold.
    """
    # Arrange
    tripwire_manager = TripWireManager(redis_tripwire)
    total_users = 100  # Total users in the system
    rule_name = "scam_message_rule"

    # Act: Add affected users just below the threshold
    for i in range(4):  # 4% of 100 users
        tripwire_manager.apply_tripwire_if_needed(rule_name, f"user_{i}", total_users)

    # Assert: Rule is not disabled yet
    assert not tripwire_manager.is_rule_disabled_via_tripwire(rule_name)

    # Act: Add one more user to exceed the threshold
    tripwire_manager.apply_tripwire_if_needed(rule_name, "user_5", total_users)

    # Assert: Rule is now disabled
    assert tripwire_manager.is_rule_disabled_via_tripwire(rule_name)

    # Assert: Verify Redis storage
    assert redis_tripwire.hget("tripwire:states", rule_name) == "1"
    affected_users = redis_tripwire.hgetall(f"tripwire:affected_users:{rule_name}")
    assert len(affected_users) == 5


def test_tripwire_removes_expired_users(redis_tripwire):
    """
    Test that expired affected users are removed from the tripwire's affected user list.
    """
    # Arrange
    tripwire_manager = TripWireManager(redis_tripwire)
    rule_name = "unique_zip_code_rule"
    total_users = 100
    current_time = time.time()

    # Add affected users with timestamps
    redis_tripwire.hset(
        f"tripwire:affected_users:{rule_name}",
        mapping={
            "user_1": str(current_time - 400),  # Expired (400 seconds ago, window=300)
            "user_2": str(current_time - 200),  # Valid
        },
    )

    # Act: Apply tripwire logic
    tripwire_manager.apply_tripwire_if_needed(rule_name, "user_3", total_users)

    # Assert: Verify expired user is removed
    affected_users = redis_tripwire.hgetall(f"tripwire:affected_users:{rule_name}")
    assert "user_1" not in affected_users
    assert "user_2" in affected_users
    assert "user_3" in affected_users


def test_tripwire_reactivates_rule_below_threshold(redis_tripwire):
    """
    Test that a disabled rule is re-enabled when the percentage of affected users drops below the threshold.
    """
    # Arrange
    tripwire_manager = TripWireManager(redis_tripwire)
    total_users = 100
    rule_name = "chargeback_ratio_rule"

    # Add affected users to exceed the threshold
    for i in range(6):  # 6% of 100 users
        tripwire_manager.apply_tripwire_if_needed(rule_name, f"user_{i}", total_users)

    # Assert: Rule is disabled
    assert tripwire_manager.is_rule_disabled_via_tripwire(rule_name)

    # Act: Remove some affected users to drop below the threshold
    redis_tripwire.hdel(f"tripwire:affected_users:{rule_name}", "user_0")
    redis_tripwire.hdel(f"tripwire:affected_users:{rule_name}", "user_1")
    redis_tripwire.hdel(f"tripwire:affected_users:{rule_name}", "user_2")
    redis_tripwire.hdel(f"tripwire:affected_users:{rule_name}", "user_3")
    tripwire_manager.apply_tripwire_if_needed(rule_name, "user_7", total_users)

    # Assert: Rule is re-enabled
    assert not tripwire_manager.is_rule_disabled_via_tripwire(rule_name)


def test_tripwire_and_rule_integration_stepwise(
    test_client, redis_stream, redis_user, redis_tripwire, stream_consumer_subprocess
):
    """
    Test the integration of rules, tripwire, and access flags via stepwise event posting.
    """
    # Simulate the TripWireManager in Redis
    tripwire_manager = TripWireManager(redis_tripwire)
    # Arrange
    user_1_id = "12345"
    user_2_id = "67890"
    total_users = 100  # Simulate total users in the system
    rule_name = "scam_message_rule"

    # Prepare event payloads
    event_payload_user_1 = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_1_id},
    }
    event_payload_user_2 = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_2_id},
    }

    # Act & Assert: First event for user_1
    response = test_client.post("/event", json=event_payload_user_1)
    assert response.status_code == 200
    expected_response = {
        "status": f"Event '{event_payload_user_1['name']}' added to the stream."
    }
    assert response.json() == expected_response

    time.sleep(0.5)  # Allow the consumer to process the event

    # Assert user_1's access after the first event
    user_manager = RedisUserManager(redis_user)
    user_1_data = user_manager.get_user(user_1_id)
    assert user_1_data.scam_message_flags == 1  # Only one event processed
    assert user_1_data.access_flags["can_message"]  # Rule not yet triggered

    # Act & Assert: Second event for user_1 (rule triggers here)
    response = test_client.post("/event", json=event_payload_user_1)
    assert response.status_code == 200
    expected_response = {
        "status": f"Event '{event_payload_user_1['name']}' added to the stream."
    }
    assert response.json() == expected_response

    time.sleep(0.5)  # Allow the consumer to process the event

    # Assert user_1's access after the second event
    user_1_data = user_manager.get_user(user_1_id)
    assert user_1_data.scam_message_flags == 2  # Rule threshold met
    assert not user_1_data.access_flags["can_message"]  # Rule disabled access

    # Act: Add enough users to trip the tripwire
    for i in range(int(total_users * 0.06)):  # 6% of total users
        tripwire_manager.apply_tripwire_if_needed(rule_name, f"user_{i}", total_users)

    # Assert: Validate tripwire state (rule is now disabled)
    assert tripwire_manager.is_rule_disabled_via_tripwire(rule_name)

    # Act & Assert: First event for user_2
    response = test_client.post("/event", json=event_payload_user_2)
    assert response.status_code == 200
    expected_response = {
        "status": f"Event '{event_payload_user_2['name']}' added to the stream."
    }
    assert response.json() == expected_response

    time.sleep(0.5)  # Allow the consumer to process the event

    # Assert user_2's access after the first event
    user_2_data = user_manager.get_user(user_2_id)
    assert user_2_data.scam_message_flags == 1  # Only one event processed
    assert user_2_data.access_flags["can_message"]  # Rule not triggered yet

    # Act & Assert: Second event for user_2 (rule would trigger but is disabled by tripwire)
    response = test_client.post("/event", json=event_payload_user_2)
    assert response.status_code == 200
    expected_response = {
        "status": f"Event '{event_payload_user_2['name']}' added to the stream."
    }
    assert response.json() == expected_response

    time.sleep(0.5)  # Allow the consumer to process the event

    # Assert user_2's access after the second event
    user_2_data = user_manager.get_user(user_2_id)
    assert user_2_data.scam_message_flags == 2  # Event count updates
    assert user_2_data.access_flags["can_message"]  # Access remains enabled

    # Assert: Check the `canmessage` endpoints for both users
    response = test_client.get(f"/canmessage?user_id={user_1_id}")
    assert response.status_code == 200
    assert response.json() == {"can_message": False}  # User_1's access remains disabled

    response = test_client.get(f"/canmessage?user_id={user_2_id}")
    assert response.status_code == 200
    assert response.json() == {"can_message": True}  # User_2's access remains enabled
