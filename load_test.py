from locust import HttpUser, TaskSet, between, task


class UserBehavior(TaskSet):
    @task(1)
    def send_event(self):
        self.client.post(
            "/event",
            json={
                "name": "purchase_made",
                "event_properties": {"user_id": "load_test_user", "amount": 100},
            },
        )

    @task(1)
    def check_can_purchase(self):
        self.client.get("/canpurchase", params={"user_id": "load_test_user"})


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 2)
