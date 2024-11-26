from models import Event, UserData
from rule_state_store import RuleStateStore
from rules import ChargebackRatioRule, ScamMessageRule, UniqueZipCodeRule
from user_store import UserStore


class BaseEventHandler:
    """
    Base class for all event handlers.
    """

    def __init__(
        self,
        rule_state_store: RuleStateStore,
        user_store: UserStore,
    ):
        self.user_store = user_store
        self.rule_state_store = rule_state_store

    async def handle(self, event: Event, user_data: UserData):
        """
        Handle the event. Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class CreditCardAddedHandler(BaseEventHandler):
    event_name = "credit_card_added"

    async def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'credit_card_added' event.
        """
        card_id = event.event_properties.get("card_id")
        zip_code = event.event_properties.get("zip_code")
        if not card_id or not zip_code:
            raise ValueError("Both 'card_id' and 'zip_code' are required.")

        # Update user data with the new credit card
        if card_id not in user_data.credit_cards:
            user_data.credit_cards[card_id] = zip_code
            user_data.total_credit_cards += 1
            user_data.unique_zip_codes.add(zip_code)

        # Instantiate and process the rule
        unique_zip_code_rule = UniqueZipCodeRule(self.rule_state_store, self.user_store)
        unique_zip_code_rule.process(user_data, event)


class ScamMessageFlaggedHandler(BaseEventHandler):
    event_name = "scam_message_flagged"

    async def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'scam_message_flagged' event.
        """
        # Increment the scam message flag count
        user_data.scam_message_flags += 1

        # Instantiate and process the rule
        scam_message_rule = ScamMessageRule(self.rule_state_store, self.user_store)
        scam_message_rule.process(user_data, event)


class ChargebackOccurredHandler(BaseEventHandler):
    event_name = "chargeback_occurred"

    async def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'chargeback_occurred' event.
        """
        amount = event.event_properties.get("amount")
        if amount is None:
            raise ValueError("'amount' is required.")

        # Update the user's total chargebacks
        user_data.total_chargebacks += amount

        # Instantiate and process the rule
        chargeback_ratio_rule = ChargebackRatioRule(
            self.rule_state_store, self.user_store
        )
        chargeback_ratio_rule.process(user_data, event)
