# user_store.py

from typing import Dict

from models import UserData


class UserStore:
    """
    Manages user-related data.
    """

    def __init__(self):
        self.users: Dict[str, UserData] = {}

    def get_user(self, user_id: str) -> UserData:
        """
        Retrieve a user by ID, creating one if not found.
        """
        if user_id not in self.users:
            self.users[user_id] = UserData(user_id)
        return self.users[user_id]
