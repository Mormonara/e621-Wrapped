from argparse import ArgumentParser
from e621_client import e621Client
from interest_generator import get_user_interests
from tqdm.auto import tqdm
import json
import csv
import matplotlib.pyplot as plt
import math
from PIL import Image, ImageDraw, ImageFont


CREDENTIALS_FILE = "credentials.json"
INTERESTS_FILE = "interests.json"
TAG_IMPLICATIONS_FILE = "data/tag_implications.csv"

MIN_PERCENT = 0.001
EXCLUDE_WORDS = ["male", "anthro", "female"]
RELATIVE_PRESENCE_CAP = 100
ALLOWED_FILE_TYPES = ["png", "jpg"]

def plot_tags(ax, tags, user_profile, override_enjoyment=None):
    """
        Plots the tags in the ax
    """
    presence = []
    relative_presence = []
    enjoyment = []
    new_tags = []
    for tag in tags:
        new_tags.append(str(tag).split(":")[-1])

        if not override_enjoyment is None:
            enjoyment.append(override_enjoyment[tag])
            continue

        presence.append(user_profile[tag]["presence"] if tag in user_profile else 0)
        relative_presence.append(user_profile[tag]["relative_presence"] if tag in user_profile else -1)
        enjoyment.append(user_profile[tag]["enjoyment"] if tag in user_profile else 0)
    tags = new_tags

    # Plot
    bars = ax.bar(tags, enjoyment, color='skyblue')
    if override_enjoyment is None:
        for idx, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{presence[idx] * 100:.1f}%", 
                    ha='center', va='bottom', fontsize=8, rotation=45)
            ax.text(bar.get_x() + bar.get_width() / 2, 0, f"{relative_presence[idx]:.1f}x", 
                    ha='center', va='bottom', fontsize=8, rotation=45)
    ax.tick_params(axis='x', labelrotation=90)


def draw_favorite(tag_name, user_profile, bb, img, first):
    """
        Given a bounding box, writes the name of the tag, its presence, and its relative presence
    """
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("fonts/liberation-fonts-ttf-2.1.5/LiberationSans-Bold.ttf", size=36 if first else 16)
    bold_font = ImageFont.truetype("fonts/liberation-fonts-ttf-2.1.5/LiberationSans-BoldItalic.ttf", size=26 if first else 14)

    text = tag_name.split(":")[1].replace("_", " ").capitalize()
    line_start_pos = 0
    for pos in range(len(text)):
        if text[pos] != " ":
            continue

        if pos - line_start_pos + 1 > 10:
            text = text[:pos] + '\n' + text[pos:]
            line_start_pos = pos + 1
    
    if len(text) > 32:
        text = text[:32] + "..."  

    x = int((bb[0] + bb[2]) / 2)
    y = int((bb[1] + bb[3]) / 2)
    draw.multiline_text(
        (x, y + 8),
        text=text,
        font=font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )

    h = (bb[3] - bb[1]) / 2
    draw.text(
        (bb[0] + h, bb[1] + 8),
        text=f"{user_profile[tag_name]['presence'] * 100:.1f}%",
        font=bold_font,
        fill=(38, 154, 255),
        anchor="mt",
        align="center"
    )
    draw.text(
        (bb[2] - h, bb[1] + 8),
        text=f"{min(999.9, user_profile[tag_name]['relative_presence']):.1f}x",
        font=bold_font,
        fill=(252, 191, 49),
        anchor="mt",
        align="center"
    )


def get_post_score(post, user_profile, weights, favorite_tag_categories, return_best_tags=False):
    score = 0

    post["clean_tags"] = []
    for topic in post["tags"]:
        for tag in post["tags"][topic]:
            post["clean_tags"].append(f"{topic}:{tag}")

    best_tags = []
    for i, favorites in enumerate(favorite_tag_categories):
        added_best_tag = False
        for tag in favorites:
            if tag in post["clean_tags"]:
                if not added_best_tag:
                    added_best_tag = True
                    best_tags.append(tag.split(":")[1])
                score += weights[i] * user_profile[tag]["enjoyment"]

    final_score = score / math.pow(len(post["clean_tags"]), 0.2) * (math.pow(post["score"]["total"], 0.1) if post["score"]["total"] > 0 else 0)
    if return_best_tags:
        return final_score, best_tags
    return final_score


