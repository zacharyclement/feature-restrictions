# rule_state_store.py

import time
from typing import Dict, Set


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

    def is_rule_disabled(self, rule_name: str) -> bool:
        """
        Check if a rule is currently disabled.
        """
        return self.rule_disabled.get(rule_name, False)

    def update_affected_users(self, rule_name: str, user_id: str, total_users: int):
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

        # Disable the rule if the percentage exceeds the threshold
        if percentage >= self.threshold:
            self.rule_disabled[rule_name] = True
        else:
            self.rule_disabled[rule_name] = False

    def clear_rules(self):
        """
        Clear all rule-related state.
        """
        self.rule_disabled.clear()
        self.affected_users.clear()
