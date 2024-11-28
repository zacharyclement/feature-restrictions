import logging
from queue import Queue

from fastapi import FastAPI, HTTPException

from feature_restriction.event_consumer import EventConsumer
from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.models import Event
from feature_restriction.tripwire_manager import TripWireManager
from feature_restriction.user_manager import UserManager
from feature_restriction.utils import (
    event_handler_registry,
    logger,
    register_event_handler,
)

# Instantiate FastAPI app
app = FastAPI()
# Attach user_manager to app state

logger.info("****************************************")
logger.info("****************************************")
# Instantiate managers
user_manager = UserManager()
tripwire_manager = TripWireManager()

# Create a global event queue
event_queue = Queue()

# Instantiate and start the EventConsumer
event_consumer = EventConsumer(event_queue, user_manager, tripwire_manager)

# register event handlers
register_event_handler(CreditCardAddedHandler(tripwire_manager, user_manager))
register_event_handler(ScamMessageFlaggedHandler(tripwire_manager, user_manager))
register_event_handler(ChargebackOccurredHandler(tripwire_manager, user_manager))


@app.on_event("startup")
def start_consumer():
    """
    Start the event consumer thread when the application starts.
    """

    event_consumer.start()


@app.post("/event")
async def handle_event(event: Event):
    """
    Endpoint to handle incoming events and enqueue them for processing.
    """
    logger.info(f"** Received event: {event}")

    # Enqueue the event for processing
    event_queue.put(event)

    return {"status": "Event enqueued for processing."}


@app.get("/canmessage")
def can_message(user_id: str):
    """
    Endpoint to check if a user has access to send/receive messages.
    """
    logger.info(f"** can message, user_id: {user_id}")

    user_data = user_manager.get_user(user_id)
    logger.info(f"user data: {user_manager.display_user_data(user_id)}")

    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_message": user_data.access_flags.get("can_message", True)}


@app.get("/canpurchase")
def can_purchase(user_id: str):
    """
    Endpoint to check if a user has access to bid/purchase.
    """
    user_id = str(user_id)
    logger.info(f"** can purchase, user_id: {user_id}")
    user_data = user_manager.get_user(user_id)
    logger.info(f"user data: {user_manager.display_user_data(user_id)}")
    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_purchase": user_data.access_flags.get("can_purchase", True)}


@app.on_event("shutdown")
async def shutdown():
    """
    Clean up resources during application shutdown.
    """
    logger.info("Shutting down FastAPI app.")
    # consumer = app.state.event_consumer

    # Stop the consumer
    if event_consumer:
        logger.info("Stopping event consumer.")
        event_consumer.stop()
        event_consumer.consumer_thread.join()  # Wait for the thread to finish
        logger.info("Event consumer stopped.")
