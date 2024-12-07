import time
from abc import ABC, abstractmethod
from typing import Dict

import redis

from feature_restriction.config import REDIS_DB_TRIPWIRE, REDIS_HOST, REDIS_PORT
from feature_restriction.utils import logger


class TripwireManager(ABC):
    @abstractmethod
    def is_rule_disabled_via_tripwire(self, rule_name: str) -> bool:
        """Check if a rule is disabled via the tripwire."""

    @abstractmethod
    def apply_tripwire_if_needed(
        self,
        rule_name: str,
        user_id: str,
        total_users: int,
    ) -> None:
        """Apply tripwire logic to disable a rule if too many users are affected within a time window."""

    @abstractmethod
    def get_disabled_rules(self) -> Dict[str, bool]:
        """Retrieve all rules and their disabled states from Redis."""


class RedisTripwireManager(TripwireManager):
    """
    Manages tripwire states and user activity for rules to prevent rules from affecting too many users.

    This class uses a dedicated Redis database to track rule states and affected users. If the number of affected
    users for a rule exceeds a certain threshold within a specified time window, the rule is disabled
    (i.e., the tripwire is "thrown"). The rule can be re-enabled if the number of affected users falls below the threshold.

    Example Redis Keys:
        - `tripwire:states`: Stores the disabled states of rules as a hash.
        - `tripwire:affected_users:{rule_name}`: Tracks affected users for a specific rule as a Redis hash.

    Attributes
    ----------
    redis_client : redis.StrictRedis
        Redis connection used for managing tripwire states and affected users.
    time_window : int
        Time window (in seconds) for tracking affected users (default: 300 seconds).
    threshold : float
        Percentage threshold of affected users to disable a rule (default: 5%).
    tripwire_states_key : str
        Redis key for storing rule states.
    affected_users_prefix : str
        Prefix for Redis keys used to store affected user data.

    Examples
    --------
    >>> redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    >>> manager = RedisTripwireManager(redis_client)
    >>> manager.apply_tripwire_if_needed('scam_message_rule', 'user_123')
    >>> manager.is_rule_disabled_via_tripwire('scam_message_rule')
    False


        tripwire:states
    -----------------
    | Field                | Value |
    -----------------
    | scam_message_rule    | 1     | -> Rule disabled
    | unique_zip_code_rule | 0     | -> Rule enabled
    | chargeback_ratio_rule| 1     |


        tripwire:affected_users:scam_message_rule
    -----------------------------------------
    | Field  | Value       |
    -----------------------------------------
    | user_1 | 1698183437  |
    | user_2 | 1698183490  |
    | user_5 | 1698183533  |


    """

    def __init__(self, redis_client: redis.StrictRedis):
        """
        Initialize the RedisTripwireManager with a dedicated Redis connection and configuration.

        Parameters
        ----------
        redis_client : redis.StrictRedis
            Redis connection used for managing tripwire states and affected users.
        """
        self.redis_client = redis_client
        self.time_window = 300  # Time window in seconds (e.g., 5 minutes)
        self.threshold = 0.05  # 5% of total users

        # Redis key names
        self.tripwire_states_key = "tripwire:states"
        self.affected_users_prefix = "tripwire:affected_users:"

    def is_rule_disabled_via_tripwire(self, rule_name: str) -> bool:
        """
        Check if a rule is disabled via the tripwire.

        Parameters
        ----------
        rule_name : str
            The name of the rule to check.

        Returns
        -------
        bool
            True if the rule is disabled, False otherwise.
        """
        disabled = self.redis_client.hget(self.tripwire_states_key, rule_name) == "1"
        logger.info(f"Rule '{rule_name}' is disabled: {disabled}")
        return disabled

    def apply_tripwire_if_needed(
        self,
        rule_name: str,
        user_id: str,
        total_users: int,
    ) -> None:
        """
        Apply tripwire logic to disable a rule if too many users are affected within a time window.

        Parameters
        ----------
        rule_name : str
            The name of the rule.
        user_id : str
            The ID of the user triggering the rule.

        Returns
        -------
        None
        """
        current_time = time.time()
        affected_users_key = f"{self.affected_users_prefix}{rule_name}"

        # Remove expired entries
        expired_users = []
        for uid, timestamp in self.redis_client.hgetall(affected_users_key).items():
            if float(timestamp) <= current_time - self.time_window:
                expired_users.append(uid)

        if expired_users:
            self.redis_client.hdel(affected_users_key, *expired_users)

        # Add or update the current user
        self.redis_client.hset(affected_users_key, user_id, current_time)

        # # Get the total number of users
        # total_users: int = self.user_manager.get_user_count()

        # Calculate the percentage of affected users
        affected_count = self.redis_client.hlen(affected_users_key)
        percentage = affected_count / total_users if total_users > 0 else 0

        # Update tripwire state based on percentage
        previously_disabled = (
            self.redis_client.hget(self.tripwire_states_key, rule_name) == "1"
        )
        if percentage >= self.threshold:
            self.redis_client.hset(self.tripwire_states_key, rule_name, "1")
            if not previously_disabled:
                logger.info(
                    f"Tripwire thrown: Rule '{rule_name}' disabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )
        else:
            self.redis_client.hset(self.tripwire_states_key, rule_name, "0")
            if previously_disabled:
                logger.info(
                    f"Tripwire disengaged: Rule '{rule_name}' re-enabled: {affected_count}/{total_users} users affected ({percentage:.2%})."
                )

    def get_disabled_rules(self) -> Dict[str, bool]:
        """
        Retrieve all rules and their disabled states from Redis.

        Returns
        -------
        Dict[str, bool]
            A dictionary with rule names as keys and their disabled states (True/False) as values.
        """

        return self.redis_client.hgetall(self.tripwire_states_key)
