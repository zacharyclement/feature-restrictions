from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)


class EventHandlerRegistry:
    """
    Manages the registration and retrieval of event handlers.
    """

    def __init__(self):
        """
        Initialize the registry for event handlers.
        """
        self.event_handler_registry = {}

    def register_event_handler(self, event_handler_instance):
        """
        Register an event handler for specific event types.

        :param event_handler_instance: An instance of a class inheriting from BaseEventHandler.
        :raises ValueError: If the handler does not have an `event_name` attribute.
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

    def get_event_handler(self, event_name):
        """
        Retrieve an event handler by its name.

        :param event_name: The name of the event.
        :return: The corresponding event handler, or None if not found.
        """
        return self.event_handler_registry.get(event_name)

    def register_default_event_handlers(self, tripwire_manager, redis_user_manager):
        """
        Register the default event handlers.

        :param tripwire_manager: Instance of TripWireManager.
        :param redis_user_manager: Instance of RedisUserManager.
        """
        self.register_event_handler(
            CreditCardAddedHandler(tripwire_manager, redis_user_manager)
        )
        self.register_event_handler(
            ScamMessageFlaggedHandler(tripwire_manager, redis_user_manager)
        )
        self.register_event_handler(
            ChargebackOccurredHandler(tripwire_manager, redis_user_manager)
        )
        self.register_event_handler(
            PurchaseMadeHandler(tripwire_manager, redis_user_manager)
        )
