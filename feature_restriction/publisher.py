import json

import redis
from fastapi import HTTPException

from feature_restriction.config import (
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.models import Event
from feature_restriction.utils import logger


class EventPublisher:
    """
    Handles adding events to a Redis stream.
    """

    def __init__(self):
        """
        Initialize the EventStreamHandler with Redis connection details.

        :param redis_host: Redis server hostname.
        :param redis_port: Redis server port.
        :param stream_key: Redis stream key for storing events.
        """
        self.redis_client = redis.StrictRedis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STREAM, decode_responses=True
        )

    def add_event_to_stream(self, event: Event) -> dict:
        """
        Add an event to the Redis stream.

        :param event: An Event object to be added to the stream.
        :return: A success message if the event was added successfully.
        :raises HTTPException: If the event could not be added to the stream.
        """
        try:
            logger.info(f"Received event: {event}")

            # Convert the Pydantic model to a dict and serialize event_properties
            event_data = event.dict()
            event_data["event_properties"] = json.dumps(event_data["event_properties"])

            # Add the event to the Redis stream
            self.redis_client.xadd(EVENT_STREAM_KEY, event_data)

            logger.info(f"Added event to Redis stream: {event_data}")
            return {"status": "Event added to the stream."}
        except Exception as e:
            logger.error(f"Failed to add event to Redis stream: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to add event to the stream"
            )
