from unittest.mock import MagicMock

import pytest

from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.models import Event, UserData
from feature_restriction.rules import (
    ChargebackRatioRule,
    ScamMessageRule,
    UniqueZipCodeRule,
)


def test_credit_card_added_handler(user_manager, tripwire_manager, sample_user_data):
    """
    Test the CreditCardAddedHandler for handling 'credit_card_added' events.
    """
    # Arrange
    event = Event(
        name="credit_card_added",
        event_properties={"card_id": "card_002", "zip_code": "54321"},
    )

    # Instantiate the handler
    handler = CreditCardAddedHandler(tripwire_manager, user_manager)

    # Act
    handler.handle(event, sample_user_data)

    # Assert: Check the state of `sample_user_data`
    assert sample_user_data.credit_cards == {
        "card_001": "12345",
        "card_002": "54321",
    }
    assert sample_user_data.total_credit_cards == 2
    assert "54321" in sample_user_data.unique_zip_codes


def test_scam_message_flagged_handler(user_manager, tripwire_manager, sample_user_data):
    """
    Test the ScamMessageFlaggedHandler for handling 'scam_message_flagged' events.
    """
    # Arrange
    event = Event(name="scam_message_flagged", event_properties={})
    user_manager.save_user = MagicMock()
    scam_message_rule = ScamMessageRule(tripwire_manager, user_manager)
    scam_message_rule.process_rule = MagicMock()
    handler = ScamMessageFlaggedHandler(tripwire_manager, user_manager)

    # Act
    handler.handle(event, sample_user_data)

    # Assert
    assert sample_user_data.scam_message_flags == 2


def test_chargeback_occurred_handler(user_manager, tripwire_manager, sample_user_data):
    """
    Test the ChargebackOccurredHandler for handling 'chargeback_occurred' events.
    """
    # Arrange
    event = Event(name="chargeback_occurred", event_properties={"amount": 50.0})
    user_manager.save_user = MagicMock()
    chargeback_ratio_rule = ChargebackRatioRule(tripwire_manager, user_manager)
    chargeback_ratio_rule.process_rule = MagicMock()
    handler = ChargebackOccurredHandler(tripwire_manager, user_manager)

    # Act
    handler.handle(event, sample_user_data)

    # Assert
    assert sample_user_data.total_chargebacks == 55.0


def test_purchase_made_handler(user_manager, tripwire_manager, sample_user_data):
    """
    Test the PurchaseMadeHandler for handling 'purchase_made' events.
    """
    # Arrange
    event = Event(name="purchase_made", event_properties={"amount": 100.0})
    user_manager.save_user = MagicMock()
    handler = PurchaseMadeHandler(tripwire_manager, user_manager)

    # Act
    handler.handle(event, sample_user_data)

    # Assert
    assert sample_user_data.total_spend == 200.0
    user_manager.save_user.assert_called_once_with(sample_user_data)


def test_credit_card_added_handler_missing_properties(
    user_manager, tripwire_manager, sample_user_data
):
    """
    Test that the CreditCardAddedHandler raises an error if required properties are missing.
    """
    # Arrange
    event = Event(name="credit_card_added", event_properties={})
    handler = CreditCardAddedHandler(tripwire_manager, user_manager)

    # Act & Assert
    with pytest.raises(ValueError, match="Both 'card_id' and 'zip_code' are required."):
        handler.handle(event, sample_user_data)


def test_chargeback_occurred_handler_missing_amount(
    user_manager, tripwire_manager, sample_user_data
):
    """
    Test that the ChargebackOccurredHandler raises an error if 'amount' is missing.
    """
    # Arrange
    event = Event(name="chargeback_occurred", event_properties={})
    handler = ChargebackOccurredHandler(tripwire_manager, user_manager)

    # Act & Assert
    with pytest.raises(ValueError, match="'amount' is required."):
        handler.handle(event, sample_user_data)


def test_purchase_made_handler_missing_amount(
    user_manager, tripwire_manager, sample_user_data
):
    """
    Test that the PurchaseMadeHandler raises an error if 'amount' is missing.
    """
    # Arrange
    event = Event(name="purchase_made", event_properties={})
    handler = PurchaseMadeHandler(tripwire_manager, user_manager)

    # Act & Assert
    with pytest.raises(ValueError, match="'amount' is required."):
        handler.handle(event, sample_user_data)
