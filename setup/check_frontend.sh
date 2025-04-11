#!/bin/bash

# Get directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking frontend container status...${NC}"

# Check if the container is running
if docker ps | grep -q "netraven-frontend-dev"; then
    echo -e "${GREEN}Container is running.${NC}"
else
    echo -e "${RED}Container is not running!${NC}"
    echo -e "${YELLOW}Checking if it exited...${NC}"
    
    if docker ps -a | grep -q "netraven-frontend-dev"; then
        echo -e "${RED}Container exists but is not running. Checking logs:${NC}"
        docker logs netraven-frontend-dev
    else
        echo -e "${RED}Container does not exist!${NC}"
    fi
fi

# Check if the frontend port is responding
echo -e "${YELLOW}Checking if frontend is accessible...${NC}"
if curl -s --head --fail http://localhost:5173 > /dev/null; then
    echo -e "${GREEN}Frontend is accessible at http://localhost:5173${NC}"
else
    echo -e "${RED}Frontend is not accessible!${NC}"
fi

# Basic troubleshooting steps
echo -e "${YELLOW}Troubleshooting steps:${NC}"
echo -e "1. Make sure the Vite config has host: '0.0.0.0' in the server options"
echo -e "2. Check for errors in the container logs: docker logs netraven-frontend-dev"
echo -e "3. Try rebuilding the container: docker-compose build frontend && docker-compose up -d"
echo -e "4. Check if ports are properly exposed: docker-compose ps"

# Make executable
chmod +x "$ROOT_DIR/setup/check_frontend.sh"
