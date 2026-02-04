@echo off
REM Quick start script for Windows

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo WARNING: Please edit .env and add your CLAUDE_API_KEY
)

REM Run the server
echo Starting Sherlocke Homes API...
python -m app.main

pause
