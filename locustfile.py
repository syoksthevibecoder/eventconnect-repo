from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    @task
    def index_page(self):
        self.client.get("/")
    
    @task(3)  # This task is 3x more likely to be executed
    def about_page(self):
        self.client.get("/about")
    
    def on_start(self):
        # Called when a user starts
        self.client.post("/login", json={"username":"test", "password":"test"})