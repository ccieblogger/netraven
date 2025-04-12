#!/bin/bash

# NetRaven Management Script
# This script manages the startup, teardown, and environment switching for NetRaven.

set -e  # Exit on any errors
set -u  # Treat unset variables as errors
set -o pipefail  # Fail if any command in a pipeline fails

# Directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.pids"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print usage
usage() {
    echo "Usage: $0 [start|stop|reset-db|install-deps|switch-env|restart] [dev|release|service]"
    echo ""
    echo "Commands:"
    echo "  start         Start all NetRaven services"
    echo "  stop          Stop all NetRaven services"
    echo "  reset-db      Reset the database (drop and recreate tables)"
    echo "  install-deps  Install all dependencies (Python, Node.js, Redis)"
    echo "  switch-env    Switch between dev and release environments"
    echo "  restart       Restart individual services (frontend, backend, redis, postgres)"
    echo ""
    echo "Environment:"
    echo "  dev           Development environment"
    echo "  release       Release/Production environment"
    exit 1
}

# Check arguments
if [ "$#" -lt 1 ]; then
    usage
fi

COMMAND=$1

# For commands other than 'restart', treat the second argument as the environment
if [ "$COMMAND" != "restart" ]; then
    ENVIRONMENT=${2:-dev}

    # Validate environment
    if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "release" ]]; then
        echo -e "${RED}Invalid environment: $ENVIRONMENT. Use 'dev' or 'release'.${NC}"
        usage
    fi
fi

# Set environment-specific variables
if [ "$COMMAND" != "restart" ]; then
    if [ "$ENVIRONMENT" == "dev" ]; then
        export APP_ENV="dev"
        export DATABASE_URL="postgresql+psycopg2://netraven:netraven@postgres:5432/netraven"
        export VITE_API_URL="http://localhost:8000"
    else
        export APP_ENV="release"
        export DATABASE_URL="postgresql+psycopg2://netraven:netraven@postgres:5432/netraven"
        export VITE_API_URL="https://api.netraven.com"
    fi
fi

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Install dependencies
install_deps() {
    echo -e "${YELLOW}Installing dependencies...${NC}"

    # Install Poetry
    if ! command -v poetry &> /dev/null; then
        echo -e "${YELLOW}Installing Poetry...${NC}"
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH" # Ensure Poetry is in PATH
    fi

    # Install Python dependencies
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    poetry install

    # Install Node.js (if not installed)
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}Installing Node.js...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    # Install Node.js dependencies
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    cd "$ROOT_DIR"

    echo -e "${GREEN}Dependencies installed successfully.${NC}"
}

# Reset database
reset_db() {
    echo -e "${RED}Resetting the database...${NC}"
    read -p "Are you sure you want to reset the database? This will delete all data. (yes/no): " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        echo "Database reset cancelled."
        exit 0
    fi

    echo -e "${YELLOW}Ensuring PostgreSQL container is running...${NC}"
    if ! docker ps | grep -q netraven-postgres; then
        echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
        docker-compose up -d postgres
        # Wait for PostgreSQL to be ready
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
        sleep 5
    fi

    # Drop and recreate schema using the containerized PostgreSQL
    echo -e "${YELLOW}Dropping and recreating database schema...${NC}"
    poetry run python "$ROOT_DIR/setup/dev_runner.py" --drop-schema
    poetry run python "$ROOT_DIR/setup/dev_runner.py" --create-schema

    echo -e "${GREEN}Database reset successfully.${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting NetRaven services...${NC}"

    # Start Docker Compose services (including Redis and PostgreSQL)
    echo -e "${YELLOW}Starting Docker containers (Redis, PostgreSQL)...${NC}"
    docker-compose up -d

    # Check if PostgreSQL is up and running
    echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
    max_attempts=10
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker exec netraven-postgres pg_isready -U netraven > /dev/null 2>&1; then
            echo -e "${GREEN}PostgreSQL is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 3
    done

    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}PostgreSQL failed to start. Check the logs with 'docker logs netraven-postgres'.${NC}"
        exit 1
    fi

    # Start API service
    "$ROOT_DIR/setup/start_netraven.sh"

    # Start Frontend
    echo -e "${YELLOW}Starting frontend development server...${NC}"
    cd "$FRONTEND_DIR"
    npm run dev &> "$LOG_DIR/frontend.log" &
    echo $! > "$PID_DIR/frontend.pid"
    cd "$ROOT_DIR"

    echo -e "${GREEN}NetRaven services started.${NC}"
}

# Stop services
stop_services() {
    echo -e "${YELLOW}Stopping NetRaven services...${NC}"

    # Stop backend services
    "$ROOT_DIR/setup/stop_netraven.sh"

    # Stop Docker Compose services (including frontend, Redis, and PostgreSQL)
    echo -e "${YELLOW}Stopping Docker Compose services...${NC}"
    docker-compose down

    echo -e "${GREEN}NetRaven services stopped.${NC}"
}

# Restart individual services
restart_service() {
    local service=$1

    case "$service" in
        frontend)
            echo -e "${YELLOW}Restarting frontend container...${NC}"
            docker-compose restart frontend
            echo -e "${GREEN}Frontend container restarted.${NC}"
            ;;
        backend)
            echo -e "${YELLOW}Restarting backend service...${NC}"
            "$ROOT_DIR/setup/stop_netraven.sh"
            "$ROOT_DIR/setup/start_netraven.sh"
            echo -e "${GREEN}Backend service restarted.${NC}"
            ;;
        redis)
            echo -e "${YELLOW}Restarting Redis container...${NC}"
            docker-compose restart redis
            echo -e "${GREEN}Redis container restarted.${NC}"
            ;;
        postgres)
            echo -e "${YELLOW}Restarting PostgreSQL container...${NC}"
            docker-compose restart postgres
            # Wait for PostgreSQL to be ready again
            echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
            while ! docker exec netraven-postgres pg_isready -U netraven > /dev/null 2>&1; do
                echo -n "."
                sleep 1
            done
            echo ""
            echo -e "${GREEN}PostgreSQL container restarted.${NC}"
            ;;
        *)
            echo -e "${RED}Invalid service: $service. Use 'frontend', 'backend', 'redis', or 'postgres'.${NC}"
            exit 1
            ;;
    esac
}

# Switch environment
switch_env() {
    echo -e "${YELLOW}Switching to $ENVIRONMENT environment...${NC}"
    export APP_ENV="$ENVIRONMENT"
    echo -e "${GREEN}Environment switched to $ENVIRONMENT.${NC}"
}

# Execute command
case "$COMMAND" in
    install-deps)
        install_deps
        ;;
    reset-db)
        reset_db
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        if [ "$#" -lt 2 ]; then
            echo -e "${RED}Please specify a service to restart (frontend, backend, redis, postgres).${NC}"
            usage
        fi
        restart_service "$2"
        ;;
    switch-env)
        switch_env
        ;;
    *)
        usage
        ;;
esac
