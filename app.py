import json

import redis
from fastapi import FastAPI, HTTPException

from feature_restriction.clients import (
    RedisStreamClient,
    RedisTripwireClient,
    RedisUserClient,
)
from feature_restriction.config import (
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.endpoint_access import RedisEndpointAccess
from feature_restriction.models import Event
from feature_restriction.publisher import RedisEventPublisher
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.utils import logger

app = FastAPI()


# Instantiate and connect to each Redis client
redis_client_stream = RedisStreamClient(
    REDIS_HOST, REDIS_PORT, REDIS_DB_STREAM
).connect()
redis_client_user = RedisUserClient(REDIS_HOST, REDIS_PORT, REDIS_DB_USER).connect()

user_manager = RedisUserManager(redis_client_user)


logger.info("*********************************")
logger.info("*********************************")


@app.on_event("startup")
async def startup_event():
    """
    Perform Redis connection checks and cleanup for stream and user databases on application startup.

    Performs the following:
    - Tests connection to Redis stream and user databases.
    - Clears the Redis stream and user databases.
    - Logs the number of keys in each database after cleanup.

    Raises
    ------
    redis.ConnectionError
        If there is an issue connecting to Redis databases.
    Exception
        If an unexpected error occurs during Redis cleanup.
    """
    try:
        # Test connection to Redis stream and user databases
        redis_client_stream.ping()
        redis_client_user.ping()
        logger.info("Successfully connected to both Redis stream and user databases!")

        # Clear the stream database
        redis_client_stream.flushdb()
        logger.info("Cleared Redis stream database.")

        # Clear the user database
        redis_client_user.flushdb()
        logger.info("Cleared Redis user database.")

        # Log the number of keys in each database after cleanup
        stream_keys_count = len(redis_client_stream.keys("*"))
        user_keys_count = len(redis_client_user.keys("*"))
        logger.info(f"Number of keys in Redis stream database: {stream_keys_count}")
        logger.info(f"Number of keys in Redis user database: {user_keys_count}")

    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e

    except Exception as e:
        logger.error(f"An unexpected error occurred during Redis cleanup: {e}")
        raise e


@app.post("/event")
async def handle_event(event: Event):
    """
    Add the incoming event to the Redis stream.

    Parameters
    ----------
    event : Event
        The event data to be added to the Redis stream.

    Returns
    -------
    dict
        The response from the event publisher.

    Raises
    ------
    HTTPException
        If there is an issue with adding the event to the stream.
    """
    response = RedisEventPublisher(redis_client_stream).add_event_to_stream(event)
    return response


@app.get("/canmessage")
def can_message(user_id: str):
    """
    Check if a user has access to send/receive messages.

    Parameters
    ----------
    user_id : str
        The ID of the user.

    Returns
    -------
    dict
        The access status for messaging.

    Raises
    ------
    HTTPException
        If there is an error checking access.
    """
    endpoint_access = RedisEndpointAccess(user_manager)
    return endpoint_access.check_access(user_id, "can_message")


@app.get("/canpurchase")
def can_purchase(user_id: str):
    """
    Check if a user has access to make purchases.

    Parameters
    ----------
    user_id : str
        The ID of the user.

    Returns
    -------
    dict
        The access status for purchasing.

    Raises
    ------
    HTTPException
        If there is an error checking access.
    """
    endpoint_access = RedisEndpointAccess(user_manager)
    return endpoint_access.check_access(user_id, "can_purchase")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup Redis on app shutdown.

    Performs the following:
    - Clears the Redis user database.
    - Clears the Redis stream database.

    Raises
    ------
    Exception
        If an error occurs during Redis cleanup.
    """
    try:
        redis_client_user.flushdb()
        logger.info("Cleared Redis user database.")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")

    try:
        redis_client_stream.flushdb()
        logger.info("Cleared Redis stream database.")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")
