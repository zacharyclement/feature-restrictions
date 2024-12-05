import json
import logging
import threading
import time

import redis

from feature_restriction.config import (
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.models import Event
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.registry import EventHandlerRegistry, RuleRegistry
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.utils import logger


class RedisStreamConsumer:
    def __init__(
        self,
        redis_client,
        user_manager,
        tripwire_manager,
        rule_registry,
        event_registry,
    ):
        self.redis_client_stream = redis_client
        self.stream_key = EVENT_STREAM_KEY
        self.consumer_group = "group1"
        self.consumer_name = "consumer1"

        # Ensure the consumer group exists
        try:
            self.redis_client_stream.xgroup_create(
                self.stream_key, self.consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError:
            logger.info(f"Consumer group '{self.consumer_group}' already exists.")

        # Initialize user manager, tripwire manager, and registries
        self.user_manager = user_manager
        self.tripwire_manager = tripwire_manager
        self.rule_registry = rule_registry
        self.event_registry = event_registry

        # Register defaults
        self.rule_registry.register_default_rules(
            self.tripwire_manager, self.user_manager
        )
        self.event_registry.register_default_event_handlers(
            self.tripwire_manager, self.user_manager
        )

    def process_event(self, event_id, event_data):
        try:
            logger.info(f"Processing event: {event_data.get('name')}")
            event_data["event_properties"] = json.loads(event_data["event_properties"])
            event = Event(**event_data)

            user_id = event.event_properties["user_id"]
            try:
                user_data = self.user_manager.get_user(user_id)
            except KeyError:
                user_data = self.user_manager.create_user(user_id)

            logger.info(
                f"display user data before handler: {self.user_manager.display_user_data(user_id)}"
            )
            handler = self.event_registry.get_event_handler(event.name)
            if handler:
                handler.handle(event, user_data)

            logger.info(
                f"display user data after handler: {self.user_manager.display_user_data(user_id)}"
            )

            rule_names = self.event_registry.get_rules_for_event(event.name)
            for rule_name in rule_names:
                rule = self.rule_registry.get_rule(rule_name)
                if rule:
                    rule.process_rule(user_data)

            logger.info(
                f"display user data after rule: {self.user_manager.display_user_data(user_id)}"
            )
            logger.info(f"Event '{event.name}' processed successfully.")

        except Exception as e:
            logger.error(f"Error processing event '{event_id}': {e}")

    def start(self):
        logger.info(f"Starting Redis Stream Consumer on stream: {self.stream_key}")
        while True:
            try:
                events = self.redis_client_stream.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_key: ">"},
                    count=10,
                    block=1000,
                )
                for stream, event_list in events:
                    for event_id, event_data in event_list:
                        self.process_event(event_id, event_data)
                        self.redis_client_stream.xack(
                            self.stream_key, self.consumer_group, event_id
                        )
            except Exception as e:
                logger.error(f"Error consuming events: {e}")

    def stop(self):
        """
        Signal the consumer to stop and perform cleanup.
        """
        logger.info("Stopping Redis Stream Consumer...")
        self._stop_event.set()


if __name__ == "__main__":
    """
    Script entry point for running the RedisStreamConsumer.
    """
    redis_client_stream = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STREAM, decode_responses=True
    )

    # Needs user access to delete all users on shutdown
    redis_client_user = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_USER, decode_responses=True
    )

    redis_client_tripwire = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_TRIPWIRE, decode_responses=True
    )
    user_manager = RedisUserManager(redis_client_user)
    tripwire_manager = TripWireManager(redis_client_tripwire)
    rule_registry = RuleRegistry()
    event_registry = EventHandlerRegistry()

    try:
        redis_client_tripwire.flushdb()
        logger.info("Cleared Redis tripwire database.")
        tripwire_count = len(redis_client_tripwire.keys("*"))
        logger.info(f"Number of tripwires currently in Redis: {tripwire_count}")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")

    while True:
        try:
            consumer = RedisStreamConsumer(
                redis_client_stream,
                user_manager,
                tripwire_manager,
                rule_registry,
                event_registry,
            )

            consumer.start()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
        except KeyboardInterrupt:
            logger.info("Shutting down Redis Stream Consumer.")
            redis_client_stream.flushdb()
            redis_client_user.flushdb()
            redis_client_tripwire.flushdb()
            logger.info("Cleared Redis user database.")
            break
