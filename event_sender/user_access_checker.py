import requests


class UserAccessChecker:
    def __init__(self, base_url):
        """
        Initialize the UserAccessChecker with the base URL of the FastAPI app.
        :param base_url: Base URL of the FastAPI app (e.g., "http://127.0.0.1:8000").
        """
        self.base_url = base_url

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


if __name__ == "__main__":
    # Initialize the user access checker with the base URL of your FastAPI app
    base_url = "http://127.0.0.1:8000"
    checker = UserAccessChecker(base_url)

    # Example user IDs
    user_ids = [str(i) for i in range(1, 2)]

    # Check access for each user
    for user_id in user_ids:
        checker.check_can_message(user_id)
        checker.check_can_purchase(user_id)
