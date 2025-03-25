#!/bin/bash
set -e

echo "Starting NetRaven initialization..."

# Setup NetMiko logs directory without trying to change permissions
NETMIKO_LOG_DIR=${NETMIKO_LOG_DIR:-/app/data/netmiko_logs}
if [ ! -d "$NETMIKO_LOG_DIR" ]; then
    echo "Creating NetMiko logs directory: $NETMIKO_LOG_DIR"
    mkdir -p "$NETMIKO_LOG_DIR"
else
    echo "NetMiko logs directory already exists: $NETMIKO_LOG_DIR"
fi

# Initialize database
python -m netraven.scripts.init_container

# Run database migrations if needed (placeholder for future use)
# alembic upgrade head

# Start the application
if [ "$SERVICE_TYPE" = "api" ]; then
    echo "Starting API service..."
    exec uvicorn netraven.web:app --host 0.0.0.0 --port 8000
elif [ "$SERVICE_TYPE" = "gateway" ]; then
    echo "Starting Gateway service..."
    GATEWAY_PORT=${GATEWAY_PORT:-8001}
    exec gunicorn -w 4 -b 0.0.0.0:$GATEWAY_PORT "netraven.gateway.api:app"
else
    echo "Unknown service type: $SERVICE_TYPE"
    echo "Valid options are 'api' or 'gateway'"
    exit 1
fi 