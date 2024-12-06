import random
import string
from threading import Lock

from locust import FastHttpUser, constant_pacing, task

# Shared list for storing user IDs
user_ids = []
user_ids_lock = Lock()


def random_user_id():
    """Generate a random user ID."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


class GetTestUser(FastHttpUser):
    """
    Simulates a user making GET requests to the service.
    """

    host = "http://localhost:8000"  # Update as needed
    wait_time = constant_pacing(1 / 2000)  # 1,500 RPS per task

    @task(1)
    def check_can_message(self):
        """Simulate checking the /canmessage endpoint for existing users."""
        with user_ids_lock:
            if user_ids:
                user_id = random.choice(user_ids)
                response = self.client.get(f"/canmessage?user_id={user_id}")
                assert (
                    response.status_code == 200
                ), f"Check can_message failed: {response.json()}"

    @task(1)
    def check_can_purchase(self):
        """Simulate checking the /canpurchase endpoint for existing users."""
        with user_ids_lock:
            if user_ids:
                user_id = random.choice(user_ids)
                response = self.client.get(f"/canpurchase?user_id={user_id}")
                assert (
                    response.status_code == 200
                ), f"Check can_purchase failed: {response.json()}"
