#!/bin/sh
# This script orchestrates the startup of the application components.

# Exit immediately if a command exits with a non-zero status.
set -e

# Set PROFILE to 'local' for development-specific settings (e.g., database path)
export PROFILE=local

echo "Starting WallBot application (core + web)..."
# The Python app will start both the core bot and the web server.
exec python3 -m src.wallbot