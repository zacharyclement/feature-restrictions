import pytest
from fastapi.testclient import TestClient
from main import UserData, app, users

client = TestClient(app)


def test_rule1_scam_message_flag():
    user_id = "test_user1"
    users[user_id] = UserData(user_id)

    # First scam message
    response = client.post(
        "/event",
        json={"name": "scam_message_flagged", "event_properties": {"user_id": user_id}},
    )
    assert response.status_code == 200
    assert users[user_id].access_flags["can_message"] == True

    # Second scam message
    response = client.post(
        "/event",
        json={"name": "scam_message_flagged", "event_properties": {"user_id": user_id}},
    )
    assert response.status_code == 200
    assert users[user_id].access_flags["can_message"] == False


def test_rule2_credit_card_zip_codes():
    user_id = "test_user2"
    users[user_id] = UserData(user_id)

    # Add credit cards
    cards = [
        {"card_id": "card1", "zip_code": "10001"},
        {"card_id": "card2", "zip_code": "10002"},
        {"card_id": "card3", "zip_code": "10003"},
        {"card_id": "card4", "zip_code": "10004"},
    ]
    for card in cards:
        response = client.post(
            "/event",
            json={
                "name": "credit_card_added",
                "event_properties": {"user_id": user_id, **card},
            },
        )
        assert response.status_code == 200

    # Should have 100% unique zip codes
    assert users[user_id].access_flags["can_purchase"] == False


def test_rule3_chargeback_ratio():
    user_id = "test_user3"
    users[user_id] = UserData(user_id)

    # Make purchases
    purchases = [100, 200]
    for amount in purchases:
        response = client.post(
            "/event",
            json={
                "name": "purchase_made",
                "event_properties": {"user_id": user_id, "amount": amount},
            },
        )
        assert response.status_code == 200

    # Apply chargebacks
    chargebacks = [10, 15]  # Total chargebacks = $25
    for amount in chargebacks:
        response = client.post(
            "/event",
            json={
                "name": "chargeback_occurred",
                "event_properties": {"user_id": user_id, "amount": amount},
            },
        )
        assert response.status_code == 200

    # Total spend = $300, total chargebacks = $25, ratio ~8%
    assert users[user_id].access_flags["can_purchase"] == True

    # Add another chargeback to exceed 10%
    response = client.post(
        "/event",
        json={
            "name": "chargeback_occurred",
            "event_properties": {"user_id": user_id, "amount": 10},
        },
    )
    assert response.status_code == 200

    # Now, total chargebacks = $35, ratio ~11.6%
    assert users[user_id].access_flags["can_purchase"] == False
