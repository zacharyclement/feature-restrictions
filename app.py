import logging

from fastapi import FastAPI, HTTPException

from event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    ScamMessageFlaggedHandler,
)
from models import Event, UserData
from rule_state_store import RuleStateStore
from rules import ChargebackRatioRule, ScamMessageRule, UniqueZipCodeRule
from user_store import UserStore
from utils import event_handler_registry, logger, register_event_handler, register_rule

# Instantiate FastAPI app
app = FastAPI()


# Instantiate stores
user_store = UserStore()
rule_state_store = RuleStateStore()

# Create and register rules
# register_rule(UniqueZipCodeRule(rule_state_store, user_store))
# register_rule(ScamMessageRule(rule_state_store, user_store))
# register_rule(ChargebackRatioRule(rule_state_store, user_store))

# Create and register event handlers
register_event_handler(CreditCardAddedHandler(rule_state_store, user_store))
register_event_handler(ScamMessageFlaggedHandler(rule_state_store, user_store))
register_event_handler(ChargebackOccurredHandler(rule_state_store, user_store))


@app.post("/event")
async def handle_event(event: Event):
    """
    Endpoint to handle incoming events and dispatch them to the appropriate handler.
    """
    # Validate event properties
    user_id = event.event_properties.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=400, detail="'user_id' is required in event properties."
        )

    # Retrieve or create user data
    user_data = user_store.get_user(user_id)

    # Retrieve the appropriate handler for the event
    handler = event_handler_registry.get(event.name)
    if not handler:
        raise HTTPException(
            status_code=400, detail=f"No handler registered for event: {event.name}"
        )
    logger.info(f"**handler: {handler}")

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
    user_data = user_store.get_user(user_id)
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
    user_data = user_store.get_user(user_id)
    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_purchase": user_data.access_flags.get("can_purchase", True)}
