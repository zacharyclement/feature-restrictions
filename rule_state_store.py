# rule_state_store.py

import time
from typing import Dict, Set

from utils import logger


class RuleStateStore:
    """
    Manages state for rules, including tripwires and disabling.
    """

    def __init__(self):
        self.rule_disabled: Dict[str, bool] = {}
        self.affected_users: Dict[str, Dict[str, float]] = (
            {}
        )  # rule_name -> {user_id: timestamp}
        self.time_window: int = 300  # Time window in seconds (e.g., 5 minutes)
        self.threshold: float = 0.05  # 5%
        logger.info(
            f"Rule state store initialized with time window: {self.time_window}s, threshold: {self.threshold}."
        )

    def is_rule_disabled(self, rule_name: str) -> bool:
        """
        is rule diabled or not
        """
        disabled = self.rule_disabled.get(rule_name, False)
        logger.info(f"disabled: {disabled}")
        logger.info(f"rule '{rule_name}' is disabled: {disabled}")
        return disabled

    def update_affected_users(
        self, rule_name: str, user_id: str, total_users: int
    ) -> None:
        """
        Update the affected users for a rule and determine if the rule should be disabled.
        """
        current_time = time.time()
        affected_users = self.affected_users.setdefault(rule_name, {})

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
        previously_disabled = self.rule_disabled.get(rule_name, False)
        if percentage >= self.threshold:
            self.rule_disabled[rule_name] = True
            if not previously_disabled:  # Log only if the state changes
                logger.info(
                    f"Rule '{rule_name}' disabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )
        else:
            self.rule_disabled[rule_name] = False
            if previously_disabled:  # Log only if the state changes
                logger.info(
                    f"Rule '{rule_name}' re-enabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )

    def clear_rules(self) -> None:
        """
        Clear all rule-related state.
        """
        logger.info("Clearing all rule states and affected user data.")
        self.rule_disabled.clear()
        self.affected_users.clear()
