import logging
import time
from queue import Queue

import redis
from fastapi import FastAPI, HTTPException

from feature_restriction.event_consumer import EventConsumer
from feature_restriction.models import Event
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.utils import logger

# Instantiate FastAPI app
app = FastAPI()

# Global Redis connection
redis_client = None

logger.info("****************************************")
logger.info("****************************************")

# Global setup for event queue
event_queue = Queue()

# Instantiate and start the EventConsumer
# The RedisUserManager and TripWireManager are initialized inside EventConsumer
event_consumer = EventConsumer(event_queue)


@app.on_event("startup")
def start_consumer():
    """
    Start the event consumer thread when the application starts.
    """
    event_consumer.start()

    global redis_client

    try:
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        # Test the connection
        redis_client.ping()
        logger.info("Connected to Redis successfully!")
        # Count the number of keys (users) in Redis
        redis_client.flushdb()
        user_count = len(redis_client.keys("*"))
        logger.info(f"Number of users currently in Redis: {user_count}")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e


@app.post("/event")
async def handle_event(event: Event):
    """
    Endpoint to handle incoming events and enqueue them for processing.
    """
    logger.info(f"************* Received event: {event}")

    # Enqueue the event for processing
    event_queue.put(event)

    return {"status": "Event enqueued for processing."}


@app.get("/canmessage")
def can_message(user_id: str):
    """
    Endpoint to check if a user has access to send/receive messages.
    """
    logger.info(f"************* can message, user_id: {user_id}")

    redis_user_manager = RedisUserManager()
    user_data = redis_user_manager.get_user(user_id)

    logger.info(f"user data: {user_data}")
    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_message": user_data.access_flags.get("can_message", True)}


@app.get("/canpurchase")
def can_purchase(user_id: str):
    """
    Endpoint to check if a user has access to bid/purchase.
    """
    redis_user_manager = RedisUserManager()
    user_id = str(user_id)
    logger.info(f"************* can purchase, user_id: {user_id}")
    user_data = redis_user_manager.get_user(user_id)

    logger.info(f"user data: {user_data}")

    if not user_data:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{user_id}' not found."
        )
    return {"can_purchase": user_data.access_flags.get("can_purchase", True)}


@app.on_event("shutdown")
async def shutdown():
    """
    Clean up resources during application shutdown.
    """
    logger.info("Shutting down FastAPI app.")

    global redis_client

    try:
        logger.info("Clearing Redis keys...")
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        redis_client.flushdb()  # Clears the Redis database
        logger.info("Disconnected from Redis.")
        redis_client.close()
    except Exception as e:
        logger.error(f"Error during redis shutdown: {e}")

    # Stop the consumer
    if event_consumer:
        logger.info("Stopping event consumer.")
        event_consumer.stop()
        # Wait for the thread to finish
        time.sleep(1)
        logger.info("Event consumer stopped.")
