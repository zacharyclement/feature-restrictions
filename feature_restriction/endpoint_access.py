from fastapi import HTTPException

from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.utils import logger


class EndpointAccess:
    """
    Handles user access logic for the 'can_message' and 'can_purchase' endpoints.
    """

    def __init__(self, redis_user_manager: RedisUserManager):
        self.redis_user_manager = redis_user_manager

    def check_access(self, user_id: str, access_key: str) -> dict:
        """
        Check user access for a given access key.

        :param user_id: The ID of the user.
        :param access_key: The key in the user's access_flags to check.
        :return: A dictionary containing the access status or an error message.
        """
        try:
            user_data = self.redis_user_manager.get_user(user_id)
            reply = user_data.access_flags.get(access_key)
            logger.info(f"User with ID '{user_id}' access '{access_key}': {reply}.")
            return {access_key: reply}
        except KeyError:
            logger.error(f"User with ID '{user_id}' not found.")
            return {"error": f"No user found with ID '{user_id}'"}
        except Exception as e:
            logger.error(f"Unexpected error in '{access_key}' check: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
