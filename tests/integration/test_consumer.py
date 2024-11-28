import time
from queue import Queue
from threading import Thread


def test_event_processing_with_consumer(
    client, reset_user_manager, reset_tripwire_manager
):
    """
    Test the consumer processes events correctly.
    """
    # Create a new queue for the test
    event_queue = Queue()

    # Initialize the consumer
    from feature_restriction.event_consumer import (
        EventConsumer,  # Import your consumer class
    )

    consumer = EventConsumer(event_queue, reset_user_manager, reset_tripwire_manager)

    # Start the consumer in a separate thread
    consumer_thread = Thread(target=consumer.consume_events, daemon=True)
    consumer_thread.start()

    try:
        # Arrange: Post an event to the endpoint
        event_payload = {
            "name": "credit_card_added",
            "event_properties": {
                "user_id": 1,
                "card_id": "card_123",
                "zip_code": "12345",
            },
        }
        response = client.post("/event", json=event_payload)

        # Assert: Verify the response
        assert response.status_code == 200
        assert response.json() == {"status": "Event enqueued for processing."}

        # Wait briefly to allow the consumer to process
        time.sleep(1)

        # Check the user state to verify the event was processed
        user_data = reset_user_manager.get_user("1")
        assert user_data.total_credit_cards == 1
        assert "card_123" in user_data.credit_cards

    finally:
        # Stop the consumer
        consumer.stop()
        consumer_thread.join()
