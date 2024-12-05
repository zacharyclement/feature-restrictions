import redis

from .config import REDIS_DB_USER, REDIS_HOST, REDIS_PORT
from .models import UserData
from .utils import logger


class RedisUserManager:
    """
    A manager for handling user data stored in a Redis database.
    """

    def __init__(self, redis_client):
        """
        Initialize the RedisUserManager with a Redis connection.
        """
        self.redis_client = redis_client

    def get_user(self, user_id: str) -> UserData:
        """
        Retrieve an existing user by their ID.

        :param user_id: The unique ID of the user to retrieve.
        :return: A UserData object representing the user's data.
        :raises KeyError: If the user does not exist.
        """
        try:
            user_data_json = self.redis_client.get(user_id)
            if user_data_json:
                logger.info(f"Retrieved existing user with ID '{user_id}'.")
                return UserData.parse_raw(user_data_json)
            else:
                raise KeyError(f"User ID '{user_id}' not found.")
        except Exception as e:
            logger.warning(f"Error in get_user for user_id '{user_id}': {e}")
            raise

    def create_user(self, user_id: str) -> UserData:
        """
        Create a new user with default values.

        :param user_id: The unique ID of the user to create.
        :return: A UserData object representing the newly created user's data.
        """
        try:
            default_user = UserData(user_id=user_id)
            self.save_user(default_user)
            return default_user
        except Exception as e:
            logger.error(f"Error in create_user for user_id '{user_id}': {e}")
            raise

    def save_user(self, user_data: UserData):
        """
        Save a UserData object to Redis.

        :param user_data: The UserData object to save.
        """
        try:
            self.redis_client.set(user_data.user_id, user_data.json())
            logger.info(f"User ID '{user_data.user_id}' saved to Redis.")
        except Exception as e:
            logger.error(f"Error saving user with ID '{user_data.user_id}': {e}")
            raise

    def delete_user(self, user_id: str):
        """
        Delete a user from Redis.

        :param user_id: The unique ID of the user to delete.
        """
        try:
            self.redis_client.delete(user_id)
            logger.info(f"User ID '{user_id}' deleted from Redis.")
        except Exception as e:
            logger.error(f"Error deleting user with ID '{user_id}': {e}")
            raise

    def get_user_count(self) -> int:
        """
        Get the total number of users in the Redis store.

        :return: The number of users currently stored in Redis.
        """
        try:
            keys = self.redis_client.keys("*")
            count = len(keys)
            logger.info(f"Total number of users in Redis: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0

    def clear_all_users(self):
        """
        Clear all user data from the Redis store.
        """
        try:
            keys = self.redis_client.keys("*")
            if keys:
                self.redis_client.delete(*keys)
            logger.info("All user data cleared from Redis.")
        except Exception as e:
            logger.error(f"Error clearing all user data from Redis: {e}")
            raise

    def display_user_data(self, user_id: str, user_data: UserData = None) -> str:
        """
        Display all the data associated with a given user in a human-readable format.

        :param user_id: The unique identifier for the user whose data is to be displayed.
        :param user_data: Optional pre-fetched UserData object to avoid redundant lookups.
        :return: A formatted string containing all the user's data or a message if the user is not found.
        """
        try:
            if not user_data:
                user_data = self.get_user(user_id)  # Only fetch if not provided

            return (
                f"User ID: {user_data.user_id}\n"
                f"Scam Message Flags: {user_data.scam_message_flags}\n"
                f"Credit Cards: {user_data.credit_cards}\n"
                f"Total Credit Cards: {user_data.total_credit_cards}\n"
                f"Unique Zip Codes: {user_data.unique_zip_codes}\n"
                f"Total Spend: {user_data.total_spend}\n"
                f"Total Chargebacks: {user_data.total_chargebacks}\n"
                f"Access Flags: {user_data.access_flags}\n"
            )
        except KeyError:
            return f"User ID '{user_id}' not found."
        except Exception as e:
            logger.error(f"Error displaying data for user_id '{user_id}': {e}")
            return f"Error displaying data for user_id '{user_id}'."
