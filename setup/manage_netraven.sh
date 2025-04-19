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
    echo "Usage: $0 [start|stop|reset-db|reset-all|install-deps|switch-env|restart] [dev|release|service]"
    echo ""
    echo "Commands:"
    echo "  start         Start all NetRaven services"
    echo "  stop          Stop all NetRaven services"
    echo "  reset-db      Reset only the database (drop and recreate PostgreSQL)"
    echo "  reset-all     Reset all containers and volumes (complete reinstall)"
    echo "  install-deps  Install all dependencies (Python, Node.js, Redis)"
    echo "  switch-env    Switch between dev and release environments"
    echo "  restart       Restart individual services (nginx, frontend, api, backend, redis, postgres)"
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

# Map release to prod for Docker Compose files
DOCKER_ENV="$ENVIRONMENT"
if [ "$ENVIRONMENT" == "release" ]; then
    DOCKER_ENV="prod"
fi

# Set environment-specific variables
if [ "$COMMAND" != "restart" ]; then
    if [ "$ENVIRONMENT" == "dev" ]; then
        export APP_ENV="dev"
        export DATABASE_URL="postgresql+psycopg2://netraven:netraven@postgres:5432/netraven"
        export VITE_API_URL="http://localhost:8000"
        export DOCKER_COMPOSE_FILE="docker-compose.yml"
    else
        export APP_ENV="release"
        export DATABASE_URL="postgresql+psycopg2://netraven:netraven@postgres:5432/netraven"
        export VITE_API_URL="https://api.netraven.com"
        export DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
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

# Helper to run the seed script in the API container (dev only)
run_seed_script() {
    if [ "$ENVIRONMENT" == "dev" ]; then
        # Run the seed script, capture output and status
        output=$(docker exec netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run python scripts/seed_dev_data.py" 2>&1)
        status=$?
        if [ $status -ne 0 ]; then
            echo -e "${RED}Seeding development database with test data failed!${NC}"
            echo "$output"
        fi
    fi
}

# Reset database
reset_db() {
    echo -e "${RED}Resetting the database...${NC}"
    read -p "Are you sure you want to reset the database? This will delete all data. (yes/no): " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        echo "Database reset cancelled."
        exit 0
    fi

    # Stop and remove PostgreSQL container 
    echo -e "${YELLOW}Stopping and removing PostgreSQL container...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE stop postgres
    docker-compose -f $DOCKER_COMPOSE_FILE rm -f postgres

    # Remove PostgreSQL volume to completely clear data
    echo -e "${YELLOW}Removing PostgreSQL volume to clear all data...${NC}"
    docker volume rm $(docker volume ls -q | grep postgres-data) || true
    
    # Start PostgreSQL container fresh
    echo -e "${YELLOW}Starting fresh PostgreSQL container...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d postgres
    
    # Wait for PostgreSQL to be ready
    echo -e "${YELLOW}Waiting for PostgreSQL to initialize...${NC}"
    max_attempts=15
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec netraven-postgres pg_isready -U netraven > /dev/null 2>&1; then
            echo -e "${GREEN}PostgreSQL is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}PostgreSQL failed to start. Check the logs with 'docker logs netraven-postgres'.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}PostgreSQL container reset successfully.${NC}"
    
    # Check if other services are running, if not ask if user wants to start them
    API_RUNNING=false
    if docker ps | grep -q netraven-api; then
        API_RUNNING=true
        echo -e "${YELLOW}API container is already running. You may need to restart it to connect to the new database.${NC}"
        read -p "Would you like to restart the API container? (yes/no): " restart_api
        if [[ "$restart_api" == "yes" ]]; then
            echo -e "${YELLOW}Restarting API container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart api
        fi
    else
        read -p "API container is not running. Would you like to start it? (yes/no): " start_api
        if [[ "$start_api" == "yes" ]]; then
            echo -e "${YELLOW}Starting API container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE up -d api
            API_RUNNING=true
        fi
    fi
    
    # If API was started/restarted, wait for it to be ready
    if [[ "$API_RUNNING" == true && ("$restart_api" == "yes" || "$start_api" == "yes") ]]; then
        echo -e "${YELLOW}Waiting for API to initialize...${NC}"
        max_attempts=15
        attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -s http://localhost:8000/health > /dev/null; then
                echo -e "${GREEN}API service is ready.${NC}"
                break
            fi
            attempt=$((attempt+1))
            echo -e "${YELLOW}Waiting for API to be ready (attempt $attempt/$max_attempts)...${NC}"
            sleep 5
        done
        
        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}API service failed to start. Check the logs with 'docker logs netraven-api-${DOCKER_ENV}'.${NC}"
        fi
    fi
    
    # Check if other containers are running
    REDIS_RUNNING=false
    FRONTEND_RUNNING=false
    NGINX_RUNNING=false
    
    if docker ps | grep -q netraven-redis; then
        REDIS_RUNNING=true
    fi
    
    if docker ps | grep -q netraven-frontend; then
        FRONTEND_RUNNING=true
    fi
    
    if docker ps | grep -q netraven-nginx; then
        NGINX_RUNNING=true
    fi
    
    # Ask to start other containers if they're not running
    if [[ "$REDIS_RUNNING" == false || "$FRONTEND_RUNNING" == false || "$API_RUNNING" == false || "$NGINX_RUNNING" == false ]]; then
        read -p "Some containers are not running. Would you like to start them all? (yes/no): " start_all
        if [[ "$start_all" == "yes" ]]; then
            if [[ "$REDIS_RUNNING" == false ]]; then
                echo -e "${YELLOW}Starting Redis container...${NC}"
                docker-compose -f $DOCKER_COMPOSE_FILE up -d redis
            fi
            
            if [[ "$API_RUNNING" == false ]]; then
                echo -e "${YELLOW}Starting API container...${NC}"
                docker-compose -f $DOCKER_COMPOSE_FILE up -d api
            fi
            
            if [[ "$FRONTEND_RUNNING" == false ]]; then
                echo -e "${YELLOW}Starting Frontend container...${NC}"
                docker-compose -f $DOCKER_COMPOSE_FILE up -d frontend
            fi
            
            if [[ "$NGINX_RUNNING" == false ]]; then
                echo -e "${YELLOW}Starting Nginx container...${NC}"
                docker-compose -f $DOCKER_COMPOSE_FILE up -d nginx
            fi
            
            echo -e "${GREEN}All containers started.${NC}"
        fi
    fi
    
    echo -e "${GREEN}Database reset completed.${NC}"
    run_seed_script
    print_status_table
}

