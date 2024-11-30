import json
import logging
import time

import redis

from feature_restriction.config import (
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.models import Event
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.registry import EventHandlerRegistry
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.utils import logger


class RedisStreamConsumer:
    """
    Reads and processes events from a Redis stream.
    """

    def __init__(
        self,
        redis_client,
        stream_key="event_stream",
        consumer_group="group1",
        consumer_name="consumer1",
    ):
        """
        Initialize the RedisStreamConsumer.
        """
        self.redis_client = redis_client
        self.stream_key = stream_key
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name

        # Ensure the consumer group exists
        try:
            self.redis_client.xgroup_create(
                self.stream_key, self.consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError:
            logger.info(f"Consumer group '{self.consumer_group}' already exists.")

        self.redis_user_manager = RedisUserManager()

        # Use the EventHandlerRegistry for managing handlers
        self.event_handler_registry = EventHandlerRegistry()
        self.event_handler_registry.register_default_event_handlers(
            tripwire_manager=TripWireManager(),
            redis_user_manager=self.redis_user_manager,
        )

    def process_event(self, event_id, event_data):
        """
        Process an individual event from the stream.
        """
        try:
            # Deserialize event_properties in place
            event_data["event_properties"] = json.loads(
                event_data["event_properties"]
            )  # Deserialize event_properties

            # Ensure user_id is treated as a string
            event_data["event_properties"]["user_id"] = str(
                event_data["event_properties"]["user_id"]
            )

            # Create an Event object from the updated data
            event = Event(**event_data)

            user_id = str(event.event_properties["user_id"])
            try:
                user_data = self.redis_user_manager.get_user(user_id)
            except KeyError:
                user_data = self.redis_user_manager.create_user(user_id)
            logger.info(
                f"User data before processing: {self.redis_user_manager.display_user_data(user_id, user_data)}"
            )

            # Find the appropriate handler for the event
            handler = self.event_handler_registry.get_event_handler(event.name)
            if not handler:
                logger.error(f"No handler registered for event: {event.name}")
                return

            # Handle the event
            handler.handle(event, user_data)
            logger.info(
                f"User data after processing: {self.redis_user_manager.display_user_data(user_id, user_data)}"
            )

            logger.info(f"Processed event '{event.name}' with ID '{event_id}'.")
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode event properties for event '{event_id}': {e}"
            )
        except Exception as e:
            logger.error(f"Error processing event '{event_id}': {e}")

    def start(self):
        """
        Start consuming events from the Redis stream.
        """
        logger.info(f"Starting Redis Stream Consumer on stream: {self.stream_key}")
        while True:
            try:
                events = self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_key: ">"},
                    count=10,
                    block=5000,
                )
                for stream, event_list in events:
                    for event_id, event_data in event_list:
                        self.process_event(event_id, event_data)

                        # Acknowledge the event
                        self.redis_client.xack(
                            self.stream_key, self.consumer_group, event_id
                        )
            except Exception as e:
                logger.error(f"Error consuming events: {e}")


if __name__ == "__main__":
    """
    Script entry point for running the RedisStreamConsumer.
    """
    redis_client = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STREAM, decode_responses=True
    )
    stream_key = EVENT_STREAM_KEY
    consumer_group = "group1"
    consumer_name = "consumer1"

    while True:
        try:
            consumer = RedisStreamConsumer(
                redis_client, stream_key, consumer_group, consumer_name
            )
            consumer.start()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Shutting down Redis Stream Consumer.")
            break
