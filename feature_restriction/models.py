# model.py

from typing import Any, Dict, Optional, Set

from pydantic import BaseModel


class Event(BaseModel):
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
    user_id: str
    scam_message_flags: int = 0
    credit_cards: Dict[str, str] = {}  # card_id -> zip_code
    total_credit_cards: int = 0
    unique_zip_codes: Set[str] = set()
    total_spend: float = 0.0
    total_chargebacks: float = 0.0
    access_flags: Dict[str, bool] = {"can_message": True, "can_purchase": True}
