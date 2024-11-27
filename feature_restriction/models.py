# model.py

from typing import Any, Dict, Set

from pydantic import BaseModel


class Event(BaseModel):
    name: str
    event_properties: Dict[str, Any]


class UserData:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.scam_message_flags = 0
        self.credit_cards: Dict[str, str] = {}  # card_id -> zip_code
        self.total_credit_cards = 0
        self.unique_zip_codes: Set[str] = set()
        self.total_spend = 0.0
        self.total_chargebacks = 0.0
        self.access_flags = {"can_message": True, "can_purchase": True}
        self.last_login_time = None  # Example additional property
