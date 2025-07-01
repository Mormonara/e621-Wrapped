from argparse import ArgumentParser
from e621_client import e621Client
from interest_generator import get_user_interests
from tqdm.auto import tqdm
import json
import csv
import matplotlib.pyplot as plt
import math


CREDENTIALS_FILE = "credentials.json"
INTERESTS_FILE = "interests.json"
RESULT_FILE = "Wrapped.png"
TAG_IMPLICATIONS_FILE = "data/tag_implications.csv"

MIN_PERCENT = 0.001
EXCLUDE_WORDS = ["male", "anthro", "female"]
RELATIVE_PRESENCE_CAP = 100

def plot_tags(ax, tags, user_profile):
    presence = []
    relative_presence = []
    enjoyment = []
    new_tags = []
    for tag in tags:
        new_tags.append(tag.split(":")[1])
        presence.append(user_profile[tag]["presence"])
        relative_presence.append(user_profile[tag]["relative_presence"])
        enjoyment.append(user_profile[tag]["enjoyment"])
    tags = new_tags

    # Plot
    bars = ax.bar(tags, enjoyment, color='skyblue')
    for idx, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{presence[idx] * 100:.2f}%", 
                ha='center', va='bottom', fontsize=8, rotation=45)
        ax.text(bar.get_x() + bar.get_width() / 2, 0, f"{relative_presence[idx]:.2f}x", 
                ha='center', va='bottom', fontsize=8, rotation=45)
    ax.tick_params(axis='x', labelrotation=45)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="E621 Wrapped",
        description="Generates a review of your favorite tags!"
    )
    parser.add_argument("-u", "--user", required=True, help="The user_id to make the Wrapped for")
    parser.add_argument("-p", "--pages", default=10, help="The max amount of pages to look for favorites in. Each page contains 320 users (at least 1 second per page)")
    args = parser.parse_args()

    with open(INTERESTS_FILE, "r") as f:
        global_interests = json.load(f)
    
    e621 = e621Client(CREDENTIALS_FILE)
    
    # Get favorites
    favs = []
    for i in tqdm(range(int(args.pages)), "Getting favorites", unit=" pages", total=int(args.pages)):
        new_favs = e621.get_favorites(args.user, i)
        for fav in new_favs:
            favs.append(fav)
        if len(new_favs) < 320:
            print("Stopping early! Got all favorites")
            break
    
    # Compute interests
    user_interests = get_user_interests(favs)

    # Compute profile
    user_profile = {}
    min_percent = min(global_interests.values())
    for tag in user_interests:
        # Exclude criteria
        if user_interests[tag] < MIN_PERCENT:
            continue

        word_excluded = False
        for word in EXCLUDE_WORDS:
            if word in tag:
                word_excluded = True
                break
        if word_excluded:
            continue

        # Calculates profile
        # percent - How present this tag is in the users favorites
        # relative_presence - How present this tag is in the users favorites compared to the global average
        # enjoyment - The harmonic mean between the capped normalized relative_presence and the presence
        user_profile[tag] = {
            "presence": user_interests[tag],
            "relative_presence": user_interests[tag] / (global_interests[tag] if tag in global_interests else min_percent)
        }
        user_profile[tag]["enjoyment"] = 2 / (1 / (min(RELATIVE_PRESENCE_CAP, user_profile[tag]["relative_presence"]) / RELATIVE_PRESENCE_CAP) + 1 / user_profile[tag]["presence"])

    tags_by_enjoyment = sorted(user_profile.keys(), key=lambda tag: user_profile[tag]["enjoyment"], reverse=True)
    tags_by_presence = sorted(user_profile.keys(), key=lambda tag: user_profile[tag]["presence"], reverse=True)

    # Create tags dict
    with open(TAG_IMPLICATIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        implication_dict = {}
        for row in reader:
            if row["status"] == "active":
                if not row["consequent_name"] in implication_dict:
                    implication_dict[row["consequent_name"]] = []
                implication_dict[row["consequent_name"]].append(row["antecedent_name"])
    
    i = 0
    changed = True
    while changed:
        changed = False

        # If a <- b <- c, simplifies it to a <- b, c
        to_change = {}
        for tag in implication_dict:
            for implicator_tag in implication_dict[tag]:
                if implicator_tag in implication_dict:
                    to_change[implicator_tag] = tag
                
        if len(to_change) > 0:
            changed = True
        
        for tag in to_change:
            for implicator_tag in implication_dict[tag]:
                if not implicator_tag in implication_dict[to_change[tag]]:
                    implication_dict[to_change[tag]].append(implicator_tag)
            implication_dict[tag] = []

        to_delete = []
        for tag in implication_dict:
            if len(implication_dict[tag]) == 0:
                to_delete.append(tag)
        for tag in to_delete:
            del implication_dict[tag]

    tag_to_parent = {}
    for tag in implication_dict:
        tag_to_parent[tag] = tag
        for implicator_tag in implication_dict[tag]:
            tag_to_parent[implicator_tag] = tag

    with open("test2.json", 'w') as f:
        json.dump(tag_to_parent, f, indent=4)

    # Build favorite tags
    favorite_tags = []
    included_categories = {}
    for tag in tags_by_enjoyment:
        split_tag = tag.split(":")
        category = split_tag[0]
        name = split_tag[1]

        if not category in ["general", "lore"]:
            continue
        if name in tag_to_parent:
            if tag_to_parent[name] in included_categories:
                continue
            included_categories[tag_to_parent[name]] = True
        
        favorite_tags.append(tag)

    # Build favorite species
    favorite_species = []
    included_categories = {}
    for tag in tags_by_enjoyment:
        split_tag = tag.split(":")
        category = split_tag[0]
        name = split_tag[1]

        if not category == "species":
            continue
        if name in tag_to_parent:
            if tag_to_parent[name] in included_categories:
                continue
            included_categories[tag_to_parent[name]] = True
        
        favorite_species.append(tag)
    
    # Build favorite characters
    favorite_characters = []
    for tag in tags_by_enjoyment:
        split_tag = tag.split(":")
        category = split_tag[0]
        name = split_tag[1]

        if not category == "character":
            continue
        
        favorite_characters.append(tag)
    
    # Build favorite artists
    favorite_artists = []
    for tag in tags_by_enjoyment:
        split_tag = tag.split(":")
        category = split_tag[0]
        name = split_tag[1]

        if not category == "artist":
            continue
        
        favorite_artists.append(tag)
    
    # Plot

    favorites = [favorite_tags, favorite_species, favorite_characters, favorite_artists]
    titles = ["Favorite tags", "Favorite species", "Favorite characters", "Favorite artists"]
    fig, axes = plt.subplots(2, 2, figsize=(32, 16))
    for i in range(4):
        ax = axes[int(i / 2)][i % 2]
        plot_tags(ax, favorites[i][:25], user_profile)
        ax.set_title(titles[i])
    plt.tight_layout()
    plt.savefig("result.png")

    # Find your favorite post
    post_scores = {}
    for fav in tqdm(favs, "Looking for favorite post", unit=" posts", total=len(favs)):
        score = 0
        favorite_tag_categories = [favorite_tags, favorite_species, favorite_characters, favorite_artists]
        weights = [1.0, 1.0, 1.0, 1.0]
        for idx, favorite_tags in enumerate(favorite_tag_categories):
            weights[idx] *= 1.0 / user_profile[favorite_tags[0]]["enjoyment"]

        fav["clean_tags"] = []
        for topic in fav["tags"]:
            for tag in fav["tags"][topic]:
                fav["clean_tags"].append(f"{topic}:{tag}")

        for i, favorite_tags in enumerate(favorite_tag_categories):
            for tag in favorite_tags:
                if tag in fav["clean_tags"]:
                    score += weights[i] * user_profile[tag]["enjoyment"]

        post_scores[fav["id"]] = score / math.pow(len(fav["clean_tags"]), 0.1) * (math.pow(fav["score"]["total"], 0.1) if fav["score"]["total"] > 0 else 0)
    
    post_by_scores = sorted(post_scores.keys(), key=lambda post: post_scores[post], reverse=True)
    print(post_by_scores[:10])
        


