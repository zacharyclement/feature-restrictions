# model.py

from typing import Any, Dict, Set

from pydantic import BaseModel


class Event(BaseModel):
    name: str
    event_properties: Dict[str, Any]


from typing import Dict, Optional, Set

from pydantic import BaseModel


class UserData(BaseModel):
    user_id: str
    scam_message_flags: int = 0
    credit_cards: Dict[str, str] = {}  # card_id -> zip_code
    total_credit_cards: int = 0
    unique_zip_codes: Set[str] = set()
    total_spend: float = 0.0
    total_chargebacks: float = 0.0
    access_flags: Dict[str, bool] = {"can_message": True, "can_purchase": True}
