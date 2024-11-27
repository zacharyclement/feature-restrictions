import logging
from typing import Dict

# Global registries
event_handler_registry: Dict[str, "BaseEventHandler"] = {}


def register_event_handler(event_handler_instance: "BaseEventHandler"):
    """
    Register an event handler instance in the global event handler registry.

    :param event_handler_instance: An instance of a class inheriting from BaseEventHandler.
    :raises ValueError: If a handler for the same event_name is already registered.
    """
    event_name = getattr(event_handler_instance, "event_name", None)
    if not event_name:
        raise ValueError(
            f"The event handler '{event_handler_instance.__class__.__name__}' must have an 'event_name' attribute."
        )

    if event_name in event_handler_registry:
        raise ValueError(f"An event handler for '{event_name}' is already registered.")

    event_handler_registry[event_name] = event_handler_instance


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler("server.log", mode="a"),  # Output to a file
    ],
)

logger = logging.getLogger(
    "fastapi_server"
)  # Create a specific logger for the FastAPI app