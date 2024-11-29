# user_manager.py

from typing import Dict

from .models import UserData
from .utils import logger


class UserManager:
    """
    This class provides methods for managing user information in memory. It ensures
    that each user is only created once and allows retrieval and display of user data.

    Attributes:
        users (dict): A dictionary mapping user IDs (str) to their corresponding UserData objects.

    Methods:
        get_user(user_id: str) -> UserData:
            Retrieve a user by their ID. If the user does not exist, create a new UserData object for them.

        display_user_data(user_id: str) -> str:
            Retrieve and format all the data associated with a given user for display purposes.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        # If no instance exists, create one
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.users = {}  # Initialize the shared state
        return cls._instance

    def __init__(self):
        self.users = {}

    def get_user(self, user_id: str) -> UserData:
        """
        Retrieve a user by their ID. If the user does not already exist, create a new UserData object.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            UserData: The UserData object associated with the given user ID.
        """
        logger.info(f"Retrieving user from UserManager with id: {id(self)}")
        if user_id not in self.users:
            logger.info(f"Creating new user with ID '{user_id}'.")
            logger.info(f"Initializing UserManager with id: {id(self)}")
            self.users[user_id] = UserData(user_id)

        return self.users[user_id]

    def display_user_data(self, user_id: str):
        """
        Display all the data associated with a given user in a human-readable format.

        Args:
            user_id (str): The unique identifier for the user whose data is to be displayed.

        Returns:
            str: A formatted string containing all the user's data, or a message indicating
                 that the user ID was not found.
        """
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

    def reset(self):
        """
        Clear the state of the singleton (useful for testing).
        """
        self.users.clear()
