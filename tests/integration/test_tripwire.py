import pytest
from fastapi.testclient import TestClient

from app import app
from feature_restriction.user_manager import UserManager


def test_tripwire_disables_rule(
    client, consumer_with_queue, reset_user_manager, reset_tripwire_manager
):
    """
    Test that a tripwire disables a rule when too many users are affected within the time window.
    """
    tripwire_manager = reset_tripwire_manager
    user_manager = reset_user_manager

    # Simulate total users in the system
    total_users = 10

    # Arrange: Add 100 users
    for i in range(total_users):
        user_id = str(i + 1)
        user_manager.get_user(user_id)

    # Simulate multiple users triggering the rule
    for i in range(6):  # 6 users = 6% of total users, exceeding the 5% threshold
        user_id = str(i + 1)
        event_payload = {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": user_id,
                "card_id": f"card_{i}",
                "zip_code": f"{10000 + i}",
            },
        }
        client.post("/event", json=event_payload)

    # Wait for the consumer to process events
    consumer_with_queue.event_queue.join()

    # Assert: Verify the tripwire disables the rule
    assert (
        tripwire_manager.is_rule_disabled_via_tripwire("unique_zip_code_rule") is True
    )


def test_tripwire_disables_and_clears(
    client, consumer_with_queue, reset_user_manager, reset_tripwire_manager
):
    """
    Test that a rule is re-enabled after the tripwire state is cleared.
    """
    tripwire_manager = reset_tripwire_manager
    user_manager = reset_user_manager

    # Simulate total users in the system
    total_users = 10

    # Arrange: Add 100 users
    for i in range(total_users):
        user_id = str(i + 1)
        user_manager.get_user(user_id)

    # Simulate multiple users triggering the rule
    for i in range(6):  # 6 users = 6% of total users, exceeding the 5% threshold
        user_id = str(i + 1)
        event_payload = {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": user_id,
                "card_id": f"card_{i}",
                "zip_code": f"{10000 + i}",
            },
        }
        client.post("/event", json=event_payload)

    # Wait for the consumer to process events
    consumer_with_queue.event_queue.join()

    # Verify the rule is initially disabled
    assert (
        tripwire_manager.is_rule_disabled_via_tripwire("unique_zip_code_rule") is True
    )

    # Act: Clear the tripwire state
    tripwire_manager.clear_rules()

    # Assert: Verify the rule is re-enabled
    assert (
        tripwire_manager.is_rule_disabled_via_tripwire("unique_zip_code_rule") is False
    )
