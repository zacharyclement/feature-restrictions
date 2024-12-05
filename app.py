import json

import redis
from fastapi import FastAPI, HTTPException

from feature_restriction.config import (
    REDIS_DB_STREAM,
    REDIS_DB_TRIPWIRE,
    REDIS_DB_USER,
    REDIS_HOST,
    REDIS_PORT,
)
from feature_restriction.endpoint_access import EndpointAccess
from feature_restriction.models import Event
from feature_restriction.publisher import EventPublisher
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.utils import logger

# Initialize FastAPI app
app = FastAPI()

# Redis stream client, for testing connection on start
redis_client_stream = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STREAM, decode_responses=True
)

# Needs user access to delete all users on shutdown
redis_client_user = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_USER, decode_responses=True
)
user_manager = RedisUserManager(redis_client_user)


redis_client_tripwire = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_TRIPWIRE, decode_responses=True
)


# Logger setup
logger.info("*********************************")
logger.info("*********************************")


@app.on_event("startup")
async def startup_event():
    """
    Perform Redis connection checks and cleanup for stream and user databases on application startup.
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
    """
    response = EventPublisher(redis_client_stream).add_event_to_stream(event)
    return response


@app.get("/canmessage")
def can_message(user_id: str):
    """
    Check if a user has access to send/receive messages.
    """
    endpoint_access = EndpointAccess(user_manager)
    return endpoint_access.check_access(user_id, "can_message")


@app.get("/canpurchase")
def can_purchase(user_id: str):
    """
    Check if a user has access to make purchases.
    """
    endpoint_access = EndpointAccess(user_manager)
    return endpoint_access.check_access(user_id, "can_purchase")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup Redis on app shutdown.
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
