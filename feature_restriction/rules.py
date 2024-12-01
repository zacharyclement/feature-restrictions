from abc import ABC, abstractmethod

from .models import Event, UserData
from .redis_user_manager import RedisUserManager
from .tripwire_manager import TripWireManager
from .utils import logger


class BaseRule(ABC):
    """
    Abstract base class for all rules.
    """

    name: str  # Unique identifier for the rule

    def __init__(
        self, tripwire_manager: TripWireManager, user_manager: RedisUserManager
    ):
        self.tripwire_manager = tripwire_manager
        self.user_manager = user_manager

    def process_rule(self, user_data: UserData):
        """
        Process the rule:
        - Check if the rule is disabled.
        - Evaluate the rule.
        - Update tripwires and take actions if the rule condition is met.
        """
        logger.info(f"Processing rule: {self.name}")
        logger.info(
            f"Tripwire disabled rules, after processing: {self.tripwire_manager.get_disabled_rules()}"
        )

        if self.tripwire_manager.is_rule_disabled_via_tripwire(self.name):
            logger.info(f"Rule '{self.name}' is currently disabled via tripwire.")
            return False  # Rule is disabled, no action taken

        # Evaluate the rule, should we modify the data?
        condition_met = self.evaluate_rule(user_data)
        logger.info(f"Rule condition met: {condition_met}")

        if condition_met:
            # Apply rule, flip user data flags to false
            self.apply_rule(user_data)
            logger.info(f"rule {self.name} applied to user {user_data.user_id}")

            # Get the total number of users from Redis
            total_users = self.user_manager.get_user_count()

            # Update affected users for tripwire logic
            self.tripwire_manager.apply_tripwire_if_needed(
                self.name, user_data.user_id, total_users
            )

            # Save the updated user data back to Redis
            self.user_manager.save_user(user_data)
            logger.info(f"User data saved after processing rule: {self.name}")

        logger.info(
            f"Tripwire disabled rules, after processing: {self.tripwire_manager.get_disabled_rules()}"
        )
        return condition_met

    @abstractmethod
    def evaluate_rule(self, user_data: UserData) -> bool:
        """
        Evaluate the rule based on user data and event.
        """
        pass

    @abstractmethod
    def apply_rule(self, user_data: UserData):
        """
        Apply specific actions if the rule condition is met.
        modifies access flags in user data
        """
        pass


class UniqueZipCodeRule(BaseRule):
    name = "unique_zip_code_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
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

    def evaluate_rule(self, user_data: UserData) -> bool:
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

    def evaluate_rule(self, user_data: UserData) -> bool:
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
