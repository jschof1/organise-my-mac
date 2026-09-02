#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set default path to Downloads if no argument is provided
TARGET_PATH="${1:-$HOME/Downloads}"

# Expand the path (in case it contains ~)
TARGET_PATH="${TARGET_PATH/#\~/$HOME}"

echo "=== Organise My Mac ==="
echo "Target folder: $TARGET_PATH"
echo "Starting organization process..."

# Run the Python script and pass the target path
echo "$TARGET_PATH" | python3 main.py

echo -e "\nPress Enter to exit..."
read 