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

            # Validate event fields
            if not event.name or not event.event_properties:
                raise ValueError("Event is missing required fields")

            # Convert the Pydantic model to a dict and serialize event_properties
            event_data = event.dict()
            event_data["event_properties"] = json.dumps(event_data["event_properties"])

            # Add the event to the Redis stream
            self.redis_client.xadd(EVENT_STREAM_KEY, event_data)

            logger.info(f"Added event to Redis stream: {event_data}")
            return {"status": f"Event '{event.name}' added to the stream."}
        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise HTTPException(status_code=400, detail=f"Validation error: {ve}")
        except Exception as e:
            logger.error(f"Failed to add event to Redis stream: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to add event to the stream"
            )
