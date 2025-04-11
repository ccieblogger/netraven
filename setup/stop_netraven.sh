#!/bin/bash

# NetRaven Services Stop Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$ROOT_DIR/.pids"

echo "Stopping NetRaven services..."

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "Stopping $service_name (PID $pid)..."
            kill $pid
            sleep 2
            # Force kill if still running
            if ps -p $pid > /dev/null; then
                echo "Force stopping $service_name..."
                kill -9 $pid
            fi
        else
            echo "$service_name is not running."
        fi
        rm "$pid_file"
    else
        echo "$service_name is not running."
    fi
}

# Only stop backend services
stop_service "scheduler"
stop_service "api"

echo "All NetRaven backend services stopped."
echo "To stop the frontend containers:"
echo "- Development environment: docker-compose down"
echo "- Production environment: docker-compose -f docker-compose.prod.yml down"
