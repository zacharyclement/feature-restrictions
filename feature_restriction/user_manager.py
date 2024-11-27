# user_manager.py

from typing import Dict

from .models import UserData
from .utils import logger


class UserManager:
    """
    Thread-safe Singleton class for managing user-related data.
    """

    def __init__(self):
        self.users = {}

    def get_user(self, user_id: str) -> UserData:
        if user_id not in self.users:
            logger.info(f"Creating new user with ID '{user_id}'.")
            self.users[user_id] = UserData(user_id)
        return self.users[user_id]

    def display_user_data(self, user_id: str):
        if user_id not in self.users:
            return f"User with ID '{user_id}' not found."
        user_data = self.users[user_id]
        return (
            f"User ID: {user_data.user_id}\n"
            f"Scam Message Flags: {user_data.scam_message_flags}\n"
            f"Credit Cards: {user_data.credit_cards}\n"
            f"Total Credit Cards: {user_data.total_credit_cards}\n"
            f"Unique Zip Codes: {user_data.unique_zip_codes}\n"
            f"Total Spend: {user_data.total_spend}\n"
            f"Total Chargebacks: {user_data.total_chargebacks}\n"
            f"Access Flags: {user_data.access_flags}\n"
            f"Last Login Time: {user_data.last_login_time}"
        )
