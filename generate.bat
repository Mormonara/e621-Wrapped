@echo off
setlocal enabledelayedexpansion

echo - Don't let the console window scare you ^<:3
echo - I'm setting things up so we can generate your E621 Wrapped :3

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

:: STEP 2: Create virtual environment
echo - Creating virtual environment... please wait a sec :3c
python -m venv .venv

:: STEP 3: Activate virtual environment
call .venv\Scripts\activate.bat

:: STEP 4: Install requirements
if exist requirements.txt (
    echo - Installing requirements... ^>:3
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)

:: STEP 5: Ask user for ID
echo.
echo ###
echo.
set /p USER_ID=- Enter your E621 user_id. That's the number that appears at the end of the URL to your user page: 

:: STEP 6: Run the Python program
python e621_wrapped.py -u %USER_ID%

pause