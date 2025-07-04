from argparse import ArgumentParser
from e621_client import e621Client
from e621_wrapped import get_post_score
import json
import os


CREDENTIALS_FILE = "credentials.json"


if __name__ == "__main__":
    ##################
    # Initialization #
    ##################
    parser = ArgumentParser(
        prog="E621 Recommendation Engine",
        description="Finds posts that match your profile"
    )
    parser.add_argument("-u", "--user", required=True, help="The user_id to make the Wrapped for")
    parser.add_argument("-p", "--pages", default=10, help="The number of pages to look for posts in. Each page contains 320 posts (at least 1 second per page)")
    parser.add_argument("-s", "--score", default=6, help="Minimum score to recommend a post")
    parser.add_argument("-m", "--min_upvotes", default=100, help="Minimum upvote score of searched posts")
    parser.add_argument("-t", "--extra_tags", default="", help="Extra tags to be used on searched posts", nargs="*")
    parser.add_argument("-a", "--add_to_set", default="n", help="Adds posts gathered to a new set (y/n)")
    args = parser.parse_args()
    
    e621 = e621Client(CREDENTIALS_FILE)
    user_data = e621.get_user(args.user)
    user_name = user_data["name"]
    print(f"- Hi {user_name}! Let's look for some posts you might like...")

    if not os.path.exists(f"{user_name}_profile.json"):
        print(f"\n- Sorry, I couldn't find your profile <:3c")
        print("- Please make sure to run e621_wrapped.py before running this script :3")
        exit(0)
    with open(f"{user_name}_profile.json") as f:
        profile = json.load(f)

    if args.add_to_set == "y":
        if not "set" in profile:
            new_id = e621.create_set(f"{user_name} Wrapped Recommendations", f"{user_name}_wrapped_recommendations")
            if new_id == -1:
                exit(0)

            profile["set"] = {
                "id": new_id,
                "posts": {}
            }
    

    ###################
    # Recommend posts #
    ###################
    recommended_posts = profile["fav_dict"]
    if args.add_to_set == "y":
        recommended_posts.update(profile["set"]["posts"])
    max_score = 0

    for i in range(int(args.pages)):
        print(f"\n- Looking for posts in page {i + 1}... :3c\n")

        posts = e621.get_random_posts(int(args.min_upvotes), "+".join(args.extra_tags))
        recommended_ids = []
        for post in posts:
            if str(post["id"]) in recommended_posts:
                continue

            score, best_tags = get_post_score(post, profile["profile"], profile["weights"], profile["favorites"], True)
            if score >= int(args.score):
                recommended_posts[str(post["id"])] = True
                recommended_ids.append(post["id"])

                print(f"{str(int(score)) + ('*' if score > max_score and max_score != 0 else ''):3s}| https://e621.net/posts/{str(post['id']):10s} | {' '.join(best_tags)}")
                if score > max_score:
                    max_score = score
        
        if args.add_to_set == "y" and len(recommended_ids) > 0:
            e621.add_posts_to_set(profile["set"]["id"], recommended_ids)
            print("Added posts to set!")

    if args.add_to_set == "y":
        profile["set"]["posts"] = recommended_ids
        with open(f"{user_name}_profile.json", "w") as f:
            json.dump(profile, f, indent=4)




