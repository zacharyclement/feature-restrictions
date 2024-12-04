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


redis_client_tripwire = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_TRIPWIRE, decode_responses=True
)


# Logger setup
logger.info("*********************************")
logger.info("*********************************")


@app.on_event("startup")
async def startup_event():
    """
    Test Redis connection and log details on startup.
    """
    try:
        redis_client_stream.ping()
        logger.info("Connected to Redis stream successfully!")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
    try:
        redis_client_user.flushdb()
        logger.info("Cleared Redis user database.")
        user_count = len(redis_client_user.keys("*"))
        logger.info(f"Number of users currently in Redis: {user_count}")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")

    try:
        redis_client_tripwire.flushdb()
        logger.info("Cleared Redis tripwire database.")
        tripwire_count = len(redis_client_tripwire.keys("*"))
        logger.info(f"Number of tripwires currently in Redis: {tripwire_count}")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")


@app.post("/event")
async def handle_event(event: Event):
    """
    Add the incoming event to the Redis stream.
    """
    response = EventPublisher().add_event_to_stream(event)
    return response


@app.get("/canmessage")
def can_message(user_id: str):
    """
    Check if a user has access to send/receive messages.
    """
    endpoint_access = EndpointAccess()
    return endpoint_access.check_access(user_id, "can_message")


@app.get("/canpurchase")
def can_purchase(user_id: str):
    """
    Check if a user has access to make purchases.
    """
    endpoint_access = EndpointAccess()
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
        redis_client_tripwire.flushdb()
        logger.info("Cleared Redis tripwire database.")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")
