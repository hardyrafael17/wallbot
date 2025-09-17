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

# Execute the main startup script
chmod +x ./start.sh
exec ./start.sh