import pytest

from feature_restriction.models import UserData
from feature_restriction.rules import (
    ChargebackRatioRule,
    ScamMessageRule,
    UniqueZipCodeRule,
)


def test_unique_zip_code_rule_evaluation_passes(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the UniqueZipCodeRule correctly evaluates when the condition is met.
    """
    sample_user_data.credit_cards = {"card_001": "12345", "card_002": "54321"}
    sample_user_data.total_credit_cards = 3
    sample_user_data.unique_zip_codes = {"12345", "54321", "67890"}

    rule = UniqueZipCodeRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is True


def test_unique_zip_code_rule_evaluation_fails(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the UniqueZipCodeRule correctly evaluates when the condition is not met.
    """
    sample_user_data.credit_cards = {"card_001": "12345", "card_002": "12345"}
    sample_user_data.total_credit_cards = 2
    sample_user_data.unique_zip_codes = {"12345"}

    rule = UniqueZipCodeRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is False


def test_unique_zip_code_rule_application(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the UniqueZipCodeRule correctly applies changes to user data.
    """
    sample_user_data.credit_cards = {"card_001": "12345", "card_002": "54321"}
    sample_user_data.total_credit_cards = 3
    sample_user_data.unique_zip_codes = {"12345", "54321", "67890"}

    rule = UniqueZipCodeRule(tripwire_manager, user_manager)
    rule.apply_rule(sample_user_data)

    assert sample_user_data.access_flags["can_purchase"] is False


def test_scam_message_rule_evaluation_passes(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ScamMessageRule correctly evaluates when the condition is met.
    """
    sample_user_data.scam_message_flags = 2
    rule = ScamMessageRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is True


def test_scam_message_rule_evaluation_fails(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ScamMessageRule correctly evaluates when the condition is not met.
    """
    sample_user_data.scam_message_flags = 1
    rule = ScamMessageRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is False


def test_scam_message_rule_application(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ScamMessageRule correctly applies changes to user data.
    """
    sample_user_data.scam_message_flags = 2
    rule = ScamMessageRule(tripwire_manager, user_manager)
    rule.apply_rule(sample_user_data)

    assert sample_user_data.access_flags["can_message"] is False


def test_chargeback_ratio_rule_evaluation_passes(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ChargebackRatioRule correctly evaluates when the condition is met.
    """
    sample_user_data.total_spend = 100.0
    sample_user_data.total_chargebacks = 15.0
    rule = ChargebackRatioRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is True


def test_chargeback_ratio_rule_evaluation_fails(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ChargebackRatioRule correctly evaluates when the condition is not met.
    """
    sample_user_data.total_spend = 100.0
    sample_user_data.total_chargebacks = 5.0
    rule = ChargebackRatioRule(tripwire_manager, user_manager)
    assert rule.evaluate_rule(sample_user_data) is False


def test_chargeback_ratio_rule_application(
    tripwire_manager, user_manager, sample_user_data
):
    """
    Test that the ChargebackRatioRule correctly applies changes to user data.
    """
    sample_user_data.total_spend = 100.0
    sample_user_data.total_chargebacks = 15.0
    rule = ChargebackRatioRule(tripwire_manager, user_manager)
    rule.apply_rule(sample_user_data)

    assert sample_user_data.access_flags["can_purchase"] is False
