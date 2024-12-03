import random
import time

import requests


class EventPoster:
    def __init__(self, base_url):
        """
        Initialize the EventPoster with the base URL of the FastAPI app.
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


if __name__ == "__main__":
    # Initialize the event poster with the base URL of your FastAPI app
    base_url = "http://127.0.0.1:8000"
    poster = EventPoster(base_url)

    # Example user IDs
    user_ids = [str(i) for i in range(1, 2)]

    # Send multiple events for testing
    for user_id in user_ids:
        # Send a 'scam_message_flagged' event
        poster.send_event("scam_message_flagged", {"user_id": user_id})
        time.sleep(1)

        # Send a 'credit_card_added' event
        poster.send_event(
            "credit_card_added",
            {
                "user_id": user_id,
                "card_id": f"card_{random.randint(1, 100)}",
                "zip_code": f"{random.randint(10000, 99999)}",
            },
        )
        time.sleep(1)

        # Send a 'purchase_made' event
        poster.send_event(
            "purchase_made",
            {"user_id": user_id, "amount": round(random.uniform(100.0, 500.0), 2)},
        )
        time.sleep(1)

        # Send a 'chargeback_occurred' event
        poster.send_event(
            "chargeback_occurred",
            {"user_id": user_id, "amount": round(random.uniform(10.0, 100.0), 2)},
        )
        time.sleep(1)
