import threading
from queue import Empty, Queue
from typing import Dict

from .event_handlers import (
    BaseEventHandler,
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    ScamMessageFlaggedHandler,
)
from .models import Event
from .redis_user_manager import RedisUserManager
from .tripwire_manager import TripWireManager
from .utils import logger


class EventConsumer:
    """
    Manages event consumption, processing, and event handler registration.
    """

    def __init__(self, event_queue: Queue):
        """
        Initialize the EventConsumer and register event handlers.
        :param event_queue: The queue holding incoming events.
        """
        self.event_queue = event_queue
        self.redis_user_manager = RedisUserManager()  # Handles user data persistence
        self.tripwire_manager = TripWireManager()  # Handles rule tripwires
        self.consumer_thread = None
        self._stop_event = threading.Event()  # Event to signal the thread to stop

        # Local registry for event handlers
        self.event_handler_registry: Dict[str, BaseEventHandler] = {}

        # Register default event handlers
        self.register_default_event_handlers()

    def register_event_handler(self, event_handler_instance: "BaseEventHandler"):
        """
        Register an event handler instance in the local event handler registry.

        :param event_handler_instance: An instance of a class inheriting from BaseEventHandler.
        :raises ValueError: If a handler for the same event_name is already registered.
        """
        event_name = getattr(event_handler_instance, "event_name", None)
        if not event_name:
            raise ValueError(
                f"The event handler '{event_handler_instance.__class__.__name__}' must have an 'event_name' attribute."
            )

        if event_name in self.event_handler_registry:
            raise ValueError(
                f"An event handler for '{event_name}' is already registered."
            )

        self.event_handler_registry[event_name] = event_handler_instance
        logger.info(f"Registered handler for event: {event_name}")

    def register_default_event_handlers(self):
        """
        Register default event handlers for known events.
        """
        logger.info("Registering default event handlers...")
        self.register_event_handler(
            CreditCardAddedHandler(self.tripwire_manager, self.redis_user_manager)
        )
        self.register_event_handler(
            ScamMessageFlaggedHandler(self.tripwire_manager, self.redis_user_manager)
        )
        self.register_event_handler(
            ChargebackOccurredHandler(self.tripwire_manager, self.redis_user_manager)
        )
        logger.info("Default event handlers registered successfully.")

    def process_event(self, event: Event):
        """
        Process a single event using the appropriate handler.
        """
        user_id = event.event_properties.get("user_id")
        user_id = str(user_id)
        if not user_id:
            logger.error("'user_id' is required in event properties.")
            return

        # Retrieve or create user data from Redis
        user_data = self.redis_user_manager.get_user(user_id)
        logger.info(
            f"user data before: {self.redis_user_manager.display_user_data(user_id)}"
        )

        # Retrieve the appropriate handler for the event
        handler = self.event_handler_registry.get(event.name)
        if not handler:
            logger.error(f"No handler registered for event: {event.name}")
            return

        # Process the event
        try:
            handler.handle(event, user_data)
            logger.info(
                f"user data after: {self.redis_user_manager.display_user_data(user_id)}"
            )

        except Exception as e:
            logger.error(f"An error occurred while processing the event: {str(e)}")

    def consume_events(self):
        """
        Continuously consume events from the queue and process them.
        """
        logger.info("Entering event consumption loop.")
        while not self._stop_event.is_set():
            try:
                # logger.info("In event consumption loop.")
                # Wait for an event with a timeout to allow graceful stop checks
                event = self.event_queue.get(timeout=1)
                logger.info(f"Processing event: {event}")

                # Process the event
                self.process_event(event)

                # Mark the task as done
                self.event_queue.task_done()
            except Empty:  # If no event is received within timeout
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def start(self):
        """
        Start the consumer thread.
        """
        if not self.consumer_thread:
            self.consumer_thread = threading.Thread(
                target=self.consume_events, daemon=True
            )
            self.consumer_thread.start()
            logger.info("Event consumer thread started.")

    def stop(self):
        """
        Stop the consumer thread gracefully.
        """
        if self.consumer_thread:
            logger.info("Stopping event consumer thread...")
            self._stop_event.set()  # Signal the thread to stop
            self.consumer_thread.join(
                timeout=5
            )  # Wait for the thread to finish with a timeout
            if self.consumer_thread.is_alive():
                logger.warning("Event consumer thread did not stop in time!")
            else:
                logger.info("Event consumer thread stopped successfully.")
            self.consumer_thread = None