# Reset all containers
reset_all() {
    echo -e "${RED}Resetting all containers and data...${NC}"
    read -p "Are you sure you want to reset all containers? This will delete all data. (yes/no): " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        echo "Reset cancelled."
        exit 0
    fi

    # Stop and remove all containers
    echo -e "${YELLOW}Stopping and removing all containers...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE down
    
    # Remove volumes to completely clear data
    echo -e "${YELLOW}Removing volumes to clear all data...${NC}"
    docker volume rm $(docker volume ls -q | grep postgres-data) || true
    docker volume rm $(docker volume ls -q | grep redis-data) || true
    
    # Start all containers fresh
    echo -e "${YELLOW}Starting all containers fresh...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    docker-compose -f $DOCKER_COMPOSE_FILE up -d worker
    
    # Wait for PostgreSQL to be ready
    echo -e "${YELLOW}Waiting for PostgreSQL to initialize...${NC}"
    max_attempts=15
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec netraven-postgres pg_isready -U netraven > /dev/null 2>&1; then
            echo -e "${GREEN}PostgreSQL is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 5
    done
    
    # Wait for API to be ready
    echo -e "${YELLOW}Waiting for API to initialize...${NC}"
    max_attempts=15
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}API service is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for API to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 5
    done
    
    # Wait for Nginx to be ready
    echo -e "${YELLOW}Waiting for Nginx to initialize...${NC}"
    max_attempts=10
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost/health > /dev/null; then
            echo -e "${GREEN}Nginx service is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for Nginx to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 3
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}Nginx service failed to start. Check the logs with 'docker logs netraven-nginx-${DOCKER_ENV}'.${NC}"
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}API service failed to start. Check the logs with 'docker logs netraven-api-${DOCKER_ENV}'.${NC}"
    else
        echo -e "${GREEN}All containers reset and started successfully.${NC}"
        echo -e "${GREEN}Application is accessible at http://localhost/${NC}"
        echo -e "${GREEN}API documentation is available at http://localhost/docs${NC}"
        run_seed_script
        print_status_table
    fi
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting NetRaven services for ${ENVIRONMENT} environment...${NC}"

    # Start Docker Compose services (Redis, PostgreSQL, API, Worker)
    echo -e "${YELLOW}Starting containerized services (Redis, PostgreSQL, API, Worker)...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d redis postgres api worker

    # Check if PostgreSQL is up and running
    echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
    max_attempts=10
    attempt=0
    POSTGRES_CONTAINER="netraven-postgres"
    if [ "$ENVIRONMENT" == "release" ]; then
        POSTGRES_CONTAINER="netraven-postgres-prod"
    fi
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec $POSTGRES_CONTAINER pg_isready -U netraven > /dev/null 2>&1; then
            echo -e "${GREEN}PostgreSQL is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 3
    done

    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}PostgreSQL failed to start. Check the logs with 'docker logs $POSTGRES_CONTAINER'.${NC}"
        exit 1
    fi

    # Check if API is up and running
    echo -e "${YELLOW}Verifying API connection...${NC}"
    max_attempts=10
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}API service is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for API to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 3
    done

    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}API service failed to start. Check the logs with 'docker logs netraven-api-${DOCKER_ENV}'.${NC}"
    fi

    # Start other backend services that aren't containerized yet
    "$ROOT_DIR/setup/start_netraven.sh"

    # Start Frontend via Docker Compose
    echo -e "${YELLOW}Starting frontend container...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d frontend
    
    # Start Nginx container
    echo -e "${YELLOW}Starting Nginx container...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d nginx
    
    # Check if Nginx is up and running
    echo -e "${YELLOW}Verifying Nginx connection...${NC}"
    max_attempts=5
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost/health > /dev/null; then
            echo -e "${GREEN}Nginx service is ready.${NC}"
            break
        fi
        attempt=$((attempt+1))
        echo -e "${YELLOW}Waiting for Nginx to be ready (attempt $attempt/$max_attempts)...${NC}"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}Nginx service failed to start. Check the logs with 'docker logs netraven-nginx-${DOCKER_ENV}'.${NC}"
    fi

    echo -e "${GREEN}NetRaven services started.${NC}"
    
    run_seed_script
    print_status_table
    if [ "$ENVIRONMENT" == "dev" ]; then
        echo -e "${GREEN}Application is accessible at http://localhost/${NC}"
        echo -e "${GREEN}API documentation is available at http://localhost/docs${NC}"
    else
        echo -e "${GREEN}Application is accessible at https://netraven.com/${NC}"
        echo -e "${GREEN}API documentation is available at https://netraven.com/docs${NC}"
    fi
}

