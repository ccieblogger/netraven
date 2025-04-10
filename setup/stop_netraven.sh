#!/bin/bash

# NetRaven Services Stop Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$ROOT_DIR/.pids"

echo "Stopping NetRaven services..."

# Kill processes by finding their PIDs
api_pid=$(pgrep -f "uvicorn api.main:app")
scheduler_pid=$(pgrep -f "api.scheduler:main")
frontend_pid=$(pgrep -f "node.*vite")

# Kill also any orphaned Vite-related processes
esbuild_pid=$(pgrep -f "esbuild --service")

# Stop frontend
if [ ! -z "$frontend_pid" ]; then
  echo "Stopping frontend (PID $frontend_pid)..."
  kill -9 $frontend_pid
else
  echo "Frontend process not found."
fi

# Stop esbuild
if [ ! -z "$esbuild_pid" ]; then
  echo "Stopping esbuild (PID $esbuild_pid)..."
  kill -9 $esbuild_pid
else
  echo "Esbuild process not found."
fi

# Stop scheduler
if [ ! -z "$scheduler_pid" ]; then
  echo "Stopping scheduler (PID $scheduler_pid)..."
  kill -9 $scheduler_pid
else
  echo "Scheduler process not found."
fi

# Stop API
if [ ! -z "$api_pid" ]; then
  echo "Stopping api (PID $api_pid)..."
  kill -9 $api_pid
else
  echo "API process not found."
fi

# Additional check for any remaining Vite processes
additional_vite_pids=$(pgrep -f "node.*vite")
if [ ! -z "$additional_vite_pids" ]; then
  echo "Stopping additional Vite processes (PIDs $additional_vite_pids)..."
  kill -9 $additional_vite_pids
fi

echo "All NetRaven services stopped."
