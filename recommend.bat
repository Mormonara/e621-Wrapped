@echo off
setlocal enabledelayedexpansion

echo - Don't let the console window scare you ^<:3
echo - I'm setting things up so we can recommend some posts based on your profile :3
echo.

:: STEP 1: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo - Couldn't find a Python installation :o
    echo - Please install Python from https://www.python.org/downloads/
    echo - Opening download page in your browser...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: STEP 2: Create and activate virtual environment if it doesn't exist
if exist .venv (
    echo - Virtual environment already exists! Skipping creation and pip install.
) else (
    echo - Creating virtual environment... please wait a sec :3c
    python -m venv .venv
)

:: STEP 3: Activate virtual environment
call .venv\Scripts\activate.bat

:: STEP 4: Install requirements if venv was just created
if not exist .venv\Scripts\pip.exe (
    echo - Could not find pip in the virtual environment. Something went wrong.
    pause
    exit /b 1
)

if exist requirements.txt (
    if not exist .venv\installed.flag (
        echo - Installing requirements... ^>:3
        echo.
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        echo done > .venv\installed.flag
    )
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)

:: STEP 5: Ask user for ID
echo.
echo ### 
echo.
set /p USER_ID=- Enter your E621 user_id. That's the number that appears at the end of the URL to your user page: 
set /p PAGES=- Enter total number of pages to search in (try starting with 10): 
set /p STARS=- Enter the minimum amount of stars for a post to be recommended (this depends on user profile. Start with 6 and adjust until you like the posts that come out): 
set /p TAGS=- Add any extra tags to search for. The more suited to you they are, the more recommended posts will be found: 
set /p ADD=- Should we create a set in your profile to store these posts? (y/n) (This requires credentials.json. You should experiment with settings to make sure you like the generated posts before turning this on): 

:: STEP 6: Run the Python program
python e621_recommendation_engine.py -u %USER_ID% -p %PAGES% -s %STARS% -t "%TAGS%" -a %ADD%

pause