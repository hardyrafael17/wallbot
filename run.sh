#!/bin/bash
set -e

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "The Python application will load variables from the .env file directly."
echo "Ensure your .env file exists and contains the BOT_TOKEN."

# Set PROFILE to 'local' for development-specific settings (e.g., database path)
export PROFILE=local

echo "Starting WallBot application (core + web)..."
# The Python app will start both the core bot and the web server.
exec python3 -m src.wallbot