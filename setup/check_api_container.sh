#!/bin/bash

# NetRaven API Container Test Script
# This script tests the status and functionality of the containerized API service

set -e  # Exit on any errors

# Directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Environment detection
ENV="dev"
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
    ENV="prod"
fi

if [ "$ENV" == "dev" ]; then
    CONTAINER_NAME="netraven-api-dev"
    DOCKER_COMPOSE_FILE="docker-compose.yml"
else
    CONTAINER_NAME="netraven-api-prod"
    DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
fi

# Print header
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}      API Container Connection Test       ${NC}"
echo -e "${GREEN}      Environment: ${ENV}                 ${NC}"
echo -e "${GREEN}==========================================${NC}"

# Check if the API container is running
echo -e "\n${YELLOW}Checking if API container is running...${NC}"
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}✓ API container is running.${NC}"
else
    echo -e "${RED}✗ API container is not running.${NC}"
    echo -e "${YELLOW}Checking if it exited...${NC}"
    
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}Container exists but is not running. Checking logs:${NC}"
        docker logs "$CONTAINER_NAME" | tail -n 20
        
        echo -e "${YELLOW}Starting API container...${NC}"
        if docker-compose -f "$DOCKER_COMPOSE_FILE" up -d api; then
            echo -e "${GREEN}✓ API container started successfully.${NC}"
            # Wait for container to be ready
            echo -e "${YELLOW}Waiting for API to be ready...${NC}"
            sleep 5
        else
            echo -e "${RED}✗ Failed to start API container. Check docker-compose configuration.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Container does not exist!${NC}"
        echo -e "${YELLOW}Building and starting API container...${NC}"
        
        if "$ROOT_DIR/setup/build_api_container.sh" ${ENV/dev/} ${ENV/prod/--env prod}; then
            echo -e "${GREEN}✓ API container built and started successfully.${NC}"
        else
            echo -e "${RED}✗ Failed to build and start API container.${NC}"
            exit 1
        fi
    fi
fi

# Check container health status
echo -e "\n${YELLOW}Checking API container health status...${NC}"
if docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "healthy"; then
    echo -e "${GREEN}✓ API container is healthy.${NC}"
else
    echo -e "${YELLOW}⚠ API container is not marked as healthy or health check is still running.${NC}"
    echo -e "${YELLOW}  Current status: $(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")${NC}"
    
    # Check last health check output
    echo -e "${YELLOW}Last health check output:${NC}"
    docker inspect --format='{{json .State.Health}}' "$CONTAINER_NAME" 2>/dev/null | jq -r '.Log[-1].Output' 2>/dev/null || echo "Unable to retrieve health check logs"
fi

# Check if the API is responding
echo -e "\n${YELLOW}Testing API health endpoint...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API health endpoint is responding.${NC}"
    
    # Check the health endpoint response
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo -e "${GREEN}  Response: $HEALTH_RESPONSE${NC}"
else
    echo -e "${RED}✗ API health endpoint is not responding.${NC}"
    echo -e "${YELLOW}  Checking API container logs for errors:${NC}"
    docker logs "$CONTAINER_NAME" --tail 20
fi

# Check API documentation
echo -e "\n${YELLOW}Testing API documentation endpoint...${NC}"
if curl -s -I http://localhost:8000/api/docs | grep -q "200 OK"; then
    echo -e "${GREEN}✓ API documentation is accessible.${NC}"
else
    echo -e "${RED}✗ API documentation is not accessible.${NC}"
fi

# Test database connectivity from the API
echo -e "\n${YELLOW}Checking database connectivity from API...${NC}"
DB_LOG=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -i "Database session configured" | tail -n 1)
if [[ -n "$DB_LOG" ]]; then
    echo -e "${GREEN}✓ API has connected to the database.${NC}"
    echo -e "${GREEN}  $DB_LOG${NC}"
else
    echo -e "${YELLOW}⚠ Could not find database connection log.${NC}"
    echo -e "${YELLOW}  This could be normal if logs are not verbose enough.${NC}"
fi

# Test Redis connectivity from the API
echo -e "\n${YELLOW}Checking Redis connectivity from API...${NC}"
REDIS_LOG=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -i "Connected to Redis" | tail -n 1)
if [[ -n "$REDIS_LOG" ]]; then
    echo -e "${GREEN}✓ API has connected to Redis.${NC}"
    echo -e "${GREEN}  $REDIS_LOG${NC}"
else
    echo -e "${YELLOW}⚠ Could not find Redis connection log.${NC}"
    echo -e "${YELLOW}  This could be normal if logs are not verbose enough.${NC}"
fi

# Print troubleshooting steps
echo -e "\n${YELLOW}Troubleshooting steps if issues were found:${NC}"
echo -e "1. Check container logs: docker logs $CONTAINER_NAME"
echo -e "2. Verify database is running: docker-compose -f $DOCKER_COMPOSE_FILE ps postgres"
echo -e "3. Verify Redis is running: docker-compose -f $DOCKER_COMPOSE_FILE ps redis"
echo -e "4. Try rebuilding the container: ./setup/build_api_container.sh --rebuild ${ENV/dev/} ${ENV/prod/--env prod}"
echo -e "5. Check environment variables: docker inspect $CONTAINER_NAME | grep NETRAVEN"

# Print summary
echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}     API Container Test Complete          ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}API is accessible at: http://localhost:8000${NC}"
echo -e "${GREEN}API documentation: http://localhost:8000/api/docs${NC}"
echo -e "${GREEN}==========================================${NC}"

exit 0 