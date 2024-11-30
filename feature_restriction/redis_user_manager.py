import redis

from .models import UserData
from .utils import logger


class RedisUserManager:
    """
    A manager for handling user data stored in a Redis database.
    """

    def __init__(self, redis_host="localhost", redis_port=6379, db=0):
        """
        Initialize the RedisUserManager with a Redis connection.

        :param redis_host: The Redis server hostname.
        :param redis_port: The Redis server port.
        :param db: The Redis database index.
        """
        self.redis_client = redis.StrictRedis(
            host=redis_host, port=redis_port, db=db, decode_responses=True
        )
        logger.info(f"user count in redis: {self.get_user_count}")

    def get_user(self, user_id: str) -> UserData:
        """
        Retrieve a user by their ID. If the user does not exist, initialize with default values.

        :param user_id: The unique ID of the user to retrieve.
        :return: A UserData object representing the user's data.
        """
        try:
            user_data_json = self.redis_client.get(user_id)
            if user_data_json:
                # Use Pydantic's parse_raw to create a UserData object from JSON
                logger.info(f"Retrieved existing user with ID '{user_id}'.")
                return UserData.parse_raw(user_data_json)

            # If user doesn't exist, create a default UserData object
            logger.info(f"User ID '{user_id}' not found. Creating new user.")
            default_user = UserData(user_id=user_id)
            self.save_user(default_user)
            logger.info(f"New user with ID '{user_id}' created and saved.")
            return default_user
        except Exception as e:
            logger.error(f"Error in get_user for user_id '{user_id}': {e}")
            raise

    def save_user(self, user_data: UserData):
        """
        Save a UserData object to Redis.

        :param user_data: The UserData object to save.
        """
        try:
            # Use Pydantic's json() to serialize the UserData object
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

    def display_user_data(self, user_id: str) -> str:
        """
        Display all the data associated with a given user in a human-readable format.

        :param user_id: The unique identifier for the user whose data is to be displayed.
        :return: A formatted string containing all the user's data or a message if the user is not found.
        """
        try:
            user_data = self.get_user(user_id)
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
        except Exception as e:
            logger.error(f"Error displaying data for user_id '{user_id}': {e}")
            return f"Error displaying data for user_id '{user_id}'."
