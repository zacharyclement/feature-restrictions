import logging
import time

import pytest
from fastapi.testclient import TestClient

from app import app, event_queue, user_manager


@pytest.fixture
def test_client():
    """
    Fixture for the FastAPI test client.
    """
    return TestClient(app)


def test_event_post_endpoint_processing(test_client, caplog):
    with caplog.at_level(logging.INFO):
        # Arrange
        event_payload = {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": "1",
                "card_id": "card_123",
                "zip_code": "12345",
            },
        }

        # Act: Send a POST request to the /event endpoint
        response = test_client.post("/event", json=event_payload)
        print("response: ", response.json())

        # Assert: Verify the response
        assert response.status_code == 200
        assert response.json() == {"status": "Event enqueued for processing."}

        # Wait for the EventConsumer to process the event
        # event_queue.join()
        print("Start")
        time.sleep(1)
        print("End")

        # Assert: Verify that the event was processed correctly
        user_data = user_manager.get_user("1")
        assert user_data.total_credit_cards == 1
        assert user_data.credit_cards["card_123"] == "12345"
        assert "12345" in user_data.unique_zip_codes
        assert user_data.access_flags["can_purchase"] is True
