#!/bin/bash

echo "- Don't let the console window scare you < :3"
echo "- I'm setting things up so we can recommend some posts based on your profile :3"
echo

# STEP 1: Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "- Couldn't find a Python installation :o"
    echo "- Please install Python from https://www.python.org/downloads/"
    echo "- Opening download page in your browser..."
    xdg-open https://www.python.org/downloads/ || open https://www.python.org/downloads/
    exit 1
fi

# STEP 2: Create virtual environment if it doesn't exist
if [ -d ".venv" ]; then
    echo "- Virtual environment already exists! Skipping creation and pip install."
else
    echo "- Creating virtual environment... please wait a sec :3c"
    python -m venv .venv
fi

# STEP 3: Activate virtual environment
# shellcheck source=/dev/null
source .venv/bin/activate

# STEP 4: Install requirements if venv was just created
if [ ! -f ".venv/bin/pip" ]; then
    echo "- Could not find pip in the virtual environment. Something went wrong."
    exit 1
fi

if [ -f "requirements.txt" ]; then
    if [ ! -f ".venv/installed.flag" ]; then
        echo "- Installing requirements... >:3"
        echo
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        echo done > .venv/installed.flag
    fi
else
    echo "[WARNING] requirements.txt not found. Skipping dependency installation."
fi

# STEP 5: Ask user for ID
echo
echo "###"
echo
read -rp "- Enter your E621 user_id. That's the number that appears at the end of the URL to your user page: " USER_ID
read -rp "- Enter total number of pages to search in (try starting with 10): " PAGES
read -rp "- Enter the minimum amount of stars for a post to be recommended (this depends on user profile. Start with 6 and adjust until you like the posts that come out): " STARS
read -rp "- Add any extra tags to search for. The more suited to you they are, the more recommended posts will be found: " TAGS
read -rp "- Should we create a set in your profile to store these posts? (y/n) (This requires credentials.json. You should experiment with settings to make sure you like the generated posts before turning this on): " ADD

# STEP 6: Run the Python program
python e621_recommendation_engine.py -u "$USER_ID" -p "$PAGES" -s "$STARS" -t "$TAGS" -a "$ADD"
