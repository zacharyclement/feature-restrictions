# user_store.py

from threading import Lock
from typing import Dict

from models import UserData
from utils import logger


class UserStore:
    """
    Thread-safe Singleton class for managing user-related data.
    """

    _instance = None
    _lock = Lock()  # Ensure thread safety during instantiation

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  # Only one thread can access this block at a time
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
                    cls._instance._initialize()
        logger.info(f"UserStore instance created: {id(cls._instance)}")
        return cls._instance

    def _initialize(self):
        self.users = {}

    def get_user(self, user_id: str) -> UserData:
        logger.info(f"UserStore contents before retrieval: {self.users}")
        if user_id not in self.users:
            logger.info(f"Creating new user with ID '{user_id}'.")
            self.users[user_id] = UserData(user_id)
        logger.info(f"UserStore contents after retrieval: {self.users}")
        logger.info(f"UserData object ID: {id(self.users[user_id])}")
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
