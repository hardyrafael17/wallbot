@echo off
SETLOCAL

:: --- Configuration ---
:: Activate virtual environment
IF EXIST "venv\Scripts\activate.bat" (
    echo "Activating Python virtual environment..."
    call venv\Scripts\activate.bat
) ELSE (
    echo "Creating virtual environment..."
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo "Installing dependencies..."
pip install -r requirements.txt

:: The Python application will load variables from the .env file directly.
:: Ensure your .env file exists and contains the BOT_TOKEN.

:: Set PROFILE to 'local' for development-specific settings (e.g., database path)
set "PROFILE=local"

echo "Starting WallBot application (core + web)..."
:: The Python app will start both the core bot and the web server.
python -m src.wallbot