from .models import Event, UserData
from .redis_user_manager import RedisUserManager
from .utils import logger


class BaseEventHandler:
    """
    Base class for all event handlers.

    Attributes
    ----------
    user_manager : RedisUserManager
        Manager for handling user data in Redis.

    """

    def __init__(
        self,
        user_manager: RedisUserManager,
    ):
        """
        Initialize the BaseEventHandler.

        Parameters
        ----------

        user_manager : RedisUserManager
            Instance of the user manager for interacting with Redis.
        """
        self.user_manager = user_manager

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the event. Must be overridden by subclasses.

        Parameters
        ----------
        event : Event
            The event to be handled.
        user_data : UserData
            The user data associated with the event.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by the subclass.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class CreditCardAddedHandler(BaseEventHandler):
    """
    Handler for the 'credit_card_added' event.
    """

    event_name = "credit_card_added"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'credit_card_added' event.

        Parameters
        ----------
        event : Event
            The event to be handled, containing event properties.
        user_data : UserData
            The user data associated with the event.

        Raises
        ------
        ValueError
            If required properties 'card_id' or 'zip_code' are missing.
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
    """
    Handler for the 'scam_message_flagged' event.
    """

    event_name = "scam_message_flagged"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'scam_message_flagged' event.

        Parameters
        ----------
        event : Event
            The event to be handled, containing event properties.
        user_data : UserData
            The user data associated with the event.
        """
        logger.info(f"Handling {self.event_name}")

        # Increment the scam message flag count
        user_data.scam_message_flags += 1

        # Save the updated user data back to Redis
        self.user_manager.save_user(user_data)
        logger.info(f"User data saved after event handling {self.event_name}")


class ChargebackOccurredHandler(BaseEventHandler):
    """
    Handler for the 'chargeback_occurred' event.
    """

    event_name = "chargeback_occurred"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'chargeback_occurred' event.

        Parameters
        ----------
        event : Event
            The event to be handled, containing event properties.
        user_data : UserData
            The user data associated with the event.

        Raises
        ------
        ValueError
            If the required property 'amount' is missing.
        """
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
    """
    Handler for the 'purchase_made' event.
    """

    event_name = "purchase_made"

    def handle(self, event: Event, user_data: UserData):
        """
        Handle the 'purchase_made' event.

        Parameters
        ----------
        event : Event
            The event to be handled, containing event properties.
        user_data : UserData
            The user data associated with the event.

        Raises
        ------
        ValueError
            If the required property 'amount' is missing.
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
