from abc import ABC, abstractmethod

from fastapi import HTTPException

from feature_restriction.redis_user_manager import RedisUserManager, UserManager
from feature_restriction.utils import logger


class EndpointAccess:
    @abstractmethod
    def check_access(self, user_id: str, access_key: str) -> dict:
        """Check user access for a given feature or endpoint."""


class RedisEndpointAccess(EndpointAccess):
    """
    Handles user access logic for the 'can_message' and 'can_purchase' endpoints.

    This class interacts with the `RedisUserManager` to verify whether a user
    has access to specific features based on access flags stored in the Redis database.

    Attributes
    ----------
    redis_user_manager : RedisUserManager
        An instance of the RedisUserManager used to interact with the Redis database.

    Methods
    -------
    check_access(user_id, access_key)
        Checks whether a user has access to a specific feature based on their access flags.
    """

    def __init__(self, redis_user_manager: UserManager):
        """
        Initialize the RedisEndpointAccess class.

        Parameters
        ----------
        redis_user_manager : RedisUserManager
            An instance of RedisUserManager for interacting with user data in Redis.
        """
        self.redis_user_manager = redis_user_manager

    def check_access(self, user_id: str, access_key: str) -> dict:
        """
        Check user access for a given feature or endpoint.

        This method retrieves the user's data from the Redis database using the
        `RedisUserManager` and checks if the specified `access_key` exists in the
        user's `access_flags`. If the user is not found or an unexpected error occurs,
        appropriate logging and error handling are performed.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user.
        access_key : str
            The access flag key to check (e.g., 'can_message', 'can_purchase').

        Returns
        -------
        dict
            A dictionary containing the access status for the specified key.
            For example:
            - If successful: {"can_message": True}
            - If user not found: {"error": "No user found with ID '<user_id>'"}
            - On unexpected error: Raises HTTPException with a 500 status code.

        Raises
        ------
        HTTPException
            If an unexpected error occurs during the access check.

        Notes
        -----
        - Logging is used to track successful and failed access attempts.
        - Errors such as missing users or unexpected issues are logged appropriately.
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
