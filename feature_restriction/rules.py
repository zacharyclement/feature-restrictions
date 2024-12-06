from abc import ABC, abstractmethod

from .models import UserData
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

    @abstractmethod
    def evaluate_rule(self, user_data: UserData) -> bool:
        """
        Evaluate the rule based on user data.
        """
        pass

    @abstractmethod
    def apply_rule(self, user_data: UserData):
        """
        Apply specific actions if the rule condition is met.
        """
        pass

    def process_rule(self, user_data: UserData) -> bool:
        """
        Process the rule:
        - Check if the rule is disabled.
        - Evaluate the rule.
        - Update tripwires and take actions if the rule condition is met.
        """
        logger.info(f"Processing rule: {self.name}")
        if self.tripwire_manager.is_rule_disabled_via_tripwire(self.name):
            logger.info(f"Rule '{self.name}' is currently disabled via tripwire.")
            return False

        if self.evaluate_rule(user_data):
            self.apply_rule(user_data)
            logger.info(f"applied rule {self.name} to user {user_data.user_id}")

            # Save the updated user data back to Redis
            self.user_manager.save_user(user_data)
            logger.info(f"User data saved after processing rule: {self.name}")
            return True


class UniqueZipCodeRule(BaseRule):
    name = "unique_zip_code_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
        if user_data.total_credit_cards <= 2:
            logger.info(
                f"Not enough credit cards to evaluate the rule. total_cards: {user_data.total_credit_cards}"
            )
            return False
        ratio = len(user_data.unique_zip_codes) / user_data.total_credit_cards
        return ratio > 0.75

    def apply_rule(self, user_data: UserData):
        user_data.access_flags["can_purchase"] = False


class ScamMessageRule(BaseRule):
    name = "scam_message_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
        return user_data.scam_message_flags >= 2

    def apply_rule(self, user_data: UserData):
        user_data.access_flags["can_message"] = False


class ChargebackRatioRule(BaseRule):
    name = "chargeback_ratio_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
        if user_data.total_spend == 0:
            return False
        ratio = user_data.total_chargebacks / user_data.total_spend
        return ratio > 0.10

    def apply_rule(self, user_data: UserData):
        user_data.access_flags["can_purchase"] = False
