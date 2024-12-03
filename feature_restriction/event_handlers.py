from .models import Event, UserData
from .redis_user_manager import RedisUserManager
from .rules import ChargebackRatioRule, ScamMessageRule, UniqueZipCodeRule
from .tripwire_manager import TripWireManager
from .utils import logger


class BaseEventHandler:
    """
    Base class for all event handlers.
    """

    def __init__(
        self,
        tripwire_manager: TripWireManager,
        user_manager: RedisUserManager,
    ):
        self.user_manager = user_manager
        self.tripwire_manager = tripwire_manager

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the event. Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class CreditCardAddedHandler(BaseEventHandler):
    event_name = "credit_card_added"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'credit_card_added' event.
        """
        logger.info(f"Handling {self.event_name}")
        card_id = event.event_properties.get("card_id")
        zip_code = event.event_properties.get("zip_code")
        if not card_id or not zip_code:
            raise ValueError("Both 'card_id' and 'zip_code' are required.")

        # Update user data with the new credit card
        if card_id not in user_data.credit_cards:
            logger.info(f"Total credit cards before: {user_data.total_credit_cards}")
            user_data.credit_cards[card_id] = zip_code
            user_data.total_credit_cards += 1
            user_data.unique_zip_codes.add(zip_code)
            logger.info(f"Total credit cards after: {user_data.total_credit_cards}")

        # Save the updated user data back to Redis
        self.user_manager.save_user(user_data)
        logger.info(f"User data saved after event handling {self.event_name}")


class ScamMessageFlaggedHandler(BaseEventHandler):
    event_name = "scam_message_flagged"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'scam_message_flagged' event.
        """
        logger.info(f"Handling {self.event_name}")

        # Increment the scam message flag count
        user_data.scam_message_flags += 1

        # Save the updated user data back to Redis
        self.user_manager.save_user(user_data)
        logger.info(f"User data saved after event handling {self.event_name}")


class ChargebackOccurredHandler(BaseEventHandler):
    event_name = "chargeback_occurred"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'chargeback_occurred' event.
        """
        logger.info(f"Handling {self.event_name}")
        amount = event.event_properties.get("amount")
        if amount is None:
            raise ValueError("'amount' is required.")

        # Update the user's total chargebacks
        user_data.total_chargebacks += amount

        # Save the updated user data back to Redis
        self.user_manager.save_user(user_data)
        logger.info(f"User data saved after event handling {self.event_name}")


class PurchaseMadeHandler(BaseEventHandler):
    event_name = "purchase_made"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'purchase_made' event.
        """
        logger.info(f"Handling {self.event_name}")

        # Get the purchase amount from the event
        amount = event.event_properties.get("amount")
        if amount is None:
            raise ValueError("'amount' is required.")

        # Update the user's total spend
        logger.info(f"Total spend before: {user_data.total_spend}")
        user_data.total_spend += amount
        logger.info(f"Total spend after: {user_data.total_spend}")

        # Save the updated user data back to Redis
        self.user_manager.save_user(user_data)
        logger.info(f"User data saved after event handling {self.event_name}")
