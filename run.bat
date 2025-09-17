@echo off
setlocal

REM Check if venv exists
if not exist venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    venv\Scripts\pip.exe install -r requirements.txt
    echo Setup complete.
)

set PROFILE=dev

echo Starting the application...
venv\Scripts\python.exe -m src.wallbot