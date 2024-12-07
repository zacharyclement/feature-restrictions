import random

import redis
from locust import FastHttpUser, constant_pacing, task

from feature_restriction.config import REDIS_DB_LOCUST


class GetEventsUser(FastHttpUser):
    host = "http://localhost:8000"
    wait_time = constant_pacing(1 / 2000)

    def on_start(self):
        # Initialize Redis connection
        self.redis_client = redis.StrictRedis(
            host="localhost", port=6379, db=REDIS_DB_LOCUST
        )

    @task(1)
    def check_can_message(self):
        """Simulate checking the /canmessage endpoint for existing users from Redis."""
        user_id = self._get_random_user_id()
        if user_id is not None:
            response = self.client.get(f"/canmessage?user_id={user_id}")
            assert (
                response.status_code == 200
            ), f"Check can_message failed: {response.text}"

    @task(1)
    def check_can_purchase(self):
        """Simulate checking the /canpurchase endpoint for existing users from Redis."""
        user_id = self._get_random_user_id()
        if user_id is not None:
            response = self.client.get(f"/canpurchase?user_id={user_id}")
            assert (
                response.status_code == 200
            ), f"Check can_purchase failed: {response.text}"

    def _get_random_user_id(self):
        # Use SRANDMEMBER to get a random user_id from the Redis set
        user_id = self.redis_client.srandmember("locust_user_ids")
        return user_id.decode("utf-8") if user_id else None
