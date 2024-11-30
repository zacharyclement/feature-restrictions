import time
from typing import Dict

from .utils import logger


class TripWireManager:
    """
    Automatically disables a rule if too many users are affected within a specified time window.
    Manages state for rules, including tripwires and disabling.

    Example `affected_users` data structure:
    {
        "scam_message_rule": {
            "user_1": 1698183437.453,  # Timestamp when this user was affected
            "user_2": 1698183438.678
        },
        "unique_zip_code_rule": {
            "user_3": 1698183445.123
        }
    }
    """

    _instance = None  # Class-level attribute to store the singleton instance

    def __new__(cls, *args, **kwargs):
        # Ensure only one instance is created
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()  # Initialize instance variables
        return cls._instance

    def _initialize(self):
        """
        Initialize instance variables. Called only once during the singleton creation.
        """
        self.tripwire_disabled_rules: Dict[str, bool] = {}
        self.affected_users: Dict[str, Dict[str, float]] = {}
        self.time_window: int = 300  # Time window in seconds (e.g., 5 minutes)
        self.threshold: float = 0.05  # 5%

    def is_rule_disabled_via_tripwire(self, rule_name: str) -> bool:
        """
        Check if a rule is disabled via the tripwire.

        :param rule_name: The name of the rule to check.
        :return: True if the rule is disabled, False otherwise.
        """
        disabled = self.tripwire_disabled_rules.get(rule_name, False)
        logger.info(f"Rule '{rule_name}' is disabled: {disabled}")
        return disabled

    def apply_tripwire_if_needed(
        self, rule_name: str, user_id: str, total_users: int
    ) -> None:
        """
        Apply the tripwire logic to disable a rule if too many users are affected
        within a specified time window.

        :param rule_name: The name of the rule.
        :param user_id: The ID of the user triggering the rule.
        :param total_users: Total number of users in the system.
        """
        current_time = time.time()
        affected_users = self.affected_users.setdefault(rule_name, {})
        logger.info(f"self.affected_users before applying: {self.affected_users}")

        # Remove expired entries
        expired_users = [
            uid
            for uid, timestamp in affected_users.items()
            if timestamp <= current_time - self.time_window
        ]
        for uid in expired_users:
            del affected_users[uid]

        # Add or update the current user
        affected_users[user_id] = current_time
        logger.info(f"self.affected_users after applied: {self.affected_users}")

        # Calculate the percentage of affected users
        affected_count = len(affected_users)
        percentage = affected_count / total_users if total_users > 0 else 0

        # Disable or enable the rule based on the percentage
        previously_disabled = self.tripwire_disabled_rules.get(rule_name, False)
        if percentage >= self.threshold:
            self.tripwire_disabled_rules[rule_name] = True
            if not previously_disabled:  # Log only if the state changes
                logger.info(
                    f"Tripwire thrown: Rule '{rule_name}' disabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )
        else:
            self.tripwire_disabled_rules[rule_name] = False
            if previously_disabled:  # Log only if the state changes
                logger.info(
                    f"Tripwire disengaged: Rule '{rule_name}' re-enabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )

    def clear_rules(self) -> None:
        """
        Clear all tripwire states and affected user data.
        """
        logger.info("Clearing all tripwire states and affected user data.")
        self.tripwire_disabled_rules.clear()
        self.affected_users.clear()
