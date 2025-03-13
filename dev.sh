#!/bin/bash

# Ensure script is executable: chmod +x dev.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== NetRaven Development Environment ===${NC}"

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" != *"venv"* ]]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate virtual environment. Make sure venv exists.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Virtual environment already activated.${NC}"
fi

# Check if Docker is running
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    echo -e "${RED}If using Docker Desktop with WSL, make sure WSL integration is enabled.${NC}"
    exit 1
fi

# Start Docker Compose services
echo -e "${GREEN}Starting NetRaven services...${NC}"
docker compose up --build

# Deactivate virtual environment when done (this will only run if the user presses Ctrl+C)
echo -e "${GREEN}Shutting down...${NC}" 