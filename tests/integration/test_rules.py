def test_trigger_unique_zip_code_rule(client, reset_user_manager):
    """
    Test the unique zip code rule is triggered correctly.
    """
    user_manager = reset_user_manager

    # Arrange: Create a user with multiple credit cards
    event_payload = {
        "name": "credit_card_added",
        "event_properties": {
            "user_id": "1",
            "card_id": "card_123",
            "zip_code": "12345",
        },
    }
    client.post("/event", json=event_payload)
    event_payload["event_properties"]["card_id"] = "card_456"
    event_payload["event_properties"]["zip_code"] = "67890"
    client.post("/event", json=event_payload)

    # Act: Add another card to trigger the rule
    event_payload["event_properties"]["card_id"] = "card_789"
    event_payload["event_properties"]["zip_code"] = "54321"
    client.post("/event", json=event_payload)

    # Assert: Verify the user cannot purchase
    response = client.get("/canpurchase", params={"user_id": "1"})
    assert response.json() == {"can_purchase": False}


def test_trigger_scam_message_rule(client, reset_user_manager):
    """
    Test the scam message rule is triggered correctly.
    """
    user_manager = reset_user_manager

    # Arrange: Create a user and simulate flagged messages
    event_payload = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": "1"},
    }
    client.post("/event", json=event_payload)
    client.post("/event", json=event_payload)

    # Assert: Verify the user cannot message
    response = client.get("/canmessage", params={"user_id": "1"})
    assert response.json() == {"can_message": False}


def test_trigger_chargeback_rule(client, reset_user_manager):
    """
    Test the chargeback ratio rule is triggered correctly.
    """
    user_manager = reset_user_manager

    # Arrange: Simulate purchases and chargebacks for a user
    event_payload_purchase = {
        "name": "purchase_made",
        "event_properties": {"user_id": "1", "amount": 100},
    }
    event_payload_chargeback = {
        "name": "chargeback_occurred",
        "event_properties": {"user_id": "1", "amount": 20},
    }
    client.post("/event", json=event_payload_purchase)
    client.post("/event", json=event_payload_chargeback)
    client.post("/event", json=event_payload_chargeback)

    # Assert: Verify the user cannot purchase
    response = client.get("/canpurchase", params={"user_id": "1"})
    assert response.json() == {"can_purchase": False}
