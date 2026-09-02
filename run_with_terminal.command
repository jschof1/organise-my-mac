#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the organiser script
./run_organiser.sh

# Keep the terminal window open
echo "Press Enter to exit..."
read 