import random
import string

import redis
from locust import FastHttpUser, constant_pacing, task

from feature_restriction.config import REDIS_DB_LOCUST


def random_user_id():
    """Generate a random user ID."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


class PostEventsUser(FastHttpUser):
    host = "http://localhost:8000"
    wait_time = constant_pacing(1 / 2000)

    def on_start(self):
        # Initialize Redis connection
        self.redis_client = redis.StrictRedis(
            host="localhost", port=6379, db=REDIS_DB_LOCUST
        )

    @task(1)
    def send_event(self):
        """Simulate sending an event to the /event endpoint and store the user_id in Redis."""
        user_id = random_user_id()

        event_types = [
            {
                "name": "credit_card_added",
                "event_properties": {
                    "user_id": user_id,
                    "card_id": f"card_{random.randint(1, 100)}",
                    "zip_code": f"{random.randint(10000, 99999)}",
                },
            },
            {
                "name": "scam_message_flagged",
                "event_properties": {"user_id": user_id},
            },
            {
                "name": "purchase_made",
                "event_properties": {
                    "user_id": user_id,
                    "amount": round(random.uniform(10, 100), 2),
                },
            },
        ]
        event = random.choice(event_types)
        response = self.client.post("/event", json=event)

        if response.status_code == 200:
            # Store user_id in Redis set
            self.redis_client.sadd("locust_user_ids", user_id)
        else:
            print(f"Event post failed: {response.status_code}, {response.text}")
