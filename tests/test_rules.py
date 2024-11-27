def test_scam_message_rule_trigger():
    # Arrange
    user_id = "user_test_8"
    event_data = {
        "name": "scam_message_flagged",
        "event_properties": {"user_id": user_id},
    }

    # Act
    # First scam message flagged
    response1 = client.post("/event", json=event_data)
    # Second scam message flagged - should trigger the rule
    response2 = client.post("/event", json=event_data)

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    user_data = user_store.get_user(user_id)
    assert user_data.scam_message_flags == 2
    assert user_data.access_flags["can_message"] == False


def test_unique_zip_code_rule_trigger():
    # Arrange
    user_id = "user_test_9"
    zip_codes = ["11111", "22222", "33333", "44444"]
    for i, zip_code in enumerate(zip_codes):
        event_data = {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": user_id,
                "card_id": f"card_{i}",
                "zip_code": zip_code,
            },
        }
        # Act
        response = client.post("/event", json=event_data)
        assert response.status_code == 200

    # Assert
    user_data = user_store.get_user(user_id)
    # Should have 4 credit cards with 4 unique zip codes
    assert user_data.total_credit_cards == 4
    assert len(user_data.unique_zip_codes) == 4
    # The ratio of unique zip codes to total credit cards is 1.0 (>0.75)
    assert user_data.access_flags["can_purchase"] == False
