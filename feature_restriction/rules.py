from abc import ABC, abstractmethod

from .models import UserData
from .redis_user_manager import RedisUserManager
from .tripwire_manager import RedisTripwireManager
from .utils import logger


class BaseRule(ABC):
    """
    Abstract base class for all rules.

    This class defines the structure for rules that evaluate user data
    and apply specific actions based on defined conditions.

    Attributes
    ----------
    name : str
        Unique identifier for the rule.
    tripwire_manager : RedisTripwireManager
        Manager to handle tripwires and check if rules are disabled.
    user_manager : RedisUserManager
        Manager to handle user data stored in Redis.
    """

    name: str  # Unique identifier for the rule

    def __init__(
        self, tripwire_manager: RedisTripwireManager, user_manager: RedisUserManager
    ):
        """
        Initialize a BaseRule instance.

        Parameters
        ----------
        tripwire_manager : RedisTripwireManager
            Manager to handle tripwire states.
        user_manager : RedisUserManager
            Manager to interact with user data stored in Redis.
        """
        self.tripwire_manager = tripwire_manager
        self.user_manager = user_manager

    @abstractmethod
    def evaluate_rule(self, user_data: UserData) -> bool:
        """
        Evaluate the rule based on user data.

        Parameters
        ----------
        user_data : UserData
            The user data object containing information for evaluation.

        Returns
        -------
        bool
            True if the rule condition is met, False otherwise.
        """
        pass

    @abstractmethod
    def apply_rule(self, user_data: UserData):
        """
        Apply specific actions if the rule condition is met.

        Parameters
        ----------
        user_data : UserData
            The user data object to which actions are applied.
        """
        pass

    def process_rule(self, user_data: UserData) -> bool:
        """
        Process the rule:
        - Check if the rule is disabled.
        - Evaluate the rule and apply actions if necessary.

        Parameters
        ----------
        user_data : UserData
            The user data object to evaluate and modify.

        Returns
        -------
        bool
            True if the rule was successfully processed and applied, False otherwise.
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
    """
    Rule to check if the ratio of unique zip codes to total credit cards is above a threshold.

    Attributes
    ----------
    name : str
        Unique identifier for the rule.
    """

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
    """
    Rule to check if the number of scam message flags exceeds a threshold.

    Attributes
    ----------
    name : str
        Unique identifier for the rule.
    """

    name = "scam_message_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
        return user_data.scam_message_flags >= 2

    def apply_rule(self, user_data: UserData):
        user_data.access_flags["can_message"] = False


class ChargebackRatioRule(BaseRule):
    """
    Rule to check if the chargeback ratio exceeds a threshold.

    Attributes
    ----------
    name : str
        Unique identifier for the rule.
    """

    name = "chargeback_ratio_rule"

    def evaluate_rule(self, user_data: UserData) -> bool:
        if user_data.total_spend == 0:
            return False
        ratio = user_data.total_chargebacks / user_data.total_spend
        return ratio > 0.10

    def apply_rule(self, user_data: UserData):
        user_data.access_flags["can_purchase"] = False
