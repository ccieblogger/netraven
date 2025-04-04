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

# Set environment variable to indicate we are running in a container
export NETRAVEN_CONTAINER=true

# Check if environment variables are set
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
    echo "ERROR: One or more required PostgreSQL environment variables are not set."
    echo "Required: POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB"
    exit 1
fi

# Check if database is already initialized before running init container
echo "Checking database connection and schema..."
if ! python -m scripts.db_check --postgres-only; then
    echo "Database connection failed or schema validation failed"
    echo "Running database initialization..."
    # Initialize database
    python -m netraven.scripts.init_container
    if [ $? -ne 0 ]; then
        echo "ERROR: Database initialization failed"
        exit 1
    fi
else
    echo "Database connection and schema validation successful"
fi

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