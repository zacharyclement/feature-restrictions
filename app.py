import logging

from fastapi import FastAPI, HTTPException

from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.models import Event
from feature_restriction.trip_wire_manager import TripWireManager
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


# Instantiate stores
user_manager = UserManager()
trip_wire_manager = TripWireManager()

# register event handlers
register_event_handler(CreditCardAddedHandler(trip_wire_manager, user_manager))
register_event_handler(ScamMessageFlaggedHandler(trip_wire_manager, user_manager))
register_event_handler(ChargebackOccurredHandler(trip_wire_manager, user_manager))


@app.post("/event")
async def handle_event(event: Event):
    """
    Endpoint to handle incoming events and dispatch them to the appropriate handler.
    """

    logger.info(f"** Received event: {event}")
    # Validate event properties

    user_id = event.event_properties.get("user_id")
    user_id = str(user_id)
    if not user_id:
        raise HTTPException(
            status_code=400, detail="'user_id' is required in event properties."
        )

    # Retrieve or create user data
    user_data = user_manager.get_user(user_id)

    # Retrieve the appropriate handler for the event
    handler = event_handler_registry.get(event.name)
    if not handler:
        raise HTTPException(
            status_code=400, detail=f"No handler registered for event: {event.name}"
        )

    # Process the event
    try:
        return await handler.handle(event, user_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the event: {str(e)}",
        )


@app.get("/canmessage")
async def can_message(user_id: str):
    """
    Endpoint to check if a user has access to send/receive messages.
    """
    logger.info(f"** can message, user_id: {user_id}")

    user_data = user_manager.get_user(user_id)

    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_message": user_data.access_flags.get("can_message", True)}


@app.get("/canpurchase")
async def can_purchase(user_id: str):
    """
    Endpoint to check if a user has access to bid/purchase.
    """
    user_id = str(user_id)
    logger.info(f"** can purchase, user_id: {user_id}")
    logger.info(f"user data before: {user_manager.display_user_data(user_id)}")
    user_data = user_manager.get_user(user_id)
    logger.info(f"user data after: {user_manager.display_user_data(user_id)}")
    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_purchase": user_data.access_flags.get("can_purchase", True)}
