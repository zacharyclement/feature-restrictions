# rules.py

from abc import ABC, abstractmethod

from models import Event, UserData
from rule_state_store import RuleStateStore
from user_store import UserStore

# rules.py


class BaseRule(ABC):
    """
    Abstract base class for all rules.
    """

    name: str  # Unique identifier for the rule

    def __init__(self, rule_state_store: RuleStateStore, user_store: UserStore):
        self.rule_state_store = rule_state_store
        self.user_store = user_store

    def process(self, user_data: UserData, event: Event):
        """
        Process the rule:
        - Check if the rule is disabled.
        - Evaluate the rule.
        - Update tripwires and take actions if the rule condition is met.
        """
        if self.rule_state_store.is_rule_disabled(self.name):
            return False  # Rule is disabled, no action taken

        # Evaluate the rule
        condition_met = self.evaluate(user_data, event)

        if condition_met:
            # Apply action
            self.apply_action(user_data)
            # Update affected users for tripwire logic
            total_users = len(self.user_store.users)
            self.rule_state_store.update_affected_users(
                self.name, user_data.user_id, total_users
            )
        return condition_met

    @abstractmethod
    def evaluate(self, user_data: UserData, event: Event) -> bool:
        """
        Evaluate the rule based on user data and event.
        """
        pass

    @abstractmethod
    def apply_action(self, user_data: UserData):
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
        card_id = event.event_properties.get("card_id")
        zip_code = event.event_properties.get("zip_code")
        if not card_id or not zip_code:
            raise ValueError("Both 'card_id' and 'zip_code' are required.")

        # Simulate adding the new card
        temp_total_credit_cards = user_data.total_credit_cards
        temp_unique_zip_codes = user_data.unique_zip_codes.copy()

        if card_id not in user_data.credit_cards:
            temp_total_credit_cards += 1
            temp_unique_zip_codes.add(zip_code)

        ratio = (
            len(temp_unique_zip_codes) / temp_total_credit_cards
            if temp_total_credit_cards > 0
            else 0
        )

        return ratio > 0.75

    def apply_action(self, user_data: UserData):
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

    def apply_action(self, user_data: UserData):
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
        amount = event.event_properties.get("amount")
        if amount is None:
            raise ValueError("'amount' is required.")

        temp_total_spend = user_data.total_spend
        temp_total_chargebacks = user_data.total_chargebacks

        if event.name == "purchase_made":
            temp_total_spend += amount
        elif event.name == "chargeback_occurred":
            temp_total_chargebacks += amount

        ratio = temp_total_chargebacks / temp_total_spend if temp_total_spend > 0 else 0

        return ratio > 0.10

    def apply_action(self, user_data: UserData):
        """
        Disable the 'can_purchase' flag if the rule condition is met.
        """
        user_data.access_flags["can_purchase"] = False
