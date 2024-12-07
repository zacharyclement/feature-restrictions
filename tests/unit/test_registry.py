from unittest.mock import MagicMock

import pytest

from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.registry import EventHandlerRegistry


def test_register_success(event_registry):
    """
    Test successful registration of an event handler.
    """
    mock_handler = MagicMock()
    mock_handler.event_name = "test_event"
    event_registry.register(mock_handler)

    assert event_registry.get("test_event") is mock_handler


def test_register_with_valid_handler():
    registry = EventHandlerRegistry()

    # Create a mock event handler with the required 'event_name' attribute
    mock_handler = MagicMock()
    mock_handler.event_name = "test_event"

    # Register the mock handler
    registry.register(mock_handler)

    # Assert that the handler is registered correctly
    assert registry.get("test_event") == mock_handler


def test_register_with_duplicate_event_name():
    registry = EventHandlerRegistry()

    # Create two mock event handlers with the same 'event_name'
    mock_handler_1 = MagicMock()
    mock_handler_1.event_name = "test_event"
    mock_handler_2 = MagicMock()
    mock_handler_2.event_name = "test_event"

    # Register the first handler
    registry.register(mock_handler_1)

    # Attempt to register the second handler with the same event_name should raise ValueError
    with pytest.raises(ValueError, match="Duplicate event name detected"):
        registry.register(mock_handler_2)


def test_register_duplicate_event_name(event_registry):
    """
    Test registering multiple handlers with the same 'event_name' raises an error.
    """
    mock_handler1 = MagicMock()
    mock_handler1.event_name = "test_event"
    mock_handler2 = MagicMock()
    mock_handler2.event_name = "test_event"

    event_registry.register(mock_handler1)

    with pytest.raises(ValueError, match="is already registered"):
        event_registry.register(mock_handler2)


def test_get_not_found(event_registry):
    """
    Test retrieving a non-existent event handler returns None.
    """
    handler = event_registry.get("non_existent_event")
    assert handler is None


def test_register_default(event_registry, tripwire_manager, user_manager):
    """
    Test registering default event handlers.
    """
    event_registry.register_default(tripwire_manager, user_manager)

    # Verify each handler is registered
    assert isinstance(event_registry.get("credit_card_added"), CreditCardAddedHandler)
    assert isinstance(
        event_registry.get("scam_message_flagged"),
        ScamMessageFlaggedHandler,
    )
    assert isinstance(
        event_registry.get("chargeback_occurred"),
        ChargebackOccurredHandler,
    )
    assert isinstance(event_registry.get("purchase_made"), PurchaseMadeHandler)

    # Verify handlers are initialized with correct dependencies
    handler = event_registry.get("credit_card_added")
    assert handler.tripwire_manager == tripwire_manager
    assert handler.user_manager == user_manager


from unittest.mock import MagicMock

import pytest

from feature_restriction.registry import RuleRegistry
from feature_restriction.rules import (
    ChargebackRatioRule,
    ScamMessageRule,
    UniqueZipCodeRule,
)


def test_register_success():
    """
    Test successful registration of a rule.
    """
    rule_registry = RuleRegistry()
    mock_rule = MagicMock()
    mock_rule.name = "test_rule"

    rule_registry.register(mock_rule)

    assert rule_registry.get("test_rule") == mock_rule


def test_register_with_duplicate_name():
    """
    Test registering two rules with the same name raises an error.
    """
    rule_registry = RuleRegistry()

    mock_rule_1 = MagicMock()
    mock_rule_1.name = "test_rule"
    mock_rule_2 = MagicMock()
    mock_rule_2.name = "test_rule"

    rule_registry.register(mock_rule_1)

    with pytest.raises(ValueError, match="is already registered"):
        rule_registry.register(mock_rule_2)


def test_get_rule_not_found():
    """
    Test retrieving a non-existent rule returns None.
    """
    rule_registry = RuleRegistry()
    rule = rule_registry.get("non_existent_rule")
    assert rule is None


def test_register_default(tripwire_manager, user_manager):
    """
    Test registering default rules.
    """
    rule_registry = RuleRegistry()
    rule_registry.register_default(tripwire_manager, user_manager)

    # Verify that each default rule is registered
    assert isinstance(rule_registry.get("unique_zip_code_rule"), UniqueZipCodeRule)
    assert isinstance(rule_registry.get("scam_message_rule"), ScamMessageRule)
    assert isinstance(rule_registry.get("chargeback_ratio_rule"), ChargebackRatioRule)

    # Verify that rules are initialized with the correct dependencies
    rule = rule_registry.get("unique_zip_code_rule")
    assert rule.tripwire_manager == tripwire_manager
    assert rule.user_manager == user_manager
