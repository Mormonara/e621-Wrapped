# 🦊 e621 Wrapped

This is a Python application for generating overviews of a user's favorite tags in e621 based on public favorite data.

## ⚙ Quickstart

### Requirements

To run this application, you will need to have Python 3.10 installed. It can be downloaded from https://www.python.org/downloads/

### Running

You can download this repository by clicking **Download ZIP** on the **Code** dropdown (green button on the top right). Unzip it wherever you want

To generate your e621 Wrapped, simply double click `generate.bat` on **Windows** or run `generate.sh` on **Linux**. This will generate a terminal window that will install the required libraries and ask you for your USER_ID (the numbers that appear at the end of your profile's url). Finally, it will generate the files `username.png`, which contains your e621 Wrapped, and `username_detailed.png`, which contains a more thorough report, with information on the top 25 contenders for each category

### Authentication

If you'd like to access your own private favorite information, you can optionally create a `credentials.json` file in the main directory that contains the following:

```json
{
    "username": "YOUR USER NAME HERE",
    "api_key": "YOUR API KEY HERE",
    "user_agent": "e621Wrapped/1.0 (by mormonara on e621)"
}
```

## 👀 Recommendation engine

After running `e621_wrapped.py`, the program will generate a profile that will be store as `username_profile.json`. With this, you can run `recommend.bat` on Windows or `recommend.sh` on Linux to search through a selection of tags and extract non-favorited posts that match with your profile. If you have authentication set up, you also have the option to have the program automatically create a private set in your profile and add the recommended posts to it, so you can more easily sort through them

## ❓ How it works

e621 Wrapped uses public favorite information to create a user profile and compares it to the average user

### Creating an average user profile

The file `interests.json` stores information about the **presence** of each tag in the average user's favorites. That is, what percentage of posts in their favorites contain this tag. This file was generated from the public favorites of a couple thousand users, starting from e621's top users. You can run `interest_generator.py` with a custom amount of pages using the option `-p total_pages` to regenerate the average user profile, but keep in mind that this will take at least 6 minutes per page due to e621's API's limits.

### Computing a user's profile

When you run `e621_wrapped.py`, a user_profile is generated that, for each tag present in your favorites, computes the values in the following table. This user_profile is used only to generate your Wrapped and is not stored.

|Field|Description|
|-|-|
|**presence**|What percentage of your favorite posts contain this tag|
|**relative_presence**|How many times more present this tag is in your favorites than in the average user|
|**enjoyment**|The harmonic mean of **presence** and the (capped at 100 and normalized) **relative presence**. This means that the higher and the more balanced the two other fields are, the higher **enjoyment** be|

Tags are then sorted in order of **enjoyment**. We also use tag implications to consider only the most enjoyed tag from a collection of similar ones. This process uses the tag implication data in `data/tag_implications.csv`, which was downloaded from the [db_export](https://e621.net/db_export/) on 06/30/2025. Feel free to replace it for the newest version. Just make sure to give it the same name.

### Finding posts that match your profile

Posts in your favorites are scored on the 4 major categories presented in the Wrapped in such a way that they are balanced to have similar weight. For each category. For each post, its score...

- Is the sum of the enjoyment (balanced by major category) of each tag it contains
- Gets a penalty based on the amount of tags it has (so as not to favor bloated posts)
- Gets a bonus based on score (so as to favor posts other people have enjoyed)

## 📝 Credits

This was made by... me! I'm @mormonara on Twitter and Bsky (visit at your own risk 🔞). Please don't remove the link on the bottom left of the images generated with this program so that other people can find this repository. Otherwise, feel free to do whatever you want with the generated images
