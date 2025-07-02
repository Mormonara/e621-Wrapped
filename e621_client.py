import requests
import json
import time
from PIL import Image
from io import BytesIO
import os


class e621Client():
    def __init__(self, credentials_path, delay = 1):
        if os.path.exists("credentials.json"):
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
                self.auth = (credentials["username"], credentials["api_key"])
                self.headers = {
                    "User-Agent": credentials["user_agent"]
                }
        else:
            print("- Running in unauthenticated mode :o to access private favorite data, please provide a credentials.json as specified in the README")
            self.auth = None
            self.headers = {
                    "User-Agent": "e621Wrapped/1.0 (by mormonara on e621)"
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


    def get_random_posts(self, min_upvotes, extra_tags):
        url = f"https://e621.net/posts.json?tags=order:random+score:>={min_upvotes}{'+' + extra_tags if len(extra_tags) > 0 else ''}"
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get posts - An unexpected error occurred")
            return []
        
        if response.status_code != 200:
            print(f"Failed to get posts - Status: {response.status_code}")
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
    

    def get_user(self, user_id):
        url = f"https://e621.net/users/{user_id}.json"
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get post - An unexpected error occurred")
            return[]
        
        if response.status_code != 200:
            print(f"Failed to get post - Status: {response.status_code}")
            return []
        
        return response.json()


    def get_post_thumb(self, post_id, side):
        url = f"https://e621.net/posts/{post_id}.json"
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get post - An unexpected error occurred")
            return[]
        
        if response.status_code != 200:
            print(f"Failed to get post - Status: {response.status_code}")
            return []
        
        data = response.json()
        url = data["post"]["file"]["url"]
        try:
            self.wait_delay()
            response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
        except:
            print(f"Failed to get post - An unexpected error occurred")
            return[]
        
        if response.status_code != 200:
            print(f"Failed to get post - Status: {response.status_code}")
            return []

        img = Image.open(BytesIO(response.content))
        l = int(min(img.size[0], img.size[1]) / 2)
        xc = int(img.size[0] / 2)
        yc = int(img.size[1] / 2)
        img = img.crop((xc - l, yc - l, xc + l, yc + l))
        img = img.resize((side, side))
        return img