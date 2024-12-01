import random
import string
from threading import Lock

from locust import FastHttpUser, HttpUser, constant_pacing, task

# Shared list for storing user IDs
user_ids = []
user_ids_lock = Lock()


def random_user_id():
    """Generate a random user ID."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


class FeatureRestrictionServiceUser(FastHttpUser):
    """
    Simulates a single user interacting with the service.
    """

    wait_time = constant_pacing(1 / 2000)  # 1,500 RPS per task

    @task(1)  # Task for sending events
    def send_event(self):
        """
        Simulate sending an event to the /event endpoint.
        """
        # Generate a random user ID and store it
        user_id = random_user_id()
        with user_ids_lock:
            user_ids.append(user_id)

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
        self.client.post("/event", json=event)

    @task(1)  # Task for /canmessage
    def check_can_message(self):
        """
        Simulate checking the /canmessage endpoint for existing users.
        """
        with user_ids_lock:
            if user_ids:
                user_id = random.choice(user_ids)  # Use an existing user ID
                self.client.get(f"/canmessage?user_id={user_id}")

    @task(1)  # Task for /canpurchase
    def check_can_purchase(self):
        """
        Simulate checking the /canpurchase endpoint for existing users.
        """
        with user_ids_lock:
            if user_ids:
                user_id = random.choice(user_ids)  # Use an existing user ID
                self.client.get(f"/canpurchase?user_id={user_id}")
