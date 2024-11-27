import threading
from queue import Queue

from feature_restriction.models import Event
from feature_restriction.utils import logger


class EventConsumer:
    """
    Manages event consumption and processing.
    """

    def __init__(self, event_queue: Queue, user_manager, tripwire_manager):
        """
        Initialize the EventConsumer.
        :param event_queue: The queue holding incoming events.
        :param user_manager: The UserManager instance for managing user data.
        :param tripwire_manager: The TripWireManager instance for managing tripwires.
        """
        self.event_queue = event_queue
        self.user_manager = user_manager
        self.tripwire_manager = tripwire_manager
        self.consumer_thread = None

    def process_event(self, event: Event):
        """
        Process a single event using the appropriate handler.
        """
        user_id = event.event_properties.get("user_id")
        user_id = str(user_id)
        if not user_id:
            logger.error("'user_id' is required in event properties.")
            return

        # Retrieve or create user data
        user_data = self.user_manager.get_user(user_id)

        # Retrieve the appropriate handler for the event
        handler = event_handler_registry.get(event.name)
        if not handler:
            logger.error(f"No handler registered for event: {event.name}")
            return

        # Process the event
        try:
            handler.handle(event, user_data)
        except Exception as e:
            logger.error(f"An error occurred while processing the event: {str(e)}")

    def consume_events(self):
        """
        Continuously consume events from the queue and process them.
        """
        while True:
            try:
                # Get the next event from the queue
                event = self.event_queue.get()

                logger.info(f"Processing event: {event}")

                # Process the event
                self.process_event(event)

                # Mark the task as done
                self.event_queue.task_done()
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
