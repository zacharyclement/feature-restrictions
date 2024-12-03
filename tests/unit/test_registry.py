from unittest.mock import MagicMock

import pytest

from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.registry import EventHandlerRegistry


def test_register_event_handler_success(registry):
    """
    Test successful registration of an event handler.
    """
    mock_handler = MagicMock()
    mock_handler.event_name = "test_event"
    registry.register_event_handler(mock_handler)

    assert registry.get_event_handler("test_event") is mock_handler


def test_register_event_handler_no_event_name(registry):
    """
    Test registering a handler without an 'event_name' raises an error.
    """
    mock_handler = MagicMock()
    del mock_handler.event_name  # Simulate missing `event_name` attribute

    with pytest.raises(ValueError, match="must have an 'event_name' attribute"):
        registry.register_event_handler(mock_handler)


def test_register_event_handler_duplicate_event_name(registry):
    """
    Test registering multiple handlers with the same 'event_name' raises an error.
    """
    mock_handler1 = MagicMock()
    mock_handler1.event_name = "test_event"
    mock_handler2 = MagicMock()
    mock_handler2.event_name = "test_event"

    registry.register_event_handler(mock_handler1)

    with pytest.raises(ValueError, match="is already registered"):
        registry.register_event_handler(mock_handler2)


def test_get_event_handler_not_found(registry):
    """
    Test retrieving a non-existent event handler returns None.
    """
    handler = registry.get_event_handler("non_existent_event")
    assert handler is None


def test_register_default_event_handlers(registry, tripwire_manager, user_manager):
    """
    Test registering default event handlers.
    """
    registry.register_default_event_handlers(tripwire_manager, user_manager)

    # Verify each handler is registered
    assert isinstance(
        registry.get_event_handler("credit_card_added"), CreditCardAddedHandler
    )
    assert isinstance(
        registry.get_event_handler("scam_message_flagged"), ScamMessageFlaggedHandler
    )
    assert isinstance(
        registry.get_event_handler("chargeback_occurred"), ChargebackOccurredHandler
    )
    assert isinstance(registry.get_event_handler("purchase_made"), PurchaseMadeHandler)

    # Verify handlers are initialized with correct dependencies
    handler = registry.get_event_handler("credit_card_added")
    assert handler.tripwire_manager == tripwire_manager
    assert handler.user_manager == user_manager
