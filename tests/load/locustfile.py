import random
import string

from locust import HttpUser, between, task


def random_user_id():
    """Generate a random user ID."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


class FeatureRestrictionServiceUser(HttpUser):
    """
    Simulates a user interacting with the service, sending events and requesting feature restrictions.
    """

    wait_time = between(0.01, 0.1)  # Simulate very little think time

    @task(3)  # 3x more likely to send an event than request a restriction
    def send_event(self):
        """Simulate posting a new event."""
        event_types = [
            {
                "name": "credit_card_added",
                "event_properties": {
                    "user_id": random_user_id(),
                    "card_id": f"card_{random.randint(1, 100)}",
                    "zip_code": f"{random.randint(10000, 99999)}",
                },
            },
            {
                "name": "scam_message_flagged",
                "event_properties": {"user_id": random_user_id()},
            },
            {
                "name": "purchase_made",
                "event_properties": {
                    "user_id": random_user_id(),
                    "amount": round(random.uniform(10, 100), 2),
                },
            },
        ]
        event = random.choice(event_types)
        self.client.post("/event", json=event)

    @task(1)  # Less frequent than event posting
    def check_feature_restriction(self):
        """Simulate checking a user's feature restriction."""
        user_id = random_user_id()
        endpoints = [
            f"/canmessage?user_id={user_id}",
            f"/canpurchase?user_id={user_id}",
        ]
        self.client.get(random.choice(endpoints))


# Set the host for Locust to the Docker service name
FeatureRestrictionServiceUser.host = "http://fastapi-app:8000"
