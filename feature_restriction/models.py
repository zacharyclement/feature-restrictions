# model.py

from typing import Any, Dict, Optional, Set

from pydantic import BaseModel


class Event(BaseModel):
    """
    Represents an event with a name and associated properties.

    Attributes
    ----------
    name : str
        The name of the event.
    event_properties : Dict[str, Any]
        A dictionary containing the properties of the event.

    Methods
    -------
    user_id
        Extracts and validates the user ID from the event properties.
    """

    name: str
    event_properties: Dict[str, Any]

    @property
    def user_id(self) -> str:
        """
        Extracts and validates the user_id from event_properties.
        """
        user_id = self.event_properties.get("user_id")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Event is missing a valid 'user_id' in event_properties")
        return user_id


class UserData(BaseModel):
    """
    Represents a user's data, including flags, credit cards, and transaction metrics.

    Attributes
    ----------
    user_id : str
        The unique identifier for the user.
    scam_message_flags : int, optional
        The number of flagged scam messages (default is 0).
    credit_cards : Dict[str, str], optional
        A dictionary mapping card IDs to zip codes (default is an empty dictionary).
    total_credit_cards : int, optional
        The total number of credit cards (default is 0).
    unique_zip_codes : Set[str], optional
        A set of unique zip codes associated with the user's credit cards (default is an empty set).
    total_spend : float, optional
        The total amount spent by the user (default is 0.0).
    total_chargebacks : float, optional
        The total amount of chargebacks issued by the user (default is 0.0).
    access_flags : Dict[str, bool], optional
        A dictionary indicating access flags for user actions, such as "can_message" and "can_purchase"
        (default is {"can_message": True, "can_purchase": True}).
    """

    user_id: str
    scam_message_flags: int = 0
    credit_cards: Dict[str, str] = {}  # card_id -> zip_code
    total_credit_cards: int = 0
    unique_zip_codes: Set[str] = set()
    total_spend: float = 0.0
    total_chargebacks: float = 0.0
    access_flags: Dict[str, bool] = {"can_message": True, "can_purchase": True}
