from unittest.mock import MagicMock, patch

from feature_restriction.models import Event
from stream_consumer import RedisStreamConsumer


def test_initialize_consumer_group(mock_redis):
    """
    Test that the consumer group is created if it doesn't already exist.
    """
    RedisStreamConsumer(
        redis_client=mock_redis,
        stream_key="test_event_stream",
        consumer_group="test_group",
        consumer_name="test_consumer",
    )
    mock_redis.xgroup_create.assert_called_once_with(
        "test_event_stream", "test_group", id="0", mkstream=True
    )


from unittest.mock import call, patch


def test_process_event_with_registered_handler(
    stream_consumer, user_manager, sample_user_data
):
    """
    Test processing an event with a registered handler.
    """
    # Mock the event handler
    mock_handler = MagicMock()
    stream_consumer.event_handler_registry.get_event_handler = MagicMock(
        return_value=mock_handler
    )

    # Mock user retrieval
    with patch.object(
        user_manager, "get_user", return_value=sample_user_data
    ) as mock_get_user:
        # Mock user saving
        with patch.object(user_manager, "save_user") as mock_save_user:
            # Event data to be processed
            event_data = {
                "name": "credit_card_added",
                "event_properties": '{"user_id": "test_user", "card_id": "card_001", "zip_code": "12345"}',
            }

            # Call the process_event method
            stream_consumer.process_event("event_id_1", event_data)

            # Verify handler was invoked
            mock_handler.handle.assert_called_once_with(
                Event(
                    name="credit_card_added",
                    event_properties={
                        "user_id": "test_user",
                        "card_id": "card_001",
                        "zip_code": "12345",
                    },
                ),
                sample_user_data,
            )

            # Verify user retrieval calls
            assert mock_get_user.call_count == 3
            mock_get_user.assert_has_calls(
                [call("test_user"), call("test_user"), call("test_user")]
            )


def test_process_event_creates_user_if_not_found(
    stream_consumer, user_manager, sample_user_data
):
    """
    Test processing an event creates a user if not found.
    """
    # Simulate KeyError for the get_user method
    with patch.object(user_manager, "get_user", side_effect=KeyError):
        # Mock create_user to return sample_user_data
        with patch.object(user_manager, "create_user", return_value=sample_user_data):
            event_data = {
                "name": "credit_card_added",
                "event_properties": '{"user_id": "test_user", "card_id": "card_001", "zip_code": "12345"}',
            }

            stream_consumer.process_event("event_id_1", event_data)

            # Assert user creation and saving
            user_manager.create_user.assert_called_once_with("test_user")


def test_start_reads_and_processes_events(stream_consumer, mock_redis):
    mock_redis.xreadgroup.return_value = [
        ("test_event_stream", [("event_id_1", {"name": "test_event"})])
    ]

    stream_consumer.process_event = MagicMock()

    def mock_start():
        events = mock_redis.xreadgroup(
            groupname="test_group",
            consumername="test_consumer",
            streams={"test_event_stream": ">"},
            count=10,
            block=1000,
        )
        for _, event_list in events:
            for event_id, event_data in event_list:
                stream_consumer.process_event(event_id, event_data)

    with patch("stream_consumer.RedisStreamConsumer.start", side_effect=mock_start):
        stream_consumer.start()

    # Assertions
    mock_redis.xreadgroup.assert_called_once()
    stream_consumer.process_event.assert_called_once_with(
        "event_id_1", {"name": "test_event"}
    )
