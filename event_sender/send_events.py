import random

import requests


class EventSender:
    def __init__(self, base_url):
        """
        Initialize the EventSender with the base URL of the FastAPI app.
        :param base_url: Base URL of the FastAPI app (e.g., "http://127.0.0.1:8000").
        """
        self.base_url = base_url

    def send_event(self, event_name, event_properties):
        """
        Send an event to the /event endpoint.
        :param event_name: Name of the event (e.g., "scam_message_flagged").
        :param event_properties: Dictionary of event properties (e.g., {"user_id": "user123"}).
        """
        url = f"{self.base_url}/event"
        payload = {"name": event_name, "event_properties": event_properties}
        try:
            response = requests.post(url, json=payload)
            print(
                f"Event: {event_name}, Response: {response.status_code}, {response.json()}"
            )
        except requests.exceptions.RequestException as e:
            print(f"Error sending event: {e}")

    def check_can_message(self, user_id):
        """
        Check if a user can send/receive messages.
        :param user_id: User ID to check.
        """
        url = f"{self.base_url}/canmessage"
        params = {"user_id": user_id}
        try:
            response = requests.get(url, params=params)
            print(
                f"Check Can Message for User '{user_id}': Response: {response.status_code}, {response.json()}"
            )
        except requests.exceptions.RequestException as e:
            print(f"Error checking can_message: {e}")

    def check_can_purchase(self, user_id):
        """
        Check if a user can bid/purchase.
        :param user_id: User ID to check.
        """
        url = f"{self.base_url}/canpurchase"
        params = {"user_id": user_id}
        try:
            response = requests.get(url, params=params)
            print(
                f"Check Can Purchase for User '{user_id}': Response: {response.status_code}, {response.json()}"
            )
        except requests.exceptions.RequestException as e:
            print(f"Error checking can_purchase: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize the event sender with the base URL of your FastAPI app
    base_url = "http://127.0.0.1:8000"
    sender = EventSender(base_url)

    # Example user IDs
    user_ids = [i for i in range(1, 2)]

    # Send multiple events for testing
    for user_id in user_ids:
        # Send a 'scam_message_flagged' event
        sender.send_event("scam_message_flagged", {"user_id": user_id})

        # Send a 'credit_card_added' event
        sender.send_event(
            "credit_card_added",
            {
                "user_id": user_id,
                "card_id": f"card_{random.randint(1, 100)}",
                "zip_code": f"{random.randint(10000, 99999)}",
            },
        )

        # Send a 'chargeback_occurred' event
        sender.send_event(
            "chargeback_occurred",
            {"user_id": user_id, "amount": round(random.uniform(10.0, 500.0), 2)},
        )

        # Send a 'purchase_made' event
        sender.send_event(
            "purchase_made",
            {"user_id": user_id, "amount": round(random.uniform(10.0, 500.0), 2)},
        )

        # Check if the user can send/receive messages
        sender.check_can_message(user_id)

        # Check if the user can bid/purchase
        sender.check_can_purchase(user_id)
