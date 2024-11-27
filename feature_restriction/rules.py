from abc import ABC, abstractmethod

from .models import Event, UserData
from .tripwire_manager import TripWireManager
from .user_manager import UserManager
from .utils import logger


class BaseRule(ABC):
    """
    Abstract base class for all rules.
    """

    name: str  # Unique identifier for the rule

    def __init__(self, tripwire_manager: TripWireManager, user_manager: UserManager):
        self.tripwire_manager = tripwire_manager
        self.user_manager = user_manager

    def process(self, user_data: UserData, event: Event):
        """
        Process the rule:
        - Check if the rule is disabled.
        - Evaluate the rule.
        - Update tripwires and take actions if the rule condition is met.
        """
        logger.info(f"Processing rule: {self.name}")
        logger.info(
            f"rule disabled, before processing: {self.tripwire_manager.rule_disabled}"
        )
        if self.tripwire_manager.is_rule_disabled(self.name):
            return False  # Rule is disabled, no action taken

        # Evaluate the rule, should we modify the data?
        condition_met = self.evaluate(user_data, event)
        logger.info(f"Rule condition met: {condition_met}")

        if condition_met:
            # Apply action, flip user data flags to false
            self.apply_rule(user_data)
            logger.info(f"rule {self.name} applied to user {user_data.user_id}")
            # Update affected users for tripwire logic
            total_users = len(self.user_manager.users)
            self.tripwire_manager.apply_tripwire_if_needed(
                self.name, user_data.user_id, total_users
            )
        logger.info(
            f"rule disabled, after processing: {self.tripwire_manager.rule_disabled}"
        )
        return condition_met

    @abstractmethod
    def evaluate(self, user_data: UserData, event: Event) -> bool:
        """
        Evaluate the rule based on user data and event.
        """
        pass

    @abstractmethod
    def apply_rule(self, user_data: UserData):
        """
        Apply specific actions if the rule condition is met.
        """
        pass


class UniqueZipCodeRule(BaseRule):
    name = "unique_zip_code_rule"

    def evaluate(self, user_data: UserData, event: Event) -> bool:
        """
        Evaluates whether the ratio of unique zip codes to total credit cards exceeds 0.75.
        """
        # Ensure there are credit cards
        if user_data.total_credit_cards == 0:
            return False

        # Calculate the ratio directly from updated user data
        ratio = len(user_data.unique_zip_codes) / user_data.total_credit_cards
        return ratio > 0.75

    def apply_rule(self, user_data: UserData):
        """
        Disable the 'can_purchase' flag if the rule condition is met.
        """
        user_data.access_flags["can_purchase"] = False


class ScamMessageRule(BaseRule):
    name = "scam_message_rule"

    def evaluate(self, user_data: UserData, event: Event) -> bool:
        """
        Evaluates whether the user has reached the scam message flag threshold.
        """
        # Assume scam_message_flags has already been incremented by the handler
        return user_data.scam_message_flags >= 2

    def apply_rule(self, user_data: UserData):
        """
        Disable the 'can_message' flag if the rule condition is met.
        """
        user_data.access_flags["can_message"] = False


class ChargebackRatioRule(BaseRule):
    name = "chargeback_ratio_rule"

    def evaluate(self, user_data: UserData, event: Event) -> bool:
        """
        Evaluates whether the ratio of total chargebacks to total spend exceeds 10%.
        """
        # Ensure there is spend to calculate the ratio
        if user_data.total_spend == 0:
            return False

        # Calculate the ratio directly from updated user data
        ratio = user_data.total_chargebacks / user_data.total_spend
        return ratio > 0.10

    def apply_rule(self, user_data: UserData):
        """
        Disable the 'can_purchase' flag if the rule condition is met.
        """
        user_data.access_flags["can_purchase"] = False