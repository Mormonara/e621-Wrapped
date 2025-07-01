from e621_client import e621Client
from argparse import ArgumentParser
import json
from tqdm.auto import tqdm


def get_user_interests(favs):
    user_interests = {}
    for fav in favs:
        for topic in fav["tags"]:
            for tag in fav["tags"][topic]:
                tag_name = f"{topic}:{tag}"
                if not tag_name in user_interests:
                    user_interests[tag_name] = 0
                user_interests[tag_name] += 1
    
    for tag in user_interests:
        user_interests[tag] /= len(favs)
    
    return user_interests


CREDENTIALS_FILE = "credentials.json"
INTERESTS_FILE = "interests.json"

MIN_FAVORITES = 100

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Interest generator",
        description="Generates medium tag interest from the favorites of top uploaders"
    )
    parser.add_argument("-p", "--pages", default=1, help="The amount of pages to look for users in. Each page contains 320 users (at least 1 second per user)")
    args = parser.parse_args()

    e621 = e621Client(CREDENTIALS_FILE)
    
    interests = {}

    total_users = 0
    for i in range(int(args.pages)):
        users = e621.get_top_users(i)
        for user in tqdm(users, f" Analyzing page {i + 1} of users", unit=" users", total=len(users)):
            favs = e621.get_favorites(user["id"], 0)

            if len(favs) < MIN_FAVORITES:
                continue

            user_interests = get_user_interests(favs)
            
            for tag in user_interests:
                if not tag in interests:
                    interests[tag] = 0.0
            
            for tag in interests:
                user_interest_in_tag = user_interests[tag] if tag in user_interests else 0.0
                interests[tag] = (interests[tag] * total_users + user_interest_in_tag) / (total_users + 1)

            total_users += 1
    
    with open(INTERESTS_FILE, 'w') as f:
        json.dump(interests, f, indent=4)