# Stop services
stop_services() {
    echo -e "${YELLOW}Stopping NetRaven services...${NC}"

    # Stop backend services that aren't containerized yet
    "$ROOT_DIR/setup/stop_netraven.sh"

    # Stop Docker Compose services (including frontend, Redis, PostgreSQL, API)
    echo -e "${YELLOW}Stopping Docker Compose services...${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE down

    echo -e "${GREEN}NetRaven services stopped.${NC}"
}

# Restart individual services
restart_service() {
    local service=$1

    case "$service" in
        nginx)
            echo -e "${YELLOW}Restarting Nginx container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart nginx
            echo -e "${GREEN}Nginx container restarted.${NC}"
            echo -e "${GREEN}Application is accessible at http://localhost/${NC}"
            ;;
        frontend)
            echo -e "${YELLOW}Restarting frontend container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart frontend
            echo -e "${GREEN}Frontend container restarted.${NC}"
            ;;
        api)
            echo -e "${YELLOW}Restarting API container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart api
            echo -e "${GREEN}API container restarted.${NC}"
            ;;
        backend)
            echo -e "${YELLOW}Restarting backend service...${NC}"
            "$ROOT_DIR/setup/stop_netraven.sh"
            "$ROOT_DIR/setup/start_netraven.sh"
            echo -e "${GREEN}Backend service restarted.${NC}"
            ;;
        redis)
            echo -e "${YELLOW}Restarting Redis container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart redis
            echo -e "${GREEN}Redis container restarted.${NC}"
            ;;
        postgres)
            echo -e "${YELLOW}Restarting PostgreSQL container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart postgres
            # Wait for PostgreSQL to be ready again
            echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
            POSTGRES_CONTAINER="netraven-postgres"
            if [ "$ENVIRONMENT" == "release" ]; then
                POSTGRES_CONTAINER="netraven-postgres-prod"
            fi
            while ! docker exec $POSTGRES_CONTAINER pg_isready -U netraven > /dev/null 2>&1; do
                echo -n "."
                sleep 1
            done
            echo ""
            echo -e "${GREEN}PostgreSQL container restarted.${NC}"
            ;;
        worker)
            echo -e "${YELLOW}Restarting worker container...${NC}"
            docker-compose -f $DOCKER_COMPOSE_FILE restart worker
            echo -e "${GREEN}Worker container restarted.${NC}"
            ;;
        *)
            echo -e "${RED}Invalid service: $service. Use 'nginx', 'frontend', 'api', 'backend', 'redis', 'postgres', or 'worker'.${NC}"
            exit 1
            ;;
    esac
}

