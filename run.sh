#!/bin/bash

# Set PROFILE for development
export PROFILE=dev

# Check for python3
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 is not installed. Please install python3 and try again."
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for BOT_TOKEN environment variable
if [ -z "$BOT_TOKEN" ]; then
    read -p "Please enter your Telegram BOT_TOKEN: " BOT_TOKEN
    export BOT_TOKEN
fi

# Run the application
echo "Starting the application..."
python3 -m src.wallbot