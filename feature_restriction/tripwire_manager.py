# tripwire_manager.py

import time
from typing import Dict, Set

from .utils import logger


class TripWireManager:
    """
        automatically disables a rule if too many users are affected within a specified time window
        Manages state for rules, including tripwires and disabling.
        Example affect_users data structure:
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

    def __init__(self):
        self.tripwire_disabled_rules: Dict[str, bool] = {}
        self.affected_users: Dict[str, Dict[str, float]] = {}
        self.time_window: int = 300  # Time window in seconds (e.g., 5 minutes)
        self.threshold: float = 0.05  # 5%

    def is_tripwire_disabled_rules(self, rule_name: str) -> bool:
        """
        is rule diabled or not
        """
        disabled = self.tripwire_disabled_rules.get(rule_name, False)
        logger.info(f"rule '{rule_name}' is disabled: {disabled}")
        return disabled

    def apply_tripwire_if_needed(
        self, rule_name: str, user_id: str, total_users: int
    ) -> None:
        """
        the tripwire disables the rule if too many users are affected within a specified time window.
        This method updates the affected_users structure when a rule is applied to a user.
        And determine if the rule should be disabled.
        """

        current_time = time.time()
        # If the rule (rule_name) is not already in self.affected_users, initialize it as an empty dictionary.
        affected_users = self.affected_users.setdefault(rule_name, {})
        logger.info(f"self.affected_users: {self.affected_users}")

        # Remove entries outside the time window
        expired_users = [
            uid
            for uid, timestamp in affected_users.items()
            if timestamp <= current_time - self.time_window
        ]
        for uid in expired_users:
            del affected_users[uid]

        # Add or update the current user
        affected_users[user_id] = current_time

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
        Clear all rule-related state.
        """
        logger.info("Clearing all tripwire states and affected user data.")
        self.tripwire_disabled_rules.clear()
        self.affected_users.clear()
