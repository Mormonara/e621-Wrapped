#!/bin/bash

echo "- Don't let the console window scare you <:3"
echo "- I'm setting things up so we can generate your E621 Wrapped :3"
echo

# STEP 1: Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "- Couldn't find a Python installation :o"
    echo "- Please install Python from https://www.python.org/downloads/"
    echo "- Opening download page in your browser..."
    xdg-open https://www.python.org/downloads/ 2>/dev/null || open https://www.python.org/downloads/
    read -p "Press enter to exit..."
    exit 1
fi

# STEP 2: Create virtual environment if it doesn't exist
if [ -d .venv ]; then
    echo "- Virtual environment already exists! Skipping creation and pip install."
else
    echo "- Creating virtual environment... please wait a sec :3c"
    python3 -m venv .venv
fi

# STEP 3: Activate virtual environment
source .venv/bin/activate

# STEP 4: Install requirements only if not already installed
if [ -f requirements.txt ]; then
    if [ ! -f .venv/installed.flag ]; then
        echo "- Installing requirements... >:3"
        echo
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
        echo "done" > .venv/installed.flag
    fi
else
    echo "[WARNING] requirements.txt not found. Skipping dependency installation."
fi

# STEP 5: Ask user for ID
echo
echo "###"
echo
read -p "- Enter your E621 user_id. That's the number that appears at the end of the URL to your user page: " USER_ID

# STEP 6: Run the Python program
python3 e621_wrapped.py -u "$USER_ID"

read -p "Press enter to exit..."
