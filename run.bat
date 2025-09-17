@echo off
cd /d %~dp0
setlocal

if not exist venv\Scripts\activate.bat (
    echo "Creating virtual environment..."
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt

set PROFILE=dev

echo "Starting the application..."
python -m src.wallbot