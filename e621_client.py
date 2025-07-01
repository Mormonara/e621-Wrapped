import requests
import json
import time


class e621Client():
    def __init__(self, credentials_path, delay = 1):
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
            self.auth = (credentials["username"], credentials["api_key"])
            self.headers = {
                "User-Agent": credentials["user_agent"]
            }
        self.delay = delay
        self.time_since_last_request = 0.0
    

    def wait_delay(self):
        new_time = time.time()
        if new_time - self.time_since_last_request < self.delay:
            time.sleep(self.delay - new_time + self.time_since_last_request)
        self.time_since_last_request = time.time()


    def get_favorites(self, user_id, page_num):
        url = f'https://e621.net/favorites.json?limit=320&user_id={user_id}&page={page_num}'
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get favorites for {user_id} - An unexpected error occurred")
            return []
        
        if response.status_code != 200:
            print(f"Failed to get favorites for {user_id} - Status: {response.status_code}")
            return []
        
        data = response.json()
        return data['posts']
    

    def get_top_users(self, page_num):
        url = f"https://e621.net/users.json?limit=320&page={page_num}&search[order]=post_upload_count"
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get users - An unexpected error occurred")
            return[]
        
        if response.status_code != 200:
            print(f"Failed to get users - Status: {response.status_code}")
            return []
        
        return response.json()