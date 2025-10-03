@echo off
SETLOCAL

:: --- Configuration ---
:: Activate virtual environment. This assumes the venv exists.
:: The main run.bat script is responsible for creating it.
IF EXIST "venv\Scripts\activate.bat" (
    echo "Activating Python virtual environment..."
    call venv\Scripts\activate.bat
) ELSE (
    echo "Virtual environment not found. Please run 'run.bat' first to create it."
    exit /b 1
)

:: Set PROFILE to 'local' for development-specific settings (e.g., database path)
set "PROFILE=local"

echo "Running the show_searches script..."
:: Run the utility script
python scripts/capture_reponses.py

echo "Script finished."