import pytest
from fastapi.testclient import TestClient

from app import app
from feature_restriction.rules import ScamMessageRule, UniqueZipCodeRule
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.user_manager import UserManager


def test_zip_code_rule(client, reset_user_manager):
    """
    Test the /canmessage endpoint.
    """
    # Arrange: Create a user and simulate an event that changes their state
    # user_manager = UserManager()
    # trip_wire_manager = TripWireManager()
    # user_ddata = user_manager.get_user("1")
    # user_data.scam_message_flags = 2  # Trigger the "scam_message_rule"
    # print("TEST, scam message flags: ", user_data.scam_message_flags)
    # Act: Check the /canmessage endpoint

    # ScamMessageRule(trip_wire_manager, user_manager).process_rule(user_data)
    # print("TEST, user data after processing: ", user_data.access_flags)

    event_payload_1 = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "1",
            "card_id": "card_123",
            "zip_code": "12345",
        },
    }

    response = client.post("/event", json=event_payload_1)

    event_payload_2 = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "1",
            "card_id": "card_456",
            "zip_code": "56789",
        },
    }

    response = client.post("/event", json=event_payload_2)
    print("TEST, response: ", response.json())

    # response = client.get("/canmessage", params={"user_id": "1"})

    # Assert: Verify the user cannot message
    # assert response.status_code == 200
    # assert response.json() == {"can_purchase": False}


# def test_event_endpoint(client, reset_user_manager):
#     """
#     Test posting an event to the /event endpoint.
#     """

#     # Define the event payload
#     event_payload = {
#         "name": "credit_card_added",
#         "event_properties": {"user_id": 1, "card_id": "card_123", "zip_code": "12345"},
#     }

#     # Act: Send the POST request
#     response = client.post("/event", json=event_payload)

#     # Assert: Check the response
#     assert response.status_code == 200
#     assert response.json() == {"status": "Event enqueued for processing."}

#     # Assert: Verify the user state
#     user_data = user_manager.get_user("1")
#     assert user_data.total_credit_cards == 1
#     assert "card_123" in user_data.credit_cards


# def test_can_purchase(client, reset_user_manager):
#     """
#     Test the /canpurchase endpoint.
#     """
#     # Arrange: Create a user and simulate adding credit cards
#     user_manager = reset_user_manager
#     user_data = user_manager.get_user("1")
#     user_data.credit_cards = {"card_123": "12345", "card_456": "67890"}
#     user_data.total_credit_cards = 2
#     user_data.unique_zip_codes = {"12345", "67890"}

#     # Act: Check the /canpurchase endpoint
#     response = client.get("/canpurchase", params={"user_id": "1"})

#     # Assert: Verify the user can still purchase
#     assert response.status_code == 200
#     assert response.json() == {"can_purchase": True}
