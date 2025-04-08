#!/bin/bash

# Simple script to start the Vue/Vite frontend development server

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Navigate to the project root (one level up from setup)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found at $FRONTEND_DIR" >&2
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo "Error: package.json not found in $FRONTEND_DIR. Did you run 'npm install'?" >&2
    exit 1
fi

echo "Navigating to $FRONTEND_DIR..."
cd "$FRONTEND_DIR" || exit

echo "Starting frontend development server (npm run dev)..."
echo "Access the UI at the URL provided by Vite (usually http://localhost:5173)"
echo "Press Ctrl+C to stop the server."

# Execute the dev server command
npm run dev

# Optional: Capture exit code if needed
# exit_code=$?
# echo "Frontend dev server exited with code $exit_code"
# exit $exit_code
