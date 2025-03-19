#!/bin/bash

# This script builds and runs NetRaven in test mode following best practices

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building and running NetRaven in test mode...${NC}"

# Parse command line arguments
TEST_PATH="tests"

while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            TEST_PATH="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if docker and docker-compose are available
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker and Docker Compose are required to run NetRaven.${NC}"
    exit 1
fi

# Make sure we're in the project root directory
cd "$(dirname "$0")/.."

# Stop any running containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Remove existing images to ensure we rebuild with test dependencies
echo -e "${YELLOW}Removing existing images to ensure clean build...${NC}"
docker rmi netraven-api:latest netraven-device_gateway:latest 2>/dev/null || true

# Create test artifacts directory
mkdir -p test-artifacts
chmod 777 test-artifacts

# Set environment variables for test mode
export NETRAVEN_ENV=test

# Build and start the containers with clean build
echo -e "${YELLOW}Building containers with test dependencies...${NC}"
docker-compose build

echo -e "${YELLOW}Starting containers in test mode...${NC}"
docker-compose up -d

# Check if containers started successfully
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to start containers.${NC}"
    exit 1
fi

# Check container health
echo -e "${YELLOW}Waiting for services to become healthy...${NC}"
for i in $(seq 1 30); do
    if docker ps | grep "netraven-api" | grep -q "healthy"; then
        echo -e "${GREEN}API service is healthy!${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}Timeout waiting for API service to become healthy.${NC}"
        echo -e "${RED}Check container logs with: docker-compose logs api${NC}"
        exit 1
    fi
    
    echo -n "."
    sleep 2
done

# Verify environment variables
echo -e "${YELLOW}Verifying test environment variables...${NC}"
CONTAINER_ENV=$(docker exec netraven-api-1 env | grep NETRAVEN_ENV)
if [[ "$CONTAINER_ENV" != *"test"* ]]; then
    echo -e "${RED}Error: Container is not in test mode. Found: $CONTAINER_ENV${NC}"
    echo -e "${RED}Please check your docker-compose configuration.${NC}"
    exit 1
fi
echo -e "${GREEN}Container environment is correctly set to test mode.${NC}"

# Provide helpful command examples
echo -e "\n${GREEN}NetRaven test environment is running!${NC}"
echo -e "\n${GREEN}Example commands to run tests:${NC}"
echo -e "${YELLOW}Run all tests:${NC}"
echo "docker exec netraven-api-1 python -m pytest"
echo -e "${YELLOW}Run UI tests:${NC}"
echo "docker exec netraven-api-1 python -m pytest tests/ui -v"
echo -e "${YELLOW}Run specific test:${NC}"
echo "docker exec netraven-api-1 python -m pytest tests/ui/test_flows/test_login.py -v"
echo -e "${YELLOW}View test artifacts:${NC}"
echo "ls -la test-artifacts/"
echo -e "${YELLOW}To view logs: docker-compose logs -f api${NC}"
echo -e "${YELLOW}To stop the environment: docker-compose down${NC}" 