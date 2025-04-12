#!/bin/bash

# Script to build and run the NetRaven API container

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Print header
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}       Build and Run API Container        ${NC}"
echo -e "${GREEN}==========================================${NC}"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Parse arguments
ENV="dev"
REBUILD=false

print_usage() {
    echo "Usage: $0 [-e|--env prod|dev] [-r|--rebuild]"
    echo "  -e, --env      Environment (dev or prod), default: dev"
    echo "  -r, --rebuild  Force rebuild of the container"
    exit 1
}

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -e|--env)
            ENV="$2"
            if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
                echo -e "${RED}Invalid environment: $ENV. Use 'dev' or 'prod'.${NC}"
                print_usage
            fi
            shift 2
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $key${NC}"
            print_usage
            ;;
    esac
done

# Set variables based on environment
if [ "$ENV" == "dev" ]; then
    DOCKERFILE="docker/api/Dockerfile.dev"
    CONTAINER_NAME="netraven-api-dev"
    ENV_FILE=".env.dev"
    COMPOSE_FILE="docker-compose.yml"
else
    DOCKERFILE="docker/api/Dockerfile.prod"
    CONTAINER_NAME="netraven-api-prod"
    ENV_FILE=".env.prod"
    COMPOSE_FILE="docker-compose.prod.yml"
fi

cd "$ROOT_DIR"

echo -e "${YELLOW}Building and running API container for ${ENV} environment...${NC}"

# Check if container is already running
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${YELLOW}Container $CONTAINER_NAME is already running. Stopping it...${NC}"
    docker stop "$CONTAINER_NAME" && docker rm "$CONTAINER_NAME"
fi

# Rebuild if requested
if [ "$REBUILD" = true ]; then
    echo -e "${YELLOW}Forcing rebuild of the API container...${NC}"
    docker-compose -f "$COMPOSE_FILE" build --no-cache api
fi

# Run the container
echo -e "${YELLOW}Starting API container...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d api

# Check if container started successfully
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}API container $CONTAINER_NAME is now running.${NC}"
    echo -e "${GREEN}API is accessible at http://localhost:8000${NC}"
    echo -e "${GREEN}API documentation is available at http://localhost:8000/api/docs${NC}"
else
    echo -e "${RED}Failed to start API container. Check docker logs.${NC}"
    echo -e "${YELLOW}View logs with: docker logs $CONTAINER_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}==========================================${NC}" 