# Switch environment
switch_env() {
    echo -e "${YELLOW}Switching to $ENVIRONMENT environment...${NC}"
    export APP_ENV="$ENVIRONMENT"
    
    # Stop services in the old environment
    stop_services
    
    # Update environment variable for Docker Compose file
    if [ "$ENVIRONMENT" == "dev" ]; then
        export DOCKER_COMPOSE_FILE="docker-compose.yml"
    else
        export DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
    fi
    
    echo -e "${GREEN}Environment switched to $ENVIRONMENT.${NC}"
    echo -e "${YELLOW}You can now start services in the $ENVIRONMENT environment.${NC}"
}

# Print a summary table of container and HTTP status
print_status_table() {
    local services=(postgres redis api frontend nginx worker)
    local containers=(netraven-postgres netraven-redis netraven-api-dev netraven-frontend-dev netraven-nginx-dev netraven-worker-dev)
    local http_urls=("" "" "http://localhost:8000/health" "http://localhost:5173" "http://localhost/health" "")
    local statuses=()
    local details=()
    local all_healthy=true

    printf "\n+-----------+----------+-----------------------------+\n"
    printf "| %-9s | %-8s | %-27s |\n" "Service" "Status" "Details"
    printf "+-----------+----------+-----------------------------+\n"

    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local container="${containers[$i]}"
        local url="${http_urls[$i]}"
        local health="unknown"
        local http_status=""
        local detail=""

        # Check container health (if healthcheck exists)
        if docker inspect --format='{{.State.Health.Status}}' $container &>/dev/null; then
            health=$(docker inspect --format='{{.State.Health.Status}}' $container)
        else
            # Fallback: check if running
            if docker ps | grep -q $container; then
                health="running"
            else
                health="not running"
            fi
        fi

        # Check HTTP endpoint if applicable
        if [ -n "$url" ]; then
            if curl -s --max-time 2 "$url" > /dev/null; then
                http_status="HTTP: OK"
            else
                http_status="HTTP: not responding"
                all_healthy=false
            fi
            detail="$http_status"
        else
            detail="Ready"
        fi

        # Color status
        local color="$GREEN"
        if [ "$health" != "healthy" ] && [ "$health" != "running" ]; then
            color="$RED"
            all_healthy=false
        elif [ -n "$http_status" ] && [ "$http_status" != "HTTP: OK" ]; then
            color="$YELLOW"
        fi

        printf "| %-9s | %b%-8s%b | %-27s |\n" "$service" "$color" "$health" "$NC" "$detail"
    done
    printf "+-----------+----------+-----------------------------+\n"

    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}All containers are up and healthy. Application is accessible at http://localhost/${NC}"
    else
        echo -e "${RED}Some services are not healthy or not responding. Check logs with: docker ps; docker logs <container>${NC}"
    fi
}

# Process commands
case "$COMMAND" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    reset-db)
        reset_db
        ;;
    reset-all)
        reset_all
        ;;
    install-deps)
        install_deps
        ;;
    switch-env)
        switch_env
        ;;
    restart)
        if [ "$#" -lt 2 ]; then
            echo -e "${RED}Missing service name. Usage: $0 restart [nginx|frontend|api|backend|redis|postgres|worker]${NC}"
            exit 1
        fi
        SERVICE=$2
        restart_service "$SERVICE"
        ;;
    *)
        usage
        ;;
esac

exit 0
