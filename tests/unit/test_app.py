import json

import pytest
from fastapi.testclient import TestClient

from app import app, tripwire_manager, user_manager
from feature_restriction.models import Event

client = TestClient(app)


@pytest.fixture(autouse=True)
def run_before_each_test():
    # Clear user store and tripwire state before each test
    user_manager.users.clear()
    tripwire_manager.clear_rules()


def test_handle_valid_event():
    # Arrange
    event_data = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "user_test_1",
            "card_id": "card_123",
            "zip_code": "12345",
        },
    }

    # Act
    response = client.post("/event", json=event_data)

    # Assert
    assert response.status_code == 200
    user_data = user_manager.get_user("user_test_1")
    assert user_data.total_credit_cards == 1
    assert "card_123" in user_data.credit_cards
    assert user_data.credit_cards["card_123"] == "12345"
    assert "12345" in user_data.unique_zip_codes


def test_handle_event_missing_user_id():
    # Arrange
    event_data = {
        "name": "credit_card_added",
        "event_properties": {"card_id": "card_123", "zip_code": "12345"},
    }

    # Act
    response = client.post("/event", json=event_data)

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "'user_id' is required in event properties."}


def test_handle_unregistered_event():
    # Arrange
    event_data = {
        "name": "unknown_event",
        "event_properties": {"user_id": "user_test_2", "some_property": "value"},
    }

    # Act
    response = client.post("/event", json=event_data)

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "No handler registered for event: unknown_event"
    }


def test_handle_event_processing_error():
    # Arrange
    event_data = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "user_test_3",
            "zip_code": "12345",  # Missing 'card_id'
        },
    }

    # Act
    response = client.post("/event", json=event_data)

    # Assert
    assert response.status_code == 500
    assert "An error occurred while processing the event" in response.json()["detail"]


def test_can_message_true():
    # Arrange
    user_id = "user_test_4"
    # Create user and ensure 'can_message' is True
    user_data = user_manager.get_user(user_id)
    user_data.access_flags["can_message"] = True

    # Act
    response = client.get(f"/canmessage?user_id={user_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_message": True}


def test_can_message_false():
    # Arrange
    user_id = "user_test_5"
    # Create user and set 'can_message' to False
    user_data = user_manager.get_user(user_id)
    user_data.access_flags["can_message"] = False

    # Act
    response = client.get(f"/canmessage?user_id={user_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_message": False}


def test_can_message_nonexistent_user():
    # Arrange
    user_id = "nonexistent_user"
    # Ensure the user does not exist
    if user_id in user_manager.users:
        del user_manager.users[user_id]

    # Act
    response = client.get(f"/canmessage?user_id={user_id}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": f"User with ID '{user_id}' not found."}


def test_can_purchase_true():
    # Arrange
    user_id = "user_test_6"
    user_data = user_manager.get_user(user_id)
    user_data.access_flags["can_purchase"] = True

    # Act
    response = client.get(f"/canpurchase?user_id={user_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_purchase": True}


def test_can_purchase_false():
    # Arrange
    user_id = "user_test_7"
    user_data = user_manager.get_user(user_id)
    user_data.access_flags["can_purchase"] = False

    # Act
    response = client.get(f"/canpurchase?user_id={user_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"can_purchase": False}


def test_can_purchase_nonexistent_user():
    # Arrange
    user_id = "nonexistent_user_purchase"
    if user_id in user_manager.users:
        del user_manager.users[user_id]

    # Act
    response = client.get(f"/canpurchase?user_id={user_id}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": f"User with ID '{user_id}' not found."}
