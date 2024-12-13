import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import List

import redis

from feature_restriction.clients import (
    RedisStreamClient,
    RedisTripwireClient,
    RedisUserClient,
)
from feature_restriction.config import (
    CONSUMER_GROUP,
    CONSUMER_NAME,
    EVENT_STREAM_KEY,
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.models import Event
from feature_restriction.redis_user_manager import RedisUserManager, UserManager
from feature_restriction.registry import EventHandlerRegistry, Registry, RuleRegistry
from feature_restriction.tripwire_manager import RedisTripwireManager, TripwireManager
from feature_restriction.utils import logger


class StreamConsumer(ABC):
    @abstractmethod
    def start(self):
        """start"""

    @abstractmethod
    def stop(self):
        """stop"""

    @abstractmethod
    def process_event(self, event_id, event_data):
        """process_event"""


class RedisStreamConsumer(StreamConsumer):
    """
    A consumer for processing events from a Redis stream.

    This class initializes a Redis stream consumer group, processes events from the stream, and applies
    event handlers and rules for each event.

    Parameters
    ----------
    redis_client : redis.StrictRedis
        The Redis client connected to the event stream database.
    user_manager : RedisUserManager
        The manager for handling user-related operations in Redis.
    tripwire_manager : RedisTripwireManager
        The manager for handling tripwire logic in Redis.
    rule_registry : RuleRegistry
        The registry for managing rules applied to events.
    event_registry : EventHandlerRegistry
        The registry for managing event handlers.

    Attributes
    ----------
    redis_client_stream : redis.StrictRedis
        The Redis client connected to the event stream database.
    user_manager : RedisUserManager
        The manager for handling user-related operations.
    tripwire_manager : RedisTripwireManager
        The manager for tripwire logic.
    rule_registry : RuleRegistry
        The registry for managing rules.
    event_registry : EventHandlerRegistry
        The registry for managing event handlers.
    """

    def __init__(
        self,
        redis_client: RedisStreamClient,
        user_manager: UserManager,
        tripwire_manager: TripwireManager,
        rule_registry: Registry,
        event_registry: Registry,
    ):
        self.redis_client_stream = redis_client
        self.user_manager = user_manager
        self.tripwire_manager = tripwire_manager
        self.rule_registry = rule_registry
        self.event_registry = event_registry

        self._initialize_consumer_group()
        self._initialize_registries()

    def _initialize_consumer_group(self) -> None:
        """
        Initializes the Redis stream consumer group.
        """
        try:
            # Create the consumer group. Using mkstream=True ensures that if the stream doesn't exist,
            # it will be created automatically.
            # Using id="$" starts the group at the end of the stream to avoid empty stream errors.
            self.redis_client_stream.xgroup_create(
                EVENT_STREAM_KEY, CONSUMER_GROUP, id="$", mkstream=True
            )
            logger.info(
                f"Consumer group '{CONSUMER_GROUP}' created on stream '{EVENT_STREAM_KEY}'."
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{CONSUMER_GROUP}' already exists.")
            else:
                raise e

    def _initialize_registries(self) -> None:
        """
        Registers default rules and event handlers in the corresponding registries.
        """
        # Register defaults
        self.rule_registry.register_default(self.tripwire_manager, self.user_manager)
        self.event_registry.register_default(self.user_manager, self.user_manager)

    def process_event(self, event_id: str, event_data: dict):
        """
        Processes a single event from the Redis stream.

        This method applies event handlers and rules associated with the event and updates the user data accordingly.

        Parameters
        ----------
        event_id : str
            The unique identifier of the event.
        event_data : dict
            The data associated with the event.

        Raises
        ------
        Exception
            If an error occurs during event processing.
        """
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
            # STEP !: process the event
            handler = self.event_registry.get(event.name)
            if handler:
                handler.handle(event, user_data)

            logger.info(
                f"display user data after handler: {self.user_manager.display_user_data(user_id)}"
            )

            # STEP 2: process the rules
            rule_names: List[str] = self.event_registry.get_rules_for_event(event.name)
            for rule_name in rule_names:
                rule = self.rule_registry.get(rule_name)
                if rule:
                    rule_applied: bool = rule.process_rule(user_data)

                    # Apply the tripwire logic after processing the rule

                    if rule_applied:
                        # STEP 3: apply tripwire if needed
                        logger.info(
                            f"disabled rules before: {self.tripwire_manager.get_disabled_rules()}"
                        )
                        # Get the total number of users
                        total_users: int = self.user_manager.get_user_count()
                        self.tripwire_manager.apply_tripwire_if_needed(
                            rule.name, user_data.user_id, total_users
                        )
                        logger.info(
                            f"disabled rules after: {self.tripwire_manager.get_disabled_rules()}"
                        )

            logger.info(
                f"display user data after rule: {self.user_manager.display_user_data(user_id)}"
            )
            logger.info(f"Event '{event.name}' processed successfully.")
            logger.info(f"*******************")

        except Exception as e:
            logger.error(f"Error processing event '{event_id}': {e}")

    def start(self):
        """
        Starts consuming events from the Redis stream.

        Continuously reads events from the stream, processes them, and acknowledges them in the consumer group.
        """
        logger.info(f"Starting Redis Stream Consumer on stream: {EVENT_STREAM_KEY}")
        while True:
            try:
                events = self.redis_client_stream.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={EVENT_STREAM_KEY: ">"},
                    count=10,
                    block=1000,
                )
                for stream, event_list in events:
                    for event_id, event_data in event_list:
                        self.process_event(event_id, event_data)
                        self.redis_client_stream.xack(
                            EVENT_STREAM_KEY, CONSUMER_GROUP, event_id
                        )
            except Exception as e:
                logger.error(f"Error consuming events: {e}")

    def stop(self):
        """
        Signals the consumer to stop and performs cleanup operations.
        """
        logger.info("Stopping Redis Stream Consumer...")
        self._stop_event.set()


if __name__ == "__main__":
    # Connect to Redis
    time.sleep(5)  # Wait for Redis to start
    redis_client_stream = RedisStreamClient(
        REDIS_HOST, REDIS_PORT, REDIS_DB_STREAM
    ).connect()
    redis_client_user = RedisUserClient(REDIS_HOST, REDIS_PORT, REDIS_DB_USER).connect()
    redis_client_tripwire = RedisTripwireClient(
        REDIS_HOST, REDIS_PORT, REDIS_DB_TRIPWIRE
    ).connect()

    try:
        # Test connection to Redis
        redis_client_stream.ping()
        redis_client_user.ping()
        redis_client_tripwire.ping()
        logger.info("Successfully connected to Redis databases!")

        # Clear databases only once at startup (if that's desired)
        logger.info("Clearing Redis databases before starting consumer...")
        redis_client_stream.flushdb()
        redis_client_user.flushdb()
        redis_client_tripwire.flushdb()
        logger.info("Databases cleared.")

        stream_keys_count = len(redis_client_stream.keys("*"))
        user_keys_count = len(redis_client_user.keys("*"))
        tripwire_count = len(redis_client_tripwire.keys("*"))

        logger.info(f"Number of keys in Redis stream database: {stream_keys_count}")
        logger.info(f"Number of keys in Redis user database: {user_keys_count}")
        logger.info(f"Number of tripwires currently in Redis: {tripwire_count}")

    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e

    user_manager = RedisUserManager(redis_client_user)
    tripwire_manager = RedisTripwireManager(redis_client_tripwire)
    rule_registry = RuleRegistry()
    event_registry = EventHandlerRegistry()

    # Create the consumer after flushing the DB and ensuring a clean state
    consumer = RedisStreamConsumer(
        redis_client_stream,
        user_manager,
        tripwire_manager,
        rule_registry,
        event_registry,
    )

    try:
        consumer.start()
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
    except KeyboardInterrupt:
        logger.info("Shutting down Redis Stream Consumer.")
        redis_client_stream.flushdb()
        redis_client_user.flushdb()
        redis_client_tripwire.flushdb()
        logger.info("Shutdown complete.")