if __name__ == "__main__":
    ##################
    # Initialization #
    ##################
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
    user_data = e621.get_user(args.user)
    user_name = user_data["name"]
    print(f"- Hi {user_name}! I'm generating your e621 Wrapped, so hang tight :3\n")
    
    ########################
    # Compute user profile #
    ########################
    # Get favorites
    favs = []
    fav_dict = {}
    for i in tqdm(range(int(args.pages)), "Getting favorites", unit=" pages", total=int(args.pages)):
        new_favs = e621.get_favorites(args.user, i)
        for fav in new_favs:
            favs.append(fav)
            fav_dict[fav["id"]] = True
        if len(new_favs) < 320:
            break
    
    print("\n- Got your favorites! Now just give me a moment to sort through them... <:3c")
    
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

    ###############
    # Tag pooling #
    ###############
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

    ####################
    # Building results #
    ####################
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
        if name in ["sound_warning", "conditional_dnp"]:
            continue
        
        favorite_artists.append(tag)
    
    # Build least favorite tags
    least_favorite_tags_dict = {}
    for tag in global_interests:
        word_excluded = False
        for word in EXCLUDE_WORDS:
            if word in tag:
                word_excluded = True
                break
        if word_excluded:
            continue

        least_favorite_tags_dict[tag] = global_interests[tag] - (user_profile[tag]["presence"] if tag in user_profile else 0)
    tags_by_least_favorite = sorted(least_favorite_tags_dict.keys(), key=lambda x: least_favorite_tags_dict[x], reverse=True)
    
    least_favorite_tags = []
    for tag in tags_by_least_favorite:
        split_tag = tag.split(":")
        category = split_tag[0]
        name = split_tag[1]

        if not category in ["general", "lore", "species"]:
            continue
        
        least_favorite_tags.append(tag)

    # Favorite post
    favorite_tag_categories = [favorite_tags, favorite_species, favorite_characters, favorite_artists]
    weights = [1.0, 1.0, 1.0, 1.0]
    for idx, favorites in enumerate(favorite_tag_categories):
        weights[idx] *= 1.0 / user_profile[favorites[0]]["enjoyment"]

    post_scores = {}
    
    for fav in favs:
        if fav["file"]["url"] is None:
            continue
        if not fav["file"]["url"].split(".")[-1] in ALLOWED_FILE_TYPES:
            continue
            
        post_scores[fav["id"]] = get_post_score(fav, user_profile, weights, favorite_tag_categories)
    
    post_by_scores = sorted(post_scores.keys(), key=lambda post: post_scores[post], reverse=True)

    saved_profile = {
        "profile": user_profile,
        "weights": weights, 
        "favorites": favorite_tag_categories,
        "fav_dict": fav_dict
    }

    with open(f"{user_name}_profile.json", "w") as f:
        json.dump(saved_profile, f, indent=4)
    print(f"- Saved your profile as {user_name}_profile.json :3\n")

    ######################
    # Generating Wrapped #
    ######################
    print("- And that's everything! Now just give me a moment to create your e621 Wrapped >:3c")

    wrapped = Image.new("RGBA", (1080, 1080))

    try:
        fav_post = e621.get_post_thumb(post_by_scores[0], 400)
        wrapped.paste(fav_post, (582, 608))
    except:
        pass

    try:
        user_pfp = e621.get_post_thumb(user_data["avatar_id"], 300)
        wrapped.paste(user_pfp, (30, 13))
    except:
        pass

    template = Image.open("template.png")
    wrapped.paste(template, (0, 0), template)

    favorites = [favorite_tags, favorite_species, favorite_artists, favorite_characters]
    bounding_boxes = [
        [(63, 451, 463, 541), (66, 556, 256, 626), (267, 556, 457, 626), (66, 639, 256, 709), (267, 639, 457, 709)],
        [(63, 801, 463, 891), (66, 906, 256, 976), (267, 906, 457, 976)],
        [(624, 111, 1024, 201), (627, 216, 817, 286), (828, 216, 1018, 285)],
        [(624, 387, 1024, 477), (627, 492, 817, 562), (828, 492, 1018, 562)],
    ]
    for f_idx, favorite in enumerate(favorites):
        for b_idx, bb in enumerate(bounding_boxes[f_idx]):
            draw_favorite(favorite[b_idx], user_profile, bb, wrapped, b_idx == 0)

    draw = ImageDraw.Draw(wrapped)

    fontsize = 36
    if len(user_name) > 11:
        fontsize = 24
    if len(user_name) > 18:
        fontsize=12

    font = ImageFont.truetype("fonts/liberation-fonts-ttf-2.1.5/LiberationSans-BoldItalic.ttf", size=fontsize)

    x = int((bb[0] + bb[2]) / 2)
    y = int((bb[1] + bb[3]) / 2)
    draw.text(
        (470, 65),
        text=user_name,
        font=font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )

    id_img = Image.new("RGBA", (1080, 1080))
    id_center = (1040, 805)
    draw = ImageDraw.Draw(id_img)
    id_font = ImageFont.truetype("fonts/liberation-fonts-ttf-2.1.5/LiberationSans-BoldItalic.ttf", size=36)
    draw.text(
        (id_center[0] - 200, id_center[1]),
        text=f"ID {post_by_scores[0]}",
        font=font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )
    id_img = id_img.rotate(270, center=(id_center[0] - 200, id_center[1]))
    id_img = id_img.transform(id_img.size, Image.AFFINE, (1, 0, -200, 0, 1, 0))
    wrapped.paste(id_img, (0, 0), id_img)

    wrapped.save(f"{user_name}.png")

    #############################
    # Plotting detailed results #
    #############################
    print(f"- Done! Your e621 Wrapped has been saved as {user_name}.png B3")

    favorites = [favorite_tags, favorite_species, favorite_characters, favorite_artists]
    titles = ["Favorite tags", "Favorite species", "Favorite characters", "Favorite artists", "Least favorite tags"]
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    for i in range(4):
        ax = axes[int(i / 3)][i % 3]
        plot_tags(ax, favorites[i][:25], user_profile)
        ax.set_title(titles[i])
        ax.set_ylabel("Enjoyment")
    
    extras = [least_favorite_tags, post_by_scores]
    titles = ["Least favorite tags", "Your likes in one post"]
    override_user_profile = [least_favorite_tags_dict, post_scores]
    ylabels = ["How much less present than the average", "Post score"]
    for i in range(2):
        ax = axes[int((i + 4) / 3)][(i + 4) % 3]
        plot_tags(ax, extras[i][:25], user_profile, override_user_profile[i])
        ax.set_title(titles[i])
        ax.set_ylabel(ylabels[i])

    plt.suptitle(f"{user_name}'s e621 Wrapped (detailed)")
    plt.tight_layout()
    plt.savefig(f"{user_name}_detailed.png")

    print(f"\n- Saved your detailed report as {user_name}_detailed.png :3")
    print(f"\n- So you're into {favorite_tags[0].split(':')[1].replace('_', ' ')}, huh... ;3\n")

        


